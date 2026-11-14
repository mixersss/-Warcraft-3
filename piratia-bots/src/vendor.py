"""Sell broad audited ordinary loot to real NPCs; quest/valuable items stay protected."""
import json,math,struct
from pathlib import Path
from town import Town,trade_page
from adventure import talk_request

def sell_request(npc,slot,count):
 if not 0<=slot<256 or not 1<=count<=99:raise ValueError('Invalid NPC sale')
 return struct.pack('>IHBBB',npc,309,0,slot,count)

class Vendor(Town):
 def __init__(self,world,life,gear,role,rng,home,assets):
  super().__init__(world,life,gear,role,rng,home)
  self.junk={int(k):v for k,v in json.loads((Path(assets)/'junk-items.json').read_text())['items'].items()}
  self.next_sale=0;self.sales=self.confirmed_sales=self.sale_timeouts=0;self.batch=0;self.sale_target=None;self.sale_slot=None;self.sale_goals=[];self.failed_shops=set()
 def choices(self,policy):
  w=self.world
  if not w.bag_ready or w.bag_disabled:return []
  protected=policy.market.protected(policy) if policy.market else set()
  for feature in (policy.career,policy.story):
   if feature:
    protected.update(feature.needed_items())
    # A filled objective still needs its complete stack for delivery.
    quest=getattr(feature,'quest',None)
    if isinstance(quest,dict) and feature.active():
     protected.update(n['id'] for n in quest.get('needs',[]) if n['kind']==1)
  if policy.adventure:
   task=policy.adventure.farm()
   if task and task[1]:protected.add(task[1])
   for identity in policy.adventure.journal:
    objective=policy.adventure.grind.get(identity)
    if objective and objective[1]:protected.add(objective[1])
  choices=[]
  for slot,item in sorted(w.bag.items()):
   if item.identity not in self.junk or item.identity in protected or not item.valid:continue
   if item.forge or any(item.parameters) or any(a or b for a,b in item.instance_attributes):continue
   count=min(99,item.count)
   if count>0:choices.append((slot,item.identity,count))
  return choices
 def finish_sale(self,now):
  self.context=None;self.pending=None;self.sale_target=None;self.sale_slot=None;self.batch=0;self.next_sale=now;self.sale_goals=[];self.failed_shops.clear()
 def observe(self,command,payload,now,send):
  if not self.context:return False
  npc,stage,deadline=self.context
  if command==802 and stage=='talk':
   result=super().observe(command,payload,now,send)
   if not self.context:self.finish_sale(now)
   return result
  if command==805 and stage=='shop':
   source,_=trade_page(payload)
   if source==npc:self.context=npc,'ready',now+60
   return True
  return command in (801,802,803,805,806,807,808)
 def tick(self,now,policy,safe,dialogue_busy=False):
  w=self.world
  if self.pending:
   slot,identity,before,cash,deadline=self.pending
   item=w.bag.get(slot);after=item.count if item and item.identity==identity else 0
   if after<before and w.own.values.get(8,cash)>cash:
    self.confirmed_sales+=1;self.pending=None;self.batch+=1
    self.context=self.context[0],'ready',now+60
   elif now>=deadline:self.sale_timeouts+=1;self.finish_sale(now)
   return True
  if self.context:
   npc,stage,deadline=self.context
   if now>=deadline:self.sale_timeouts+=1;self.finish_sale(now);return False
   if stage=='ready':
    choices=self.choices(policy)
    actor=w.entities.get(npc)
    if not choices or not actor or math.dist(actor.position,policy.position(now))>250:self.finish_sale(now);return False
    slot,identity,count=choices[0];item=w.bag[slot]
    policy.send(308,sell_request(npc,slot,count));self.sales+=1
    self.pending=slot,identity,item.count,w.own.values.get(8,0),now+12
    self.context=npc,'confirmation',now+12
   return True
  if not safe or dialogue_busy:
   self.reason='ожидает безопасного завершения боя или другого диалога';return False
  choices=self.choices(policy)
  if not choices:
   self.reason='нет разрешённых простых трофеев для продажи';return False
  shops=self.life.services['shops'].get(w.map,[])
  if not shops:self.reason='нет известного торговца на текущей карте';return False
  if not self.sale_target:
   available=[s for s in shops if tuple(s['position']) not in self.failed_shops]
   if not available:
    self.failed_shops.clear();self.reason='ищет доступный путь к другому торговцу';return False
   self.sale_target=min(available,key=lambda s:math.dist(policy.position(now),s['position']))
   point=self.sale_target['position'];goals=[]
   # Stop beside the merchant within interaction range, rather than its centre.
   for dx,dy in ((-150,0),(0,-150),(150,0),(0,150),(-100,-100),(100,-100),(-100,100),(100,100),(0,0)):
    g=policy.nav.nearest((point[0]+dx,point[1]+dy),1)
    if isinstance(g,(tuple,list)) and len(g)==2 and math.dist(g,point)<=220 and tuple(g) not in goals:goals.append(tuple(g))
   goals.sort(key=lambda g:math.dist(policy.position(now),g))
   self.sale_goals=goals
  point=self.sale_target['position']
  self.reason='продаёт лишние обычные трофеи торговцу'
  npc=next((e for e in w.entities.values() if e.control in (2,3) and math.dist(e.position,point)<350),None)
  if npc and math.dist(policy.position(now),npc.position)<=220:
   policy.send(301,talk_request(npc.identity));self.context=npc.identity,'talk',now+8;return True
  while self.sale_goals:
   if policy.move_to(self.sale_goals[0],now):return True
   self.sale_goals.pop(0)
  self.failed_shops.add(tuple(point));self.sale_target=None
  self.reason='ищет доступный путь к другому торговцу';return False
 def summary(self):return {'destination':self.sale_target['position'] if self.sale_target else None,'route_goal':list(self.sale_goals[0]) if self.sale_goals else None,'sale_requests':self.sales,'confirmed_sales':self.confirmed_sales,'confirmation_timeouts':self.sale_timeouts,'state':self.reason or 'ожидание лишних трофеев','pending_sale':bool(self.pending),'free_bag_slots':max(0,(self.world.bag_capacity or 0)-len(self.world.bag)), 'bag_capacity':self.world.bag_capacity,'bag_used':len(self.world.bag),'bag_items':[{'slot':slot,'id':item.identity,'count':item.count,'plain':not(item.forge or any(item.parameters) or any(a or b for a,b in item.instance_attributes)),'junk_whitelisted':item.identity in self.junk} for slot,item in sorted(self.world.bag.items())]}
