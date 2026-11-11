"""Quest-only drops from recently attacked mobs with observed earned XP/level credit."""
import math
import struct


class QuestLoot:
    def __init__(self, world):
        self.world = world
        self.attacked = {}
        self.attempted = {}
        self.requests = 0

    def note_attack(self, target, now):
        # Keep the first baseline, so continuous attacks do not erase credit evidence.
        if target not in self.attacked:
            self.attacked[target] = (self.world.own.values.get(0),self.world.own.values.get(15),now)
        if len(self.attacked)>64:
            self.attacked.pop(next(iter(self.attacked)))

    def tick(self, now, policy, needed):
        if not needed:
            return False
        for identity,(_,_,when) in list(self.attacked.items()):
            if now-when>90: self.attacked.pop(identity,None)
        for identity,item in self.world.items.items():
            model,handle,position,kind,source,created = item
            evidence = self.attacked.get(source)
            if (model not in needed or kind != 0 or not handle or not evidence
                    or now-created>60 or self.attempted.get((source,handle),0)>now):
                continue
            level,xp,when = evidence
            own = self.world.own
            if level is None or xp is None:
                continue
            if not (own.values.get(0,0)>level or own.values.get(15,-1)>xp):
                continue
            if math.dist(policy.position(now),position)>1200:
                continue
            if math.dist(policy.position(now),position)>180:
                goal = policy.nav.nearest(position,2)
                return bool(goal and policy.move_to(goal,now))
            from hunter import action_header
            policy.emit(action_header(own.identity,policy.sequence,8)+struct.pack('>II',identity,handle))
            policy.next_action = now+2
            self.attempted[(source,handle)] = now+60
            while len(self.attempted)>128: self.attempted.pop(next(iter(self.attempted)))
            self.requests += 1
            return True
        return False
