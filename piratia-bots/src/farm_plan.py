"""Adaptive hunting preferences from observed fights; never grants XP, gear or money."""
import hashlib,json,math,random
from pathlib import Path

PROFILES=(
 ('осторожный',0,.75,2.0,.9),('уравновешенный',2,.65,3.0,.7),
 ('искатель вызова',3,.6,4.0,.6),('практичный',1,.7,2.5,.8),
 ('собиратель',2,.7,3.0,.75),('упорный',2,.65,3.5,.65))
FIELDS=('wins','losses','stalls','seconds','hp_cost','xp','gold','level_ups','dry_wins','observed_level','level_xp','level_seconds','level_wins')

PREFERRED_LEVEL_GAP=5
MAX_RECOVERY_LEVEL_GAP=9

def xp_level_divisor(actor_level,monster_level):
 # Exact level-only divisor from the supplied ShareTeamExp, before other bonuses.
 gap=actor_level-monster_level
 if gap>=4:return min(10,1+abs(gap-4)*.4)
 if gap<=-10:return min(4,1+abs(gap-10)*.1)
 return 1

def projected_combat(own,mob,hp=None,level=None):
 """Estimate native XP before server multipliers, time, and incoming damage."""
 values=own.values
 mage=values.get(4) in (4,5,13,14,16)
 attack=(values.get(33,0)+values.get(34,0))/2
 if mage:attack=max(attack,values.get(29,0)*4)
 reward=mob.get('base_xp',0)
 if attack<=0 or reward<=0:return None
 effective=max(1,attack-(0 if mage else mob.get('defence',0)))
 hits=max(1,math.ceil((hp if hp is not None else mob['hp'])/effective))
 interval=max(.45,min(5,values.get(42,0)/1000 or 1.5))
 if mage:interval=max(1.5,interval)
 incoming=hits*max(1,mob.get('attack_max',1)-values.get(35,0))
 if mage or values.get(4) in (2,12):incoming*=.65
 return reward/xp_level_divisor(values.get(0,1),level or mob['level']),hits*interval,incoming

class HuntLearning:
 def __init__(self,seed):
  digest=hashlib.sha256(str(seed).encode()).digest();self.seed=int.from_bytes(digest[:8],'big')
  self.profile=PROFILES[self.seed%len(PROFILES)];self.rng=random.Random(self.seed)
  self.rows={};self.avoid={};self.danger_until={};self.active=None;self.path=None;self.dirty=False;self.save_errors=0
  self.signature=None;self.selected=set();self.until=0;self.scores={};self.last_save=0
  self.events=[];self.location_observer=None
  self.async_rewards=False;self.pending_rewards=[];self.reward_xp_floor=None
  self.server_xp_rate=None;self.session_combat_rates={}
  self.catalog=None
  self.inefficient_models=set();self.candidate_details={}
  self.probe_attempts={};self.probing=False;self.last_probe_trial=-1
  self.session_start=None;self.session_xp=None;self.session_last_xp=None;self.session_gain=0;self.session_loss=0
  self.progress_signature=None;self.last_progress_at=None;self.last_clock=0;self.next_idle_probe=0;self.idle_probes=0
 def load(self,path):
  self.path=Path(path)
  try:
   data=json.loads(self.path.read_text(encoding='utf-8'))
   if data.get('version')!=1:return
   for key,row in data.get('models',{}).items():
    if str(key).isdigit() and isinstance(row,dict) and len(self.rows)<256:
     clean={f:row.get(f,0) for f in FIELDS}
     if all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=1e12 for v in clean.values()):self.rows[str(key)]=clean
  except (OSError,ValueError,TypeError,AttributeError):pass
 def save(self,now,force=False):
  if not self.path or not self.dirty or (not force and now-self.last_save<60):return
  try:
   self.path.parent.mkdir(parents=True,exist_ok=True)
   temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps({'version':1,'level_penalty_model':'owner-ShareTeamExp','profile':self.profile[0],'models':self.rows},ensure_ascii=False),encoding='utf-8');temp.replace(self.path)
   self.dirty=False;self.last_save=now
  except OSError:self.save_errors+=1;self.last_save=now
 def blocked(self,model,now):return self.avoid.get(model,0)>now
 def dangerous(self,model,now):return self.danger_until.get(model,0)>now
 def note_server_xp_rate(self,rate):
  if rate>0 and rate!=self.server_xp_rate:
   self.server_xp_rate=rate;self.session_combat_rates.clear()
 def base_combat_rate(self,model,level):
  wins,xp,seconds=self.session_combat_rates.get((level,model),(0,0,0))
  if self.server_xp_rate and wins>=2:return xp/seconds/self.server_xp_rate
  return None
 def release_target(self,identity):
  active=self.active
  if not active or active['id']!=identity:return
  if self.async_rewards and 'death_seen' in active:
   if len(self.pending_rewards)>=32:return
   self.pending_rewards.append(active)
  self.active=None
 def begin(self,world,target,now):
  if self.active and self.active['id']==target.identity and self.active['handle']==target.handle:return
  if self.async_rewards and self.active and 'death_seen' in self.active:
   if len(self.pending_rewards)>=32:return # Never lose a pending native reward record.
   self.release_target(self.active['id'])
  own=world.own
  self.active={'id':target.identity,'handle':target.handle,'model':target.model,'start':now,
               'hp':own.values.get(1,0),'low':own.values.get(1,0),'max_hp':max(1,own.values.get(31,1)),
               'level':own.values.get(0,1),'xp':own.values.get(15,0),'gold':own.values.get(8,0)}
  if self.location_observer:
   self.active.update(map=world.map,point=target.position)
 def finish(self,world,now,outcome):
  a=self.active
  if not a:return
  self.active=None;own=world.own
  row=self.rows.setdefault(str(a['model']),{k:0 for k in FIELDS})
  duration=max(1,(a.get('death_seen',now) if self.async_rewards else now)-a['start']);cost=max(0,a['hp']-a['low'])/a['max_hp']
  row['seconds']+=duration;row['hp_cost']+=cost
  if row.get('observed_level')!=a['level']:
   row.update(observed_level=a['level'],level_xp=0,level_seconds=0,level_wins=0)
  row['level_seconds']+=duration
  if outcome=='win':
   row['wins']+=1
   level_ups=max(0,own.values.get(0,a['level'])-a['level']);row['level_ups']+=level_ups
   # Native ATTR_CEXP is cumulative, including a level transition.
   baseline=a['xp']
   if self.async_rewards and self.reward_xp_floor is not None:baseline=max(baseline,self.reward_xp_floor)
   earned=max(0,own.values.get(15,a['xp'])-baseline)
   if self.async_rewards:self.reward_xp_floor=own.values.get(15,a['xp'])
   if earned and self.server_xp_rate:
    key=(a['level'],a['model'])
    wins,xp,seconds=self.session_combat_rates.get(key,(0,0,0))
    self.session_combat_rates[key]=(wins+1,xp+earned,seconds+duration)
   if earned and self.location_observer and a.get('map')==world.map:
    hit=world.own_hits.get(a['id'])
    if hit and hit[1] and hit[0]>=a['start']:
     target=world.entities.get(a['id'])
     if target is None or target.handle==a['handle']:
      self.location_observer(a['map'],a['model'],target.position if target else a['point'],
                             (a['id'],a['handle']))
   row['xp']+=earned;row['level_xp']+=earned;row['level_wins']+=1
   row['dry_wins']=0 if earned or level_ups else row.get('dry_wins',0)+1
   if row['dry_wins']>=4:self.avoid[a['model']]=now+120
   row['gold']+=max(0,own.values.get(8,0)-a['gold'])
  else:
   row['losses' if outcome=='danger' else 'stalls']+=1
   self.avoid[a['model']]=now+(240 if outcome=='danger' else 90)
   if outcome=='danger':self.danger_until[a['model']]=now+240
  self.until=0;self.dirty=True;self.events.append(outcome);self.events=self.events[-8:]
 def observe(self,world,now):
  if self.async_rewards and world.own:
   xp=world.own.values.get(15)
   if xp is not None and self.reward_xp_floor is not None and xp<self.reward_xp_floor:self.reward_xp_floor=xp
   while self.pending_rewards:
    record=self.pending_rewards[0]
    progressed=world.own.values.get(0,0)>record['level'] or world.own.values.get(15,0)>record['xp']
    if not progressed and now-record['death_seen']<2:break
    current=self.active;self.active=self.pending_rewards.pop(0)
    self.finish(world,now,'win');self.active=current
  a=self.active
  if not a or not world.own:return
  own=world.own;a['low']=min(a['low'],own.values.get(1,0))
  if not own.alive or own.values.get(1,0)<=own.values.get(31,1)*.35:self.finish(world,now,'danger');return
  target=world.entities.get(a['id']);hit=world.own_hits.get(a['id'])
  credited_death=bool(hit and hit[1] and hit[0]>=a['start'])
  dead=bool(target and not target.alive) or credited_death
  progressed=own.values.get(0,0)>a['level'] or own.values.get(15,0)>a['xp']
  if dead and (progressed or credited_death):
   if 'death_seen' not in a:a['death_seen']=now
   # The XP attribute update can follow the death packet. Do not train on a
   # fabricated zero-XP result simply because those messages arrived separately.
   if progressed or now-a['death_seen']>=2:self.finish(world,now,'win')
 def waiting_reward(self,now):
  if self.async_rewards:return len(self.pending_rewards)>=32
  return bool(self.active and 'death_seen' in self.active and now-self.active['death_seen']<2)
 def farms_in_band(self,region,low,high):
  farms=region['farms']
  if self.catalog is None:
   return ((key,record) for key,record in farms.items() if low<=record['level']<=high)
  keys=map(str,self.catalog.ground_models_in_band(low,high))
  return ((key,farms[key]) for key in keys if key in farms and low<=farms[key]['level']<=high)
 def minimum_farm_level(self,region,own,now):
  level=own.values.get(0,1);hp=max(1,own.values.get(31,1))
  for model,r in self.farms_in_band(region,max(1,level-PREFERRED_LEVEL_GAP),level+max(3,self.profile[1])):
   if (r.get('territory',0)==0 and r['points'] and r.get('base_xp',1)>0
       and not self.blocked(int(model),now) and not self.dangerous(int(model),now)
       and r['hp']<=hp*self.profile[3]):
    return max(1,level-PREFERRED_LEVEL_GAP)
  return max(1,level-MAX_RECOVERY_LEVEL_GAP)
 def admissible(self,region,own,now,recovery=False):
  """Safe observed opportunities, even if the current shortlist is elsewhere."""
  level=own.values.get(0,1);maximum=max(1,own.values.get(31,1));result=set()
  floor=self.minimum_farm_level(region,own,now)
  for model,record in self.farms_in_band(region,floor,level if recovery else level+8):
   model=int(model);row=self.rows.get(str(model),{})
   if record.get('territory',0)!=0 or not record['points'] or record.get('base_xp',1)<=0 or self.blocked(model,now) or self.dangerous(model,now):continue
   ceiling=level if recovery else level+(8 if row.get('wins',0) else max(3,self.profile[1]))
   if not floor<=record['level']<=ceiling:continue
   if not row.get('wins') and record['hp']>maximum*self.profile[3]:continue
   result.add(model)
  return result-self.inefficient(region,result,level)
 def inefficient(self,region,models,level):
  """Reject demonstrated poor XP farms only against a currently viable benchmark.

  The two-win minimum and same-level buckets prevent a lone late XP packet or
  old low-level history from vetoing a species. Quest objectives bypass this
  ordinary-farming shortlist in Hunter.planned_models.
  """
  rates={}
  for model in models:
   row=self.rows.get(str(model),{})
   if (str(model) in region['farms'] and row.get('observed_level')==level
       and row.get('level_wins',0)>=2 and row.get('level_seconds',0)>0):
    rates[model]=row.get('level_xp',0)/row['level_seconds']
  best=max(rates.values(),default=0)
  return {model for model,rate in rates.items() if best>0 and rate<best*.5}
 def record_progress(self,own,now):
  progress=(own.values.get(0,1),own.values.get(15,0))
  self.last_clock=now
  if 15 in own.values:
   xp=own.values[15]
   if self.session_start is None:
    self.session_start=now;self.session_xp=xp;self.session_last_xp=xp
   delta=xp-self.session_last_xp
   self.session_gain+=max(0,delta);self.session_loss+=max(0,-delta);self.session_last_xp=xp
  previous=self.progress_signature;self.progress_signature=progress
  if previous is None or progress[0]>previous[0] or progress[1]>previous[1]:self.last_progress_at=now
 def choose(self,region,own,now,fallback=False,hold=False,position=None):
  self.record_progress(own,now)
  self.selected={m for m in self.selected if str(m) in region['farms'] and region['farms'][str(m)].get('territory',0)==0}
  idle_trial=now-self.last_progress_at>=90 and now>=self.next_idle_probe
  signature=(own.values.get(0,1),own.values.get(4,0),tuple(sorted(own.equipment.items())),fallback,id(region))
  if hold and self.selected and self.signature==signature:return set(self.selected)
  self.region_reference=region # Keep the identity alive while its cache is used.
  if signature==self.signature and now<self.until and not idle_trial:return set(self.selected)
  if self.signature and signature[:3]!=self.signature[:3]:self.avoid.clear();self.danger_until.clear()
  self.signature=signature;level=own.values.get(0,1);max_hp=max(1,own.values.get(31,1))
  floor=self.minimum_farm_level(region,own,now)
  best_rate=max((r.get('level_xp',0)/max(1,r.get('level_seconds',0)) for r in self.rows.values() if r.get('observed_level')==level),default=0)
  scored=[];alternatives=[];self.scores={};self.candidate_details={}
  for model,record in self.farms_in_band(region,floor,level+8):
   model=int(model);ml=record['level'];row=self.rows.get(str(model),{})
   if record.get('territory',0)!=0 or not record['points'] or record.get('base_xp',1)<=0 or self.blocked(model,now) or self.dangerous(model,now):continue
   if level<=3 and model==75 and not self.rows:continue
   primary=(ml<=(level+(8 if row.get('wins',0)>0 else self.profile[1]))
            and not (level<=3 and model==71))
   if not primary and ml>(level+max(3,self.profile[1])):continue
   if ml<floor:continue # Do not camp very weak mobs when a viable closer-level band exists.
   if not row.get('wins') and record['hp']>max_hp*self.profile[3]:continue
   base=max(.12,1-abs(ml-level)*.07)/(1+record['hp']/max_hp*.25)
   if position is not None:
    travel=min(math.dist(position,p) for p in record['points'])
    base/=1+travel/12000
   # Audited native monster XP and defence; observed XP/time takes priority below.
   # Low-damage armoured targets must not look as comfortable as soft ones.
   estimate=projected_combat(own,record)
   if estimate:
    reward,seconds,incoming=estimate
    efficiency=reward/(seconds*(1+incoming/max_hp))
    base*=max(.15,min(3,math.sqrt(efficiency)))
   elif record.get('base_xp') is not None:
    efficiency=record['base_xp']/xp_level_divisor(level,ml)/max(1,record['hp'])
    base*=max(.15,min(3,math.sqrt(efficiency)))
   if self.profile[0]=='искатель вызова':base*=1+max(0,ml-level)*.12
   if self.profile[0]=='собиратель':base*=1+min(10,len(record.get('drops',[])))*.035
   if row:
    wins=row.get('wins',0);losses=row.get('losses',0)+row.get('stalls',0)*.5
    safety=(wins+1)/(wins+losses+1)
    base*=safety/(1+row.get('hp_cost',0)/max(1,wins+losses))
    if best_rate>0 and row.get('level_wins',0)>=2 and row.get('observed_level')==level:
     # Real XP/time must outweigh modest level/HP/personality preferences.
     # A safe species earning ten times less XP is not an equivalent farm.
     rate=row.get('level_xp',0)/max(1,row.get('level_seconds',0));base*=.15+4*min(1,rate/best_rate)
    if row.get('level_ups',0):base*=1.15
    if wins>=2 and not row.get('xp') and not row.get('level_ups'):base*=.3
    if row.get('dry_wins',0)>=2:base*=.2
    if self.profile[0] in ('практичный','собиратель') and row.get('gold',0)>0:
     base*=1+min(.5,row['gold']/max(1,row['seconds'])/20)
   jitter=int.from_bytes(hashlib.sha256(f'{self.seed}:{model}'.encode()).digest()[:2],'big')/65535
   score=base*(.82+jitter*.36)
   (scored if primary else alternatives).append((score,model));self.scores[model]=score
   self.candidate_details[model]={'level':ml,'score':score,
     'observed_level':row.get('observed_level'),'observed_wins':row.get('level_wins',0),
     'combat_xp_per_minute':60*row.get('level_xp',0)/max(1,row.get('level_seconds',0))
       if row.get('observed_level')==level else None,
     'level_divisor':xp_level_divisor(level,ml)}
  # A failed starter must not leave cautious profiles with zero legal species.
  # Keep cooldowns, real HP limits and routes; relax only the untested level margin.
  self.alternative_search=not bool(scored) and bool(alternatives)
  if not scored:scored=alternatives;alternatives=[]
  self.inefficient_models=self.inefficient(region,{m for _,m in scored},level)
  scored=[(s,m) for s,m in scored if m not in self.inefficient_models]
  trials=sum(r.get('wins',0)+r.get('losses',0)+r.get('stalls',0) for r in self.rows.values())
  self.probing=False
  if (trials>0 and trials%3==1 and trials!=self.last_probe_trial) or idle_trial:
   unseen=[(s,m) for s,m in scored+alternatives
           if not sum(self.rows.get(str(m),{}).get(k,0) for k in ('wins','losses','stalls'))
           and now-self.probe_attempts.get(m,-1e9)>=300]
   if idle_trial:
    # A completed-fight counter cannot trigger exploration when fights stopped.
    # Try a different safe species, including a previously learned one.
    unseen=[(s,m) for s,m in scored+alternatives if m not in self.selected
            and now-self.probe_attempts.get(m,-1e9)>=300]
    self.next_idle_probe=now+120
   if unseen:
    if position is not None and scored:
     nearby=min(min(math.dist(position,p) for p in region['farms'][str(m)]['points']) for _,m in scored)
     # An idle probe must not abandon an available camp for an ever more
     # distant unknown species. Real paid travel is planned separately.
     unseen=[(s,m) for s,m in unseen if min(math.dist(position,p) for p in region['farms'][str(m)]['points'])<=nearby+6000]
   if unseen:
    if idle_trial:self.idle_probes+=1
    self.last_probe_trial=trials
    # Finish one trial before spending another trip on the same fight counter.
    # Explore a nearby viable camp rather than randomly crossing the map.
    if position is not None:
     near=min(min(math.dist(position,p) for p in region['farms'][str(m)]['points']) for _,m in unseen)
     unseen=[(s,m) for s,m in unseen if min(math.dist(position,p) for p in region['farms'][str(m)]['points'])<=near+2500]
    unseen.sort(reverse=True);_,probe=unseen[0]
    self.selected={probe};self.probe_attempts[probe]=now;self.probing=True;self.until=now+75
    return set(self.selected)
  scored.sort(reverse=True)
  count=3
  # Different persistent preferences, plus a bounded probe of a still viable alternative.
  chosen=scored[:count]
  if len(scored)>count and self.rng.random()<.18:chosen[-1]=self.rng.choice(scored[count:min(len(scored),count+5)])
  self.selected={m for _,m in chosen};self.until=now+60
  return set(self.selected)
 def summary(self):
  return {'level_penalty_model':'owner-ShareTeamExp','profile':self.profile[0],'selected_models':sorted(self.selected),'learned_species':len(self.rows),
          'inefficient_models':sorted(self.inefficient_models),'candidate_details':self.candidate_details,
          'wins':sum(r.get('wins',0) for r in self.rows.values()),'pending_native_rewards':len(self.pending_rewards),'asynchronous_reward_settlement':self.async_rewards,'dangerous_fights':sum(r.get('losses',0) for r in self.rows.values()),
          'stalled_fights':sum(r.get('stalls',0) for r in self.rows.values()),'save_errors':self.save_errors,
          'session_seconds':max(0,self.last_clock-self.session_start) if self.session_start is not None else 0,
          'session_xp_gained':self.session_gain,'session_xp_lost':self.session_loss,
          'session_xp_net':self.session_gain-self.session_loss,
          'session_xp_per_minute':round(60*(self.session_gain-self.session_loss)/max(1,self.last_clock-self.session_start),2) if self.session_start is not None else 0,
          'idle_probe_count':self.idle_probes,'seconds_without_xp':max(0,self.last_clock-self.last_progress_at) if self.last_progress_at is not None else 0,
          'using_alternative_search':getattr(self,'alternative_search',False),'probing_unfamiliar_species':self.probing}
