"""Explicit nearby human request: approach and assist one suitable visible weak monster."""
import math
class HelpPlayer:
 def __init__(self,world):
  self.world=world;self.source=None;self.until=0;self.started=0;self.last_progress=0;self.last_position=None
  self.accepted=self.finished=self.expired=0
  self.personality=None;self.bot_target=None
 def request_bot(self,source,target,now,policy):
  self.source=source;self.bot_target=target;self.until=now+90
  self.started=self.last_progress=now;self.last_position=policy.position(now);self.accepted+=1
  policy.assist_target=target
 def request(self,source,now,policy):
  person=self.world.entities.get(source)
  if not person or person.control!=1 or person.name.lower().startswith('bot'):return 'Не вижу тебя рядом. Подойди ближе и позови по имени.'
  busy=(policy.target or policy.resting or (policy.market and policy.market.busy)
        or any(getattr(f,'context',None) or getattr(f,'pending',None) for f in (policy.travel,policy.adventure,policy.story,policy.career,policy.town) if f))
  if busy:return 'Сейчас занят делом. Позови чуть позже, когда освобожусь.'
  if self.personality:
   accepted,reply=self.personality.help(False,self.world.own.values.get(1,0)/max(1,self.world.own.values.get(31,1)))
   if not accepted:return reply
  self.bot_target=None
  self.source=source;self.until=now+120;self.started=self.last_progress=now;self.last_position=policy.position(now);self.accepted+=1
  return 'Иду к тебе. Помогу с ближайшим слабым мобом, если смогу до него добраться.'
 def active(self,now):return self.source is not None and now<self.until
 def tick(self,now,policy):
  if self.source is None:return False
  person=self.world.entities.get(self.source)
  if not person or not person.alive or now>=self.until or self.world.own.values.get(1,0)<self.world.own.values.get(31,1)*.55:
   self.source=None;policy.assist_target=None;self.expired+=1;return False
  pos=policy.position(now)
  if math.dist(pos,self.last_position)>=100:self.last_position=pos;self.last_progress=now
  if not policy.target and now-self.last_progress>35:self.source=None;policy.assist_target=None;self.expired+=1;return False
  if self.bot_target is not None:
   target=self.world.entities.get(self.bot_target)
   rule=getattr(policy,'combat_allowed',None)
   if not target or not target.alive or (rule and not rule(target.position)):
    self.source=None;self.bot_target=None;policy.assist_target=None;self.finished+=1;return False
   policy.assist_target=self.bot_target
   return False
  if policy.target:return False
  if math.dist(pos,person.position)>350:
   goal=policy.nav.nearest(person.position,3)
   if goal and policy.move_to(goal,now):policy.change('идёт на просьбу о помощи');return True
   self.source=None;policy.assist_target=None;self.expired+=1;return False
  candidates=[e for e in self.world.entities.values() if e.control==5 and e.alive and e.handle
              and 0<e.values.get(0,999)<=min(45,self.world.own.values.get(0,1))
              and math.dist(e.position,person.position)<1200
              and (not policy.coordination or policy.coordination.available(policy.owner,(self.world.map,e.identity,e.handle),now))]
  rule=getattr(policy,'combat_allowed',None)
  allowed=[e for e in candidates if not rule or rule(e.position)]
  if candidates and not allowed:
   self.source=None;policy.assist_target=None;self.expired+=1;return False
  candidates=allowed
  if candidates:
   policy.assist_target=min(candidates,key=lambda e:math.dist(pos,e.position)).identity
  else:
   policy.assist_target=None;policy.next_action=now+1;policy.change('рядом с игроком; ждёт подходящего моба');return True
  return False
 def summary(self):return {'active':self.source is not None,'accepted_requests':self.accepted,'expired_requests':self.expired}
