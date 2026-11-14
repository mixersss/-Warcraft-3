"""Real level-40 class requests and objectives; unsupported travel is reported, never bypassed."""
import math
from classic_wire import Reader,ProtocolError
from adventure import talk_request,select_request,commit_request,mission_page

class Career:
    def __init__(self,world,send,role,life,regions):
        self.world,self.send,self.role,self.life,self.regions=world,send,role,life,regions
        self.quest=life.services['quests'][str(role['target_job'])]
        self.journal={};self.ready=False;self.context=None;self.pending=None;self.next_visit=0
        self.requests=self.accepted=self.delivered=self.timeouts=0;self.reason='ожидание уровня 40'
    def eligible(self):return self.world.own.values.get(0,0)>=40 and self.world.own.values.get(4)==self.role['first_job']
    def active(self):return self.eligible() and self.quest['journal'] in self.journal
    def needed_items(self):
        return {n['id'] for n in self.quest['needs'] if n['kind']==1
                and sum(i.count for i in self.world.bag.values() if i.identity==n['id'])<n['count']} if self.active() else set()
    def observe(self,command,payload,now):
        r=Reader(payload)
        if command==828:
            count=r.byte()
            if count>64:raise ProtocolError('Too many career missions')
            self.journal={r.short():r.byte() for _ in range(count)};self.ready=True
        elif command in (830,832):
            identity,state=r.short(),r.byte();self.journal[identity]=state
            if identity==self.quest['journal'] and command==832:
                self.accepted+=1;self.context=None;self.pending=None;self.next_visit=now+120
        elif command==831:
            identity=r.short();self.journal.pop(identity,None)
            if identity==self.quest['journal'] and self.pending==7:
                self.delivered+=1;self.context=None;self.pending=None;self.next_visit=now+120
        if not self.context:return False
        npc,stage,deadline=self.context
        if command==802 and stage=='talk':
            source,page=r.long(),r.byte();r.string_bytes();count=r.byte()
            if count>64:raise ProtocolError('Too many career functions')
            for _ in range(count):r.string_bytes()
            count=r.byte()
            if count>64:raise ProtocolError('Too many career offers')
            offers=[(r.string(),r.byte()) for _ in range(count)]
            if source==npc:
                index=next((i for i,(title,state) in enumerate(offers) if title==self.quest['title'] and state&3),None)
                if index is None:self.context=None;self.next_visit=now+300
                else:self.send(301,select_request(npc,index));self.context=npc,'select',now+8;self.requests+=1
            return True
        if command==827 and stage=='select':
            button,source,title,needs,choice,prizes=mission_page(payload)
            if source==npc and title==self.quest['title'] and button in (6,7) and not (choice==0 and len(prizes)>1):
                self.send(301,commit_request(npc,button));self.context=npc,'commit',now+8;self.pending=button;self.requests+=1
            else:self.context=None;self.next_visit=now+120
            return True
        return command in (801,802,803,827)
    def desired_models(self):
        if not self.active():return set()
        region=self.regions.get(self.world.map)
        if not region:return set()
        items=self.needed_items();level=self.world.own.values.get(0,1)
        kills={n['id'] for n in self.quest['needs'] if n['kind']==0}
        return {int(m) for m,r in region['farms'].items() if r['points'] and r['level']<=level and (int(m) in kills or items.intersection(r['drops']))}
    def goals(self):
        region=self.regions.get(self.world.map)
        return [p for m in self.desired_models() for p in region['farms'][str(m)]['points']] if region else []
    def tick(self,now,policy,safe,dialogue_busy=False):
        if not self.eligible():
            self.context=None;self.pending=None;return False
        if self.context:
            if now<self.context[2]:return True
            self.context=None;self.pending=None;self.timeouts+=1;self.next_visit=now+300
        if not safe or dialogue_busy or now<self.next_visit:return False
        if not self.ready:self.send(325,b'');self.next_visit=now+30;return False
        if self.active() and self.journal[self.quest['journal']]!=1 and not self.quest.get('talk'):
            self.reason='вторая профессия: сбор настоящих квестовых предметов'
            if not self.desired_models():self.reason='вторая профессия: нужна другая карта, магазин или остров'
            return False
        if self.world.map!=self.quest['map']:
            self.reason='вторая профессия: наставник на карте '+self.quest['map'];return False
        self.reason='вторая профессия: путь к наставнику'
        point=self.quest['position']
        npc=next((e for e in self.world.entities.values() if e.control in (2,3) and math.dist(e.position,point)<350),None)
        if npc and math.dist(policy.position(now),npc.position)<=220:
            self.send(301,talk_request(npc.identity));self.requests+=1;self.context=npc.identity,'talk',now+8;return True
        goal=policy.nav.nearest(point,6)
        if goal and policy.move_to(goal,now):return True
        self.reason='вторая профессия: путь к наставнику недоступен';self.next_visit=now+300;return False
    def summary(self):
        return {'state':self.reason,'journal_id':self.quest['journal'],'accepted_confirmed':self.accepted,'delivered_confirmed':self.delivered,
                'requests':self.requests,'timeouts':self.timeouts,'profession_confirmed':self.world.own.values.get(4)==self.role['target_job']}
