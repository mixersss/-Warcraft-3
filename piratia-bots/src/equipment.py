"""Equip only real owned, compatible upgrades; wait for native appearance confirmation."""
import json
import struct
from pathlib import Path


class ItemCatalog:
    def __init__(self,path):
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        self.types={int(k):v for k,v in data['types'].items()}
        self.gear={int(k):v for k,v in data['gear'].items()}

    def upgrade(self,own,identity,free_slots=None):
        gear=self.gear.get(identity)
        if (not gear or gear['level']>own.values.get(0,0) or own.model not in gear['bodies']
                or (gear['jobs']!=[-1] and own.values.get(4) not in gear['jobs'])):return None
        links=gear['links']
        if not links or any(link not in (2,3,4,6,9) for link in links):return None
        affected=set(gear.get('displaces',[links[0]]))|{links[0]}
        previous=0;occupied=0
        for link in affected:
            current=own.equipment.get(link,0)
            if not current:continue
            old=self.gear.get(current)
            if old is None:return None # Preserve unknown equipped valuables.
            previous+=old['score'];occupied+=1
        if free_slots is not None and free_slots<occupied:return None
        gain=gear['score']-previous
        return (gain,links) if gain>0 else None


class Equipment:
    def __init__(self,world,catalog,send,tell=lambda text:None):
        self.world,self.catalog,self.send,self.tell=world,catalog,send,tell
        self.pending=None
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
            if any(own.equipment.get(link)==identity for link in links):
                self.confirmed+=1;self.pending=None;self.next_action=now+1
                self.tell('Экипировка подтверждена сервером.')
            elif now>deadline:
                self.failed+=1;self.blacklist[identity]=now+300;self.pending=None
            return False
        if not safe or now<self.next_action or not self.world.bag_ready or self.world.bag_disabled:
            return False
        level,job=own.values.get(0),own.values.get(4)
        if level is None or job is None:return False
        options=[]
        for slot,item in self.world.bag.items():
            if (not item.valid or (item.max_endurance>0 and item.endurance<=0)
                    or self.blacklist.get(item.identity,0)>now):continue
            free=max(0,(self.world.bag_capacity or 0)-len(self.world.bag))
            upgrade=self.catalog.upgrade(own,item.identity,free)
            if upgrade:options.append((upgrade[0],slot,item.identity,upgrade[1]))
        if not options:return False
        _,slot,identity,links=max(options)
        from hunter import action_header
        # Native stNetUseItem: bag slot, automatic target=-1, exactly like double click.
        policy.emit(action_header(own.identity,policy.sequence,11)+struct.pack('>hh',slot,-1))
        self.requests+=1
        self.pending=identity,links,now+12
        self.next_action=now+1.5
        return True

    def summary(self):
        return {'requests':self.requests,'confirmed_equips':self.confirmed,
                'confirmation_timeouts':self.failed,'bag_received':self.world.bag_ready,
                'inventory_paused':self.world.bag_disabled,
                'equipped_items':dict(self.world.own.equipment)}
