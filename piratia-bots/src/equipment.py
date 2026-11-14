"""Equip only real owned, compatible upgrades; wait for native appearance confirmation."""
import json
import struct
from pathlib import Path


class ItemCatalog:
    def __init__(self,path):
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        self.types={int(k):v for k,v in data['types'].items()}
        self.gear={int(k):v for k,v in data['gear'].items()}

    def compatible(self,own,identity):
        gear=self.gear.get(identity)
        return bool(gear and gear['level']<=own.values.get(0,0) and own.model in gear['bodies']
                    and (gear['jobs']==[-1] or own.values.get(4) in gear['jobs']))

    def transition(self,own,identity,free_slots=None):
        """Predict native auto-equip: first empty allowed link, otherwise first link.

        9999 is the native BOTH_HAND occupancy marker, never an actual item. It is
        accepted only when the other hand contains a known two-handed item.
        """
        if not self.compatible(own,identity):return None
        gear=self.gear[identity];links=gear['links']
        if not links or any(link not in (0,2,3,4,5,6,7,8,9) for link in links):return None
        chosen=next((link for link in links if not own.equipment.get(link)),links[0])
        affected=set(gear.get('requires_links',gear.get('displaces',[chosen]))) or {chosen}
        affected.add(chosen)
        # Unfixing either occupied hand also unfixes its known two-hand partner.
        for link in tuple(affected):
            if link not in (6,9):continue
            other=9 if link==6 else 6
            current=own.equipment.get(link,0);partner=self.gear.get(own.equipment.get(other,0))
            old=self.gear.get(current)
            if current==9999:
                if not partner or not {6,9}<=set(partner.get('requires_links',partner.get('displaces',[]))):return None
                affected.add(other)
            elif old and {6,9}<=set(old.get('requires_links',old.get('displaces',[]))):affected.add(other)
        if own.values.get(4) in (4,16) and gear.get('kind')!=29:
            if any(self.types.get(own.equipment.get(link,0))==29 for link in affected):return None
        equipment=dict(own.equipment);removed=[]
        for link in affected:
            current=equipment.get(link,0)
            if current and current!=9999:
                if current not in self.gear:return None # Unknown equipped valuables stay protected.
                removed.append(current)
            equipment.pop(link,None)
        if free_slots is not None and free_slots<len(removed):return None
        equipment[chosen]=identity
        for link in affected-{chosen}:
            if link in gear.get('requires_links',[]):equipment[link]=9999
        return equipment,chosen,removed

    def loadout_score(self,own,equipment):
        total=0
        for identity in equipment.values():
            if not identity or identity==9999:continue
            gear=self.gear.get(identity)
            if gear is None:return None
            job=own.values.get(4)
            weights=({'constitution':3,'strength':1} if job==8 else
                     {'agility':3,'strength':2} if job==9 else
                     {'accuracy':3,'agility':1,'constitution':1} if job in (2,12) else
                     {'spirit':3,'constitution':1} if job in (4,5,13,14,16) else
                     {'strength':2,'agility':1,'constitution':1})
            from builds import PROFILES
            spec=PROFILES.get(getattr(own,'build_id',None))
            if spec:
                names={25:'strength',26:'accuracy',27:'agility',28:'constitution',29:'spirit'}
                peak=max(spec['weights'].values())
                weights={names[k]:3*v/peak for k,v in spec['weights'].items()}
            total+=gear['score']+sum(gear.get(k,0)*v for k,v in weights.items())
        return total

    def upgrade(self,own,identity,free_slots=None,item=None,energy_need=1):
        change=self.transition(own,identity,free_slots)
        if change is None:return None
        equipment,chosen,_=change
        # A depleted coral may be replaced by a fresh copy of the same item ID.
        if self.gear[identity].get('kind')==29:
            old_id=own.equipment.get(chosen,0);old=own.equipment_details.get(chosen,{})
            if old_id and old.get('identity')==old_id and (old.get('energy',energy_need)<energy_need or old.get('valid') is False):
                if item is None or item.energy>=energy_need:return 1,[chosen]
                return None
        # Compare only affected links: unrelated unknown armour is not a blocker.
        affected={k for k in own.equipment.keys()|equipment.keys() if own.equipment.get(k)!=equipment.get(k)}
        before=self.loadout_score(own,{k:own.equipment.get(k,0) for k in affected})
        after=self.loadout_score(own,{k:equipment.get(k,0) for k in affected})
        if before is None or after is None:return None
        gain=after-before
        return (gain,[chosen]) if gain>0 else None

    def pair_upgrade(self,world,blacklist,now):
        """A bounded two-step comparison can cross a temporarily weaker first sword.

        Uses owned, valid, unmodified swords and the ordinary native auto command.
        No forced left-hand operand, invented skill multiplier or simulated grant.
        """
        from types import SimpleNamespace
        own=world.own
        if own.values.get(4) not in (1,9):return None # Preserve other class/tank loadouts.
        before=self.loadout_score(own,{k:own.equipment.get(k,0) for k in (6,9)})
        if before is None:return None
        free=max(0,(world.bag_capacity or 0)-len(world.bag));candidates=[]
        for slot,item in world.bag.items():
            gear=self.gear.get(item.identity,{})
            if (gear.get('kind')!=1 or not self.compatible(own,item.identity)
                    or item.forge or any(item.parameters) or any(a or b for a,b in item.instance_attributes)
                    or not item.valid or (item.max_endurance>0 and item.endurance<=0)
                    or blacklist.get(item.identity,0)>now):continue
            candidates.append((gear['score'],slot,item.identity))
        candidates=sorted(candidates,reverse=True)[:8];best=None
        for _,slot,identity in candidates:
            first=self.transition(own,identity,free)
            if first is None:continue
            eq,chosen,removed=first
            mid=SimpleNamespace(model=own.model,values=own.values,equipment=eq)
            for _,second_slot,second_id in candidates:
                if second_slot==slot:continue
                second=self.transition(mid,second_id,free+1-len(removed))
                if second is None:continue
                final=second[0]
                # It must really be a pair; two-handed/marker states aren't two swords.
                if any(self.gear.get(final.get(k),{}).get('kind')!=1 for k in (6,9)):continue
                gain=self.loadout_score(own,{k:final.get(k,0) for k in (6,9)})-before
                if gain>0 and (best is None or gain>best[0]):best=(gain,slot,identity,[chosen])
        return best


class Equipment:
    def __init__(self,world,catalog,send,tell=lambda text:None):
        self.world,self.catalog,self.send,self.tell=world,catalog,send,tell
        self.pending=None;self.pending_refill=None;self.blockers=[];self.settling=False
        self.next_action=0
        self.blacklist={}
        self.requests=self.confirmed=self.failed=0

    def loot_needs(self):
        own=self.world.own
        result=set()
        for identity,(model,handle,position,kind,source,created) in self.world.items.items():
            if self.catalog.upgrade(own,model):result.add(model)
        return result

    def tick(self,now,policy,safe=True):
        own=self.world.own
        if self.pending:
            identity,links,deadline=self.pending
            refill_ok=not self.pending_refill or own.equipment_details.get(self.pending_refill[0],{}).get('energy',0)>self.pending_refill[1]
            if any(own.equipment.get(link)==identity for link in links) and refill_ok:
                self.confirmed+=1;self.pending=None;self.next_action=now+1;self.settling=True
                self.tell('Экипировка подтверждена сервером.')
            elif now>deadline:
                self.failed+=1;self.blacklist[identity]=now+300;self.pending=None
            return self.pending is not None or self.settling
        if not safe or not self.world.bag_ready or self.world.bag_disabled:return False
        if now<self.next_action:return self.settling
        self.settling=False
        level,job=own.values.get(0),own.values.get(4)
        if level is None or job is None:return False
        options=[];self.blockers=[]
        for slot,item in self.world.bag.items():
            if (not item.valid or (self.catalog.gear.get(item.identity,{}).get('kind')==29 and item.energy<=0) or (item.max_endurance>0 and item.endurance<=0)
                    or self.blacklist.get(item.identity,0)>now):continue
            free=max(0,(self.world.bag_capacity or 0)-len(self.world.bag))
            gear=self.catalog.gear.get(item.identity,{})
            coral_skill={5:213,6:216,7:214}.get(next(iter(gear.get('links',[])),None))
            need=max(1,self.world.skills.get(coral_skill,{}).get('energy',1))
            upgrade=self.catalog.upgrade(own,item.identity,free,item,need)
            if upgrade:options.append((upgrade[0],slot,item.identity,upgrade[1]))
            elif item.identity in self.catalog.gear:
                gear=self.catalog.gear[item.identity]
                reason=('нужен уровень '+str(gear['level']) if gear['level']>level else
                        'не подходит раса' if own.model not in gear['bodies'] else
                        'не подходит профессия' if gear['jobs']!=[-1] and job not in gear['jobs'] else
                        'нужно место для снятой вещи' if free<1 else 'нет подтверждённого улучшения комплекта')
                self.blockers.append({'slot':slot,'id':item.identity,'reason':reason})
        pair=self.catalog.pair_upgrade(self.world,self.blacklist,now)
        if pair:options.append(pair)
        if not options:return False
        _,slot,identity,links=max(options)
        from hunter import action_header
        # Native stNetUseItem: bag slot, automatic target=-1, exactly like double click.
        policy.emit(action_header(own.identity,policy.sequence,11)+struct.pack('>hh',slot,-1))
        self.requests+=1
        self.pending_refill=None
        if self.catalog.gear[identity].get('kind')==29 and own.equipment.get(links[0])==identity:
            self.pending_refill=(links[0],own.equipment_details.get(links[0],{}).get('energy',0))
        self.pending=identity,links,now+12
        self.next_action=now+1.5
        return True

    def summary(self):
        return {'candidate_blockers':self.blockers[:24],'pending_item':self.pending[0] if self.pending else None,'requests':self.requests,'confirmed_equips':self.confirmed,
                'confirmation_timeouts':self.failed,'bag_received':self.world.bag_ready,
                'inventory_paused':self.world.bag_disabled,
                'equipped_items':dict(self.world.own.equipment)}
