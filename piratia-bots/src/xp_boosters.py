"""Buy/use real EXP consumables; item consumption AND native state48 confirm use."""
import struct

BOOSTS=((3095,60,3,1800),(3880,60,3,900),(3879,40,2,900),(3094,0,1,1800),(3844,0,1,900))
STRIVE_AMPLIFIERS={3094,3095,3879,3880}

class XPBoosters:
 def __init__(self,world,life,economy):
  self.world,self.life,self.economy=world,life,economy
  self.pending=None;self.retry=0;self.requests=0;self.confirmed=0;self.timeouts=0;self.reason=''
  self.confirmed_items={};self.purchased_items={}
 @property
 def busy(self):return self.pending is not None
 def purchase_goals(self,offers=None):
  w=self.world
  if not w.own or w.own.values.get(0,0)<10 or getattr(w,'own_states',{}).get(48,0):return []
  if any(i.identity in {b[0] for b in BOOSTS} and i.valid for i in w.bag.values()):return []
  level=w.own.values.get(0,0);cash=w.own.values.get(8,0)
  chosen=next((i for i,minimum,_,_ in BOOSTS if minimum<=level and (offers is None or i in offers) and 0<self.life.prices.get(i,0)<=cash-2000),None)
  return [(chosen,1,'усилитель опыта для реальной прокачки')] if chosen else []
 def tick(self,now,policy,safe,dialogue_busy=False):
  w=self.world
  if self.pending:
   identity,count,rank,deadline=self.pending
   if sum(i.count for i in w.bag.values() if i.identity==identity)<count and getattr(w,'own_states',{}).get(48,0)>=rank:
    self.confirmed+=1;self.pending=None;self.reason='Усилитель опыта подтверждён сервером'
    self.confirmed_items[identity]=self.confirmed_items.get(identity,0)+1
    return False
   if now>=deadline:self.pending=None;self.timeouts+=1;self.retry=now+60
   return False
  care_pending=getattr(getattr(policy,'petcare',None),'pending',None)
  if isinstance(care_pending,dict) and care_pending.get('kind')=='berry':return False
  if (not safe or dialogue_busy or now<self.retry or w.bag_disabled or not w.bag_ready
      or getattr(w,'own_states',{}).get(48,0) or self.economy.phase(w,now)!='progression'):return False
  for identity,minimum,rank,_ in BOOSTS:
   if w.own.values.get(0,0)<minimum:continue
   slot=next((s for s,i in w.bag.items() if i.identity==identity and i.valid),None)
   if slot is None:continue
   from hunter import action_header
   policy.emit(action_header(w.own_id,policy.sequence,11)+struct.pack('>hh',slot,-1))
   count=sum(i.count for i in w.bag.values() if i.identity==identity)
   self.pending=(identity,count,rank,now+24);self.retry=now+60;self.requests+=1
   self.reason='Применяет купленный усилитель опыта; ждёт состояние48';return True
  return False
 def summary(self):return {'state':self.reason,'requests':self.requests,'confirmed':self.confirmed,'confirmed_items':dict(self.confirmed_items),'purchased_items':dict(self.purchased_items),'timeouts':self.timeouts,'native_state':getattr(self.world,'own_states',{}).get(48,0),'pending':bool(self.pending),'free_boosts_granted':False}
