"""Local situational speech; no external AI, transcripts, or player-name logging."""
from collections import deque, OrderedDict
import random
import json
from pathlib import Path
import re
import threading
from classic_wire import sequence


def say_request(text):
    encoded = text.encode('cp1251')
    if not encoded or len(encoded) > 120 or any(ord(c) < 32 for c in text):
        raise ValueError('Invalid local chat message')
    return sequence(encoded + b'\0')


class ChatBudget:
    """Shared by every bot in this process, including eventual larger populations."""
    def __init__(self):
        self.next_send = 0
        self.lock = threading.Lock()

    def claim(self, now):
        with self.lock:
            if now < self.next_send:
                return False
            self.next_send = now + 15
            return True


PHRASES = json.loads((Path(__file__).resolve().parents[1]/'assets/chat-phrases.json').read_text(encoding='utf-8'))
CITIES = {'garner':'Аргента','magicsea':'Шайтана','darkblue':'Ледяного города'}


class Social:
    def __init__(self, world, send, name, budget, seed):
        self.world, self.send, self.name, self.budget = world, send, name, budget
        self.rng = random.Random(str(seed) + ':chat')
        self.next_send = 0
        self.next_situation = None
        self.pending = None
        self.replied = OrderedDict()
        self.sent = self.replies = 0
        self.level = world.own.values.get(0)
        self.resting = False
        self.events = deque(maxlen=4)
        self.activity = 'hunt'
        self.role_label = None
        self.last_event = {}

    def event(self, kind, now):
        if kind not in PHRASES or now-self.last_event.get(kind,-1e9)<120:
            return
        self.last_event[kind]=now
        self.events.append((kind,now+45))

    def visible_humans(self):
        return [e for e in self.world.entities.values() if e.control == 1
                and e.identity != self.world.own_id and e.name and not e.name.lower().startswith('bot')]

    def hear(self, source, text, now):
        if source not in {e.identity for e in self.visible_humans()} or self.pending:
            return
        if len(text) > 240 or any(ord(c) < 32 for c in text):
            return
        words = re.findall(r'[\w]+', text.casefold())
        if self.name.casefold() not in words or self.replied.get(source, 0) > now:
            return  # No broadcast greetings or bot-to-bot reply loops.
        if any(w in words for w in ('привет', 'здравствуй', 'ку', 'hello', 'hi')):
            reply = self.rng.choice(PHRASES['greeting'])
        elif 'бот' in words or 'bot' in words:
            reply = 'Да, я местный игровой бот :)'
        elif any(w in words for w in ('уровень', 'лвл', 'level')):
            reply = f'Сейчас у меня {self.world.own.values.get(0, 1)} уровень.'
        elif any(w in words for w in ('делаешь', 'занят', 'охотишься')):
            reply = ('Восстанавливаюсь после боя.' if self.resting else
                     'Занимаюсь заданием.' if self.activity=='quest' else
                     f'Охочусь возле {CITIES.get(self.world.map,"города")}.')
        elif any(w in words for w in ('класс','профа','профессия')):
            reply = ('Мой путь: '+self.role_label+'.') if self.role_label else 'Пока начинающий.'
        elif any(w in words for w in ('где','город','место')):
            reply = f'Я сейчас возле {CITIES.get(self.world.map,"города")}.'
        elif any(w in words for w in ('квест','квесты','задание')):
            reply = 'Выполняю начальные поручения и задания своей профессии.'
        elif any(w in words for w in ('пати','party','группа','инст')):
            reply = 'Пока охочусь один, в группу вступать ещё не умею.'
        elif any(w in words for w in ('одежда','шмот','вещи')):
            reply = 'Надеваю подходящие вещи из своей сумки.'
        elif any(w in words for w in ('пока','бай','bye')):
            reply = self.rng.choice(PHRASES['farewell'])
        elif 'спасибо' in words:
            reply = 'Удачи :)'
        else:
            return
        self.pending = (source, reply, now + self.rng.uniform(2, 5), now + 20)

    def tick(self, now, resting, safe):
        if self.next_situation is None:
            self.next_situation = now + self.rng.uniform(90, 180)
        humans = self.visible_humans()
        level = self.world.own.values.get(0)
        if level and self.level and level>self.level:self.event('level',now)
        if resting and not self.resting:self.event('rest',now)
        while self.events and self.events[0][1]<now:self.events.popleft()
        event = self.events[0][0] if self.events else ('rest' if resting else self.activity)
        self.level, self.resting = level, resting
        if self.pending:
            source, text, due, expires = self.pending
            if now > expires or source not in {e.identity for e in humans}:
                self.pending = None
            elif safe and now >= due and now >= self.next_send and self.budget.claim(now):
                self.send(1, say_request(text))
                self.sent += 1
                self.replies += 1
                self.pending = None
                self.next_send = now + 90
                self.replied[source] = now + 300
                self.replied.move_to_end(source)
                while len(self.replied) > 128:
                    self.replied.popitem(last=False)
            return
        if safe and humans and now >= self.next_send and now >= self.next_situation:
            if self.budget.claim(now):
                self.send(1, say_request(self.rng.choice(PHRASES[event])))
                self.sent += 1
                if self.events:self.events.popleft()
                self.next_send = now + 90
                self.next_situation = now + self.rng.uniform(180, 360)

    def summary(self):
        return {'messages_sent': self.sent, 'simple_replies_sent': self.replies,
                'external_ai': False}
