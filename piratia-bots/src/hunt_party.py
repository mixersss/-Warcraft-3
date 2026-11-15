"""World LFG -> private reply -> bounded rendezvous -> native confirmed hunt.

The shared directory carries positions and capacity leases only. Chat packets
and the native team snapshot are required before travelling or fighting as a team.
"""
import math
import random
from classic_wire import Reader,ProtocolError
from contacts import private_request


class HuntParty:
    def __init__(self,world,policy,party,send):
        self.world,self.policy,self.party,self.send=world,policy,party,send
        self.directory=party.directory;self.name=party.name
        self.rng=random.Random(self.name+':hunt-party')
        self.leader=None;self.until=0;self.offer_until=0;self.meet=None
        self.accepted=False;self.respondents={};self.next_offer=0;self.next_reply=0
        self.replies=self.acknowledgements=self.timeouts=self.meet_moves=0
        self.progress=None;self.last_progress=None;self.unproductive_sessions=0
        self.reason='';party.recruitment=self

    def active(self):
        return bool(self.leader and len(self.party.members)>1 and
                    self.name in self.party.members and self.party.members[0]==self.leader
                    and not any(n in self.party.humans for n in self.party.members))

    def wants_xp(self,now):
        p=self.policy;w=self.world
        if (not w.own.alive or p.mandatory_work() or p.transaction_busy() or p.resting
                or getattr(p,'inventory_blocked',False)):return False
        if any(getattr(f,'context',None) or getattr(f,'pending',None) for f in
               (p.town,p.vendor,p.career,p.story,p.travel,p.adventure) if f):return False
        if p.town and getattr(p.town,'rest_until',0)>now:return False
        if getattr(getattr(p,'helper',None),'source',None) is not None:return False
        if hasattr(p.nav,'needs_recovery') and p.nav.needs_recovery(w.position(now)):return False
        economy=getattr(p,'economy',None)
        return self.active() or not economy or economy.phase(w,now)=='progression'

    def tick(self,now):
        w=self.world;p=self.policy
        target=w.entities.get(p.target)
        self.directory.annotate(self.name,wants_xp=self.wants_xp(now),
            hunt_target=target.identity if target and target.alive else None)
        if self.leader and any(n in self.party.humans for n in self.party.members):
            self.reset(now,'пати с игроком; автоматический сбор отключён');return
        if self.leader and not self.active() and now>=self.until:
            self.timeouts+=1;self.reset(now,'встреча истекла; продолжает обычные дела')
        if self.active():
            current=(w.own.values.get(0,1),w.own.values.get(15,0))
            if self.progress is None or current[0]>self.progress[0] or (current[0]==self.progress[0] and current[1]>self.progress[1]):
                self.last_progress=now
            self.progress=current
            if self.last_progress is not None and now-self.last_progress>=120:
                # Existing Party.tick sends leave only when safe and waits for
                # the real server roster. Solo hunting can resume meanwhile.
                self.party.session_until=now;self.unproductive_sessions+=1
                self.reset(now,'пати не приносит опыта; меняет охоту и безопасно выходит');return
            peer=self.directory.lookup(self.leader,now) if self.leader!=self.name else True
            if not peer or (peer is not True and peer['map']!=w.map):
                self.reset(now,'лидер недоступен; продолжает обычные дела')

    def reset(self,now,reason):
        self.leader=None;self.until=0;self.accepted=False;self.meet=None;self.respondents.clear()
        self.offer_until=0;self.next_offer=now+self.rng.uniform(180,420);self.reason=reason
        self.progress=None;self.last_progress=None
        self.directory.annotate(self.name,offer_until=0,recruits={})

    def advertisement(self,now):
        if (now<self.next_offer or self.leader or self.party.members or not self.wants_xp(now)):
            return None
        return f'Ищу пати на кач, {self.world.own.values.get(0,1)} ур. Кто рядом — пишите в ЛС!'

    def accepts(self,name,now):
        peer=self.directory.lookup(name,now)
        return bool(peer and self.leader==name and self.accepted and now<self.until and self.wants_xp(now)
                    and peer['map']==self.world.map and abs(peer['level']-self.world.own.values.get(0,1))<=3)

    def observe(self,command,payload,now):
        if command not in (5402,5403):return
        try:
            r=Reader(payload);sender=r.string()
            receiver=r.string() if command==5403 else None
            text=r.string()
            if len(r.data)-r.position==4:r.long()
            r.end()
        except (ProtocolError,UnicodeError):return
        w=self.world;level=w.own.values.get(0,1)
        if command==5402 and sender==self.name and text==self.advertisement(now):
            # Only the real world-channel echo opens a recruitment window.
            self.leader=self.name;self.until=now+90;self.offer_until=now+90
            self.meet=tuple(w.position(now));self.next_offer=now+900
            self.directory.annotate(self.name,offer_until=self.offer_until,meet=self.meet,recruits={})
            self.reason='объявление о пати подтверждено мировым чатом';return
        peer=self.directory.lookup(sender,now)
        if (not peer or peer['map']!=w.map or abs(peer['level']-level)>3
                or not peer.get('wants_xp') or not self.wants_xp(now)):return
        if command==5402:
            expected=f"Ищу пати на кач, {peer['level']} ур. Кто рядом — пишите в ЛС!"
            if (text!=expected or self.leader or self.party.members or now<self.next_reply
                    or math.dist(w.position(now),peer['position'])>12000):return
            # Receiver may process the broadcast before its sender; register the
            # same observed offer without inventing a message or an acceptance.
            if peer.get('offer_until',0)<=now:
                self.directory.annotate(sender,offer_until=now+90,meet=tuple(peer['position']),recruits={})
            if not self.directory.claim_recruit(sender,self.name,now):return
            self.send(6403,private_request(sender,f'Хочу в пати на кач, {level} ур.'))
            self.replies+=1;self.leader=sender;self.until=now+90;self.meet=tuple(peer.get('meet',peer['position']))
            self.accepted=False;self.next_reply=now+180;self.reason='откликнулся в ЛС; ждёт ответ лидера'
        elif receiver==self.name:
            if (self.leader==self.name and now<self.offer_until and
                    text==f"Хочу в пати на кач, {peer['level']} ур." and
                    math.dist(w.position(now),peer['position'])<=12000):
                if sender in self.respondents or len(self.respondents)>=4:return
                if not self.directory.claim_recruit(self.name,sender,now):return
                self.respondents[sender]=now+90
                self.send(6403,private_request(sender,'Пати на кач: встречаемся рядом со мной.'))
                self.acknowledgements+=1;self.reason='договорился о встрече в ЛС'
            elif (self.leader==sender and now<self.until and
                    text=='Пати на кач: встречаемся рядом со мной.'):
                self.accepted=True;self.reason='идёт на подтверждённую встречу для кача'

    def target(self,now):
        if not self.active() or self.leader==self.name:return None
        peer=(self.directory.lookup(self.leader,now) or {})
        entity=self.world.entities.get(peer.get('hunt_target'))
        return entity if entity and entity.alive else None

    def work(self,now,policy,safe):
        if not self.leader:return False
        if not self.wants_xp(now):
            if not self.active():self.reset(now,'срочное дело; встреча отменена')
            return False
        if not safe or policy.target or self.party.leave_pending:return False
        if self.leader==self.name and now<self.offer_until:
            peers=self.directory.peers(self.name,now)
            for name in list(self.respondents):
                peer=peers.get(name)
                if (peer and peer.get('wants_xp') and peer['map']==self.world.map
                        and abs(peer['level']-self.world.own.values.get(0,1))<=3
                        and math.dist(self.world.position(now),peer['position'])<2000):
                    if self.party.request_bot(name,now):self.reason='отправил игровое приглашение в пати'
        if self.active():
            if self.leader==self.name:return False
            peer=self.directory.lookup(self.leader,now)
            if not peer:return False
            if math.dist(self.world.position(now),peer['position'])<=1000:return False
            goal=policy.nav.nearest(peer['position'],3)
        elif now>=self.until:return False
        elif self.leader==self.name:
            # Never hold a whole fleet for an unanswered world advertisement.
            return False
        elif not self.accepted:return False
        else:
            peer=self.directory.lookup(self.leader,now)
            if not peer or peer['map']!=self.world.map:
                self.reset(now,'лидер ушёл; продолжает обычные дела');return False
            # Follow the moving leader instead of waiting at an obsolete point.
            goal=policy.nav.nearest(peer['position'],3)
            if math.dist(self.world.position(now),peer['position'])<1500:
                return False # Nearby fights remain useful while invitation arrives.
        if goal and policy.move_to(goal,now):
            self.meet_moves+=1;policy.change('идёт к своей группе для совместной охоты');return True
        self.reset(now,'к группе нет пути; продолжает обычные дела');return False

    def summary(self):
        return {'leader':self.leader,'native_team_confirmed':self.active(),'private_replies_sent':self.replies,
                'private_meeting_confirmations_sent':self.acknowledgements,'meeting_moves':self.meet_moves,
                'expired_meetings':self.timeouts,'unproductive_sessions_abandoned':self.unproductive_sessions,
                'reason':self.reason,'maximum_level_gap':3}
