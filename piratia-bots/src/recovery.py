"""Use owned beginner apples; verify real item consumption and HP recovery."""
import struct


class Recovery:
    def __init__(self,world):
        self.world=world
        self.pending=None
        self.next_use=0
        self.requests=self.confirmed=self.timeouts=0

    def tick(self,now,policy):
        own=self.world.own
        if self.pending:
            slot,count,hp,deadline=self.pending
            current=self.world.bag.get(slot)
            remaining=current.count if current and current.identity==1847 else 0
            if remaining<count and own.values.get(1,0)>hp:
                self.confirmed+=1;self.pending=None
            elif now>=deadline:
                self.timeouts+=1;self.pending=None;self.next_use=now+120
            return False
        hp,maximum=own.values.get(1,0),own.values.get(31,0)
        if (now<self.next_use or not own.alive or not self.world.bag_ready or self.world.bag_disabled
                or not maximum or hp/maximum>.55 or maximum-hp<20):return False
        candidate=next(((slot,item) for slot,item in self.world.bag.items()
                        if item.identity==1847 and item.valid and item.count>0),None)
        if candidate is None:return False
        slot,item=candidate
        from hunter import action_header
        policy.emit(action_header(own.identity,policy.sequence,11)+struct.pack('>hh',slot,-1))
        self.requests+=1
        self.pending=slot,item.count,hp,now+12
        self.next_use=now+8
        return True

    def summary(self):
        return {'apple_requests':self.requests,'confirmed_uses':self.confirmed,'timeouts':self.timeouts}
