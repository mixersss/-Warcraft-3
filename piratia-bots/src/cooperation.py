"""Nearby bot assistance starts only after a real server-echoed request."""
import math,threading

class HelpDirectory:
 def __init__(self):self.lock=threading.Lock();self.rows={}
 def register(self,name,row):
  with self.lock:self.rows[name]=dict(row)
 def peers(self,now):
  with self.lock:
   self.rows={n:r for n,r in self.rows.items() if r['until']>now}
   return {n:dict(r) for n,r in self.rows.items()}
 def remove(self,name):
  with self.lock:self.rows.pop(name,None)

class Cooperation:
 def __init__(self,world,policy,social,personality,directory):
  self.world,self.policy,self.social,self.personality,self.directory=world,policy,social,personality,directory
  self.next_request=0;self.seen={};self.requests=self.accepts=self.refusals=0
  self.last_level=world.own.values.get(0,1);self.level_messages=0
 def busy(self):
  p=self.policy
  return bool(p.target or p.resting or (p.helper and p.helper.source is not None) or (p.market and p.market.busy)
              or any(getattr(f,'context',None) or getattr(f,'pending',None) for f in (p.adventure,p.career,p.story,p.town,p.vendor,p.travel) if f))
 def tick(self,now):
  w=self.world;p=self.policy;own=w.own;target=w.entities.get(p.target)
  self.directory.register(self.social.name,{'identity':w.own_id,'map':w.map,'position':w.position(now),
    'target':target.identity if target else None,'handle':target.handle if target else None,
    'hp':own.values.get(1,0)/max(1,own.values.get(31,1)),'level':own.values.get(0,1),'busy':self.busy(),'until':now+15})
  if own.values.get(0,1)>self.last_level:
   peers=self.directory.peers(now)
   nearby=[e for e in w.entities.values() if e.control==1 and e.name in peers and e.name!=self.social.name and math.dist(w.position(now),e.position)<1800]
   if nearby and own.alive:
    other=self.personality.rng.choice(nearby);self.social.queue_line(other.name+', поднял '+str(own.values[0])+' уровень.',now);self.level_messages+=1
   self.last_level=own.values.get(0,1)
  if now<self.next_request or not target or not target.alive or not p.combat_since or now-p.combat_since<5:return
  ratio=own.values.get(1,0)/max(1,own.values.get(31,1))
  if not .35<ratio<.72:return
  peers=self.directory.peers(now)
  candidates=[e for e in w.entities.values() if e.control==1 and e.name in peers and e.name!=self.social.name
              and peers[e.name]['map']==w.map and math.dist(w.position(now),e.position)<1800]
  if not candidates:self.next_request=now+20;return
  receiver=self.personality.rng.choice(candidates)
  self.social.queue_line(receiver.name+', помоги с мобом!',now)
  self.requests+=1;self.next_request=now+120
 def hear(self,source,text,now):
  if not text.casefold().startswith(self.social.name.casefold()+', '):return False
  person=self.world.entities.get(source);peers=self.directory.peers(now)
  if not person or person.name not in peers or peers[person.name]['identity']!=source:return False
  row=peers[person.name]
  if text.casefold()==(self.social.name+', поднял '+str(row.get('level',0))+' уровень.').casefold():
   if self.seen.get(source,0)<=now:
    self.social.queue_line(person.name+', поздравляю! У меня сейчас '+str(self.world.own.values.get(0,1))+' уровень.',now);self.seen[source]=now+30
   return True
  if not any(term in text.casefold() for term in ('помоги с мобом','выручай')):return False
  if self.seen.get(source,0)>now:return True
  self.seen={s:until for s,until in self.seen.items() if until>now};self.seen[source]=now+120
  target=self.world.entities.get(row.get('target'));own=self.world.own
  allowed,reply=self.personality.help(self.busy(),own.values.get(1,0)/max(1,own.values.get(31,1)))
  if allowed:
   if (row['map']!=self.world.map or not target or target.control!=5 or not target.alive or target.handle!=row.get('handle')
       or math.dist(self.world.position(now),target.position)>2200):
    allowed=False;reply='Не вижу твоего моба. Подойди ближе.'
   elif not self.policy.combat_allowed(target.position):
    allowed=False;reply='Моб в безопасной зоне, удар не пройдёт. Выбери другого.'
   elif (target.values.get(0,999)>own.values.get(0,1)+3
         or self.policy.learning.blocked(target.model,now)):
    allowed=False;reply='Этого моба я пока не потяну. Лучше отойди и восстановись.'
   elif self.policy.coordination and not self.policy.coordination.grant_assist(person.name,self.policy.owner,(self.world.map,target.identity,target.handle),now):
    allowed=False;reply='К тебе уже идут на помощь, я пока продолжу своё дело.'
  if allowed:
   self.policy.helper.request_bot(source,target.identity,now,self.policy);self.accepts+=1
  else:self.refusals+=1
  self.social.queue_line(person.name+', '+reply,now)
  return True
 def summary(self):return {'help_requests_queued':self.requests,'accepted_help':self.accepts,'refused_help':self.refusals,'level_messages_queued':self.level_messages,'personality':self.personality.kind}
