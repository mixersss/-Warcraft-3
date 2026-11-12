"""Native opt-in bot parties; never invite or accept unknown human characters."""
import struct,threading,math
from classic_wire import Reader,string,ProtocolError

class BotDirectory:
    def __init__(self):self.lock=threading.Lock();self.rows={}
    def update(self,name,index,map_name,position,level,now):
        with self.lock:
            old=self.rows.get(name,{})
            self.rows[name]=dict(old,index=index,map=map_name,position=position,level=level,until=now+15)
    def clear_team(self,name):
        with self.lock:
            for row in self.rows.values():
                if name in row.get('team',()):row['team']=()
    def remove(self,name):
        self.clear_team(name)
        with self.lock:self.rows.pop(name,None)
    def peers(self,name,now):
        with self.lock:return {k:dict(v) for k,v in self.rows.items() if v['until']>now and k!=name}
    def team(self,names):
        with self.lock:
            if not all(n in self.rows for n in names):return False
            for n in names:self.rows[n]['team']=tuple(names)
            return True

class Party:
    def __init__(self,world,send,name,index,directory):
        self.world,self.send,self.name,self.index,self.directory=world,send,name,index,directory
        self.next_invite=0;self.pending=None;self.members=();self.invites=self.accepts=self.refreshes=0
    def observe(self,command,payload,now):
        r=Reader(payload)
        if command==5001:
            name,identity=r.string(),r.long();r.short();r.end()
            peer=self.directory.peers(self.name,now).get(name)
            # Both endpoints must be running known bots, on the same map nearby.
            if (peer and peer['index']%5==1 and peer['map']==self.world.map
                    and self.index%3 and not self.members
                    and math.dist(peer['position'],self.world.position(now))<3000):
                self.send(6002,struct.pack('>I',identity));self.accepts+=1
            else:self.send(6003,struct.pack('>I',identity))
        elif command==5002:
            kind,count=r.byte(),r.byte()
            if count>5:raise ProtocolError('Unsupported party size')
            names=[]
            for _ in range(count):
                r.long();names.append(r.string());r.string_bytes();r.short()
            r.end()
            self.directory.clear_team(self.name)
            if self.name in names and self.directory.team(names):
                self.members=tuple(names);self.refreshes+=1;self.pending=None
            elif count<=1:self.members=();self.pending=None
        elif command==5003:
            self.pending=None;self.next_invite=now+60
    def tick(self,now,index):
        w=self.world
        self.directory.update(self.name,index,w.map,w.position(now),w.own.values.get(0,1),now)
        if self.pending and now>self.pending:self.pending=None
        if index%5!=1 or index%3==0 or now<self.next_invite or self.pending or not w.own.alive:return
        peers=self.directory.peers(self.name,now)
        if self.members and self.members[0]!=self.name:return
        if len(self.members)>=3:return
        for name,peer in sorted(peers.items(),key=lambda kv:kv[1]['index']):
            if (peer['index']%3 and peer['index']%5!=1 and not peer.get('team') and peer['map']==w.map
                    and abs(peer['level']-w.own.values.get(0,1))<=5
                    and math.dist(peer['position'],w.position(now))<2500):
                self.send(6001,string(name));self.invites+=1;self.pending=now+12;self.next_invite=now+60
                break
    def summary(self):return {'invite_requests':self.invites,'accept_requests':self.accepts,'confirmed_size':len(self.members),'refreshes':self.refreshes}
