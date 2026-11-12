"""Local bounded chat and real-echo conversations; no external AI or transcripts."""
from collections import deque,OrderedDict
import random,json,re,threading
from pathlib import Path
from classic_wire import sequence


def say_request(text):
    encoded=text.encode('cp1251')
    if not encoded or len(encoded)>120 or any(ord(c)<32 for c in text):raise ValueError('Invalid local chat message')
    return sequence(encoded+b'\0')


class ChatBudget:
    def __init__(self,interval=15):
        self.interval=max(8,interval);self.next_send=0;self.lock=threading.Lock()
    def claim(self,now):
        with self.lock:
            if now<self.next_send:return False
            self.next_send=now+self.interval
            return True


PHRASES=json.loads((Path(__file__).resolve().parents[1]/'assets/chat-phrases.json').read_text(encoding='utf-8'))
CITIES={'garner':'Аргента','magicsea':'Шайтана','darkblue':'Ледяного города'}


class Social:
    def __init__(self,world,send,name,budget,seed,conversations=None):
        self.world,self.send,self.name,self.budget=world,send,name,budget
        self.rng=random.Random(str(seed)+':chat')
        self.next_send=0;self.next_reply=0;self.next_situation=None;self.pending=None
        self.replied=OrderedDict();self.sent=self.replies=self.dialogue_lines=0
        self.level=world.own.values.get(0);self.resting=False
        self.events=deque(maxlen=4);self.activity='hunt';self.role_label=None;self.last_event={}
        self.market=None;self.sale_offer=None;self.last_offer=-1e9;self.party_size=0;self.conversations=conversations

    def event(self,kind,now):
        if kind not in PHRASES or now-self.last_event.get(kind,-1e9)<120:return
        self.last_event[kind]=now;self.events.append((kind,now+45))

    def visible_humans(self):
        return [e for e in self.world.entities.values() if e.control==1 and e.identity!=self.world.own_id
                and e.name and not e.name.lower().startswith('bot')]

    def reply(self,words):
        has=lambda *terms:any(w in words for w in terms)
        if has('привет','здравствуй','здравствуйте','ку','hello','hi','qq','хай','дарова','здарова'):
            return 'greeting',self.rng.choice(PHRASES['reply_greeting'])
        if has('ансил','ансилы','руны','кель','ларек','ларёк','ларьки','торгуешь') and self.market:
            if self.market.state=='selling':return 'market','Мой ларёк открыт. Выставлены настоящие вещи из моей сумки.'
            return 'market','Коплю на экипировку, сохраняю нужные руны; заглядываю в ларьки по средствам.'
        if has('бот','bot','живой','настоящий'):return 'identity','Да, я местный игровой бот. Отвечаю простыми правилами :)'
        if has('уровень','лвл','level','левел'):return 'level',f'Сейчас у меня {self.world.own.values.get(0,1)} уровень.'
        if has('класс','профа','профессия','профессии'):return 'class',('Мой путь: '+self.role_label+'.') if self.role_label else 'Пока начинающий.'
        if has('где','город','место','куда'):return 'place',f'Я сейчас возле {CITIES.get(self.world.map,"города")}.'
        if has('пати','party','группа','группу','го','инст'):
            return 'party',(f'Сейчас нас в пати {self.party_size}.' if self.party_size>1 else 'Пока без пати, иногда собираюсь с местными ботами.')
        if has('шутка','пошути','анекдот','шутку'):return 'joke',self.rng.choice(PHRASES['joke']+PHRASES['joke_extra'])
        if has('помоги','помощь','умеешь','help','подскажи'):return 'help',self.rng.choice(PHRASES['reply_help'])
        if has('спасибо','спс','благодарю'):return 'thanks',self.rng.choice(PHRASES['reply_thanks'])
        if has('пока','бай','bye','увидимся'):return 'farewell',self.rng.choice(PHRASES['reply_farewell'])
        if has('устал','надоело','проиграл','умер','застрял'):return 'empathy',self.rng.choice(PHRASES['reply_empathy'])
        if has('куплю','продай','обмен','почем','почём'):return 'trade',('Покупаю нужное в ларьках, а лишнее выставляю сам. Личный обмен пока не умею.' if self.market else 'Пока могу предложить вещь в чате; автоматический обмен ещё не освоил.')
        if has('одежда','шмот','вещи'):return 'equipment','Надеваю подходящие вещи из своей сумки.'
        if has('квест','квесты','задание','задания'):return 'quest','Мои задания зависят от класса и текущего занятия; профессию не меняю случайно.'
        if has('фея','феи','мордо','джун'):return 'pets','Фей пока не выращиваю. Эта часть ещё впереди.'
        if has('корабль','корабли','море'):return 'sea','Морские походы ещё не освоил, пока хожу по суше.'
        if has('делаешь','занят','охотишься','фармишь'):
            return 'activity',('Отдыхаю в городе, проверяю припасы.' if self.activity=='city' else
                               'Восстанавливаюсь после боя.' if self.resting else
                               'Занимаюсь заданием.' if self.activity=='quest' else 'Пока охочусь на подходящих мобов.')
        if has('дела','настроение','норм','как'):return 'status',self.rng.choice(PHRASES['reply_status'])
        return None

    def hear(self, source, text, now):
        if len(text)>240 or any(ord(c)<32 for c in text):return
        if self.conversations and self.conversations.receive(self.name,source,text,now):return
        if source not in {e.identity for e in self.visible_humans()} or self.pending:return
        words=re.findall(r'[\w]+',text.casefold())
        addressed=self.name.casefold() in words
        if not addressed and any(re.fullmatch(r'bot[0-9a-f]{8}',w) for w in words):return
        if not addressed and not self.conversations:return
        result=self.reply(words)
        if not result:return
        intent,reply=result
        if self.replied.get((source,intent),0)>now:return
        if self.conversations and not self.conversations.claim_human(self.world.map,source,intent,now):return
        self.pending=(source,intent,reply,now+self.rng.uniform(2,5),now+20)

    def tick(self,now,resting,safe):
        if self.next_situation is None:self.next_situation=now+self.rng.uniform(90,180)
        humans=self.visible_humans()
        if self.conversations:
            self.conversations.register(self.name,self.world.map,self.world.own_id,self.world.position(now),now,
                                        safe and not self.pending and now>=self.next_send)
        level=self.world.own.values.get(0)
        if level and self.level and level>self.level:self.event('level',now)
        if resting and not self.resting:self.event('rest',now)
        while self.events and self.events[0][1]<now:self.events.popleft()
        event=self.events[0][0] if self.events else ('rest' if resting else self.activity)
        self.level,self.resting=level,resting
        if self.pending:
            source,intent,text,due,expires=self.pending
            if now>expires or source not in {e.identity for e in humans}:self.pending=None
            elif safe and now>=due and now>=self.next_reply and self.budget.claim(now):
                self.send(1,say_request(text));self.sent+=1;self.replies+=1;self.pending=None
                self.next_send=now+90;self.next_reply=now+12
                self.replied[(source,intent)]=now+300;self.replied.move_to_end((source,intent))
                while len(self.replied)>128:self.replied.popitem(last=False)
            return
        if self.conversations:
            visible={e.identity for e in self.world.entities.values() if e.control==1 and e.identity!=self.world.own_id}
            line=self.conversations.prepare(self.name,visible,now,safe)
            if line:
                token,text=line
                if self.budget.claim(now):
                    self.send(1,say_request(text));self.conversations.sent(self.name,token,now)
                    self.sent+=1;self.dialogue_lines+=1;self.next_send=now+90
                return
        if safe and humans and now>=self.next_send and now>=self.next_situation:
            if self.budget.claim(now):
                offer=self.sale_offer() if self.sale_offer and now-self.last_offer>=900 else None
                if offer and self.rng.random()<.25:text=offer;self.last_offer=now
                else:
                    if not self.events and self.rng.random()<.35:event='joke'
                    pool=PHRASES['joke']+PHRASES['joke_extra'] if event=='joke' else PHRASES[event]
                    text=self.rng.choice(pool)
                self.send(1,say_request(text));self.sent+=1
                if self.events:self.events.popleft()
                self.next_send=now+90;self.next_situation=now+self.rng.uniform(180,360)

    def summary(self):
        return {'messages_sent':self.sent,'simple_replies_sent':self.replies,
                'bot_dialogue_lines':self.dialogue_lines,'external_ai':False}
