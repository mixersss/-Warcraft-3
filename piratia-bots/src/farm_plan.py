"""Adaptive hunting preferences from observed fights; never grants XP, gear or money."""
import hashlib,json,math,random
from pathlib import Path

PROFILES=(
 ('осторожный',0,.75,2.0,.9),('уравновешенный',2,.65,3.0,.7),
 ('искатель вызова',3,.6,4.0,.6),('практичный',1,.7,2.5,.8),
 ('собиратель',2,.7,3.0,.75),('упорный',2,.65,3.5,.65))
FIELDS=('wins','losses','stalls','seconds','hp_cost','xp','gold','level_ups','dry_wins')

class HuntLearning:
 def __init__(self,seed):
  digest=hashlib.sha256(str(seed).encode()).digest();self.seed=int.from_bytes(digest[:8],'big')
  self.profile=PROFILES[self.seed%len(PROFILES)];self.rng=random.Random(self.seed)
  self.rows={};self.avoid={};self.danger_until={};self.active=None;self.path=None;self.dirty=False;self.save_errors=0
  self.signature=None;self.selected=set();self.until=0;self.scores={};self.last_save=0
  self.events=[]
  self.probe_attempts={};self.probing=False
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
   temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps({'version':1,'profile':self.profile[0],'models':self.rows},ensure_ascii=False),encoding='utf-8');temp.replace(self.path)
   self.dirty=False;self.last_save=now
  except OSError:self.save_errors+=1;self.last_save=now
 def blocked(self,model,now):return self.avoid.get(model,0)>now
 def dangerous(self,model,now):return self.danger_until.get(model,0)>now
 def begin(self,world,target,now):
  if self.active and self.active['id']==target.identity and self.active['handle']==target.handle:return
  own=world.own
  self.active={'id':target.identity,'handle':target.handle,'model':target.model,'start':now,
               'hp':own.values.get(1,0),'low':own.values.get(1,0),'max_hp':max(1,own.values.get(31,1)),
               'level':own.values.get(0,1),'xp':own.values.get(15,0),'gold':own.values.get(8,0)}
 def finish(self,world,now,outcome):
  a=self.active
  if not a:return
  self.active=None;own=world.own
  row=self.rows.setdefault(str(a['model']),{k:0 for k in FIELDS})
  duration=max(1,now-a['start']);cost=max(0,a['hp']-a['low'])/a['max_hp']
  row['seconds']+=duration;row['hp_cost']+=cost
  if outcome=='win':
   row['wins']+=1
   level_ups=max(0,own.values.get(0,a['level'])-a['level']);row['level_ups']+=level_ups
   earned=max(0,own.values.get(15,0)-a['xp']) if own.values.get(0)==a['level'] else 0
   row['xp']+=earned
   row['dry_wins']=0 if earned or level_ups else row.get('dry_wins',0)+1
   if row['dry_wins']>=4:self.avoid[a['model']]=now+120
   row['gold']+=max(0,own.values.get(8,0)-a['gold'])
  else:
   row['losses' if outcome=='danger' else 'stalls']+=1
   self.avoid[a['model']]=now+(240 if outcome=='danger' else 90)
   if outcome=='danger':self.danger_until[a['model']]=now+240
  self.until=0;self.dirty=True;self.events.append(outcome);self.events=self.events[-8:]
 def observe(self,world,now):
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
  return bool(self.active and 'death_seen' in self.active and now-self.active['death_seen']<2)
 def admissible(self,region,own,now):
  """Safe observed opportunities, even if the current shortlist is elsewhere."""
  level=own.values.get(0,1);maximum=max(1,own.values.get(31,1));result=set()
  for model,record in region['farms'].items():
   model=int(model);row=self.rows.get(str(model),{})
   if not record['points'] or self.blocked(model,now):continue
   if not max(1,level-9)<=record['level']<=level+(8 if row.get('wins',0) else max(3,self.profile[1])):continue
   if not row.get('wins') and record['hp']>maximum*self.profile[3]:continue
   result.add(model)
  return result
 def choose(self,region,own,now,fallback=False,hold=False,position=None):
  if hold and self.selected:return set(self.selected)
  progress=(own.values.get(0,1),own.values.get(15,0))
  self.last_clock=now
  if progress!=self.progress_signature:
   self.progress_signature=progress;self.last_progress_at=now
  idle_trial=now-self.last_progress_at>=90 and now>=self.next_idle_probe
  signature=(own.values.get(0,1),own.values.get(4,0),tuple(sorted(own.equipment.items())),fallback)
  if signature==self.signature and now<self.until and not idle_trial:return set(self.selected)
  if self.signature and signature[:3]!=self.signature[:3]:self.avoid.clear();self.danger_until.clear()
  self.signature=signature;level=own.values.get(0,1);max_hp=max(1,own.values.get(31,1))
  best_rate=max((r['xp']/max(1,r['seconds']) for r in self.rows.values()),default=0)
  scored=[];alternatives=[];self.scores={}
  for model,record in region['farms'].items():
   model=int(model);ml=record['level'];row=self.rows.get(str(model),{})
   if not record['points'] or self.blocked(model,now):continue
   if level<=3 and model==75 and not self.rows:continue
   primary=(ml<=(level+(8 if row.get('wins',0)>0 else self.profile[1]))
            and not (level<=3 and model==71))
   if not primary and ml>(level+max(3,self.profile[1])):continue
   if ml<max(1,level-9):continue # preserve a chance of useful experience
   if not row.get('wins') and record['hp']>max_hp*self.profile[3]:continue
   base=max(.12,1-abs(ml-level)*.07)/(1+record['hp']/max_hp*.25)
   if position is not None:
    travel=min(math.dist(position,p) for p in record['points'])
    base/=1+travel/12000
   if self.profile[0]=='искатель вызова':base*=1+max(0,ml-level)*.12
   if self.profile[0]=='собиратель':base*=1+min(10,len(record.get('drops',[])))*.035
   if row:
    wins=row.get('wins',0);losses=row.get('losses',0)+row.get('stalls',0)*.5
    safety=(wins+1)/(wins+losses+1)
    base*=safety/(1+row.get('hp_cost',0)/max(1,wins+losses))
    if best_rate>0 and wins>=2:
     # Real XP/time must outweigh modest level/HP/personality preferences.
     # A safe species earning ten times less XP is not an equivalent farm.
     rate=row.get('xp',0)/max(1,row.get('seconds',0));base*=.15+4*min(1,rate/best_rate)
    if row.get('level_ups',0):base*=1.15
    if wins>=2 and not row.get('xp') and not row.get('level_ups'):base*=.3
    if row.get('dry_wins',0)>=2:base*=.2
    if self.profile[0] in ('практичный','собиратель') and row.get('gold',0)>0:
     base*=1+min(.5,row['gold']/max(1,row['seconds'])/20)
   jitter=int.from_bytes(hashlib.sha256(f'{self.seed}:{model}'.encode()).digest()[:2],'big')/65535
   score=base*(.82+jitter*.36)
   (scored if primary else alternatives).append((score,model));self.scores[model]=score
  # A failed starter must not leave cautious profiles with zero legal species.
  # Keep cooldowns, real HP limits and routes; relax only the untested level margin.
  self.alternative_search=not bool(scored) and bool(alternatives)
  if not scored:scored=alternatives;alternatives=[]
  trials=sum(r.get('wins',0)+r.get('losses',0)+r.get('stalls',0) for r in self.rows.values())
  self.probing=False
  if (trials>0 and trials%3==1) or idle_trial:
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
    if idle_trial:self.idle_probes+=1
    unseen.sort(reverse=True);_,probe=self.rng.choice(unseen[:4])
    self.selected={probe};self.probe_attempts[probe]=now;self.probing=True;self.until=now+75
    return set(self.selected)
  scored.sort(reverse=True)
  count=4 if fallback else 3
  # Different persistent preferences, plus a bounded probe of a still viable alternative.
  chosen=scored[:count]
  if len(scored)>count and self.rng.random()<.18:chosen[-1]=self.rng.choice(scored[count:min(len(scored),count+5)])
  self.selected={m for _,m in chosen};self.until=now+60
  return set(self.selected)
 def summary(self):
  return {'profile':self.profile[0],'selected_models':sorted(self.selected),'learned_species':len(self.rows),
          'wins':sum(r.get('wins',0) for r in self.rows.values()),'dangerous_fights':sum(r.get('losses',0) for r in self.rows.values()),
          'stalled_fights':sum(r.get('stalls',0) for r in self.rows.values()),'save_errors':self.save_errors,
          'idle_probe_count':self.idle_probes,'seconds_without_xp':max(0,self.last_clock-self.last_progress_at) if self.last_progress_at is not None else 0,
          'using_alternative_search':getattr(self,'alternative_search',False),'probing_unfamiliar_species':self.probing}
