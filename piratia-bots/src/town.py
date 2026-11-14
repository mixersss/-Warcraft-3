"""Normal NPC purchases and occasional city breaks; money/inventory are server-owned."""
import math,struct
from classic_wire import Reader,ProtocolError
from adventure import talk_request

def function_request(npc,page,index):return struct.pack('>IHBB',npc,303,page,index)
def buy_request(npc,page,index,count):
    if not 0<=page<4 or not 0<=index<128 or not 1<=count<=20:raise ValueError('Invalid purchase')
    return struct.pack('>IHBBBBB',npc,309,1,page,index,0,count)

def trade_page(payload):
    r=Reader(payload);npc,kind,param,count=r.long(),r.byte(),r.long(),r.byte()
    if kind!=1 or count>4:raise ProtocolError('Unsupported NPC shop type')
    offers=[]
    for _ in range(count):
        page,n=r.byte(),r.byte()
        if page>=4 or n>128:raise ProtocolError('Unsupported shop page')
        for index in range(n):offers.append((r.short(),page,index))
    r.end();return npc,offers

class Town:
    def __init__(self,world,life,gear,role,rng,home,rest_directory=None,owner=None):
        self.world,self.life,self.gear,self.role,self.rng=world,life,gear,role,rng
        self.home=home;self.next_break=None;self.rest_until=0;self.rest_arrived=None
        self.next_shop=0;self.context=None;self.pending=None
        self.requests=self.confirmed=self.timeouts=self.breaks=0
        self.target_shop=None;self.wanted=None;self.reason=''
        self.rest_directory=rest_directory;self.owner=owner or str(world.own_id)
        self.work_kills=self.work_quests=0;self.work_baseline=None;self.last_rest=0;self.rest_due=False
        self.rest_goal=None;self.rest_pause_until=0;self.walk_stops=0
    def note_progress(self,kills,quests):
        if self.work_baseline is None:self.work_baseline=(kills,quests)
        self.work_kills=max(0,kills-self.work_baseline[0]);self.work_quests=max(0,quests-self.work_baseline[1])
        if self.work_kills>=12 or self.work_quests>=2:self.rest_due=True
    def end_rest(self,now):
        if self.rest_directory:self.rest_directory.release(self.owner)
        self.rest_until=0;self.rest_arrived=None;self.rest_due=False;self.last_rest=now
        self.work_baseline=None;self.work_kills=self.work_quests=0
        self.next_break=now+600
        self.rest_goal=None;self.rest_pause_until=0
    def choose_walk_stop(self,now,policy):
        for _ in range(12):
            angle=self.rng.uniform(0,math.tau);radius=self.rng.uniform(600,1600)
            raw=(round(self.home[0]+radius*math.cos(angle)),round(self.home[1]+radius*math.sin(angle)))
            goal=policy.nav.nearest(raw,3)
            if not goal or math.dist(goal,policy.position(now))<350:continue
            if any(e.identity!=self.world.own_id and e.control in (1,2,3) and math.dist(e.position,goal)<250 for e in self.world.entities.values()):continue
            if policy.nav.path(policy.position(now),goal):return goal
        return None
    def choose_want(self):
        w=self.world;cash=w.own.values.get(8,0)
        if not w.bag_ready or w.bag_disabled or cash<120:return None
        free=(w.bag_capacity or 0)-len(w.bag)
        if free<2:return None
        food=sum(item.count for item in w.bag.values() if item.identity==1847)
        if food<5:return 1847,min(10,15-food)
        if (not w.skills.get(241,{}).get("level",0) and w.own.values.get(13,0)>0
                and not any(i.identity==3296 for i in w.bag.values()) and cash>=20000):return 3296,1
        for identity,book in self.life.books.items():
            if (self.life.can_learn(w,book) and w.own.values.get(7,0)>=book['cost']
                    and not w.skills.get(book['skill'],{}).get('level',0)
                    and not any(i.identity==identity for i in w.bag.values())
                    and 0<self.life.prices.get(identity,0)<=cash//4):return identity,1
        owned={i.identity for i in w.bag.values()}
        for shop in self.life.services['shops'].get(w.map,[]):
            for identity in shop['offers']:
                if identity in owned or not self.gear.upgrade(w.own,identity,free):continue
                if 0<self.life.prices.get(identity,0)<=cash//4:return identity,1
        return None
    def count(self,identity):return sum(i.count for i in self.world.bag.values() if i.identity==identity)
    def observe(self,command,payload,now,send):
        if not self.context:return False
        npc,stage,deadline=self.context
        if command==802 and stage=='talk':
            r=Reader(payload);source,page=r.long(),r.byte();r.string_bytes();count=r.byte()
            if count>64:raise ProtocolError('Too many shop functions')
            labels=[r.string() for _ in range(count)]
            if source!=npc:return True
            index=next((i for i,label in enumerate(labels) if label.casefold() in ('trade','торговля','купить')),None)
            if index is None:self.finish(now,180);return True
            send(301,function_request(npc,page,index));self.context=npc,'shop',now+8
            return True
        if command==805 and stage=='shop':
            source,offers=trade_page(payload)
            if source!=npc:return True
            identity,count=self.wanted
            offer=next(((page,index) for model,page,index in offers if model==identity),None)
            price=self.life.prices.get(identity,0);cash=self.world.own.values.get(8,0)
            if price>0:count=min(count,max(0,min(cash//4,cash-100)//price))
            if offer and count>0 and price>0 and price*count<=max(0,cash-100) and price*count<=cash//4:
                send(308,buy_request(npc,*offer,count));self.requests+=1
                self.pending=identity,self.count(identity),cash,now+12
                self.context=npc,'confirmation',now+12
            else:self.finish(now,180)
            return True
        return command in (801,802,803,805,806,807,808)
    def finish(self,now,delay=120):
        self.context=None;self.pending=None;self.target_shop=None;self.wanted=None;self.next_shop=now+delay
    def tick(self,now,policy,safe,dialogue_busy=False,medical=False):
        if self.next_break is None:self.next_break=now+600
        w=self.world
        if self.pending:
            identity,before,cash,deadline=self.pending
            if self.count(identity)>before and w.own.values.get(8,cash)<cash:
                self.confirmed+=1;self.finish(now,60)
            elif now>deadline:self.timeouts+=1;self.finish(now,300)
            return True
        if self.context:
            if now>self.context[2]:self.timeouts+=1;self.finish(now,300)
            return True
        if not safe or dialogue_busy:return False
        if self.rest_until and not medical:
            if self.rest_directory and not self.rest_directory.acquire(self.owner,now):self.end_rest(now);return False
            if now>=self.rest_until:self.end_rest(now);return False
            self.reason='идёт на короткую прогулку по городу'
            if math.dist(policy.position(now),self.home)>1800:
                goal=policy.nav.nearest(self.home,6)
                if not goal or not policy.move_to(goal,now):self.end_rest(now);return False
                return True
            if self.rest_arrived is None:self.rest_arrived=now;self.rest_until=now+self.rng.uniform(40,100);self.breaks+=1
            if now<self.rest_pause_until:
                self.reason='короткая остановка во время прогулки';return True
            if self.rest_goal and math.dist(policy.position(now),self.rest_goal)<200:
                self.walk_stops+=1;self.rest_goal=None;self.rest_pause_until=now+self.rng.uniform(3,8);return True
            if not self.rest_goal:self.rest_goal=self.choose_walk_stop(now,policy)
            if self.rest_goal and policy.move_to(self.rest_goal,now):return True
            self.end_rest(now);return False
        if self.rest_due and not medical and now>=self.next_break:
            if self.rest_directory and not self.rest_directory.acquire(self.owner,now):return False
            self.rest_until=now+180;return True
        if now<self.next_shop:return False
        if not self.wanted:
            # Healthy beginners must first earn something, not all shop on login.
            hp=w.own.values.get(1,0);maximum=max(1,w.own.values.get(31,1))
            earned=(self.work_kills>=2 or self.work_quests>0 or w.own.values.get(0,1)>=4)
            if not earned and hp>=maximum*.85:return False
            self.wanted=self.choose_want()
            if not self.wanted:self.next_shop=now+120;return False
            shops=[s for s in self.life.services['shops'].get(w.map,[]) if self.wanted[0] in s['offers']]
            if not shops:self.finish(now,300);return False
            self.target_shop=min(shops,key=lambda s:math.dist(policy.position(now),s['position']))
        point=self.target_shop['position']
        self.reason='покупки у городского торговца'
        npc=next((e for e in w.entities.values() if e.control in (2,3) and math.dist(e.position,point)<350),None)
        if npc and math.dist(policy.position(now),npc.position)<=220:
            policy.send(301,talk_request(npc.identity));self.context=npc.identity,'talk',now+8;return True
        goal=policy.nav.nearest(point,6)
        if goal and policy.move_to(goal,now):return True
        self.finish(now,300);return False
    def summary(self):return {'purchase_requests':self.requests,'confirmed_purchases':self.confirmed,'timeouts':self.timeouts,'city_breaks':self.breaks,'city_walk_stops':self.walk_stops,'state':self.reason,'rest_due_after_tasks':self.rest_due,'kills_since_break':self.work_kills,'quests_since_break':self.work_quests,'bench_sitting_implemented':False}
