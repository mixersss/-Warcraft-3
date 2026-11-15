"""Bounded recovery using an owned native city ticket; never grant or move locally."""
import struct

class StuckReturn:
    def __init__(self):
        self.pending=None;self.next_try=0;self.requests=self.confirmed=self.timeouts=0
        self.reason='';self.arrival=False
        self.last_ticket=None
    def on_map(self,map_name):
        if self.pending and map_name==self.pending[1]:self.arrival=True
    def poll(self,now,policy):
        if not self.pending:return False
        identity,map_name,before,deadline=self.pending
        w=policy.world
        after=sum(i.count for i in w.bag.values() if i.identity==identity)
        if self.arrival and w.bag_ready and not w.bag_disabled and after<before:
            self.confirmed+=1;self.pending=None;self.reason='возврат билетом подтверждён сервером';return False
        if now>=deadline:
            self.timeouts+=1;self.pending=None;self.next_try=now+300
            self.reason='нет двойного подтверждения билета и прибытия';return False
        self.reason='ожидает расход билета и настоящее прибытие';return True
    def tick(self,now,policy,destination=None):
        if self.poll(now,policy):return True
        requested={'garner':4602,'magicsea':4603,'darkblue':4604,'jialebi':2445}.get(destination)
        if now<self.next_try and (requested is None or requested==self.last_ticket):return False
        w=policy.world;own=w.own
        if (not own or not own.alive or own.model not in (1,2,3,4) or not w.bag_ready
            or w.bag_disabled or policy.transaction_busy()):return False
        preferred={'garner':4602,'magicsea':4603,'darkblue':4604}.get(w.map)
        wanted={'garner':4602,'magicsea':4603,'darkblue':4604,'jialebi':2445}.get(destination)
        allowed=(4602,4603,4604,2445) if destination=='jialebi' else (4602,4603,4604)
        options=[(slot,i) for slot,i in w.bag.items() if i.identity in allowed and i.valid and i.count>0]
        if destination is not None:options=[row for row in options if row[1].identity==wanted]
        if not options:self.reason='нет собственного билета для возврата';return False
        slot,item=min(options,key=lambda row:(row[1].identity!=preferred,row[0]))
        if any(own.values.get(current,-1)<own.values.get(maximum,1) for current,maximum in ((1,31),(2,32))):
            self.reason='билет требует полные HP и SP';return False
        if policy.pending_action:return True
        if policy.sitting.tick(now,policy,False):return True
        from hunter import action_header
        policy.emit(action_header(own.identity,policy.sequence,11)+struct.pack('>hh',slot,-1))
        destination={4602:'garner',4603:'magicsea',4604:'darkblue',2445:'jialebi'}[item.identity]
        before=sum(i.count for i in w.bag.values() if i.identity==item.identity)
        self.pending=(item.identity,destination,before,now+20);self.arrival=False
        self.last_ticket=item.identity
        self.requests+=1;self.next_try=now+600;self.reason='использует собственный билет для сокращения пути' if wanted else 'использует собственный билет из застрявшей точки'
        return True
    def summary(self):
        return {'requests':self.requests,'confirmed_returns':self.confirmed,'timeouts':self.timeouts,
                'pending':bool(self.pending),'reason':self.reason}
