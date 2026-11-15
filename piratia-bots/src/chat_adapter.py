"""Nonblocking chat above unchanged native client handlers; gameplay always runs."""
import hashlib,math,random,re
from collections import Counter,deque
from classic_wire import Reader,ProtocolError
from social import say_request
from contacts import private_request
from intent_recognizer import normalize
from dialogue_memory import DialogueManager
from chat_coordinator import SocialScheduler

TRADE_INTENTS={'buy','sell','exchange','price','discount','expensive','cheap','item_details','no_money','trade_stall','patchouli','parchment','trade_safety'}
MAPS={'garner':'Аскарон','magicsea':'Магический океан','darkblue':'Синий океан','jialebi':'Карибы'}

class PersonalityProfile:
    def __init__(self,name,data):
        seed=int.from_bytes(hashlib.sha256((name+':dialogue-profile').encode()).digest()[:8],'big')
        self.rng=random.Random(seed);self.values=data.profiles[seed%len(data.profiles)];self.kind=self.values['label']

class ResponseSelector:
    def __init__(self,data,profile):self.data,self.profile=data,profile;self.recent=deque(maxlen=12)
    def select(self,intent,state):
        rows=self.data.by_intent.get(intent,self.data.by_intent['unknown'])['responses']
        choices=[s for s in rows if s not in self.recent]
        if not choices:choices=[s for s in rows if s not in list(self.recent)[-2:]] or rows
        kind=self.profile.values['id']
        ranked=sorted(choices,key=len)
        preferred=ranked[:3] if kind=='quiet' else ranked[-3:] if kind in ('veteran','helper','explorer') else choices
        template=self.profile.rng.choice(preferred)
        self.recent.append(template);reply=template.format_map(state)
        if self.profile.values['spelling']=='casual' and intent in ('greeting','status','farewell'):reply=reply[:1].lower()+reply[1:]
        if self.profile.values['humour'] and intent=='greeting' and self.profile.rng.random()<.3:reply+=' :)'
        return reply

def fit(text,maximum=120):
    text=' '.join(str(text).split()).encode('cp1251',errors='replace').decode('cp1251')
    if len(text)<=maximum:return text
    return text[:maximum-3].rsplit(' ',1)[0]+'...'

def message_parts(text,maximum=230):
    cleaned=fit(text,min(240,maximum))
    result=[]
    while len(cleaned)>120:
        cut=max(cleaned.rfind('. ',0,120),cleaned.rfind('? ',0,120),cleaned.rfind('! ',0,120))
        if cut>=40:cut+=1
        else:cut=cleaned.rfind(' ',0,120)
        if cut<1:cut=120
        result.append(cleaned[:cut].strip());cleaned=cleaned[cut:].strip()
    if cleaned:result.append(cleaned)
    return result[:2]

class ChatAdapter:
    def __init__(self,world,policy,social,public,contacts,data,coordinator,send,name):
        self.world,self.policy,self.social,self.public,self.contacts=world,policy,social,public,contacts
        self.data,self.coordinator,self.send,self.name=data,coordinator,send,name
        self.profile=PersonalityProfile(name,data);self.selector=ResponseSelector(data,self.profile)
        self.memory=DialogueManager(data.settings);self.scheduler=SocialScheduler(coordinator)
        self.queue=deque(maxlen=8);self.next_send=0;self.muted_until=0
        self.intents=Counter();self.decisions=deque(maxlen=16);self.errors=Counter();self.sent=Counter();self.queued=0
        self.next_registration=0;self.last_tick=0
        self.quote_scopes={};self.batch_serial=0
        self.next_market_sample=0;self.sale=None;self.wanted=()
    def state(self):
        w=self.world;p=self.policy;own=w.own
        from professions import describe
        from builds import PROFILES
        target=w.entities.get(p.target)
        if p.resting:activity='Восстанавливаю HP и SP.'
        elif target and target.alive:activity='Сейчас веду бой.'
        elif p.market and p.market.state=='selling' and p.market.active_confirmed:activity='Торгую в открытом ларьке.'
        elif p.offmesh_since is not None:activity='Проверяю выход с кромки берега.'
        elif p.vendor and p.vendor.sale_target:activity='Иду продать лишние трофеи.'
        elif p.move_goal:activity='Иду по выбранному маршруту.'
        else:activity='Выбираю доступное занятие.'
        pos=w.position(self.last_tick)
        fairy=getattr(p,'petcare',None)
        has_fairy=bool(fairy and any(i.identity in (231,232,233,234,235,236,237,680,681) for i in w.bag.values()))
        return {'activity':activity,'map':MAPS.get(w.map,w.map),'position':f'{int(pos[0]//100)},{int(pos[1]//100)}',
                'level':own.values.get(0,1),'class':describe(own.values.get(4,0)),
                'build':PROFILES.get(getattr(own,'build_id',None),{}).get('label','пока без закреплённого билда'),
                'personality':self.profile.kind,
                'party_size':len(p.party.members) if p.party else 0,
                'quest':getattr(p.adventure,'reason','Сейчас не подтверждено активное задание.') if p.adventure else 'Нет подтверждённого задания.',
                'fairy':('Выращиваю фею только в '+fairy.stat+'.') if has_fairy else 'Своей феи в сумке пока нет.',
                'free_slots':max(0,(w.bag_capacity or 0)-len(w.bag)),
                'stall':'Ларёк открыт, товар подтверждён сервером.' if p.market and p.market.active_confirmed else 'Подтверждённого открытого ларька пока нет.'}
    def decision(self,channel,intent,reason):
        self.decisions.append({'channel':channel,'intent':intent,'reason':reason})
    def register(self,now):
        if now<self.next_registration:return
        self.next_registration=now+1;w=self.world;p=self.policy
        visible={e.identity for e in w.entities.values() if e.control==1 and e.identity!=w.own_id and math.dist(w.position(now),w.position(now,e.identity))<=2000}
        if now>=self.next_market_sample:
            self.next_market_sample=now+10;self.sale=None;self.wanted=()
            if p.market:
                self.wanted=tuple(p.market.needed())
                if p.market.active_confirmed and p.market.state=='selling':
                    for _,price,count,slot in p.market.stock:
                        item=w.bag.get(slot)
                        if item and item.valid and item.count>=count:self.sale=(item.identity,price);break
        self.coordinator.register(self.name,{'identity':w.own_id,'map':w.map,'position':w.position(now),'visible':visible,
            'ready':w.own.alive,'cash':w.own.values.get(8,0),'until':now+15,'sale':self.sale,'wanted':self.wanted})
    def observe(self,command,payload,now):
        try:return self._observe(command,payload,now)
        except OSError:raise
        except Exception as exc:
            self.errors[type(exc).__name__]+=1;self.decision('decode','unknown','chat error isolated from gameplay');return False
    def _observe(self,command,payload,now):
        self.last_tick=now;self.register(now);r=Reader(payload);identity=None
        if command==501:
            identity=r.long();text=r.string();r.end();entity=self.world.entities.get(identity)
            if not entity or entity.control!=1:return True
            if identity!=self.world.own_id and math.dist(self.world.position(now),self.world.position(now,identity))>2000:return True
            source=entity.name;channel='local'
        elif command in (5401,5402):source,text=r.string(),r.string();channel='trade' if command==5401 else 'world'
        elif command==5403:
            source,receiver,text=r.string(),r.string(),r.string();channel='private'
            if receiver.casefold()!=self.name.casefold():return False
        else:return False
        if command!=501:
            if len(r.data)-r.position==4:r.long()
            r.end()
        if source==self.name:
            self.coordinator.note_offer(self.name,channel,self.world.map,text,now)
            self.coordinator.note_question(self.name,channel,self.world.map,text,now)
            return False
        if not source or len(source.encode('cp1251',errors='replace'))>32 or len(text)>240 or any(ord(c)<32 for c in source+text):return True
        # Existing Alpha49 LFG owns its world/PM handshake, without a second answer.
        if text.startswith(('Ищу пати на кач,','Хочу в пати на кач,','Пати на кач:')):return False
        known_bot=source in self.coordinator.rows or source.casefold().startswith('bot')
        if known_bot:
            scene=self.coordinator.scene_for(self.name,channel,source,text,now)
            if not scene:return True
            if scene['finish']:return True
            state=self.state();topic=scene['topic']
            if scene.get('closing'):
                choices=self.data.scenes.get('topics',{}).get(topic,{}).get('closings',['Ладно, удачной игры!'])
                body=self.profile.rng.choice(choices)
            elif topic=='joke':body=self.humour_reaction()
            elif topic in self.data.scenes.get('topics',{}):
                body=self.profile.rng.choice(self.data.scenes['topics'][topic]['answers']).format_map(state)
            elif topic=='trade':
                body=self.policy.commerce.public_answer('цена ID'+str(scene['item']),now) if self.policy.commerce else 'Сейчас не готов обсуждать сделку.'
            elif topic=='level':body=f"У меня {state['level']} уровень. А у тебя какой?"
            elif topic=='fairy':body=state['fairy']+' А у тебя?'
            else:body=state['activity']+' А у тебя как дела?'
            reply=fit(scene['receiver']+', '+body,120)
            self.coordinator.prepare_scene_reply(scene['id'],reply)
            self.enqueue(channel,source,reply,now,scene=scene['id']);return True
        visible={e.identity for e in self.world.entities.values() if e.control==1 and
                 math.dist(self.world.position(now),self.world.position(now,e.identity))<=2000}
        from party_dialogue import response_to_offer
        contextual=response_to_offer(text)
        offer=self.coordinator.recent_offer(self.name,channel,self.world.map,text,now,visible) if contextual or channel=='private' else None
        numeric=bool(re.fullmatch(r'(?:я |мне |у меня )?\d{1,3}(?: (?:ур|уровень|лвл))?',normalize(text)))
        question=self.coordinator.recent_question(self.name,channel,self.world.map,now,visible) if numeric or normalize(text) in ('а ты','а у тебя') else None
        preferred=offer['owner'] if offer and contextual else question['owner'] if question else None
        if channel!='private' and not self.coordinator.elect(self.name,channel,self.world.map,identity or source,text,now,visible,preferred=preferred):return True
        intent=self.data.recognizer.recognize(text);self.intents[intent.name]+=1
        reply_channel='private' if channel=='world' and (contextual and offer or question) else channel
        context=self.memory.context(reply_channel,self.world.map,source,now)
        if offer and offer['owner']==self.name:context['recent_party_offer']=offer
        if question and question['owner']==self.name and numeric and question['topic']=='level':
            context['awaiting']='level';context['topic']='level'
            from intent_recognizer import Intent
            number=re.search(r'\d+',text)[0];intent=Intent('level_answer',.95,number);text=number
        if context['muted_until']>now and intent.name!='resume':return True
        self.memory.remember(context,'peer',text)
        if intent.name=='silence' or intent.name=='spam':
            context['muted_until']=now+900;self.muted_until=now+180
            self.queue=deque((r for r in self.queue if r['channel']!=channel or r['peer']!=source),maxlen=8)
        if intent.name=='resume':context['muted_until']=0;self.muted_until=0
        if channel=='trade' and intent.name not in TRADE_INTENTS:
            self.decision(channel,intent.name,'off-topic trade message ignored');return True
        reply=self.answer(intent,text,source,identity,context,reply_channel,now)
        if not reply:return True
        if not contextual and not context.get('party_dialogue') and channel in ('local','world','trade') and self.name.casefold() not in text.casefold() and self.profile.rng.random()>self.profile.values['response_chance']:
            if intent.name not in ('combat_help','party_invite','silence','resume','buy','sell','price'):
                self.decision(channel,intent.name,'personality declined unaddressed conversation');return True
        if channel=='local':reply=source+', '+reply
        self.enqueue(reply_channel,source,reply,now,context=context)
        self.decision(channel,intent.name,'reply queued; gameplay unchanged');return True
    def humour_reaction(self):
        positive=self.profile.values.get('humour') or self.profile.rng.random()<.65
        field='laughs' if positive else 'dry_reactions'
        return self.profile.rng.choice(self.data.scenes.get(field,('Хах, улыбнуло.' if positive else 'Эта шутка не зашла.',)))
    def answer(self,intent,text,source,identity,ctx,channel,now):
        name=intent.name;p=self.policy;clean=normalize(text)
        from party_dialogue import reply as party_reply
        offer=ctx.get('recent_party_offer')
        if offer and offer['until']<=now:ctx.pop('recent_party_offer',None);offer=None
        party_answer=party_reply(self,text,source,identity,ctx,now,offer)
        if party_answer is not None:return party_answer
        if name=='joke_offer':ctx['awaiting']='joke';ctx['joke_until']=now+60
        elif ctx.get('awaiting')=='joke' and now<ctx.get('joke_until',0) and name not in ('silence','resume','complaint','combat_help','buy','sell','price','party_invite'):
            ctx['awaiting']=None;return self.humour_reaction()
        if name=='reciprocal' and ctx.get('topic') in self.data.by_intent:name=ctx['topic']
        fact=self.data.item(text)
        if re.search(r'\bнп\b|нов\w* пергам',clean):fact=self.data.item_by_id.get(684)
        if 'пачкули' in clean:fact=self.data.item_by_id.get(1000)
        if fact:ctx['item']=fact['id']
        if name not in ('end_dialogue','change_topic','continue_topic','level_answer','silence','resume','unknown','repeat','agree','disagree','when','which','where','how_many'):
            ctx['topic']=name
        if name in ('end_dialogue','change_topic'):
            ctx.update(topic=None,awaiting=None,item=None,level=None)
        if name=='repeat' and ctx['last_reply']:return ctx['last_reply']
        if name=='continue_topic' and ctx['topic']:name=ctx['topic']
        if name=='level_answer':
            if ctx['awaiting']=='level':
                ctx['level']=int(clean);ctx['awaiting']=None
                gap=abs(ctx['level']-self.world.own.values.get(0,1))
                if ctx['topic']=='level':return f"У тебя {ctx['level']}, у меня {self.world.own.values.get(0,1)} уровень. А где обычно качаешься?"
                if ctx['topic']=='hunt_advice' and p.mob_knowledge:
                    nearby=p.mob_knowledge.summary(self.world.map,self.world.position(now),ctx['level'])['nearby_spawn_regions']
                    good=[r for r in nearby if ctx['level']-3<=r['level']<=ctx['level']+2 and r['territory']==0]
                    if good:
                        row=good[0];x,y=row['nearest_region_point']
                        return f"По справочнику: {row['name']}, ур.{row['level']}, {self.world.map} {x//100},{y//100}. Живой респ не подтверждён."
                return f"У меня {self.world.own.values.get(0,1)} уровень; разница {gap}. "+('Можно обсудить группу.' if gap<=3 else 'Лучше подобрать группу ближе к твоему уровню.')
            return 'Это твой уровень? Уточни, пожалуйста.'
        if name in ('hunt_advice','hunt_offer','hunt_help','party_search','healer_search','tank_search'):ctx['awaiting']='level'
        if name in ('buy','sell','exchange','price','discount','expensive','item_details'):
            if p.commerce:
                # Public channels never reuse private quotes or negotiation details.
                item_id=ctx['item']
                query=text if not item_id or fact else text+' ID'+str(item_id)
                if channel in ('world','trade'):return p.commerce.public_answer(query,now)
                if not item_id and name in ('price','discount','expensive','item_details'):return 'О какой вещи речь? Назови предмет или ID.'
                scope=self.quote_scopes.get(source.casefold())
                if scope and scope!=channel:
                    if p.direct_trade and p.direct_trade.busy:return 'Текущий обмен нужно сначала завершить или отменить.'
                    if p.direct_trade:p.direct_trade.quotes.pop(source.casefold(),None)
                if len(self.quote_scopes)>=64:self.quote_scopes.pop(next(iter(self.quote_scopes)))
                self.quote_scopes[source.casefold()]=channel
                return p.commerce.answer(source,query,now) or 'Назови товар или ID и цену, проверю условия.'
        if name=='party_invite' and intent.confidence>=.9 and p.party:
            before=p.party.invites;answer=p.party.request_name(source,now)
            if p.party.invites>before:ctx['promises']=(ctx['promises']+[{'kind':'party_invite','until':now+15,'state':'requested'}])[-4:]
            return answer
        if name=='friend_request' and intent.confidence>=.9 and self.contacts:
            return self.contacts.invite_friend(source,now)
        if name=='party_leave':return 'Самовольно чужую группу не распускаю. Свой выход согласую с текущим занятием.'
        if name=='combat_help' and intent.confidence>=.9 and channel=='local' and identity and p.helper:
            return p.helper.request(identity,now,p)
        if name in ('item','weapon','armour','materials') and fact:return fact['text']
        if name in ('merchant_location','bank_location','port_location','npc_location'):
            provider=self.social.npc_provider
            answer=provider(clean.split()) if provider else None
            if answer:return answer
        if name in ('forge','sockets','gems','fairy_breed','ship','crafting','cooking','mining','fishing','woodcutting'):
            provider=getattr(self.social,'mechanics_provider',None)
            answer=provider(clean.split()) if provider else None
            if answer:return answer
        return self.selector.select(name,self.state())
    def enqueue(self,channel,peer,text,now,context=None,scene=None):
        maximum=120 if scene is not None or channel in ('world','trade') else self.profile.values['max_bytes']
        parts=message_parts(text,maximum)
        if not parts:return
        if any(row['text']==parts[0] and row['channel']==channel and row['peer']==peer for row in self.queue):return
        while len(self.queue)+len(parts)>8:
            old=self.queue.popleft();self.queue=deque((r for r in self.queue if r.get('batch')!=old.get('batch')),maxlen=8)
        self.batch_serial+=1;due=now+self.profile.rng.uniform(1.2,3);expiry=now+(300 if channel in ('world','trade') else 45)
        for index,part in enumerate(parts):
            self.queue.append({'channel':channel,'peer':peer,'text':part,'due':due,'expires':expiry,'context':context,
                               'scene':scene,'batch':self.batch_serial,'last_part':index==len(parts)-1,'full_reply':' '.join(parts)})
        self.queued+=len(parts)
    def tick(self,now):
        try:self._tick(now)
        except OSError:raise
        except Exception as exc:self.errors[type(exc).__name__]+=1
    def _tick(self,now):
        self.last_tick=now;self.register(now)
        for key,context in self.memory.contexts.items():
            context['promises']=[promise for promise in context['promises'] if promise['until']>now]
            for promise in context['promises']:
                if promise['kind']=='party_invite' and self.policy.party and key[2] in {n.casefold() for n in self.policy.party.members}:
                    promise['state']='confirmed_by_native_team'
        self.queue=deque((row for row in self.queue if row['expires']>now and
                          (row['scene'] is None or self.coordinator.valid_scene(row['scene']))),maxlen=8)
        if not self.world.own.alive:return
        if not self.queue and now>=self.muted_until:
            scene=self.scheduler.prepare(self.name,now)
            if scene:
                text=fit(scene['text'],120);self.coordinator.prepare_scene_reply(scene['id'],text)
                self.enqueue(scene['channel'],scene['receiver'],text,now,scene=scene['id'])
        if not self.queue or now<self.next_send:return
        row=self.queue[0]
        if now<row['due']:return
        channel,text,peer=row['channel'],row['text'],row['peer']
        if channel=='local':
            visible=[e for e in self.world.entities.values() if e.name==peer and e.control==1 and
                     math.dist(self.world.position(now),self.world.position(now,e.identity))<=2000]
            if not visible:self.queue.popleft();return
        if not self.coordinator.claim_pair(self.name,peer,channel,now):return
        if channel in ('world','trade'):
            if not self.public.reply(channel,text,now):return
        else:
            if not self.social.budget.claim(now):return
            if channel=='private':self.send(6403,private_request(peer,text))
            else:self.send(1,say_request(text))
        self.queue.popleft();self.sent[channel]+=1;self.next_send=now+(3 if not row.get('last_part',True) else 15 if self.data.settings['intensity']=='quiet' else 6 if self.data.settings['intensity']=='normal' else 4)
        if row['context'] and row.get('last_part',True):
            row['context']['last_reply']=row.get('full_reply',text);self.memory.remember(row['context'],'self',row.get('full_reply',text))
        if row['scene'] is not None:self.coordinator.sent(row['scene'],self.name,text)
    def summary(self):return {'enabled':True,**self.data.summary(),'personality':self.profile.kind,'intensity':self.data.settings['intensity'],
                              'sent_by_channel':dict(self.sent),'recognized_intents':dict(self.intents),'isolated_errors':dict(self.errors),
                              'pending_replies':len(self.queue),'memory_contexts':len(self.memory.contexts),'decisions':list(self.decisions),
                              'scene_coordination':self.coordinator.summary(),'maximum_reply_parts':2,'transcripts_saved':False,'external_llm':False,'dialogue_never_pauses_actions':True}
