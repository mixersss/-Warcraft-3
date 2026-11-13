"""Classic action21 ground sitting; pose echoes and HP remain server-owned."""
import math
import struct


def pose_request(actor,sequence,seated,angle=0):
    if not 0<=angle<360:raise ValueError('Invalid facing')
    return struct.pack('>IIBHH',actor,sequence,21,angle,16 if seated else 1)


class Sitting:
    def __init__(self,world):
        self.world=world;self.requests=self.confirmed=self.timeouts=self.hp_observed=0
        self.reset()
    def reset(self):
        self.pending=None;self.last_hp=None;self.last_hurt=-1e9;self.next_sit=0
        self.healed_at=0;self.seated_at=None;self.attempts=0
    def tick(self,now,policy,wounded):
        w=self.world;hp=w.own.values.get(1,0)
        if self.last_hp is not None:
            if hp<self.last_hp:self.last_hurt=now
            if hp>self.last_hp and w.seated:self.hp_observed+=hp-self.last_hp;self.healed_at=now
        self.last_hp=hp
        safe=(now-self.last_hurt>=5 and not policy.target and not policy.pending_action
              and not any(e.control==5 and e.alive and math.dist(w.position(now,e.identity),policy.position(now))<900 for e in w.entities.values()))
        want=bool(wounded and safe)
        if w.seated:
            if self.seated_at is None:self.seated_at=now;self.healed_at=now
            if now-self.healed_at>30:
                want=False;self.next_sit=now+60
        else:self.seated_at=None
        if self.pending:
            sequence,desired,deadline=self.pending
            if w.pose_packet_number==sequence and w.seated==desired:
                self.confirmed+=1;self.pending=None;self.attempts=0
            elif now<deadline:return True
            else:
                self.pending=None;self.timeouts+=1;self.attempts+=1
                if desired:self.next_sit=now+15;return False
                # Never report standing without the server echo. Keep retries
                # spaced; native movement/attack reject a still seated actor.
        if w.seated==want:
            return bool(want)
        if want and now<self.next_sit:return False
        if policy.pending_action:return True
        sequence=policy.sequence
        policy.emit(pose_request(w.own_id,sequence,want))
        self.requests+=1;self.pending=(sequence,want,now+5)
        return True
    def summary(self):
        return {'pose_requests':self.requests,'confirmed_pose_changes':self.confirmed,
                'confirmation_timeouts':self.timeouts,'server_seated':self.world.seated,
                'hp_increases_observed_while_seated':self.hp_observed,'awaiting_pose_echo':bool(self.pending)}
