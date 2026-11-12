"""Process-local expiring reservations; game ownership and loot rights remain server-owned."""
import threading


class Coordination:
    def __init__(self):
        self.lock=threading.Lock()
        self.targets={}
        self.zones={}

    def _expire(self,now):
        for key,(_,until) in list(self.targets.items()):
            if until<=now:self.targets.pop(key,None)
        for owner,(_,until) in list(self.zones.items()):
            if until<=now:self.zones.pop(owner,None)

    def available(self,owner,key,now):
        with self.lock:
            self._expire(now)
            return key not in self.targets or self.targets[key][0]==owner

    def claim(self,owner,key,now):
        with self.lock:
            self._expire(now)
            if key in self.targets and self.targets[key][0]!=owner:return False
            for previous,(holder,_) in list(self.targets.items()):
                if holder==owner and previous!=key:self.targets.pop(previous,None)
            self.targets[key]=(owner,now+8)
            return True

    def release(self,owner,zone=False):
        with self.lock:
            for key,(holder,_) in list(self.targets.items()):
                if holder==owner:self.targets.pop(key,None)
            if zone:self.zones.pop(owner,None)

    def choose_zone(self,owner,map_name,goals,now):
        """Keep a leased destination; otherwise prefer the least occupied real farm."""
        if not goals:return None
        goals=list(dict.fromkeys(tuple(p) for p in goals))
        with self.lock:
            self._expire(now)
            previous=self.zones.get(owner)
            if previous and previous[0][0]==map_name and previous[0][1] in goals:
                selected=previous[0][1]
            else:
                counts={p:sum(k==(map_name,p) for k,_ in self.zones.values()) for p in goals}
                selected=min(goals,key=lambda p:counts[p])
            self.zones[owner]=((map_name,selected),now+45)
            return selected

    def leave_zone(self,owner):
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
