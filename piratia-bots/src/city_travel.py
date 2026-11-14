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
    def __init__(self,world,send,index,role,portals=None):
        self.world,self.send,self.role=world,send,role
        self.home_city=home_city_for(index);self.target=None;self.context=None;self.pending=None
        self.next_trip=0;self.trip_started=None;self.last_position=None;self.last_progress=0
        self.requests=self.arrivals=self.failures=0;self.reason=''
        self.last_menu=[];self.last_problem=''
        self.portals=portals;self.portal=None;self.failed_portals={}
    def destination(self,policy):
        w=self.world;level=w.own.values.get(0,0);job=w.own.values.get(4,0)
        if 1<=level<=3:return 'garner'
        if job==0 and level>=9:return TRAINER_MAP[self.role['first_job']]
        career=getattr(policy,'career',None)
        if career and career.eligible() and (not career.active() or career.quest.get('talk')):
            return career.quest['map']
        return self.home_city
    def starter_trip(self):return 1<=self.world.own.values.get(0,0)<=3 and self.world.map!='garner'
    def needs_funds(self):
        return self.world.own.values.get(0,0)>10 and self.world.own.values.get(8,0)<500
    def abort(self,now,problem='переход не подтверждён'):
        if self.portal:self.failed_portals[tuple(self.portal['position'])]=now+300
        self.portal=None
        self.context=None;self.pending=None;self.target=None;self.trip_started=None
        required=self.world.own.values.get(4)==0 and self.world.own.values.get(0,0)>=9
        self.failures+=1;self.next_trip=now+(30 if required else 300)
        self.last_problem=problem;self.reason=problem+'; повтор через '+('30' if required else '300')+' секунд'
    def on_map(self,now):
        if self.target and self.world.map==self.target:self.arrivals+=1
        self.context=None;self.pending=None;self.target=None;self.trip_started=None;self.next_trip=now+15
        self.portal=None
    def observe(self,command,payload,now):
        if not self.context or command!=802:return False
        r=Reader(payload);source,page=r.long(),r.byte();r.string_bytes();n=r.byte()
        if n>64:raise ProtocolError('Too many teleporter functions')
        labels=[r.string() for _ in range(n)]
        npc,stage,deadline=self.context
        if source!=npc:return False
        self.last_menu=[label[:160] for label in labels]
        if stage=='menu':
            wanted='Go to '+CITIES[self.target]+'!'
            index=next((i for i,label in enumerate(labels) if label==wanted),None)
            if index is None:self.abort(now,'в меню телепортера нет '+wanted);return True
            self.send(301,function_request(npc,page,index));self.requests+=1
            self.context=npc,'confirm',now+8
        elif stage=='confirm':
            index=next((i for i,label in enumerate(labels) if label=='Teleport'),None)
            w=self.world
            if index is None:self.abort(now,'нет кнопки Teleport');return True
            if w.own.values.get(0,0)>10 and w.own.values.get(8,0)<500:self.abort(now,'для перехода требуется 500G');return True
            self.send(301,function_request(npc,page,index));self.requests+=1
            self.context=npc,'map',now+20;self.pending=self.target
        return True
    def tick(self,now,policy,safe,dialogue_busy=False):
        wanted=self.destination(policy)
        if wanted==self.world.map:
            if self.target:self.on_map(now)
            return False
        if self.context:
            if now>=self.context[2]:self.abort(now,'нет ответа телепортера на этапе '+self.context[1]);return False
            return True
        if not safe or dialogue_busy or now<self.next_trip:return False
        w=self.world
        if self.needs_funds():
            self.reason='для перехода требуется 500G';return False
        if w.map not in TELEPORTERS:
            self.reason='неизвестна точка телепортера на текущей карте'
            self.next_trip=now+120;return False
        if self.target!=wanted:
            self.target=wanted;self.trip_started=now;self.last_progress=now;self.last_position=policy.position(now)
        pos=policy.position(now)
        if math.dist(pos,self.last_position)>=100:self.last_position=pos;self.last_progress=now
        if now-self.trip_started>180 or now-self.last_progress>35:self.abort(now);return False
        if self.portals and self.portal is None:
            options=[n for n in self.portals['nodes'] if n['map']==w.map
                     and self.failed_portals.get(tuple(n['position']),0)<=now
                     and any(r['map']==wanted for r in n['routes'])]
            if not options:
                self.reason='нет доступного проверенного телепортера; продолжает искать альтернативу'
                self.next_trip=now+5;return False
            self.portal=min(options,key=lambda n:math.dist(pos,n['position']))
        point=self.portal['position'] if self.portal else TELEPORTERS[w.map]
        npc=next((e for e in w.entities.values() if e.control in (2,3) and math.dist(e.position,point)<350),None)
        self.reason='переход в '+CITIES[wanted]
        if npc and math.dist(pos,npc.position)<=220:
            self.send(301,talk_request(npc.identity));self.requests+=1;self.context=npc.identity,'menu',now+8;return True
        goal=policy.nav.nearest(point,6)
        if goal and policy.move_to(goal,now):return True
        self.abort(now);return False
    def summary(self):
        return {'home_city':self.home_city,'destination':self.target,'state':self.reason,
                'npc_requests':self.requests,'confirmed_arrivals':self.arrivals,'postponed_trips':self.failures,
                'dialogue_stage':self.context[1] if self.context else None,
                'last_problem':self.last_problem,'last_menu':self.last_menu}
