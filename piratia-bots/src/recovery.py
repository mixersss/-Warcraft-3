"""Use owned instant healing food; real consumption AND native HP are required."""
import struct

HP_FOOD={1847:20,1848:80,1849:180,3122:250,3123:300,3124:350,3125:400,3126:450,3127:500,3128:550}
SP_FOOD={3099:150,3134:38,3135:41,3136:59,3137:100,3138:111,3139:141,3140:201}


class Recovery:
    def __init__(self,world):
        self.world=world
        self.pending=None
        self.next_use=0
        self.requests=self.confirmed=self.timeouts=0
        self.used_items={};self.pending_identity=1847
        self.pending_attribute=1;self.pending_total=0

    def tick(self,now,policy):
        own=self.world.own
        if self.pending:
            slot,count,hp,deadline=self.pending
            current=self.world.bag.get(slot)
            remaining=current.count if current and current.identity==self.pending_identity else 0
            consumed=sum(i.count for i in self.world.bag.values() if i.identity==self.pending_identity)<self.pending_total
            if consumed and own.values.get(self.pending_attribute,0)>hp:
                self.confirmed+=1;self.pending=None
            elif now>=deadline:
                self.timeouts+=1;self.pending=None;self.next_use=now+120
            return False
        hp,maximum=own.values.get(1,0),own.values.get(31,0)
        if (now<self.next_use or not own.alive or not self.world.bag_ready or self.world.bag_disabled
                or not maximum):return False
        candidates=[]
        for attribute,max_attribute,threshold,foods in ((1,31,.55,HP_FOOD),(2,32,.35,SP_FOOD)):
            current,pool=own.values.get(attribute,0),own.values.get(max_attribute,0)
            if not pool or current/pool>threshold or pool-current<20:continue
            candidates=[(slot,item) for slot,item in self.world.bag.items() if item.identity in foods and item.valid and item.count>0]
            if candidates:
                hp=current;missing=pool-current;break
        # Prefer enough healing per action for a developed character. Never
        # consume a reputation cake, stat buff or fairy item by its name.
        candidate=max(candidates,key=lambda row:min(missing,foods[row[1].identity])) if candidates else None
        if candidate is None:return False
        slot,item=candidate
        from hunter import action_header
        policy.emit(action_header(own.identity,policy.sequence,11)+struct.pack('>hh',slot,-1))
        self.requests+=1
        self.pending_identity=item.identity;self.used_items[item.identity]=self.used_items.get(item.identity,0)+1
        self.pending_attribute=attribute;self.pending_total=sum(i.count for i in self.world.bag.values() if i.identity==item.identity)
        self.pending=slot,item.count,hp,now+12
        self.next_use=now+8
        return True

    def summary(self):
        return {'apple_requests':self.used_items.get(1847,0),'food_requests':self.requests,'requested_items':dict(self.used_items),'confirmed_uses':self.confirmed,'timeouts':self.timeouts}
