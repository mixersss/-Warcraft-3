"""Collect nearby earned monster drops; server bag updates confirm each pickup."""
import math
import struct

class QuestLoot:
    def __init__(self,world,collect_all=False):
        self.world=world;self.collect_all=collect_all
        self.attacked={};self.attempted={};self.retries={};self.pending=None
        self.requests=self.confirmed=self.timeouts=self.unreachable=0
        self.competitive=set()
        self.approach=None

    def note_attack(self,target,now):
        if target not in self.attacked:
            self.attacked[target]=(self.world.own.values.get(0),self.world.own.values.get(15),now)
        if len(self.attacked)>128:self.attacked.pop(next(iter(self.attacked)))

    def count(self,model):return sum(i.count for i in self.world.bag.values() if i.identity==model)

    def credited(self,source,now):
        hit=self.world.own_hits.get(source)
        # Actual own damage and observed death cover party/zero-XP kills.
        if hit and hit[1] and 0<=now-hit[0]<=120:return True
        evidence=self.attacked.get(source)
        if not evidence:return False
        level,xp,when=evidence;own=self.world.own
        return (now-when<=120 and level is not None and xp is not None
                and (own.values.get(0,0)>level or own.values.get(15,-1)>xp))

    def tick(self,now,policy,needed):
        w=self.world
        if self.pending:
            identity,handle,model,before,deadline=self.pending
            if self.count(model)>before and identity not in w.items:
                self.confirmed+=1;self.pending=None
            elif now>=deadline:
                self.timeouts+=1;self.pending=None
                self.attempted[(identity,handle)]=now+8
            else:return False
        free=(w.bag_capacity or 0)-len(w.bag)
        if w.bag_disabled or (w.bag_ready and w.bag_capacity is not None and free<=0):return False
        if not needed and not self.collect_all:return False
        for source,(_,_,when) in list(self.attacked.items()):
            if now-when>120:self.attacked.pop(source,None)
        candidates=[]
        for identity,item in w.items.items():
            model,handle,position,kind,source,created=item;key=(identity,handle)
            if (kind!=0 or not handle or now-created>90 or (not self.credited(source,now) and model not in self.competitive)
                    or self.attempted.get(key,0)>now or self.retries.get(key,0)>=2):continue
            if model not in needed and (not self.collect_all or not w.bag_ready or free<=4):continue
            dist=math.dist(policy.position(now),position)
            if dist<=2000:candidates.append((model not in needed,dist,identity,item))
        for _,dist,identity,item in sorted(candidates):
            model,handle,position,kind,source,created=item;key=(identity,handle)
            if dist>180:
                pos=policy.position(now)
                if self.approach is None or self.approach[0]!=key:
                    self.approach=[key,now,now,pos]
                elif math.dist(pos,self.approach[3])>=100:
                    self.approach[2:]=[now,pos]
                if now-self.approach[1]>=25 or now-self.approach[2]>=8:
                    self.unreachable+=1;self.attempted[key]=now+30;self.approach=None;continue
                goal=policy.nav.nearest(position,2)
                if goal and policy.move_to(goal,now):return True
                self.unreachable+=1;self.attempted[key]=now+30;continue
            self.approach=None
            from hunter import action_header
            policy.emit(action_header(w.own.identity,policy.sequence,8)+struct.pack('>II',identity,handle))
            policy.next_action=now+1
            self.attempted[key]=now+60;self.retries[key]=self.retries.get(key,0)+1
            self.pending=identity,handle,model,self.count(model),now+10
            for rows in (self.attempted,self.retries):
                while len(rows)>256:rows.pop(next(iter(rows)))
            self.requests+=1;return True
        return False

    def summary(self):
        return {'pickup_requests':self.requests,'confirmed_pickups':self.confirmed,
                'confirmation_timeouts':self.timeouts,'unreachable_drops':self.unreachable,
                'awaiting_bag_confirmation':bool(self.pending),'collect_all_earned_drops':self.collect_all}
