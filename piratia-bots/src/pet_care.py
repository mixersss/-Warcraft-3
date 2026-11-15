"""Source-backed second-generation fairy care using real bag actions and confirmations."""
import hashlib,struct
from builds import PROFILES

FAIRIES={'STR':232,'CON':233,'STA':234,'DEX':235,'AGI':236}
FRUITS={'STR':276,'CON':277,'DEX':278,'AGI':279,'STA':280}
BUILD_STATS={'crusader_speed':'STR','sharpshooter_precision':'DEX','sharpshooter_speed':'DEX',
 'cleric_spirit':'STA','sealmaster_balanced':'STA','voyager_spirit':'STA','voyager_tank':'CON','champion_tank':'CON'}
PET_IDS=set(range(231,238))|{681}
PET_BOOKS={243:(1,1),244:(1,2),246:(2,1),247:(2,2),249:(3,1),250:(3,2),252:(4,1),253:(4,2),259:(5,1),260:(5,2)}
PROTECTED=PET_IDS|set(PET_BOOKS)|set(FRUITS.values())|{227,2312,609,3844,4602,4603,4604}

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
  self.pet_skill_requests=0;self.pet_training_attempts=0;self.training_retry=0;self.training_window=None
  self.possession_requests=0;self.possession_confirmed=0;self.possession_pending=None;self.possession_retry=0
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
 def any_fairy(self):
  fairy=self.fairy()
  if fairy:return fairy
  if not self.mechanics:return None
  for slot,item in sorted(self.world.bag.items(),key=lambda pair:pair[0]!=1):
   if item.identity in PET_IDS:
    state=self.mechanics.inspect_fairy(item,self.stat)
    if state:return slot,item,state
  return None
 def urgent_hunger(self):
  fairy=self.any_fairy()
  return bool(fairy and fairy[1].endurance<=500)
 def needs_food_visit(self):
  fairy=self.any_fairy()
  return bool(fairy and fairy[1].endurance<2000 and (self.count(2312)+self.count(227)==0 or self.slot_count(2,2312)==0))
 def purchase_identity(self):
  return self.preferred
 def savings(self):
  owner=getattr(self.life,'owner_shops',None)
  if self.fairy() or not self.world.own.values.get(4,0) or not owner or not owner.get('fresh_fairies'):return 0
  return self.life.prices.get(self.preferred,0)+max(0,2-self.count(2312))*self.life.prices.get(2312,0)
 def affordable_care(self):
  for identity,count,_ in self.purchase_goals():
   if identity not in PET_IDS|{2312,227}:continue
   reserve=100+(max(0,2-self.count(2312))*self.life.prices.get(2312,0) if identity in PET_IDS else 0)
   if 0<self.life.prices.get(identity,0)<=self.world.own.values.get(8,0)-reserve:return True
  return False
 def purchase_blocker(self):
  owner=getattr(self.life,'owner_shops',None)
  if not owner or owner.get('catalog_revision',0)<48 or not owner.get('fresh_fairies'):return 'нет проверенного справочника новых магазинов; нужен RESTORE-BOT-SHOPS.cmd'
  if not self.world.own.values.get(4,0):return 'сначала обязательная первая профессия'
  if not self.world.bag_ready or self.world.bag_disabled:return 'ожидает подтверждение сумки'
  if (self.world.bag_capacity or 0)-len(self.world.bag)<2:return 'нужно два свободных места для безопасной закупки'
  if self.fairy():return ''
  return '' if self.affordable_care() else 'копит заработанное золото на фею и запас корма'
 def purchase_goals(self,now=None):
  if now is None:now=self.clock
  self.align_build()
  w=self.world
  owner=getattr(self.life,'owner_shops',None)
  if not owner or owner.get('catalog_revision',0)<48 or not owner.get('fresh_fairies') or w.own.values.get(4,0)==0:return []
  goals=[];fairy=self.fairy()
  if not fairy:goals.append((self.purchase_identity(),1,'копит и покупает выбранную фею второго поколения/Джун'))
  owned=self.any_fairy()
  if owned and self.count(2312)<6:goals.insert(0,(2312,6-self.count(2312),'пополняет запас автокорма феи'))
  if fairy:
   slot,item,state=fairy
   fruit=FRUITS[self.stat]
   if item.max_energy>0 and item.energy>=item.max_energy and not self.count(fruit):goals.append((fruit,1,'покупает плод одной выбранной статы'))
  if w.own.values.get(0,0)>=15:
   for ticket in sorted({4602,{'garner':4602,'magicsea':4603,'darkblue':4604}.get(self.home_city,4602)}):
    if not self.count(ticket):goals.append((ticket,1,'покупает нужный городской билет'))
  if (fairy and w.own.values.get(0,0)>=20 and now>=self.berry_retry and not self.count(3844)
      and w.own.values.get(8,0)>=50000):goals.append((3844,1,'покупает НЯ для предстоящего кача'))
  if fairy and w.skills.get(280,{}).get('level',0)<3 and not self.count(609):
   goals.append((609,1,'покупает Expert Fairy Possession'))
  goals.extend(g for g in self.pet_skill_goals(now) if not self.count(g[0]))
  return goals
 def slot_count(self,slot,identity):
  i=self.world.bag.get(slot);return i.count if i and i.identity==identity else 0
 def use(self,slot,target,now,policy,kind):
  from hunter import action_header
  item=self.world.bag[slot];fairy=self.any_fairy()
  self.pending={'kind':kind,'source':slot,'id':item.identity,'count':item.count,'target':target,
   'source_total':self.count(item.identity),'before':fairy[1] if fairy else None,'deadline':now+12}
  policy.emit(action_header(self.world.own_id,policy.sequence,11)+struct.pack('>hh',slot,target))
  setattr(self,kind+'_requests',getattr(self,kind+'_requests')+1);self.next_action=now+2
  if kind=='pet_skill':self.pet_training_attempts+=1
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
    elif p['kind']=='pet_skill':
     # A consumed book may randomly overwrite a different slot: never fabricate success.
     done=consumed and bool(after and before and after.parameters!=before.parameters)
     if done:self.training_retry=now+120
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
  if self.possession_pending:
   p=self.possession_pending
   if getattr(w,'own_states',{}).get(p['state'],0)>0:
    self.possession_confirmed+=1;self.possession_pending=None
   elif now>=p['deadline']:
    self.timeouts+=1;self.possession_pending=None;self.possession_retry=max(self.possession_retry,now+180)
   return self.possession_pending is not None
  if now<self.next_action or not safe or dialogue_busy or not w.bag_ready or w.bag_disabled or not w.own.alive:return False
  self.align_build()
  fairy=self.any_fairy()
  if not fairy:self.reason='нужна фея второго поколения/Джун с одной статой';return False
  slot,item,state=fairy
  if slot!=1:
   return self.move(slot,1,now,policy,'размещает фею во второй ячейке сумки')
  food=next((s for s,i in w.bag.items() if i.identity==2312 and i.valid and s!=2),None)
  if food is not None and self.slot_count(2,2312)==0:
   return self.move(food,2,now,policy,'размещает автокорм в третьей ячейке сумки')
  if item.endurance<min(item.max_endurance,5500 if w.skills.get(280,{}).get('level') else 2550):
   source=next((s for s,i in w.bag.items() if i.identity in (227,2312) and i.valid),None)
   if source is not None:self.reason='кормит свою фею';self.use(source,slot,now,policy,'feed');return True
  if not state['monostat_matches_owner_policy']:
   self.reason='сохраняет и кормит прежнюю фею; рост смешанных статов не продолжает';return False
  if item.max_energy>0 and item.energy>=item.max_energy:
   source=next((s for s,i in w.bag.items() if i.identity==FRUITS[self.stat] and i.valid),None)
   if source is not None:self.reason='развивает у феи только '+self.stat;self.use(source,slot,now,policy,'fruit');return True
  if w.skills.get(280,{}).get('level',0)<3:
   source=next((s for s,i in w.bag.items() if i.identity==609 and i.valid),None)
   if source is not None:self.reason='изучает Expert Fairy Possession';self.use(source,-1,now,policy,'skill');return True
  if self.possession_usable(now):
   from hunter import normal_attack
   self.possession_pending={'state':self.possession_state(item.identity),'deadline':now+12}
   self.reason='применяет Fairy Possession; ждёт серверное состояние'
   policy.emit(normal_attack(w.own_id,policy.sequence,0,280,w.own_id,w.own.handle,policy.position(now)))
   return True
  if now>=self.training_retry:
   for identity,_,_ in self.pet_skill_goals(now):
    source=next((s for s,i in w.bag.items() if i.identity==identity and i.valid),None)
    if source is not None:self.reason='обучает фею боевому навыку';self.use(source,slot,now,policy,'pet_skill');return True
  if now>=self.berry_retry and w.own.values.get(0,0)>=20 and not getattr(policy,'mandatory_work',lambda:False)():
   source=next((s for s,i in w.bag.items() if i.identity==3844 and i.valid),None)
   # After reconnect, wait a full possible native15-minute buff before reuse.
   if not self.berry_retry:self.berry_retry=now+900
   elif source is not None:self.reason='использует НЯ перед качем';self.use(source,-1,now,policy,'berry');return True
  self.reason='фея растёт в сумке; стата '+self.stat;return False
 def pet_skill_goals(self,now):
  if self.training_window is None:self.training_window=now
  if now-self.training_window>=1800:self.training_window=now;self.pet_training_attempts=0
  fairy=self.fairy()
  if not fairy or now<self.training_retry or self.pet_training_attempts>=9:return []
  skills={s['stone_type']:s['level'] for s in fairy[2]['skills'] if s['stone_type'] and s['level']}
  kinds=(3,1,5) if self.stat=='STA' else (2,1,4)
  # Source AddElfSkill can overwrite a different slot when adding a new type.
  # Upgrade ranks only after all desired types exist; do not overwrite unrelated earned skills.
  if set(skills)-set(kinds):return []
  missing=[k for k in kinds if not skills.get(k)]
  target=(missing[0],1) if missing else next(((k,2) for k in kinds if skills.get(k,0)<2),None)
  if not target:return []
  identity=next(i for i,pair in PET_BOOKS.items() if pair==target)
  return [(identity,1,'книга навыка феи: защита/атака/восстановление')]
 def possession_state(self,identity):
  return {231:132,232:168,233:169,234:170,235:171,236:172,237:173,681:174}.get(identity)
 def possession_usable(self,now):
  w=self.world;fairy=self.fairy();skill=w.skills.get(280,{})
  if not fairy or fairy[0]!=1 or not skill.get('level') or skill.get('state')!=1 or now<self.possession_retry:return False
  item=fairy[1];state=self.possession_state(item.identity)
  return bool(state and not getattr(w,'own_states',{}).get(state) and item.valid and item.parameters[0]//1000000000==1
              and fairy[2]['level']>0 and item.endurance>=5000
              and item.endurance>6*fairy[2]['level']/skill['level']*50 and w.own.values.get(2,0)>=skill.get('sp',20))
 def possession_sent(self,now):
  self.possession_requests+=1;skill=self.world.skills.get(280,{})
  self.possession_retry=now+max(180,skill.get('interval_ms',180000)/1000)
  if self.possession_pending:self.possession_pending['deadline']=now+12
 def move(self,source,target,now,policy,reason):
  from hunter import action_header
  if source==target:return False
  item=self.world.bag[source]
  self.pending={'kind':'move','source':source,'target':target,'id':item.identity,'count':item.count,'deadline':now+12}
  policy.emit(action_header(self.world.own_id,policy.sequence,12)+struct.pack('>hhh',source,0,target))
  self.moves+=1;self.next_action=now+2;self.reason=reason;return True
 def summary(self):
  fairy=self.fairy()
  return {'fairy_skill_requests':self.pet_skill_requests,'fairy_training_attempts':self.pet_training_attempts,'possession_cast_requests':self.possession_requests,'confirmed_possession_states':self.possession_confirmed,'native_skill_states':dict(getattr(self.world,'own_states',{})),'savings_goal':self.savings(),'purchase_blocker':self.purchase_blocker(),'purchase_choice':self.purchase_identity(),'cash':self.world.own.values.get(8,0),'goal_applies_to_every_bot':True,'food_owned':self.count(2312)+self.count(227),'autofeed_ready':bool(self.slot_count(2,2312)),'food_stock_target':6,'urgently_hungry':self.urgent_hunger(),'state':self.reason,'chosen_stat':self.stat,'preferred_fairy':self.preferred,
   'owner_shops_ready':bool(getattr(self.life,'owner_shops',None) and self.life.owner_shops.get('catalog_revision',0)>=48 and self.life.owner_shops.get('fresh_fairies')),
   'observed_fairy':dict(fairy[2],slot=fairy[0],id=fairy[1].identity) if fairy else None,
   'pending':self.pending['kind'] if self.pending else None,'moves':self.moves,'feeding_requests':self.feed_requests,
   'fruit_requests':self.fruit_requests,'growth_successes':self.growth_success,'growth_failures':self.growth_failures,
   'berry_requests':self.berry_requests,'expert_possession_requests':self.skill_requests,'confirmed':self.confirmed,'timeouts':self.timeouts}
