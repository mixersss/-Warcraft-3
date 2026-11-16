"""Verified targeted spells through native BeginAction, with real SP/coral gates."""
import json
import math
from pathlib import Path

CASTER_JOBS={4,5,13,14,16}
CORE={5:(99,),13:(99,),14:(99,),4:(214,),16:(216,214)}
PRIORITY=(99,216,214,213,97,210,211)


class CombatSkills:
    def __init__(self,world,catalog,assets):
        self.world,self.catalog=world,catalog
        self.rules={int(k):v for k,v in json.loads((Path(assets)/'combat-skills.json').read_text())['skills'].items()}
        self.ready_at={};self.last_sent_at=0;self.requests=0;self.heals=0;self.last_skill=None;self.reason=''

    def hand_ok(self,slot,requirements):
        identity=self.world.own.equipment.get(slot,0);kind=self.catalog.types.get(identity,0)
        return any((mode==1 and (value==-1 or kind==value)) or (mode==2 and identity==value)
                   for mode,value in requirements)

    def usable(self,identity,now,ignore_cooldown=False,ignore_mana=False):
        own=self.world.own;rule=self.rules.get(identity);skill=self.world.skills.get(identity,{})
        if not rule or not skill.get('level') or own.values.get(4) not in rule['jobs']:return False
        if skill.get('state')!=1:self.reason='навык не активирован сервером';return False
        if not self.hand_ok(6,rule['left']) or not self.hand_ok(9,rule['right']) or not self.hand_ok(2,rule['body']):
            self.reason='не выполнено требование оружия';return False
        if rule['coral']:
            link,_,kind=rule['coral'];item=own.equipment.get(link,0);details=own.equipment_details.get(link,{})
            if self.catalog.types.get(item)!=kind:self.reason='нет нужного коралла';return False
            if details.get('identity')!=item or not details.get('valid') or details.get('energy',0)<skill.get('energy',1):
                self.reason='коралл разряжен или заряд не подтверждён';return False
        if not ignore_mana and own.values.get(2,0)<skill.get('sp',0):self.reason='недостаточно SP';return False
        if not ignore_cooldown and now<self.ready_at.get(identity,0):self.reason='навык перезаряжается';return False
        return True

    def select(self,now,healing=False,ignore_cooldown=False):
        own=self.world.own
        choices=[]
        for identity,rule in self.rules.items():
            if rule['role']!=('heal' if healing else 'damage'):continue
            if self.usable(identity,now,ignore_cooldown):
                priority=PRIORITY.index(identity) if identity in PRIORITY else len(PRIORITY)
                choices.append((priority,identity))
        if choices:self.reason=''
        return min(choices)[1] if choices else None

    def control(self,now):
        return 213 if self.world.own.values.get(1,0)<self.world.own.values.get(31,1)*.65 and self.usable(213,now) else None

    def training_weapon_bridge(self):
        """Earn level10 after the owner's level9 promotion; never attack barehanded."""
        own=self.world.own
        if own.values.get(0)!=9 or own.values.get(4) not in (4,5):return False
        if self.reason not in ('не выполнено требование оружия','нет нужного коралла'):return False
        identity=own.equipment.get(9,0);details=own.equipment_details.get(9,{})
        return (self.catalog.types.get(identity)==1 and details.get('identity')==identity
                and details.get('valid') is True and details.get('endurance',0)>0)

    def reach(self,identity,target):
        return max(40,self.rules[identity]['range_cm']+self.world.own.radius+target.radius-20)

    def healing_target_valid(self,target,party,now):
        w=self.world
        if not target or not target.alive or not target.handle or target.control!=1:return False
        if target.identity!=w.own_id and target.name not in getattr(party,'members',()):return False
        maximum=target.values.get(31,0);hp=target.values.get(1)
        return maximum>0 and hp is not None and 0<hp<maximum*.65

    def healing_target(self,skill,party,now):
        w=self.world
        candidates=[e for e in w.entities.values() if self.healing_target_valid(e,party,now)
                    and math.dist(w.position(now),w.position(now,e.identity))<=self.reach(skill,e)]
        return min(candidates,key=lambda e:(e.values[1]/e.values[31],e.identity!=w.own_id),default=None)

    def sent(self,identity,now):
        if identity not in self.rules:return
        skill=self.world.skills[identity]
        # Server-provided current skill cost/cooldown, never guess a Lua formula.
        self.ready_at[identity]=now+max(.5,skill.get('interval_ms',0)/1000)
        self.last_sent_at=now;self.last_skill=identity;self.requests+=1
        if self.rules[identity]['role']=='heal':self.heals+=1

    def needs_mana(self,now,recovering=False):
        own=self.world.own
        if own.values.get(4) not in CASTER_JOBS:return False
        costs=[self.world.skills[i].get('sp',0) for i in CORE.get(own.values.get(4),())
               if self.usable(i,now,True,True)]
        costs=[c for c in costs if 0<c<=own.values.get(32,0)]
        if not costs:return False
        threshold=min(own.values.get(32,0),min(costs)*(2 if recovering else 1))
        return own.values.get(2,0)<threshold

    def summary(self):
        return {'cast_requests':self.requests,'healing_requests':self.heals,'last_skill':self.last_skill,
                'blocker':self.reason,'sp':self.world.own.values.get(2),'max_sp':self.world.own.values.get(32),
                'known_supported_skills':sorted(set(self.rules)&set(self.world.skills)),
                'native_skill_costs':{str(i):{k:self.world.skills[i].get(k) for k in ('level','state','sp','energy','interval_ms')} for i in sorted(set(self.rules)&set(self.world.skills))},
                'coral_charge':{str(link):dict(self.world.own.equipment_details.get(link,{})) for link in (5,6,7)
                                if self.catalog.types.get(self.world.own.equipment.get(link))==29}}
