"""Learn a stable life profession from owned native books, after the stall skill."""
import hashlib,struct

PATHS=((3226,200,2679,338,'manufacturing'),(3225,201,2699,340,'crafting'),(3294,231,2689,339,'cooking'))
PROTECTED={i for p in PATHS for i in (p[0],p[2])}|{1067,1068,1069,2300,2301,2302}

class LifeProfessions:
 def __init__(self,world,life,name,economy):
  self.world,self.life,self.economy=world,life,economy
  seed=int.from_bytes(hashlib.sha256((name+':life-profession').encode()).digest()[:8],'big')
  self.active=seed%100<15;self.path=PATHS[seed%3];self.pending=None;self.next_action=0
  self.requests=self.confirmed=self.timeouts=0;self.reason='';self.clock=0
 def next_book(self):
  w=self.world
  if not self.active or w.own.values.get(4,0)==0 or not w.skills.get(241,{}).get('level',0):return None
  first,skill,book,production,_=self.path
  if not w.skills.get(skill,{}).get('level',0):return first,skill
  if not w.skills.get(production,{}).get('level',0):return book,production
  return None
 def needs_points(self):return bool(self.next_book() and self.world.own.values.get(13,0)<1)
 def purchase_goals(self):
  book=self.next_book()
  if not book or self.world.own.values.get(13,0)<1 or self.economy.phase(self.world,self.clock)!='professions':return []
  if any(i.identity==book[0] for i in self.world.bag.values()):return []
  return [(book[0],1,'изучает мирную профессию '+self.path[-1])]
 def tick(self,now,policy,safe,dialogue_busy=False):
  self.clock=now;w=self.world
  if self.pending:
   slot,identity,skill,count,level,points,deadline=self.pending;item=w.bag.get(slot)
   if not w.bag_ready or w.bag_disabled:
    if now>=deadline:self.timeouts+=1;self.pending=None;self.next_action=now+300
    return self.pending is not None
   consumed=sum(i.count for i in w.bag.values() if i.identity==identity)<count
   if consumed and w.skills.get(skill,{}).get('level',0)>level and w.own.values.get(13,points)<points:
    self.confirmed+=1;self.pending=None;self.next_action=now+2
   elif now>=deadline:self.timeouts+=1;self.pending=None;self.next_action=now+300
   return self.pending is not None
  if (not safe or dialogue_busy or now<self.next_action or not w.bag_ready or w.bag_disabled
      or (w.bag_capacity or 0)-len(w.bag)<1 or w.own.values.get(13,0)<1
      or self.economy.phase(w,now)!='professions'):return False
  book=self.next_book()
  if not book:return False
  identity,skill=book
  slot=next((s for s,i in w.bag.items() if i.identity==identity and i.valid),None)
  if slot is None:return False
  from hunter import action_header
  policy.emit(action_header(w.own_id,policy.sequence,11)+struct.pack('>hh',slot,-1))
  self.pending=slot,identity,skill,sum(i.count for i in w.bag.values() if i.identity==identity),w.skills.get(skill,{}).get('level',0),w.own.values[13],now+15
  self.requests+=1;self.reason='изучает мирную профессию '+self.path[-1];return True
 def summary(self):
  return {'assigned':self.active,'profession':self.path[-1],'prerequisite_skill':self.path[1],
   'prerequisite_level':self.world.skills.get(self.path[1],{}).get('level',0),'production_skill':self.path[3],
   'production_level':self.world.skills.get(self.path[3],{}).get('level',0),'requests':self.requests,
   'confirmed_learns':self.confirmed,'timeouts':self.timeouts,'state':self.reason,'automatic_production_enabled':False}
