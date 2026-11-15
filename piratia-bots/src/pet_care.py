"""Source-backed second-generation fairy care using real bag actions and confirmations."""
import hashlib,struct
from builds import PROFILES

FAIRIES={'STR':232,'CON':233,'STA':234,'DEX':235,'AGI':236}
FRUITS={'STR':276,'CON':277,'DEX':278,'AGI':279,'STA':280}
BUILD_STATS={'crusader_speed':'STR','sharpshooter_precision':'DEX','sharpshooter_speed':'DEX',
 'cleric_spirit':'STA','sealmaster_balanced':'STA','voyager_spirit':'STA','voyager_tank':'CON','champion_tank':'CON'}
PET_IDS=set(range(231,238))|{681}
PROTECTED=PET_IDS|set(FRUITS.values())|{227,2312,609,3844,4602,4603,4604}

class PetCare:
 def __init__(self,world,life,mechanics,name,role=None):
  self.world,self.life,self.mechanics=world,life,mechanics
  digest=hashlib.sha256((name+':fairy').encode()).digest()
  self.build_id=getattr(world.own,'build_id',None);self.junior=digest[0]%4==0
  job=(role or {}).get('target_job',world.own.values.get(4))
  self.stat=BUILD_STATS.get(self.build_id) or {1:'STR',9:'STR',8:'CON',2:'DEX',12:'DEX',4:'STA',5:'STA',13:'STA',14:'STA',16:'STA'}.get(job,'STR')
  self.preferred=681 if self.junior else FAIRIES[self.stat]
  self.pending=None;self.next_action=0;self.berry_retry=0;self.reason='';self.clock=0;self.home_city='garner'
  self.moves=self.feed_requests=self.fruit_requests=self.berry_requests=self.skill_requests=0
  self.confirmed=self.timeouts=self.growth_success=self.growth_failures=0
 def count(self,identity):return sum(i.count for i in self.world.bag.values() if i.identity==identity)
 def align_build(self):
  current=getattr(self.world.own,'build_id',None)
  if current==self.build_id or self.pending:return
  build=PROFILES.get(current);existing=self.fairy()
  if build and (not existing or existing[2]['level']==0):
   self.stat=BUILD_STATS.get(current,'STR')
   self.preferred=681 if self.junior else FAIRIES[self.stat]
  self.build_id=current
 def fairy(self):
  if not self.mechanics:return None
  candidates=[]
  for slot,item in self.world.bag.items():
   if item.identity not in PET_IDS:continue
   state=self.mechanics.inspect_fairy(item,self.stat)
   if state and state['monostat_matches_owner_policy']:
    candidates.append((slot!=1,-state['level'],slot,item,state))
  if not candidates:return None
  _,_,slot,item,state=min(candidates,key=lambda r:r[:3]);return slot,item,state
 def purchase_goals(self,now=None):
  if now is None:now=self.clock
  self.align_build()
  w=self.world
  owner=getattr(self.life,'owner_shops',None)
  if not owner or owner.get('catalog_revision',0)<48 or not owner.get('fresh_fairies') or w.own.values.get(4,0)==0:return []
  goals=[];fairy=self.fairy()
  if not fairy:goals.append((self.preferred,1,'покупает фею второго поколения/Джун'))
  else:
   slot,item,state=fairy
   if self.count(2312)<2:goals.append((2312,2-self.count(2312),'покупает автокорм феи'))
   fruit=FRUITS[self.stat]
   if item.max_energy>0 and item.energy>=item.max_energy and not self.count(fruit):goals.append((fruit,1,'покупает плод одной выбранной статы'))
  if w.own.values.get(0,0)>=15:
   for ticket in sorted({4602,{'garner':4602,'magicsea':4603,'darkblue':4604}.get(self.home_city,4602)}):
    if not self.count(ticket):goals.append((ticket,1,'покупает нужный городской билет'))
  if (fairy and w.own.values.get(0,0)>=20 and now>=self.berry_retry and not self.count(3844)
      and w.own.values.get(8,0)>=50000):goals.append((3844,1,'покупает НЯ для предстоящего кача'))
  if fairy and w.skills.get(280,{}).get('level',0)<3 and not self.count(609):
   goals.append((609,1,'покупает Expert Fairy Possession'))
  return goals
 def slot_count(self,slot,identity):
  i=self.world.bag.get(slot);return i.count if i and i.identity==identity else 0
 def use(self,slot,target,now,policy,kind):
  from hunter import action_header
  item=self.world.bag[slot];fairy=self.fairy()
  self.pending={'kind':kind,'source':slot,'id':item.identity,'count':item.count,'target':target,
   'source_total':self.count(item.identity),'before':fairy[1] if fairy else None,'deadline':now+12}
  policy.emit(action_header(self.world.own_id,policy.sequence,11)+struct.pack('>hh',slot,target))
  setattr(self,kind+'_requests',getattr(self,kind+'_requests')+1);self.next_action=now+2
 def tick(self,now,policy,safe=True,dialogue_busy=False):
  w=self.world;self.clock=now
  if self.pending:
   p=self.pending
   if not w.bag_ready or w.bag_disabled:
    if now>=p['deadline']:self.timeouts+=1;self.pending=None;self.next_action=now+120
    return self.pending is not None
   if p['kind']=='move':
    moved=w.bag.get(p['target'])
    done=bool(moved and moved.identity==p['id'] and self.slot_count(p['source'],p['id'])<p['count'])
   else:
    consumed=self.count(p['id'])<p['source_total'];after=w.bag.get(p['target']);before=p['before']
    if p['kind']=='feed':done=bool(consumed and after and before and after.identity==before.identity and after.endurance>before.endurance)
    elif p['kind']=='fruit':
     done=bool(consumed and after and before and after.identity==before.identity and after.energy<before.energy)
     if done:
      a=self.mechanics.inspect_fairy(after,self.stat);b=self.mechanics.inspect_fairy(before,self.stat)
      if a['level']>b['level']:self.growth_success+=1
      else:self.growth_failures+=1
    elif p['kind']=='skill':done=consumed and w.skills.get(280,{}).get('level',0)>=3
    else:done=consumed
   if done:
    self.confirmed+=1
    if p['kind']=='berry':self.berry_retry=now+900
    self.pending=None
   elif now>=p['deadline']:
    self.timeouts+=1;self.pending=None;self.next_action=now+120
    if p['kind']=='berry':self.berry_retry=now+900
   return self.pending is not None
  if now<self.next_action or not safe or dialogue_busy or not w.bag_ready or w.bag_disabled or not w.own.alive:return False
  self.align_build()
  fairy=self.fairy()
  if not fairy:self.reason='нужна фея второго поколения/Джун с одной статой';return False
  slot,item,state=fairy
  if slot!=1:
   return self.move(slot,1,now,policy,'размещает фею во второй ячейке сумки')
  food=next((s for s,i in w.bag.items() if i.identity==2312 and i.valid and s!=2),None)
  if food is not None and self.slot_count(2,2312)==0:
   return self.move(food,2,now,policy,'размещает автокорм в третьей ячейке сумки')
  if item.endurance<min(item.max_endurance,2550):
   source=next((s for s,i in w.bag.items() if i.identity in (227,2312) and i.valid),None)
   if source is not None:self.reason='кормит свою фею';self.use(source,slot,now,policy,'feed');return True
  if item.max_energy>0 and item.energy>=item.max_energy:
   source=next((s for s,i in w.bag.items() if i.identity==FRUITS[self.stat] and i.valid),None)
   if source is not None:self.reason='развивает у феи только '+self.stat;self.use(source,slot,now,policy,'fruit');return True
  if w.skills.get(280,{}).get('level',0)<3:
   source=next((s for s,i in w.bag.items() if i.identity==609 and i.valid),None)
   if source is not None:self.reason='изучает Expert Fairy Possession';self.use(source,-1,now,policy,'skill');return True
  if now>=self.berry_retry and w.own.values.get(0,0)>=20 and not getattr(policy,'mandatory_work',lambda:False)():
   source=next((s for s,i in w.bag.items() if i.identity==3844 and i.valid),None)
   # After reconnect, wait a full possible native15-minute buff before reuse.
   if not self.berry_retry:self.berry_retry=now+900
   elif source is not None:self.reason='использует НЯ перед качем';self.use(source,-1,now,policy,'berry');return True
  self.reason='фея растёт в сумке; стата '+self.stat;return False
 def move(self,source,target,now,policy,reason):
  from hunter import action_header
  if source==target:return False
  item=self.world.bag[source]
  self.pending={'kind':'move','source':source,'target':target,'id':item.identity,'count':item.count,'deadline':now+12}
  policy.emit(action_header(self.world.own_id,policy.sequence,12)+struct.pack('>hhh',source,0,target))
  self.moves+=1;self.next_action=now+2;self.reason=reason;return True
 def summary(self):
  fairy=self.fairy()
  return {'state':self.reason,'chosen_stat':self.stat,'preferred_fairy':self.preferred,
   'owner_shops_ready':bool(getattr(self.life,'owner_shops',None) and self.life.owner_shops.get('catalog_revision',0)>=48 and self.life.owner_shops.get('fresh_fairies')),
   'observed_fairy':dict(fairy[2],slot=fairy[0],id=fairy[1].identity) if fairy else None,
   'pending':self.pending['kind'] if self.pending else None,'moves':self.moves,'feeding_requests':self.feed_requests,
   'fruit_requests':self.fruit_requests,'growth_successes':self.growth_success,'growth_failures':self.growth_failures,
   'berry_requests':self.berry_requests,'expert_possession_requests':self.skill_requests,'confirmed':self.confirmed,'timeouts':self.timeouts}
