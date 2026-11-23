"""Process-local expiring reservations; game ownership and loot rights remain server-owned."""
import threading
import math


class Coordination:
    def __init__(self,population=200):
        self.population=population
        self.visits={}
        self.lock=threading.Lock()
        self.targets={}
        self.zones={}
        self.assistants={}
        self.next_sweep=0

    def _expire(self,now):
        if now<self.next_sweep:return
        self.next_sweep=now+1
        for owner,(_,_,until) in list(self.visits.items()):
            if until<=now:self.visits.pop(owner,None)
        for key,(_,until) in list(self.targets.items()):
            if until<=now:self.targets.pop(key,None)
        for owner,(_,until) in list(self.zones.items()):
            if until<=now:self.zones.pop(owner,None)
        for pair,(_,until) in list(self.assistants.items()):
            if until<=now:self.assistants.pop(pair,None)
    def grant_assist(self,requester,helper,key,now):
        with self.lock:
            self._expire(now)
            holder=self.targets.get(key)
            if holder is None or holder[1]<=now:return True
            if holder[0]!=requester:return False
            if any(k==key and h!=helper and until>now for (k,h),(_,until) in self.assistants.items()):return False
            self.assistants[(key,helper)]=(requester,now+90);return True
    def _assisting(self,owner,key,now):
        grant=self.assistants.get((key,owner));holder=self.targets.get(key)
        return bool(grant and holder and grant[0]==holder[0] and grant[1]>now)

    def available(self,owner,key,now,shared=False):
        with self.lock:
            self._expire(now)
            holder=self.targets.get(key)
            return shared or holder is None or holder[1]<=now or holder[0]==owner or self._assisting(owner,key,now)

    def claim(self,owner,key,now,shared=False):
        with self.lock:
            self._expire(now)
            reservation=self.targets.get(key)
            if reservation and reservation[1]>now and reservation[0]!=owner:
                return shared or self._assisting(owner,key,now)
            for previous,(holder,_) in list(self.targets.items()):
                if holder==owner and previous!=key:self.targets.pop(previous,None)
            self.targets[key]=(owner,now+8)
            return True

    def release(self,owner,zone=False):
        with self.lock:
            for key,(holder,_) in list(self.targets.items()):
                if holder==owner:self.targets.pop(key,None)
            if zone:self.zones.pop(owner,None)
            for pair,(requester,_) in list(self.assistants.items()):
                if pair[1]==owner or requester==owner:self.assistants.pop(pair,None)

    def choose_zone(self,owner,map_name,goals,now,origin=None,mine=False):
        """Keep a leased destination; otherwise prefer the least occupied real farm."""
        if not goals:return None
        goals=list(dict.fromkeys(tuple(p) for p in goals))
        if not mine and origin is not None and len(goals)>24:
            # Do not evaluate every destination against400leases under one
            # shared lock. Only nearby real destinations can win this visit.
            goals=sorted(goals,key=lambda p:math.dist(origin,p))[:24]
        owner=(owner,'mine') if mine else owner
        map_name=(map_name,'mine') if mine else map_name
        with self.lock:
            self._expire(now)
            previous=self.zones.get(owner)
            if previous and previous[1]>now and previous[0][0]==map_name and previous[0][1] in goals:
                selected=previous[0][1]
            else:
                patches={}
                for (name,point),until in self.zones.values():
                    if name==map_name and until>now:
                        patches.setdefault((point[0]//2500,point[1]//2500),[]).append(point)
                def cost(point):
                    x,y=point[0]//2500,point[1]//2500
                    density=sum(max(0,2500-math.dist(point,p))+(1000 if point==p else 0)
                                for i in range(x-1,x+2) for j in range(y-1,y+2)
                                for p in patches.get((i,j),()))
                    travel=math.dist(origin,point)*(.08 if mine else .2) if origin is not None else 0
                    return density+travel
                selected=min(goals,key=cost)
            self.zones[owner]=((map_name,selected),now+(90 if mine else 45))
            return selected

    def visit(self,owner,map_name,point,now,mandatory=False):
        """Admission, not a queue: denied optional visitors continue hunting."""
        site=(map_name,tuple(point))
        with self.lock:
            self._expire(now)
            previous=self.visits.get(owner)
            if previous and previous[2]>now and previous[0]==site:
                self.visits[owner]=(site,mandatory,now+15);return True
            nearby=sum(until>now and m==map_name and math.dist(p,point)<500
                       for (m,p),_,until in self.visits.values())
            optional=sum(not required and until>now for _,required,until in self.visits.values())
            if not mandatory and (nearby>=2 or optional>=max(1,self.population//10)):return False
            self.visits[owner]=(site,mandatory,now+15);return True

    def leave_visit(self,owner):
        with self.lock:self.visits.pop(owner,None)

    def leave_zone(self,owner,mine=False):
        if mine:owner=(owner,'mine')
        with self.lock:self.zones.pop(owner,None)


def tactic_for(index,mode='mixed'):
    if mode=='mixed':return 'farm' if index%5 in (0,1) else 'hybrid'
    return 'farm' if mode=='hunt' else 'quests'


class TacticSchedule:
    """Stable cohort, variable-length phases; never interrupt combat or NPC exchange."""
    def __init__(self,tactic,seed):
        import random
        if tactic not in ('farm','quests','hybrid'):raise ValueError('Unknown tactic')
        self.tactic=tactic
        self.rng=random.Random(str(seed)+':phases')
        self.phase=('quests' if self.rng.randrange(2) else 'farm') if tactic=='hybrid' else tactic
        self.next_switch=None
        self.switches=0
        self.profession_hold=False
        self.effective_phase=self.phase

    def tick(self,now,busy=False,mandatory=False):
        if self.tactic!='hybrid':
            self.effective_phase=self.phase
            return self.phase
        if self.next_switch is None:self.next_switch=now+self.rng.uniform(240,480)
        if mandatory:
            self.profession_hold=True
            self.effective_phase='quests'
            return self.effective_phase
        if self.profession_hold:
            self.profession_hold=False;self.next_switch=now+self.rng.uniform(240,480)
        if now>=self.next_switch and not busy:
            self.phase='farm' if self.phase=='quests' else 'quests'
            self.switches+=1
            self.next_switch=now+self.rng.uniform(240,480)
        self.effective_phase=self.phase
        return self.phase

    def summary(self):
        return {'cohort':self.tactic,'phase':self.effective_phase,'switches':self.switches,
                'mandatory_profession_priority':self.profession_hold}
