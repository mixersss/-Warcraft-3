"""Stable 75/12.5/12.5 home preference and normal, paid NPC city teleportation."""
import math
from classic_wire import Reader,ProtocolError
from adventure import talk_request
from town import function_request

CITIES={'garner':'Argent City','magicsea':'Shaitan City','darkblue':'Icicle City'}
BIRTHPLACES=dict(CITIES,darkblue='Icicle Castle')
TELEPORTERS={'garner':(218700,277600),'magicsea':(91816,356229),'darkblue':(132304,54403)}
TRAINER_MAP={1:'garner',4:'garner',2:'darkblue',5:'magicsea'}

def home_city_for(index):
    return 'garner' if (index-1)%8<6 else 'magicsea' if (index-1)%8==6 else 'darkblue'

class CityTravel:
    def __init__(self,world,send,index,role):
        self.world,self.send,self.role=world,send,role
        self.home_city=home_city_for(index);self.target=None;self.context=None;self.pending=None
        self.next_trip=0;self.trip_started=None;self.last_position=None;self.last_progress=0
        self.requests=self.arrivals=self.failures=0;self.reason=''
    def destination(self,policy):
        w=self.world;level=w.own.values.get(0,0);job=w.own.values.get(4,0)
        if job==0 and level>=9:return TRAINER_MAP[self.role['first_job']]
        career=getattr(policy,'career',None)
        if career and career.eligible() and (not career.active() or career.quest.get('talk')):
            return career.quest['map']
        return self.home_city
    def abort(self,now):
        self.context=None;self.pending=None;self.target=None;self.trip_started=None
        self.failures+=1;self.next_trip=now+300;self.reason='переход отложен; продолжает развитие на текущей карте'
    def on_map(self,now):
        if self.target and self.world.map==self.target:self.arrivals+=1
        self.context=None;self.pending=None;self.target=None;self.trip_started=None;self.next_trip=now+15
    def observe(self,command,payload,now):
        if not self.context or command!=802:return False
        r=Reader(payload);source,page=r.long(),r.byte();r.string_bytes();n=r.byte()
        if n>64:raise ProtocolError('Too many teleporter functions')
        labels=[r.string() for _ in range(n)]
        npc,stage,deadline=self.context
        if source!=npc:return False
        if stage=='menu':
            wanted='Go to '+CITIES[self.target]+'!'
            index=next((i for i,label in enumerate(labels) if label==wanted),None)
            if index is None:self.abort(now);return True
            self.send(301,function_request(npc,page,index));self.requests+=1
            self.context=npc,'confirm',now+8
        elif stage=='confirm':
            index=next((i for i,label in enumerate(labels) if label=='Teleport'),None)
            w=self.world
            if index is None or (w.own.values.get(0,0)>10 and w.own.values.get(8,0)<500):self.abort(now);return True
            self.send(301,function_request(npc,page,index));self.requests+=1
            self.context=npc,'map',now+20;self.pending=self.target
        return True
    def tick(self,now,policy,safe,dialogue_busy=False):
        wanted=self.destination(policy)
        if wanted==self.world.map:
            if self.target:self.on_map(now)
            return False
        if self.context:
            if now>=self.context[2]:self.abort(now);return False
            return True
        if not safe or dialogue_busy or now<self.next_trip:return False
        w=self.world
        if w.map not in TELEPORTERS or (w.own.values.get(0,0)>10 and w.own.values.get(8,0)<500):
            self.next_trip=now+120;return False
        if self.target!=wanted:
            self.target=wanted;self.trip_started=now;self.last_progress=now;self.last_position=policy.position(now)
        pos=policy.position(now)
        if math.dist(pos,self.last_position)>=100:self.last_position=pos;self.last_progress=now
        if now-self.trip_started>180 or now-self.last_progress>35:self.abort(now);return False
        point=TELEPORTERS[w.map]
        npc=next((e for e in w.entities.values() if e.control in (2,3) and math.dist(e.position,point)<350),None)
        self.reason='переход в '+CITIES[wanted]
        if npc and math.dist(pos,npc.position)<=220:
            self.send(301,talk_request(npc.identity));self.requests+=1;self.context=npc.identity,'menu',now+8;return True
        goal=policy.nav.nearest(point,6)
        if goal and policy.move_to(goal,now):return True
        self.abort(now);return False
    def summary(self):
        return {'home_city':self.home_city,'destination':self.target,'state':self.reason,
                'npc_requests':self.requests,'confirmed_arrivals':self.arrivals,'postponed_trips':self.failures}
