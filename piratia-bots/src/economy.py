"""Staggered bounded earning/business phases; professions and actual fights keep priority."""
import hashlib,json,math,random
from pathlib import Path

class Economy:
 def __init__(self,name,assets):
  seed=int.from_bytes(hashlib.sha256((name+':economy').encode()).digest()[:8],'big')
  self.seed=seed;self.cycle=None;self.stages=[];self.busy=False;self.current=None;self.group_hunting=False
  self.offset=seed%1800;self.cohort=('farmer' if seed%100<15 else 'leveler' if seed%100<60 else 'fairy' if seed%100<75 else 'dungeon')
  self.data=json.loads((Path(assets)/'patchouli-farms.json').read_text());self.last_models=[];self.reason=''
  self.patchouli_to_npc=False
 def funding_models(self,world,region,learning,now):
  if not region:return set()
  rows=[];own=world.own;position=world.position(now)
  for model,source in self.data['sources'].items():
   farm=region['farms'].get(model);identity=int(model)
   if (not farm or not farm['points'] or farm['level']>min(12,own.values.get(0,1))
       or farm['hp']>own.values.get(31,1)*1.2 or learning.blocked(identity,now) or learning.dangerous(identity,now)):continue
   attack=(own.values.get(33,0)+own.values.get(34,0))/2
   hits=farm['hp']/max(1,attack-farm.get('defence',0))
   distance=min(math.dist(position,p) for p in farm['points'])
   score=source['base_factor']/(1+hits)/(1+distance/10000)
   rows.append((-score,identity))
  return {m for _,m in sorted(rows)[:2]}
 def phase(self,world,now):
  if self.group_hunting:return 'progression'
  if world.own.values.get(4,0)==0 or world.own.values.get(0,0)<10:return 'progression'
  position=(now+self.offset)%1800
  cycle=int((now+self.offset)//1800)
  if cycle!=self.cycle:
   self.cycle=cycle;rng=random.Random(str(self.seed)+':'+str(cycle))
   values=[('business',180),('history',240),('income',420 if self.cohort=='farmer' else 240),('professions',120),('trade',120)]
   self.stages=[(name,round(seconds*rng.uniform(.85,1.15))) for name,seconds in values]
   self.stages.append(('progression',1800-sum(t for _,t in self.stages)));rng.shuffle(self.stages)
  for name,seconds in self.stages:
   if position<seconds:
    desired=name if name!='income' or world.own.values.get(0,0)>=15 else 'progression'
    if not self.busy or self.current is None:self.current=desired
    return self.current
   position-=seconds
  return 'progression'
 def business(self,world,now):return self.phase(world,now) in ('business','history','professions','trade')
 def models(self,world,region,learning,now):
  self.last_models=[]
  if self.phase(world,now)!='income' or not region or sum(i.count for i in world.bag.values() if i.identity==1000)>=30:return set()
  rows=[];own=world.own;hp=max(1,own.values.get(31,1));level=own.values.get(0,1)
  for model,source in self.data['sources'].items():
   farm=region['farms'].get(model);identity=int(model)
   if (not farm or not farm['points'] or farm['level']>level or farm['hp']>hp*3
       or learning.blocked(identity,now) or learning.dangerous(identity,now)):continue
   distance=min(math.dist(own.position,p) for p in farm['points'])
   # Rate dominance is tempered by kill cost and the real map travel distance.
   score=source['base_factor']/(1+farm['hp']/hp)/(1+distance/15000)
   rows.append((-score,distance,identity))
  self.last_models=[r[2] for r in sorted(rows)[:2]]
  self.reason=('экономика: добывает Пачкули для продажи НПС по500G' if self.patchouli_to_npc else 'экономика: фармит чертежи Пачкули для ларька по500G') if rows else 'нет подходящих источников Пачкули на текущей карте; продолжает кач'
  return set(self.last_models)
 def summary(self,world,now):
  return {'cohort':self.cohort,'phase':self.phase(world,now),'state':self.reason,'patchouli_models':self.last_models,
          'randomized_cycle':self.cycle,'activity_order':[name for name,_ in self.stages],'activity_seconds':dict(self.stages),'waiting_for_current_action':self.busy,
          'patchouli_player_price':None if self.patchouli_to_npc else 500,'patchouli_npc_buyback':500 if self.patchouli_to_npc else None,'npc_price_changed':self.patchouli_to_npc,'nominal_business_seconds_per_30min':180,'nominal_history_seconds_per_30min':240,
          'nominal_profession_development_seconds_per_30min':120,'nominal_trade_preparation_seconds_per_30min':120,
          'nominal_income_seconds_per_30min':420 if self.cohort=='farmer' else 240}
