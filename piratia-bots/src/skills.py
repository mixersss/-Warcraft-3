"""Learn only the owned first-profession reward book, using real skill points."""
import struct

BOOKS={1:(3164,66),2:(3187,74),5:(3206,97),4:(3227,210)}


class Skills:
    def __init__(self,world,role):
        self.world,self.role=world,role
        self.pending=None
        self.next_action=0
        self.requests=self.confirmed=self.timeouts=0

    def tick(self,now,policy,safe):
        if self.pending:
            identity,level,points,deadline=self.pending
            if self.world.skills.get(identity,{}).get('level',0)>=level and self.world.own.values.get(7,points)<points:
                self.confirmed+=1;self.pending=None;self.next_action=now+3
            elif now>=deadline:
                self.timeouts+=1;self.pending=None;self.next_action=now+300
            return False
        own=self.world.own
        if (not safe or now<self.next_action or not self.role or own.values.get(0,0)<10
                or own.values.get(4) not in (self.role['first_job'],self.role['target_job'])):return False
        book,skill=BOOKS[self.role['first_job']]
        current=self.world.skills.get(skill,{}).get('level',0)
        points=own.values.get(7,0)
        if not current and points>=1 and self.world.bag_ready and not self.world.bag_disabled:
            slot=next((slot for slot,item in self.world.bag.items() if item.identity==book and item.valid),None)
            if slot is None:return False
            from hunter import action_header
            policy.emit(action_header(own.identity,policy.sequence,11)+struct.pack('>hh',slot,-1))
            target=1
        elif 0<current<3 and points>=3:
            policy.send(11,struct.pack('>HB',skill,1))
            target=current+1
        else:return False
        self.requests+=1
        self.pending=skill,target,points,now+12
        return True

    def summary(self):
        return {'requests':self.requests,'confirmed_learns_or_upgrades':self.confirmed,
                'confirmation_timeouts':self.timeouts,'known_skills':{k:v['level'] for k,v in self.world.skills.items()}}
