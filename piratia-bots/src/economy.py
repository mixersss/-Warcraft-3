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
  self.trade_data=None;self.last_goods=[];self.npc_income_enabled=False
  self.focused=False
  self.emergency_until=0;self.all_mobs_patchouli=False
  income_path=Path(assets)/'npc-income.json'
  self.npc_income=json.loads(income_path.read_text()) if income_path.exists() else None
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
  if now<self.emergency_until:return 'progression'
  if self.group_hunting:return 'progression'
  if world.own.values.get(4,0)==0 or world.own.values.get(0,0)<10:return 'progression'
  position=(now+self.offset)%1800
  cycle=int((now+self.offset)//1800)
  if cycle!=self.cycle:
   self.cycle=cycle;rng=random.Random(str(self.seed)+':'+str(cycle))
   values=([('income',180),('trade',120)] if self.focused else [('business',60),('history',90),('income',180 if self.cohort=='farmer' else 90),('professions',45),('trade',45)])
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
  if self.all_mobs_patchouli:return set() # Every ordinary kill earns it; no low-level detour.
  if self.trade_data and not self.focused:return self.trade_models(world,region,learning,now)
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
  if self.focused and self.npc_income_enabled and self.npc_income:
   for model,source in self.npc_income['sources'].items():
    farm=region['farms'].get(model);identity=int(model)
    if (not farm or not farm['points'] or farm['level']>level or farm['hp']>hp*3
        or learning.blocked(identity,now) or learning.dangerous(identity,now)):continue
    distance=min(math.dist(own.position,p) for p in farm['points'])
    score=source['base_factor']*2/(1+farm['hp']/hp)/(1+distance/15000)
    rows.append((-score,distance,identity))
  self.last_models=[r[2] for r in sorted(rows)[:2]]
  self.reason=('экономика: добывает Пачкули для продажи НПС по1500G' if self.patchouli_to_npc else 'экономика: фармит чертежи Пачкули для ларька по1500G') if rows else 'нет подходящих источников Пачкули на текущей карте; продолжает кач'
  return set(self.last_models)
 def trade_models(self,world,region,learning,now):
  self.last_goods=[]
  if self.phase(world,now)!='income' or not region:return set()
  own=world.own;level=own.values.get(0,1);hp=max(1,own.values.get(31,1));position=world.position(now);rows=[]
  minimum=max(1,level-(8 if self.cohort=='farmer' else 5))
  held={}
  for item in world.bag.values():held[item.identity]=held.get(item.identity,0)+item.count
  for model,source in self.trade_data['sources'].items():
   farm=region['farms'].get(model);identity=int(model)
   if (not farm or not farm['points'] or not minimum<=farm['level']<=level or farm['hp']>hp*3
       or learning.blocked(identity,now) or learning.dangerous(identity,now)):continue
   goods=[g for g in source['items'] if held.get(g['id'],0)<(15 if self.trade_data['items'][str(g['id'])]['category']=='scroll' else 20)]
   value=sum(g['base_factor']*self.trade_data['items'][str(g['id'])]['reference_price'] for g in goods)
   if not value:continue
   distance=min(math.dist(position,p) for p in farm['points'])
   score=value/(1+farm['hp']/hp)/(1+distance/15000)
   rows.append((-score,identity,[g['id'] for g in goods]))
  if self.npc_income_enabled and self.npc_income and held.get(self.npc_income['item_id'],0)<60:
   for model,source in self.npc_income['sources'].items():
    farm=region['farms'].get(model);identity=int(model)
    if (not farm or not farm['points'] or not minimum<=farm['level']<=level or farm['hp']>hp*3
        or learning.blocked(identity,now) or learning.dangerous(identity,now)):continue
    distance=min(math.dist(position,p) for p in farm['points'])
    score=source['base_factor']*self.npc_income['npc_buyback']/(1+farm['hp']/hp)/(1+distance/15000)
    rows.append((-score,identity,[self.npc_income['item_id']]))
  chosen=sorted(rows)[:2];self.last_models=[r[1] for r in chosen];self.last_goods=sorted({i for r in chosen for i in r[2]})
  self.reason='экономика: добывает свитки, экипировку20+ и проверенные материалы для ларька' if chosen else 'нет комфортного источника полезного товара; продолжает обычный кач'
  return set(self.last_models)
 def summary(self,world,now):
  return {'curated_income':bool(self.trade_data),'wanted_income_goods':self.last_goods,'cohort':self.cohort,'phase':self.phase(world,now),'state':self.reason,'patchouli_models':[] if self.trade_data else self.last_models,'income_models':self.last_models,
          'randomized_cycle':self.cycle,'activity_order':[name for name,_ in self.stages],'activity_seconds':dict(self.stages),'waiting_for_current_action':self.busy,
          'patchouli_player_price':None if self.patchouli_to_npc else 500,'patchouli_npc_buyback':1500 if self.patchouli_to_npc else None,'npc_price_changed':self.patchouli_to_npc,'nominal_business_seconds_per_30min':60,'nominal_history_seconds_per_30min':90,
          'nominal_profession_development_seconds_per_30min':45,'nominal_trade_preparation_seconds_per_30min':45,
          'nominal_income_seconds_per_30min':180 if self.cohort=='farmer' else 90}
