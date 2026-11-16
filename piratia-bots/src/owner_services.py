"""Visit real owner NPCs; profession, stall and bag changes need server echoes."""
import math
import struct
from classic_wire import Reader,ProtocolError
from adventure import talk_request
from town import function_request
from owner_shops import npc_near

LABELS={1:'Swordsman',2:'Hunter',4:'Explorer',5:'Herbalist',8:'Champion',9:'Crusader',12:'Sharpshooter',13:'Cleric',14:'Seal Master',16:'Sea Voyager'}
LOOT={1000,4915,684,860,861,862,863,864,865,866,1012}

class OwnerServices:
    def __init__(self,world,role,overlay,send):
        self.world,self.role,self.overlay,self.send=world,role,overlay,send
        self.context=None;self.pending=None;self.retry=0;self.reason=''
        self.requests=self.confirmed=self.timeouts=0
    @property
    def busy(self):return bool(self.context or self.pending)
    def profession(self):
        w=self.world;job=w.own.values.get(4,0);level=w.own.values.get(0,0)
        if job==0 and level>=9:return self.role['first_job']
        if job==self.role['first_job'] and level>=40:return self.role['target_job']
        return None
    def need(self):
        job=self.profession()
        if job:return 'profession',job
        spell={4:214,16:214,5:99,13:99,14:99}.get(self.world.own.values.get(4))
        if spell and self.world.own.values.get(0,0)>=9 and not self.world.skills.get(spell,{}).get('level'):return 'combat',spell
        if self.world.bag_ready and self.world.bag_capacity<48:return 'bags',48
        if self.world.own.values.get(0,0)>=9 and self.world.skills.get(241,{}).get('level',0)<3:return 'stall',3
        return None
    def finish(self,now,success=False):
        self.context=self.pending=None;self.retry=now+(1 if success else 30)
        if success:self.confirmed+=1
    def observe(self,command,payload,now):
        if not self.context or command!=802:return False
        npc,kind,value,deadline=self.context
        r=Reader(payload);source,page=r.long(),r.byte();r.string_bytes();count=r.byte()
        if count>64:raise ProtocolError('Too many owner services')
        labels=[r.string() for _ in range(count)]
        if source!=npc:return False
        label=('First profession: ' if value in (1,2,4,5) else 'Second profession: ')+LABELS[value] if kind=='profession' else 'Get missing bag expansions' if kind=='bags' else 'Restore basic combat spell' if kind=='combat' else 'Get level 3 stall'
        if label in labels:
            self.send(301,function_request(npc,page,labels.index(label)))
            self.pending=kind,value,(self.world.bag_capacity,tuple((s,i.identity,i.count) for s,i in self.world.bag.items())),now+12
            self.context=None;self.requests+=1
        elif kind=='profession' and value in (8,9,12,13,14,16) and 'Second profession' in labels:
            self.send(301,function_request(npc,page,labels.index('Second profession')))
            self.context=npc,kind,value,now+8
        else:
            self.reason='НПС не предлагает нужную услугу; проверь серверный патч Alpha56'
            self.finish(now)
        return True
    def tick(self,now,policy,safe,dialogue_busy=False):
        w=self.world
        if self.pending:
            kind,value,before,deadline=self.pending
            confirmed=(w.own.values.get(4)==value if kind=='profession' else
                       w.skills.get(value,{}).get('level',0)>=1 if kind=='combat' else
                       w.skills.get(241,{}).get('level',0)>=value if kind=='stall' else
                       w.bag_capacity>=value and any(3088<=i<=3093 and not any(s2==s and item.identity==i and item.count>=n for s2,item in w.bag.items()) for s,i,n in before[1]) if kind=='expand' else
                       w.bag_capacity>before[0] or any(3088<=i.identity<=3093 and (s,i.identity,i.count) not in before[1] for s,i in w.bag.items()))
            if confirmed:self.finish(now,True)
            elif now>=deadline:self.timeouts+=1;self.reason='Услуга НПС не подтверждена сервером';self.finish(now)
            return bool(self.pending)
        if self.context:
            if now>=self.context[3]:self.timeouts+=1;self.finish(now)
            return bool(self.context)
        if not safe or dialogue_busy or now<self.retry or not w.bag_ready or w.bag_disabled:return False
        # Use one expander at a time, require BOTH consumption and a larger bag.
        identity=3088+(w.bag_capacity-24)//4
        slot=next((s for s,i in w.bag.items() if i.identity==identity and i.valid),None)
        if w.bag_capacity<48 and slot is not None:
            from hunter import action_header
            policy.emit(action_header(w.own_id,policy.sequence,11)+struct.pack('>hh',slot,-1))
            self.pending='expand',w.bag_capacity+4,(w.bag_capacity,tuple((s,i.identity,i.count) for s,i in w.bag.items())),now+12
            self.reason='Применяет расширитель сумки';self.requests+=1;return True
        needed=self.need()
        if not needed:return False
        if w.map!='garner':
            self.reason='Идёт к портальщице за услугами НПС Аргента'
            return bool(policy.travel and policy.travel.tick(now,policy,safe,dialogue_busy))
        kind,value=needed
        function='OwnerJewellery' if kind=='bags' else 'OwnerProgress'
        shop=next((n for n in self.overlay['npcs'] if n['script_function']==function),None)
        if not shop:self.reason='Нет подтверждённого НПС услуг';return False
        if kind=='bags' and len(w.bag)>=(w.bag_capacity or 0):return False
        point=shop['position'];npc=npc_near(w,point)
        self.reason='Получает '+{'profession':'профессию','bags':'расширители сумки','stall':'ларёк третьего уровня','combat':'первое боевое заклинание своего класса'}[kind]
        if npc and math.dist(policy.position(now),npc.position)<=220:
            self.send(301,talk_request(npc.identity));self.context=npc.identity,kind,value,now+8;return True
        center=npc.position if npc else point
        goals=[]
        for dx,dy in ((-150,0),(0,-150),(150,0),(0,150),(0,0)):
            goal=policy.nav.nearest((center[0]+dx,center[1]+dy),2)
            if isinstance(goal,(tuple,list)) and len(goal)==2 and math.dist(goal,center)<=220:goals.append(goal)
        for goal in sorted(goals,key=lambda p:math.dist(p,policy.position(now))):
            if policy.move_to(goal,now):return True
        self.retry=now+10;self.reason='Нет проверенного подхода к НПС; продолжает охоту';return False
    def summary(self):
        return {'state':self.reason,'wanted':self.need(),'requests':self.requests,'confirmed':self.confirmed,'timeouts':self.timeouts,'bag_capacity':self.world.bag_capacity,'profession_quests_required':False}
