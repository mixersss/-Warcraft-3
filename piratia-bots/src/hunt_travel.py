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
  self.site_arrival=None;self.escaping_mine=False;self.outbound_resume=None;self.island_scout=None;self.scout_return=False
  self.requests=0;self.confirmed=0;self.timeouts=0;self.reason='';self.clock=0;self.target_started=0
 @property
 def busy(self):return bool(self.context or self.pending)
 def count(self,identity):return sum(i.count for i in self.world.bag.values() if i.identity==identity and i.valid)
 def purchase_goals(self):
  w=self.world
  if not w.own or w.own.values.get(0,0)<20 or not self.plan or self.plan.get('mine_exit'):return []
  result=[]
  if not self.plan.get('returning') and not self.count(4602):result.append((4602,1,'обратный билет в Аргент перед дальней поездкой'))
  if self.plan['kind']=='ticket' and self.plan['item_id'] not in {i for i,_,_ in result} and not self.count(self.plan['item_id']):result.append((self.plan['item_id'],1,'билет к выбранной точке прокачки'))
  return result
 def funding_target(self):
  if not self.plan or self.plan.get('returning') or self.plan.get('mine_exit'):return 0
  prices=[self.life.prices.get(identity,0) for identity,_,_ in self.purchase_goals()]
  if any(price<=0 for price in prices):return 0
  if self.plan['kind']=='portal':return sum(prices)+self.plan['fare']+2000
  return sum(prices)+(100 if prices else 0)
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
    rows.append({'kind':'portal','map':w.map,'position':node['position'],'to_map':r['map'],'arrival_cm':r['arrival_cm'],'fare':r['fare'],'label':r['label'],'name':node['name'],'island':True})
  for t in self.data['tickets']:
   if t['map'] not in self.regions.map_catalog or level<t['minimum_level']:continue
   owned=self.count(t['item_id'])
   price=self.life.prices.get(t['item_id'],0)
   if not owned and (w.map not in ('garner','magicsea','darkblue') or price<=0 or cash<price+2500):continue
   for point in t['points']:
    rows.append({'kind':'ticket','map':w.map,'to_map':t['map'],'arrival_cm':point,'arrival_options':t['points'],'fare':0 if owned else price,'item_id':t['item_id'],'name':t['birthplace']})
  if not returning:
   for node in (getattr(self.regions,'portal_catalog',None) or {}).get('nodes',[]):
    if node['map']!=w.map or not self.same_land(policy,node['position']):continue
    for edge in node['routes']:
     fee=0 if level<=edge['free_through_level'] else edge['fare']
     if edge['map'] in self.regions.map_catalog and cash>=fee+2000:
      rows.append({'kind':'portal','map':w.map,'position':node['position'],'to_map':edge['map'],
                   'arrival_cm':edge['arrival_cm'],'fare':fee,'label':edge['label'],'name':node['name']})
   for entry in self.data['entrances']:
    if entry['map']!=w.map or entry['to_map'] not in self.regions.map_catalog or not self.same_land(policy,entry['position']):continue
    rows.append({'kind':'event','map':w.map,'to_map':entry['to_map'],'position':entry['position'],'arrival_cm':entry['arrival_cm'],'fare':0,'event_id':entry['event_id'],'event_model':entry['model'],'name':entry['name']})
  return [r for r in rows if self.blocked.get(self.route_key(r),0)<=now]
 def nearby(self,map_name,point):
  known=self.knowledge.nearby_ground(map_name,tuple(point))
  observations=getattr(self.regions,'hunt_observations',None)
  if not observations:return known
  points=observations.points(map_name)
  if not points:return known
  merged=dict(known)
  for model,locations in points.items():
   mob=self.knowledge.get(model)
   if not mob or mob['territory']!=0:continue
   closest=min(math.dist(point,location) for location in locations)
   if closest<=25000:merged[model]=min(closest,merged.get(model,math.inf))
  return tuple(merged.items())
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
 def scout_goal(self,now):
  if not self.island_scout:return None
  name,point,arrived,level,xp=self.island_scout
  own=self.world.own
  if (name!=self.world.map or own.values.get(0,0)>level or own.values.get(15,0)>xp):
   self.island_scout=None;return None
  if now-arrived>=180:
   self.island_scout=None;self.scout_return=True;return None
  return point
 def choose_island_scout(self,now,policy,routes):
  last=policy.learning.last_progress_at
  if last is None or now-last<300 or not self.count(4602):return None
  actor=self.world.own
  if actor.values.get(1,0)<actor.values.get(31,1)*.85:return None
  rows=[]
  for route in routes:
   if (not route.get('island') or route.get('label')=='Go to Argent City!'
       or math.dist(actor.position,route['position'])>15000):continue
   sites=self.regions.island_scout_sites(route['to_map'],tuple(route['arrival_cm']))
   for model,(distance,point) in sites.items():
    if self.knowledge.get(model)['level']>actor.values.get(0,1):continue
    rate=self.rate(model,policy,now)
    if rate:rows.append((rate/(1+distance/15000),route,model,point))
  for _,route,model,point in sorted(rows,key=lambda row:row[0],reverse=True):
   if self.regions.reserve_island_scout(route['to_map'],tuple(route['arrival_cm']),now):
    self.preferred_model=model
    return dict(route,model=model,scout_point=point,returning=False)
  return None
 def needs_town(self,policy,now):
  w=self.world
  self.scout_goal(now)
  if self.scout_return:return True
  services=getattr(policy,'owner_services',None)
  if services and services.need():return True
  settling=self.settling_site(now,policy) or policy.hunt_before_errands(now)
  free=(w.bag_capacity or 0)-len(w.bag)
  patchouli=sum(i.count for i in w.bag.values() if i.identity==1000 and i.valid)
  needs_sale=bool(getattr(policy,'supply_funding_goal',0) and patchouli)
  if needs_sale or free<=0 or (not settling and (free<=4 or patchouli>=30)):
   shops=self.life.services['shops'].get(w.map,[])
   if not any(math.dist(policy.position(now),s['position'])<12000 and self.same_land(policy,s['position']) for s in shops):return True
  town=getattr(policy,'town',None);supply=getattr(town,'supply_plan',None)
  if supply and not getattr(policy,'supply_funding_goal',0) and (not settling or town.combat_supply_required()):
   if supply['item'] not in {i for i,_,_ in self.purchase_goals()} and (supply['map']!=w.map or not self.same_land(policy,supply['shop']['position'])):return True
  if settling:return False
  craft=getattr(policy,'crafting',None)
  if craft and craft.due(now) and (craft.goals or craft.op):return True
  market=getattr(policy,'market',None)
  if market and self.economy.phase(w,now)=='trade' and market.offers(policy):return True
  return False
 def choose(self,now,policy,returning=False,alternative_to=None,resume=None):
  w=self.world;rows=[];scout_routes=[]
  for route in self.routes(now,policy,returning):
   if (route['to_map']==w.map and math.dist(w.own.position,route['arrival_cm'])<5000
       and self.same_land(policy,route['arrival_cm'])):continue
   if route.get('island'):scout_routes.append(route)
   if alternative_to:
    ready_ticket=(route['kind']=='ticket' and self.count(route['item_id'])
                  and all(w.own.values.get(a,0)>=w.own.values.get(b,1) for a,b in ((1,31),(2,32))))
    nearby_portal=route['kind']=='portal' and math.dist(w.own.position,route['position'])<=8000
    if not self.count(4602) or not (ready_ticket or nearby_portal):continue
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
    if (resume and model==resume['model'] and route['to_map']==resume['to_map']
        and math.dist(route['arrival_cm'],resume['arrival_cm'])<10000):
     score*=2
    rows.append((score*(.8+.4*jitter),route,model))
  if not rows:
   return self.choose_island_scout(now,policy,scout_routes) if scout_routes and not (returning or alternative_to) else None
  for score,route,model in sorted(rows,key=lambda row:row[0],reverse=True):
   if returning:break
   # A ticket can land at any of its confirmed birth points. Every option
   # must offer the selected species on the same walkable component.
   arrivals=route.get('arrival_options',[route['arrival_cm']])
   sites=[self.regions.hunting_arrival_sites(route['to_map'],tuple(point)) for point in arrivals]
   if not all(model in site for site in sites):continue
   if alternative_to:
    speed=max(100,w.own.values.get(44,480))
    approach=math.dist(w.own.position,route.get('position',w.own.position))
    via=(approach+max(site[model] for site in sites))*1.5/speed+20
    if via+30>=math.dist(w.own.position,alternative_to)/speed:continue
   break
  else:
   return self.choose_island_scout(now,policy,scout_routes) if scout_routes and not (returning or alternative_to) else None
  if not returning:
   current=max((self.rate(m,policy,now) for m,d in self.nearby(w.map,w.own.position) if d<5000),default=0)
   last=getattr(policy.learning,'last_progress_at',None)
   if score<current*1.2 and last is not None and now-last<180:return None
  self.preferred_model=model
  return dict(route,model=model,returning=returning,walking_alternative=bool(alternative_to))
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
 def exit_mine(self,now,policy,entry):
  w=self.world;point=entry['position']
  route=dict(entry,kind='event',event_model=entry['model'],model=None,fare=0,mine_exit=True)
  if self.blocked.get(self.route_key(route),0)>now:return False
  if not self.plan or not self.plan.get('mine_exit') or self.route_key(self.plan)!=self.route_key(route):
   self.plan=route;self.target_started=now
   self.preferred_model=None
  if now-self.target_started>=150:
   self.abort(now,'Не дошёл до двери выхода из шахты');return False
  self.reason='Выходит из шахты: '+route['name']
  if math.dist(policy.position(now),point)>220:
   goal=policy.nav.nearest(point,3)
   if goal and policy.move_to(goal,now):return True
   self.abort(now,'Нет проверенного пути к двери шахты');return False
  return self.use_visible_event(now,policy,route)
 def use_visible_event(self,now,policy,plan):
  point=plan['position'];w=self.world
  event=next((e for e in w.entities.values() if e.model==plan['event_model'] and e.handle
              and e.event_identity==e.identity and e.event_id==plan['event_id'] and math.dist(e.position,point)<350),None)
  if not event:self.abort(now,'Вход сейчас недоступен; видимый нативный портал не найден');return False
  from hunter import action_header
  policy.emit(action_header(w.own_id,policy.sequence,18)+struct.pack('>IIH',event.identity,event.handle,event.event_id));self.requests+=1
  self.pending={'deadline':now+15,'gold':w.own.values.get(8,0),'item_count':None};return True
 def tick(self,now,policy,safe,dialogue_busy=False):
  self.clock=now;w=self.world
  if self.pending:
   plan=self.plan;points=plan.get('arrival_options',[plan['arrival_cm']])
   moved=w.map==plan['to_map'] and any(math.dist(w.own.position,p)<=2500 for p in points)
   if moved and plan.get('mine_exit'):
    moved=policy.nav.land_component(w.own.position)==plan['arrival_component']
   paid=self.count(plan['item_id'])<self.pending['item_count'] if plan['kind']=='ticket' else w.own.values.get(8,0)<=self.pending['gold']-plan['fare']
   if moved and paid and w.bag_ready:
    self.confirmed+=1;self.pending=None;self.context=None;self.plan=None
    if plan.get('mine_exit'):
     self.reason='Сервер подтвердил переход на пути выхода из шахты';return False
    self.site_arrival=(w.map,now) if plan.get('model') else None
    if plan.get('scout_point'):
     self.island_scout=(w.map,plan['scout_point'],now,w.own.values.get(0,0),w.own.values.get(15,0))
    if plan.get('returning'):self.scout_return=False
    self.site_until=now+600;self.next_check=now+(600 if plan.get('model') else 60);self.reason='Прибытие к новой точке подтверждено сервером';return False
   if now>=self.pending['deadline']:self.timeouts+=1;self.abort(now,'Переход не подтверждён')
   return self.busy
  if self.context:
   if now>=self.context['deadline']:self.timeouts+=1;self.abort(now,'Нет ответа портальщицы')
   return self.busy
  if not safe or dialogue_busy or not w.bag_ready or w.bag_disabled:return False
  entry=self.regions.mine_exit_step(w.map,w.own.position,self.escaping_mine)
  self.escaping_mine=bool(entry)
  if entry:return self.exit_mine(now,policy,entry)
  if w.own.values.get(0,0)<20:return False
  if any(i[0] in (1000,4915,684,860,861,862,863,864,865,866,1012) and math.dist(policy.position(now),i[2])<=2000 and now-i[5]<5 for i in w.items.values()):return False
  returning=self.needs_town(policy,now)
  near_argent=w.map=='garner' and any(math.dist(w.own.position,p)<16000 for p in self.data['birthplaces'].get('Argent City',{}).get('points',[]))
  if returning and self.plan and not self.plan.get('returning'):
   if self.plan.get('model'):self.outbound_resume=(self.plan,now+900)
   self.plan=None;self.preferred_model=None
  if returning and near_argent:
   self.scout_return=False
   self.plan=None;self.preferred_model=None
   return False
  if self.outbound_resume and now>=self.outbound_resume[1]:self.outbound_resume=None
  if self.plan and (self.plan['map']!=w.map or self.plan.get('returning',False)!=returning):
   self.abort(now,'Условия поездки изменились');return False
  if not returning and getattr(policy,'supply_funding_goal',0):
   if self.plan:self.target_started=now
   return False
  if not returning and self.settling_site(now,policy):return False
  if not returning and policy.camp_route_active(now) and not (self.plan and self.plan.get('walking_alternative')):
   goal=getattr(policy,'search_goal',None)
   last=policy.learning.last_progress_at
   if not goal or last is None or now-last<90 or now<self.next_check:return False
   alternative=self.choose(now,policy,alternative_to=goal)
   self.next_check=now+120
   if not alternative:return False
   self.plan=alternative;self.target_started=now
  if not returning and self.economy.phase(w,now)!='progression':
   if self.plan:self.abort(now,'Фаза дальней охоты завершена')
   return False
  if self.level!=w.own.values.get(0):self.level=w.own.values.get(0);self.next_check=0
  if not self.plan:
   if not returning and (now<self.next_check or now-getattr(policy,'started',now-90)<90):return False
   if not returning and self.outbound_resume:
    saved,_=self.outbound_resume
    self.plan=self.choose(now,policy,resume=saved)
    if self.plan:self.outbound_resume=None
   else:
    self.plan=self.choose(now,policy,returning)
   self.next_check=now+120;self.target_started=now
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
    if plan.get('walking_alternative'):
     self.abort(now,'Билет требует полные HP/SP');return False
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
  return self.use_visible_event(now,policy,plan)
 def summary(self):return {'state':self.reason,'plan':self.plan,'preferred_model':self.preferred_model,'requests':self.requests,'confirmed_arrivals':self.confirmed,'timeouts':self.timeouts,'known_island_portals':len(self.data['island_nodes']),'known_tickets':len(self.data['tickets']),'known_entrances':len(self.data['entrances']),'spawn_regions_are_not_live_mob_positions':True}
