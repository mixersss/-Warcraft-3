"""Choose source-backed hunting regions and use real portals/tickets/visible events."""
import hashlib
import math
import struct
from adventure import talk_request
from classic_wire import Reader,ProtocolError
from farm_plan import xp_level_divisor
from town import function_request

def npc_near(world,point):
 return next((e for e in world.entities.values() if e.control in (2,3) and math.dist(e.position,point)<350),None)

class HuntTravel:
 def __init__(self,world,regions,life,economy,send,name):
  self.world,self.regions,self.life,self.economy,self.send,self.name=world,regions,life,economy,send,name
  self.data=regions.hunting_travel_data;self.knowledge=regions.mob_knowledge
  self.context=None;self.pending=None;self.plan=None;self.blocked={}
  self.next_check=0;self.site_until=0;self.level=None;self.preferred_model=None
  self.site_arrival=None
  self.requests=0;self.confirmed=0;self.timeouts=0;self.reason='';self.clock=0;self.target_started=0
 @property
 def busy(self):return bool(self.context or self.pending)
 def count(self,identity):return sum(i.count for i in self.world.bag.values() if i.identity==identity and i.valid)
 def purchase_goals(self):
  w=self.world
  if not w.own or w.own.values.get(0,0)<20 or not self.plan:return []
  result=[]
  if not self.plan.get('returning') and not self.count(4602):result.append((4602,1,'обратный билет в Аргент перед дальней поездкой'))
  if self.plan['kind']=='ticket' and self.plan['item_id'] not in {i for i,_,_ in result} and not self.count(self.plan['item_id']):result.append((self.plan['item_id'],1,'билет к выбранной точке прокачки'))
  return result
 def same_land(self,policy,point):
  nearest=policy.nav.nearest(tuple(point),3)
  if nearest is None:return False
  component=getattr(policy.nav,'land_component',None)
  if not component:return True
  own=component(policy.position(self.clock));other=component(nearest)
  return not own or not other or own==other
 def route_key(self,route):
  return (route['kind'],route.get('item_id'),route.get('map'),tuple(route.get('position',())),route.get('to_map'),tuple(route['arrival_cm']))
 def routes(self,now,policy,returning=False):
  w=self.world;level=w.own.values.get(0,0);cash=w.own.values.get(8,0);rows=[]
  for node in self.data['island_nodes']:
   if node['map']!=w.map or not self.same_land(policy,node['position']):continue
   for r in node['routes']:
    if r['map'] not in self.regions.map_catalog or cash<r['fare']+2000:continue
    rows.append({'kind':'portal','map':w.map,'position':node['position'],'to_map':r['map'],'arrival_cm':r['arrival_cm'],'fare':r['fare'],'label':r['label'],'name':node['name']})
  for t in self.data['tickets']:
   if t['map'] not in self.regions.map_catalog or level<t['minimum_level']:continue
   owned=self.count(t['item_id'])
   price=self.life.prices.get(t['item_id'],0)
   if not owned and (w.map not in ('garner','magicsea','darkblue') or price<=0 or cash<price+2500):continue
   for point in t['points']:
    rows.append({'kind':'ticket','map':w.map,'to_map':t['map'],'arrival_cm':point,'arrival_options':t['points'],'fare':0 if owned else price,'item_id':t['item_id'],'name':t['birthplace']})
  if not returning:
   for entry in self.data['entrances']:
    if entry['map']!=w.map or entry['to_map'] not in self.regions.map_catalog or not self.same_land(policy,entry['position']):continue
    rows.append({'kind':'event','map':w.map,'to_map':entry['to_map'],'position':entry['position'],'arrival_cm':entry['arrival_cm'],'fare':0,'event_id':entry['event_id'],'event_model':entry['model'],'name':entry['name']})
  return [r for r in rows if self.blocked.get(self.route_key(r),0)<=now]
 def nearby(self,map_name,point):
  return self.knowledge.nearby_ground(map_name,tuple(point))
 def rate(self,model,policy,now):
  w=self.world;own=w.own;mob=self.knowledge.get(model);level=own.values.get(0,1)
  if (not max(1,level-5)<=mob['level']<=level+3 or mob['hp']>own.values.get(31,1)*4
      or policy.learning.blocked(model,now) or policy.learning.dangerous(model,now)):return 0
  attack=max(1,(own.values.get(33,1)+own.values.get(34,1))/2)
  mage=own.values.get(4) in (4,5,13,14,16)
  if mage:attack=max(attack,own.values.get(29,0)*4)
  hits=mob['hp']/max(1,attack-(0 if mage else mob.get('defence',0)))
  incoming=hits*max(1,mob.get('attack_max',1)-own.values.get(35,0))*(.65 if mage or own.values.get(4) in (2,12) else 1)
  if incoming>own.values.get(31,1)*.85:return 0
  seconds=max(1,hits*max(.5,getattr(policy,'attack_interval',1.5)))
  observed=policy.learning.rows.get(str(model),{})
  if observed.get('observed_level')==level and observed.get('level_wins',0)>=2 and observed.get('level_seconds',0)>0:
   return observed.get('level_xp',0)/observed['level_seconds']
  return mob.get('base_xp',0)/xp_level_divisor(level,mob['level'])/seconds
 def settling_site(self,now,policy):
  if not self.site_arrival:return False
  map_name,arrived=self.site_arrival
  progress=policy.learning.last_progress_at
  return self.world.map==map_name and now-arrived<180 and (progress is None or progress<=arrived)
 def needs_town(self,policy,now):
  w=self.world
  services=getattr(policy,'owner_services',None)
  if services and services.need():return True
  settling=self.settling_site(now,policy) or policy.hunt_before_errands(now)
  free=(w.bag_capacity or 0)-len(w.bag)
  if free<=0 or (not settling and (free<=4 or sum(i.count for i in w.bag.values() if i.identity==1000)>=30)):
   shops=self.life.services['shops'].get(w.map,[])
   if not any(math.dist(policy.position(now),s['position'])<12000 and self.same_land(policy,s['position']) for s in shops):return True
  town=getattr(policy,'town',None);supply=getattr(town,'supply_plan',None)
  if supply and (not settling or town.combat_supply_required()):
   if supply['item'] not in {i for i,_,_ in self.purchase_goals()} and (supply['map']!=w.map or not self.same_land(policy,supply['shop']['position'])):return True
  if settling:return False
  craft=getattr(policy,'crafting',None)
  if craft and craft.due(now) and (craft.goals or craft.op):return True
  market=getattr(policy,'market',None)
  if market and self.economy.phase(w,now)=='trade' and market.offers(policy):return True
  return False
 def choose(self,now,policy,returning=False):
  w=self.world;rows=[]
  for route in self.routes(now,policy,returning):
   if route['to_map']==w.map and math.dist(w.own.position,route['arrival_cm'])<5000:continue
   if returning:
    argents=self.data['birthplaces'].get('Argent City',{}).get('points',[])
    if route['to_map']!='garner' or not any(math.dist(route['arrival_cm'],p)<3000 for p in argents):continue
    score=1/(1+math.dist(w.own.position,route.get('position',w.own.position))/250+route['fare']/400)
    rows.append((score,route,None));continue
   # Planning a paid trip must be possible BEFORE buying its tickets. Actual
   # departure below still requires an owned return ticket and native use.
   approach=math.dist(policy.position(now),route.get('position',policy.position(now)))/250
   for model,distance in self.nearby(route['to_map'],route['arrival_cm']):
    score=self.rate(model,policy,now)
    if not score:continue
    score*=600/(600+approach+distance/250+route['fare']/400)
    jitter=int.from_bytes(hashlib.sha256(f'{self.name}:{model}:{int(now//900)}'.encode()).digest()[:2],'big')/65535
    rows.append((score*(.8+.4*jitter),route,model))
  if not rows:return None
  for score,route,model in sorted(rows,key=lambda row:row[0],reverse=True):
   if returning:break
   # A ticket can land at any of its confirmed birth points. Every option
   # must offer the selected species on the same walkable component.
   arrivals=route.get('arrival_options',[route['arrival_cm']])
   if all(model in self.regions.hunting_arrival_sites(route['to_map'],tuple(point)) for point in arrivals):break
  else:return None
  if not returning:
   current=max((self.rate(m,policy,now) for m,d in self.nearby(w.map,w.own.position) if d<5000),default=0)
   last=getattr(policy.learning,'last_progress_at',None)
   if score<current*1.2 and last is not None and now-last<180:return None
  self.preferred_model=model
  return dict(route,model=model,returning=returning)
 def abort(self,now,reason):
  if self.plan:self.blocked[self.route_key(self.plan)]=now+900
  self.context=None;self.pending=None;self.plan=None;self.preferred_model=None
  self.next_check=now+60;self.reason=reason+'; продолжает доступную охоту'
 def observe(self,command,payload,now):
  if command!=802 or not self.context or not self.plan:return False
  r=Reader(payload);npc,page=r.long(),r.byte();r.string_bytes();n=r.byte()
  if n>64:raise ProtocolError('Unsupported hunt teleporter menu')
  labels=[r.string() for _ in range(n)]
  if npc!=self.context['npc']:return False
  label=self.plan['label'] if self.context['stage']=='menu' else 'Teleport'
  if label not in labels:self.abort(now,'Портальщица не предлагает выбранный переход');return True
  if self.world.own.values.get(8,0)<self.plan['fare']+2000:self.abort(now,'Не хватает денег на переход');return True
  self.send(301,function_request(npc,page,labels.index(label)));self.requests+=1
  if self.context['stage']=='menu':self.context.update(stage='confirm',deadline=now+8)
  else:
   self.pending={'deadline':now+15,'gold':self.world.own.values.get(8,0),'item_count':None};self.context=None
  return True
 def tick(self,now,policy,safe,dialogue_busy=False):
  self.clock=now;w=self.world
  if self.pending:
   plan=self.plan;points=plan.get('arrival_options',[plan['arrival_cm']])
   moved=w.map==plan['to_map'] and any(math.dist(w.own.position,p)<=2500 for p in points)
   paid=self.count(plan['item_id'])<self.pending['item_count'] if plan['kind']=='ticket' else w.own.values.get(8,0)<=self.pending['gold']-plan['fare']
   if moved and paid and w.bag_ready:
    self.confirmed+=1;self.pending=None;self.context=None;self.plan=None
    self.site_arrival=(w.map,now) if plan.get('model') else None
    self.site_until=now+600;self.next_check=now+(600 if plan.get('model') else 60);self.reason='Прибытие к новой точке подтверждено сервером';return False
   if now>=self.pending['deadline']:self.timeouts+=1;self.abort(now,'Переход не подтверждён')
   return self.busy
  if self.context:
   if now>=self.context['deadline']:self.timeouts+=1;self.abort(now,'Нет ответа портальщицы')
   return self.busy
  if not safe or dialogue_busy or not w.bag_ready or w.bag_disabled or w.own.values.get(0,0)<20:return False
  if any(i[0] in (1000,4915,684,860,861,862,863,864,865,866,1012) and math.dist(policy.position(now),i[2])<=2000 and now-i[5]<5 for i in w.items.values()):return False
  returning=self.needs_town(policy,now)
  near_argent=w.map=='garner' and any(math.dist(w.own.position,p)<16000 for p in self.data['birthplaces'].get('Argent City',{}).get('points',[]))
  if returning and near_argent:
   self.plan=None;self.preferred_model=None
   return False
  if self.plan and (self.plan['map']!=w.map or self.plan.get('returning',False)!=returning):
   self.abort(now,'Условия поездки изменились');return False
  if not returning and (self.settling_site(now,policy) or policy.camp_route_active(now)):return False
  if not returning and self.economy.phase(w,now)!='progression':
   if self.plan:self.abort(now,'Фаза дальней охоты завершена')
   return False
  if self.level!=w.own.values.get(0):self.level=w.own.values.get(0);self.next_check=0
  if not self.plan:
   if not returning and (now<self.next_check or now-getattr(policy,'started',now-90)<90):return False
   self.plan=self.choose(now,policy,returning);self.next_check=now+120;self.target_started=now
  if not self.plan:return False
  missing=self.purchase_goals()
  if now-self.target_started>=120:
   self.abort(now,'Не удалось купить билеты вовремя' if missing else 'Истекло время подхода к переходу');return False
  if missing:
   prices=[self.life.prices.get(identity,0) for identity,_,_ in missing]
   fare=self.plan['fare'] if self.plan['kind']=='portal' else 0
   if min(prices)<=0 or w.own.values.get(8,0)<sum(prices)+(fare+2000 if self.plan['kind']=='portal' else 100):
    self.abort(now,'Не хватает денег на билеты или переход');return False
   self.reason='Ожидает покупку билетов; доступна местная охота';return False
  plan=self.plan;self.reason='Переход к точке прокачки: '+plan['name']
  if plan['kind']=='ticket':
   slot=next(s for s,i in w.bag.items() if i.identity==plan['item_id'] and i.valid)
   if any(w.own.values.get(a,0)<w.own.values.get(b,1) for a,b in ((1,31),(2,32))):
    policy.resting=True;policy.mana_resting=True;self.reason='Восстанавливает HP/SP для собственного билета';return False
   from hunter import action_header
   before=self.count(plan['item_id'])
   policy.emit(action_header(w.own_id,policy.sequence,11)+struct.pack('>hh',slot,-1));self.requests+=1
   self.pending={'deadline':now+20,'item_count':before,'gold':w.own.values.get(8,0)};return True
  point=plan['position']
  if math.dist(policy.position(now),point)>220:
   goal=policy.nav.nearest(point,3)
   if goal and policy.move_to(goal,now):return True
   self.abort(now,'Нет проверенного маршрута к переходу');return False
  if plan['kind']=='portal':
   npc=npc_near(w,point)
   if not npc:self.abort(now,'Нет видимой портальщицы');return False
   self.send(301,talk_request(npc.identity));self.context={'npc':npc.identity,'stage':'menu','deadline':now+8};return True
  event=next((e for e in w.entities.values() if e.model==plan['event_model'] and e.event_identity==e.identity and e.event_id==plan['event_id'] and math.dist(e.position,point)<350),None)
  if not event:self.abort(now,'Вход сейчас недоступен; видимый нативный портал не найден');return False
  from hunter import action_header
  policy.emit(action_header(w.own_id,policy.sequence,18)+struct.pack('>IIH',event.identity,event.handle,event.event_id));self.requests+=1
  self.pending={'deadline':now+15,'gold':w.own.values.get(8,0),'item_count':None};return True
 def summary(self):return {'state':self.reason,'plan':self.plan,'preferred_model':self.preferred_model,'requests':self.requests,'confirmed_arrivals':self.confirmed,'timeouts':self.timeouts,'known_island_portals':len(self.data['island_nodes']),'known_tickets':len(self.data['tickets']),'known_entrances':len(self.data['entrances']),'spawn_regions_are_not_live_mob_positions':True}
