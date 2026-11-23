"""Equip only real owned, compatible upgrades; wait for native appearance confirmation."""
import json
import struct
from pathlib import Path


class ItemCatalog:
    def __init__(self,path):
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        self.types={int(k):v for k,v in data['types'].items()}
        self.gear={int(k):v for k,v in data['gear'].items()}
        mechanics=Path(path).with_name('mechanics.json')
        self.gems=json.loads(mechanics.read_text())['stones'] if mechanics.exists() else {}

    def effective(self,identity,item=None):
        gear=self.gear.get(identity)
        parameters=(item.get('parameters',(0,0)) if isinstance(item,dict) else getattr(item,'parameters',(0,0)))
        base=(parameters[1]>>16)&65535
        if gear and 5000<=identity<6000 and base in self.gear:
            source=self.gear[base]
            if source['kind']==gear['kind'] or {source['kind'],gear['kind']}<={22,27}:
                gear=dict(source,bodies=[b for b in source['bodies'] if b in gear['bodies']],links=gear['links'])
        return gear

    def compatible(self,own,identity,item=None):
        gear=self.effective(identity,item)
        return bool(gear and gear['level']<=own.values.get(0,0) and own.model in gear['bodies']
                    and (gear['jobs']==[-1] or own.values.get(4) in gear['jobs']))

    def transition(self,own,identity,free_slots=None,item=None):
        """Predict native auto-equip: first empty allowed link, otherwise first link.

        9999 is the native BOTH_HAND occupancy marker, never an actual item. It is
        accepted only when the other hand contains a known two-handed item.
        """
        if not self.compatible(own,identity,item):return None
        gear=self.effective(identity,item);links=gear['links']
        if not links or any(link not in (0,2,3,4,5,6,7,8,9) for link in links):return None
        chosen=next((link for link in links if not own.equipment.get(link)),links[0])
        if gear.get('kind')==26 and self.types.get(own.equipment.get(7))==29 and 8 in links:chosen=8
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
            if any(link in getattr(own,'required_coral_links',(5,6,7)) and self.types.get(own.equipment.get(link,0))==29 for link in affected):return None
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

    def loadout_score(self,own,equipment,item_overrides=None):
        total=0
        for link,identity in equipment.items():
            if not identity or identity==9999:continue
            supplied=(item_overrides or {}).get(link)
            observed=getattr(own,'equipment_details',{}).get(link,{})
            instance=supplied or (observed if observed.get('identity')==identity else None)
            gear=self.effective(identity,instance)
            if gear is None:return None
            if gear.get('kind')==29 and hasattr(own,'required_coral_links') and link not in own.required_coral_links:continue
            supplied=(item_overrides or {}).get(link)
            worn=getattr(own,'equipment_details',{}).get(link,{})
            if supplied is None and worn.get('identity')==identity and worn.get('valid') is False:continue
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
            total+=gear['score']+sum(gear.get(k,0)*v for k,v in weights.items())+gear.get('movement_speed',0)*.15+gear.get('movement_coefficient',0)*.072
            supplied=(item_overrides or {}).get(link)
            observed=getattr(own,'equipment_details',{}).get(link,{})
            attributes=(supplied.instance_attributes if supplied else observed.get('instance_attributes',()) if observed.get('identity')==identity else ())
            names={26:'strength',27:'agility',28:'accuracy',29:'constitution',30:'spirit'}
            for key,value in attributes:
                if key in names:total+=(value-gear.get(names[key],0))*weights.get(names[key],0)
                elif key in (34,35,36,37,38):
                    field,factor={34:('min_attack',1),35:('max_attack',1),36:('defence',4),37:('max_hp',.05),38:('max_sp',.05)}[key]
                    total+=(value-gear.get(field,0))*factor
            parameters=instance.get('parameters',(0,0)) if isinstance(instance,dict) else getattr(instance,'parameters',(0,0))
            from mechanics import forge_parts
            for stone in forge_parts(parameters[0])['slots']:
                rule=self.gems.get(str(stone['stone_type']))
                if not rule:continue
                key=rule['attribute_id'];value=rule['bonus_per_level']*stone['level']
                if key in names:total+=value*weights.get(names[key],0)
                else:total+=value*({34:2 if rule.get('attack_adds_min_and_max') else 1,35:1,36:4,37:.05,38:.05,47:4}.get(key,0))
        return total

    def upgrade(self,own,identity,free_slots=None,item=None,energy_need=1):
        change=self.transition(own,identity,free_slots,item)
        if change is None:return None
        equipment,chosen,_=change
        worn=getattr(own,'equipment_details',{}).get(chosen,{})
        if self.gear[identity].get('kind')!=29 and item and item.valid and own.equipment.get(chosen)==identity and worn.get('identity')==identity and worn.get('valid') is False:
            if item.endurance>worn.get('endurance',0):return 1,[chosen]
        # A depleted coral may be replaced by a fresh copy of the same item ID.
        if self.gear[identity].get('kind')==29:
            if hasattr(own,'required_coral_links') and chosen not in own.required_coral_links:return None
            old_id=own.equipment.get(chosen,0);old=own.equipment_details.get(chosen,{})
            if self.types.get(old_id)==29 and old.get('identity')==old_id and (old.get('energy',energy_need)<energy_need or old.get('valid') is False):
                if item is None or item.energy>=energy_need:return 1,[chosen]
                return None
            if hasattr(own,'required_coral_links') and chosen in own.required_coral_links and self.types.get(old_id)!=29:
                if item is None or item.energy>=energy_need:return 1,[chosen]
                return None
        # Compare only affected links: unrelated unknown armour is not a blocker.
        affected={chosen}|{k for k in own.equipment.keys()|equipment.keys() if own.equipment.get(k)!=equipment.get(k)}
        job=own.values.get(4)
        essential=({3,4} if job in (2,12) else {9} if job in (5,13,14) else set())
        incoming=self.gear[identity].get('kind')
        working_class_links=set()
        for link in (6,9):
            equipped=own.equipment.get(link)
            details=getattr(own,'equipment_details',{}).get(link,{})
            if (self.types.get(equipped) in essential and details.get('valid',True)
                    and (details.get('max_endurance',0)<=0 or details.get('endurance',0)>0)):
                working_class_links.add(link)
        # The reverse swap must not undo the same class requirement that
        # gives a starter staff or bow priority over a higher-scoring sword.
        if incoming not in essential and working_class_links and working_class_links<=affected:
            return None
        before=self.loadout_score(own,{k:own.equipment.get(k,0) for k in affected})
        after=self.loadout_score(own,{k:equipment.get(k,0) for k in affected},{chosen:item} if item else None)
        if before is None or after is None:return None
        gain=after-before
        if incoming in essential and not working_class_links:
            gain=max(1,gain) # A class weapon enables ranged attacks/spells even if a novice sword scores higher.
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
        self.pending=None;self.pending_refill=None;self.pending_restore=None;self.blockers=[];self.settling=False
        self.next_action=0
        self.progression_first=False;self.next_optional=0;self.pending_bag=None
        self.blacklist={}
        self.requests=self.confirmed=self.failed=0

    def loot_needs(self):
        own=self.world.own
        result=set()
        for identity,(model,handle,position,kind,source,created) in self.world.items.items():
            if self.catalog.upgrade(own,model):result.add(model)
        return result

    def urgent_upgrade(self,own,identity,link,need):
        kind=self.catalog.types.get(identity)
        worn=own.equipment_details.get(link,{})
        if kind==29:
            return link in own.required_coral_links and (self.catalog.types.get(own.equipment.get(link))!=29
                    or worn.get('energy',0)<need or worn.get('valid') is False)
        job=own.values.get(4)
        weapon=({3,4} if job in (2,12) else {9} if job in (5,13,14) else set())
        for hand in (6,9):
            equipped=own.equipment_details.get(hand,{})
            if (self.catalog.types.get(own.equipment.get(hand)) in weapon and equipped.get('valid',True)
                    and (equipped.get('max_endurance',0)<=0 or equipped.get('endurance',0)>0)):
                return False
        return kind in weapon

    def tick(self,now,policy,safe=True):
        own=self.world.own
        from coral_supplies import required_links
        own.required_coral_links=required_links(self.world)
        if self.pending:
            identity,links,deadline=self.pending
            refill_ok=not self.pending_refill or own.equipment_details.get(self.pending_refill[0],{}).get('energy',0)>self.pending_refill[1]
            restore_ok=not self.pending_restore or (own.equipment_details.get(self.pending_restore[0],{}).get('valid') is True and own.equipment_details.get(self.pending_restore[0],{}).get('endurance',0)>self.pending_restore[1])
            bag_changed=True
            if self.pending_bag:
                slot,before=self.pending_bag
                bag_changed=self.world.bag_ready and not self.world.bag_disabled and self.world.bag.get(slot)!=before
            if any(own.equipment.get(link)==identity for link in links) and refill_ok and restore_ok and bag_changed:
                self.confirmed+=1;self.pending=None;self.next_action=now+1;self.settling=True
                self.tell('Экипировка подтверждена сервером.')
            elif now>deadline:
                self.failed+=1;self.blacklist[identity]=now+300;self.pending=None
            return self.pending is not None or self.settling
        if not safe or not self.world.bag_ready or self.world.bag_disabled:return False
        if now<self.next_action:return self.settling
        self.settling=False
        signature=(own.model,own.values.get(0),own.values.get(4),getattr(own,'build_id',None),
                   self.world.bag_capacity,tuple(sorted(self.world.bag.items())),tuple(sorted(own.equipment.items())),
                   tuple((link,d.get('identity'),d.get('energy'),d.get('endurance'),d.get('valid')) for link,d in sorted(own.equipment_details.items())),
                   tuple((i,s.get('level'),s.get('energy')) for i,s in sorted(self.world.skills.items())))
        if signature==getattr(self,'scan_signature',None) and now<getattr(self,'scan_until',0):
            self.cached_scans=getattr(self,'cached_scans',0)+1;return False
        self.scan_signature=signature;self.scan_until=now+5;self.plan_scans=getattr(self,'plan_scans',0)+1
        level,job=own.values.get(0),own.values.get(4)
        if level is None or job is None:return False
        options=[];self.blockers=[]
        optional=not self.progression_first or (now>=self.next_optional and not policy.local_combat_ready(now))
        for slot,item in self.world.bag.items():
            if item.identity in self.catalog.gear and (not item.valid or item.max_endurance>0 and item.endurance<=0):
                self.blockers.append({'slot':slot,'id':item.identity,'reason':'вещь непригодна или изношена; нужен ремонт'});continue
            if (not item.valid or (self.catalog.gear.get(item.identity,{}).get('kind')==29 and item.energy<=0) or (item.max_endurance>0 and item.endurance<=0)
                    or self.blacklist.get(item.identity,0)>now):continue
            free=max(0,(self.world.bag_capacity or 0)-len(self.world.bag))
            gear=self.catalog.gear.get(item.identity,{})
            coral_skill={5:213,6:216,7:214}.get(next(iter(gear.get('links',[])),None))
            need=max(1,self.world.skills.get(coral_skill,{}).get('energy',1))
            upgrade=self.catalog.upgrade(own,item.identity,free,item,need)
            if upgrade:
                urgent=self.urgent_upgrade(own,item.identity,upgrade[1][0],need)
                if optional or urgent:
                    options.append((upgrade[0]+(1000000 if urgent else 0),slot,item.identity,upgrade[1]))
            elif item.identity in self.catalog.gear:
                gear=self.catalog.gear[item.identity]
                reason=('нужен уровень '+str(gear['level']) if gear['level']>level else
                        'не подходит раса' if own.model not in gear['bodies'] else
                        'не подходит профессия' if gear['jobs']!=[-1] and job not in gear['jobs'] else
                        'нужно место для снятой вещи' if free<1 else 'нет подтверждённого улучшения комплекта')
                self.blockers.append({'slot':slot,'id':item.identity,'reason':reason})
        pair=self.catalog.pair_upgrade(self.world,self.blacklist,now) if optional else None
        if pair:options.append(pair)
        if not options:return False
        score,slot,identity,links=max(options)
        from hunter import action_header
        # Native stNetUseItem: bag slot, automatic target=-1, exactly like double click.
        destination=-2 if self.catalog.types.get(identity)==26 and links==[8] else -1
        policy.emit(action_header(own.identity,policy.sequence,11)+struct.pack('>hh',slot,destination))
        self.requests+=1
        self.pending_bag=(slot,self.world.bag[slot]) if self.progression_first else None
        if self.progression_first and score<1000000:self.next_optional=now+60
        self.pending_refill=None
        self.pending_restore=None
        worn=own.equipment_details.get(links[0],{})
        if self.catalog.gear[identity].get('kind')!=29 and own.equipment.get(links[0])==identity and worn.get('valid') is False:self.pending_restore=(links[0],worn.get('endurance',0))
        if self.catalog.gear[identity].get('kind')==29 and own.equipment.get(links[0])==identity:
            self.pending_refill=(links[0],own.equipment_details.get(links[0],{}).get('energy',0))
        self.pending=identity,links,now+12
        self.next_action=now+1.5
        return True

    def summary(self):
        return {'plan_scans':getattr(self,'plan_scans',0),'cached_plan_reuses':getattr(self,'cached_scans',0),'candidate_blockers':self.blockers[:24],'pending_item':self.pending[0] if self.pending else None,'requests':self.requests,'confirmed_equips':self.confirmed,
                'confirmation_timeouts':self.failed,'bag_received':self.world.bag_ready,
                'inventory_paused':self.world.bag_disabled,
                'equipped_items':dict(self.world.own.equipment),'equipped_item_details':dict(self.world.own.equipment_details)}
