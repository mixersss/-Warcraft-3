"""Choose source-backed hunting regions and use real portals/tickets/visible events."""
import hashlib
import math
import struct
from adventure import talk_request
from classic_wire import Reader,ProtocolError
from farm_plan import PREFERRED_LEVEL_GAP,projected_combat
from town import function_request

def npc_near(world,point):
 return next((e for e in world.entities.values() if e.control in (2,3) and math.dist(e.position,point)<350),None)

class HuntTravel:
 def __init__(self,world,regions,life,economy,send,name):
  self.world,self.regions,self.life,self.economy,self.send,self.name=world,regions,life,economy,send,name
  self.data=regions.hunting_travel_data;self.knowledge=regions.mob_knowledge
  self.context=None;self.pending=None;self.plan=None;self.blocked={}
  self.next_check=0;self.site_until=0;self.level=None;self.preferred_model=None
  self.site_arrival=None;self.site_camp=None;self.escaping_mine=False;self.outbound_resume=None
  self.deep_mine_cohort=hashlib.sha256((name+':silver-floor').encode()).digest()[0]%4==0
  self.next_deep_check=0
  self.hunt_options=[]
  self.approach_clock=None;self.mine_requests=0;self.mine_arrivals=0;self.last_arrival=None
  self.requests=0;self.confirmed=0;self.timeouts=0;self.reason='';self.clock=0;self.target_started=0
 @property
 def busy(self):return bool(self.context or self.pending)
 def mine_approach(self):
  plan=self.plan
  return bool(plan and plan['kind']=='event' and plan['to_map']=='eastgoaf' and 'Mine' in plan.get('name','')
              and not plan.get('mine_exit') and not self.purchase_goals())
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
 def supplier_distances(self,policy,now):
  distances={}
  origin=policy.position(now)
  for shop in getattr(self.life,'services',{}).get('shops',{}).get(self.world.map,()):
   point=shop['position']
   distance=math.dist(origin,point)
   if distance>12000 or not self.same_land(policy,point):continue
   for identity in shop['offers']:
    distances[identity]=min(distance,distances.get(identity,math.inf))
  return distances
 def routes(self,now,policy,returning=False):
  w=self.world;level=w.own.values.get(0,0);cash=w.own.values.get(8,0);rows=[]
  sellers=self.supplier_distances(policy,now)
  return_ticket=self.count(4602)
  purchase_distance=0 if returning or return_ticket else sellers.get(4602,math.inf)
  if not returning and not return_ticket and purchase_distance==math.inf:
   return []
  for node in self.data['island_nodes']:
   if node['map']!=w.map or not self.same_land(policy,node['position']):continue
   for r in node['routes']:
    if r['map'] not in self.regions.map_catalog or cash<r['fare']+2000:continue
    rows.append({'kind':'portal','map':w.map,'position':node['position'],'to_map':r['map'],'arrival_cm':r['arrival_cm'],'fare':r['fare'],'label':r['label'],'name':node['name'],'island':True})
  for t in self.data['tickets']:
   if t['map'] not in self.regions.map_catalog or level<t['minimum_level']:continue
   owned=self.count(t['item_id'])
   price=self.life.prices.get(t['item_id'],0)
   if not owned and (t['item_id'] not in sellers or price<=0 or cash<price+2500):continue
   for point in t['points']:
    rows.append({'kind':'ticket','map':w.map,'to_map':t['map'],'arrival_cm':point,'arrival_options':t['points'],'fare':0 if owned else price,'item_id':t['item_id'],'name':t['birthplace'],
                 'ticket_shop_distance':0 if owned else sellers[t['item_id']]})
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
  return [dict(r,shopping_distance=max(purchase_distance,r.get('ticket_shop_distance',0)))
          for r in rows if self.blocked.get(self.route_key(r),0)<=now]
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
  if (not mob or mob.get('territory',0)!=0 or not max(1,level-PREFERRED_LEVEL_GAP)<=mob['level']<=level+3
      or mob['hp']>own.values.get(31,1)*4
      or policy.learning.blocked(model,now) or policy.learning.dangerous(model,now)):return 0
  estimate=projected_combat(own,mob)
  if estimate is None:return 0
  reward,seconds,incoming=estimate
  if incoming>own.values.get(31,1)*.85:return 0
  observed=getattr(policy.learning,'base_combat_rate',lambda *args:None)(model,level)
  return observed if observed is not None else reward/seconds
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
  patchouli=sum(i.count for i in w.bag.values() if i.identity==1000 and i.valid)
  needs_sale=bool(getattr(policy,'supply_funding_goal',0) and patchouli)
  if needs_sale or free<=0 or (not settling and (free<=4 or patchouli>=30)):
   shops=self.life.services['shops'].get(w.map,[])
   local_limit=12000 if free<=0 else 35000
   if not any(math.dist(policy.position(now),s['position'])<local_limit and self.same_land(policy,s['position']) for s in shops):return True
  town=getattr(policy,'town',None);supply=getattr(town,'supply_plan',None)
  if supply and not getattr(policy,'supply_funding_goal',0) and (not settling or town.combat_supply_required()):
   if supply['item'] not in {i for i,_,_ in self.purchase_goals()} and (supply['map']!=w.map or not self.same_land(policy,supply['shop']['position'])):return True
  if settling:return False
  craft=getattr(policy,'crafting',None)
  if craft and craft.due(now) and (craft.goals or craft.op):return True
  market=getattr(policy,'market',None)
  if market and self.economy.phase(w,now)=='trade' and market.offers(policy):return True
  return False
 def deeper_mine_plan(self,now,policy):
  w=self.world;own=w.own
  if (w.map!='eastgoaf' or not self.deep_mine_cohort or own.values.get(0,0)<40
      or own.values.get(1,0)<own.values.get(31,1)*.85 or not self.count(4602)
      or now<self.next_deep_check or now-getattr(policy,'started',now-90)<90
      or (self.site_arrival and now-self.site_arrival[1]<45)):return None
  self.next_deep_check=now+30
  entry=next((row for row in self.data['entrances'] if row['name']=='Silver Mine 2 - Silver Mine 3'),None)
  if not entry or not self.same_land(policy,entry['position']):return None
  plan=dict(entry,kind='event',event_model=entry['model'],fare=0,returning=False,deep_mine=True)
  if self.blocked.get(self.route_key(plan),0)>now:return None
  sites=self.regions.hunting_arrival_camps(w.map,tuple(plan['arrival_cm']))
  score,model=max(((self.rate(model,policy,now)/(1+points[0][0]/12000),model)
                   for model,points in sites.items()),default=(0,None))
  return dict(plan,model=model,landing_camps=[(plan['arrival_cm'],[point for _,point in sites[model]])]) if score>0 else None
 def choose(self,now,policy,returning=False,alternative_to=None,resume=None):
  w=self.world;rows=[];landings={}
  if not returning:self.hunt_options=[]
  level=w.own.values.get(0,1)
  origin=policy.position(now);rates={}
  def rate(model):
   if model not in rates:rates[model]=self.rate(model,policy,now)
   return rates[model]
  for route in self.routes(now,policy,returning):
   if (route['to_map']==w.map and math.dist(w.own.position,route['arrival_cm'])<5000
       and self.same_land(policy,route['arrival_cm'])):continue
   if alternative_to:
    ready_ticket=(route['kind']=='ticket' and self.count(route['item_id'])
                  and all(w.own.values.get(a,0)>=w.own.values.get(b,1) for a,b in ((1,31),(2,32))))
    nearby_portal=route['kind']=='portal' and math.dist(w.own.position,route['position'])<=8000
    mine_door=(route['kind']=='event' and 'Mine' in route['name']
               and 'eastgoaf' in (route['map'],route['to_map'])
               and math.dist(w.own.position,route['position'])<=8000)
    if not self.count(4602) or not (ready_ticket or nearby_portal or mine_door):continue
   if returning:
    argents=self.data['birthplaces'].get('Argent City',{}).get('points',[])
    if route['to_map']!='garner' or not any(math.dist(route['arrival_cm'],p)<3000 for p in argents):continue
    score=1/(1+math.dist(w.own.position,route.get('position',w.own.position))/250+route['fare']/400)
    rows.append((score,route,None));continue
   # Planning a paid trip must be possible BEFORE buying its tickets. Actual
   # departure below still requires an owned return ticket and native use.
   approach=(math.dist(origin,route.get('position',origin))
             +route.get('shopping_distance',0))/250
   key=route['to_map'],tuple(route['arrival_cm'])
   if key not in landings:landings[key]=self.regions.hunting_arrival_camps(*key)
   for model,points in landings[key].items():
    score=rate(model)
    if not score:continue
    score*=600/(600+approach+points[0][0]/250+route['fare']/400)
    jitter=int.from_bytes(hashlib.sha256(f'{self.name}:{model}:{int(now//900)}'.encode()).digest()[:2],'big')/65535
    if (resume and model==resume['model'] and route['to_map']==resume['to_map']
        and math.dist(route['arrival_cm'],resume['arrival_cm'])<10000):
     score*=2
    rows.append((score*(.8+.4*jitter),route,model))
  choices=[]
  for score,route,model in sorted(rows,key=lambda row:row[0],reverse=True):
   if returning:
    self.preferred_model=None
    return dict(route,model=None,returning=True,walking_alternative=False)
   if choices and score<choices[0][0]*.9:break
   # A ticket can land at any of its confirmed birth points. Every option
   # must offer the selected species on the same walkable component.
   arrivals=route.get('arrival_options',[route['arrival_cm']])
   if any(other['to_map']==route['to_map']
          and any(math.dist(point,previous)<2500 for point in arrivals
                  for previous in other.get('arrival_options',[other['arrival_cm']]))
          for _,other,_ in choices):continue
   sites=[]
   for point in arrivals:
    key=route['to_map'],tuple(point)
    if key not in landings:landings[key]=self.regions.hunting_arrival_camps(*key)
    sites.append(landings[key])
   if not all(model in site for site in sites):continue
   if alternative_to:
    speed=max(100,w.own.values.get(44,480))
    approach=math.dist(w.own.position,route.get('position',w.own.position))
    via=(approach+max(site[model][0][0] for site in sites))*1.5/speed+20
    if via+30>=math.dist(w.own.position,alternative_to)/speed:continue
   landing_camps=[(arrival,[point for _,point in site[model]]) for arrival,site in zip(arrivals,sites)]
   choices.append((score,dict(route,landing_camps=landing_camps),model))
   if len(choices)==3:break
  if not choices:
   return None
  current=max((rate(m) for m,d in self.nearby(w.map,w.own.position) if d<5000),default=0)
  last=getattr(policy.learning,'last_progress_at',None)
  if last is not None and now-last<180:choices=[row for row in choices if row[0]>=current*1.2]
  if not choices:return None
  self.hunt_options=[{'map':r['to_map'],'arrival_cm':r['arrival_cm'],'via':r['name'],'model':m,
                      'landing_camps':r['landing_camps']} for _,r,m in choices]
  selected=int.from_bytes(hashlib.sha256(f'{self.name}:{level}:{w.map}:camp'.encode()).digest()[:2],'big')
  _,route,model=choices[selected%len(choices)]
  self.preferred_model=model
  return dict(route,model=model,returning=returning,walking_alternative=bool(alternative_to))
 def abort(self,now,reason):
  if self.plan:self.blocked[self.route_key(self.plan)]=now+900
  self.context=None;self.pending=None;self.plan=None;self.preferred_model=None;self.approach_clock=None
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
  if plan['to_map']=='eastgoaf' and 'Mine' in plan.get('name','') and not plan.get('mine_exit'):self.mine_requests+=1
  self.pending={'deadline':now+15,'gold':w.own.values.get(8,0),'item_count':None};return True
 def approach_expired(self,now,plan,search=None):
  key=self.route_key(plan)
  position=self.world.own.position
  old=self.approach_clock
  if not old or old[0]!=key:
   speed=max(100,min(self.world.own.values.get(44,480),3000))
   seconds=max(120,min(420,30+2*math.dist(position,plan['position'])/speed))
   self.approach_clock=(key,now+seconds,position,now,search)
   return now-self.target_started>=seconds
  _,deadline,anchor,advanced,old_search=old
  if math.dist(position,anchor)>=100:
   anchor,advanced=position,now
  if search and old_search and search[0]==old_search[0] and search[1]>old_search[1]:
   advanced=now
  self.approach_clock=key,deadline,anchor,advanced,search
  return now>=deadline or now-advanced>=35
 def tick(self,now,policy,safe,dialogue_busy=False):
  self.clock=now;w=self.world
  if self.pending:
   plan=self.plan;points=plan.get('arrival_options',[plan['arrival_cm']])
   moved=w.map==plan['to_map'] and any(math.dist(w.own.position,p)<=2500 for p in points)
   if moved and plan.get('mine_exit'):
    moved=policy.nav.land_component(w.own.position)==plan['arrival_component']
   if moved and plan.get('deep_mine'):
    moved=policy.nav.land_component(w.own.position)==policy.nav.land_component(plan['arrival_cm'])
   paid=self.count(plan['item_id'])<self.pending['item_count'] if plan['kind']=='ticket' else w.own.values.get(8,0)<=self.pending['gold']-plan['fare']
   if moved and paid and w.bag_ready:
    self.confirmed+=1;self.pending=None;self.context=None;self.plan=None;self.approach_clock=None
    self.last_arrival={'name':plan.get('name'),'map':w.map,'position':list(w.own.position),'kind':plan['kind']}
    if w.map=='eastgoaf' and 'Mine' in plan.get('name','') and not plan.get('mine_exit'):self.mine_arrivals+=1
    if plan.get('mine_exit'):
     self.reason='Сервер подтвердил переход на пути выхода из шахты';return False
    self.site_arrival=(w.map,now) if plan.get('model') else None
    self.site_camp=None
    if plan.get('landing_camps'):
     _,points=min(plan['landing_camps'],key=lambda row:math.dist(w.own.position,row[0]))
     self.site_camp=(w.map,plan['model'],tuple(map(tuple,points)))
    self.site_until=now+600;self.next_check=now+(600 if plan.get('model') else 60);self.reason='Прибытие к новой точке подтверждено сервером';return False
   if now>=self.pending['deadline']:self.timeouts+=1;self.abort(now,'Переход не подтверждён')
   return self.busy
  if self.context:
   if now>=self.context['deadline']:self.timeouts+=1;self.abort(now,'Нет ответа портальщицы')
   return self.busy
  if not safe or dialogue_busy or not w.bag_ready or w.bag_disabled:
   self.approach_clock=None
   return False
  entry=self.regions.mine_exit_step(w.map,w.own.position,self.escaping_mine)
  self.escaping_mine=bool(entry)
  if entry:return self.exit_mine(now,policy,entry)
  if w.own.values.get(0,0)<20:return False
  if any(i[0] in (1000,4915,684,860,861,862,863,864,865,866,1012) and math.dist(policy.position(now),i[2])<=2000 and now-i[5]<5 for i in w.items.values()):return False
  returning=self.needs_town(policy,now)
  if not returning and not self.plan:
   self.plan=self.deeper_mine_plan(now,policy)
   if self.plan:
    self.preferred_model=self.plan['model'];self.target_started=now
  deep_mine=bool(self.plan and self.plan.get('deep_mine'))
  local_combat=getattr(policy,'local_combat_ready',None)
  last_xp=policy.learning.last_progress_at
  productive=last_xp is None or now-last_xp<120
  if not returning and not deep_mine and productive and local_combat and local_combat(now) is True:
   if self.plan:self.target_started=now
   return False
  near_argent=w.map=='garner' and any(math.dist(w.own.position,p)<16000 for p in self.data['birthplaces'].get('Argent City',{}).get('points',[]))
  if returning and self.plan and not self.plan.get('returning'):
   if self.plan.get('model'):self.outbound_resume=(self.plan,now+900)
   self.plan=None;self.preferred_model=None
  if returning and near_argent:
   self.plan=None;self.preferred_model=None
   return False
  if self.outbound_resume and now>=self.outbound_resume[1]:self.outbound_resume=None
  if self.plan and (self.plan['map']!=w.map or self.plan.get('returning',False)!=returning):
   self.abort(now,'Условия поездки изменились');return False
  if not returning and getattr(policy,'supply_funding_goal',0):
   if self.plan:self.target_started=now
   return False
  if not returning and not deep_mine and self.settling_site(now,policy):return False
  if not returning and not self.plan and policy.camp_route_active(now):
   goal=getattr(policy,'search_goal',None)
   last=policy.learning.last_progress_at
   if not goal or last is None or now-last<30 or now<self.next_check:return False
   alternative=self.choose(now,policy,alternative_to=goal)
   self.next_check=now+120
   if not alternative:return False
   self.plan=alternative;self.target_started=now
  if not returning and not self.mine_approach() and self.economy.phase(w,now)!='progression':
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
  if missing:
   self.approach_clock=None
   if now-self.target_started>=120:
    self.abort(now,'Не удалось купить билеты вовремя');return False
   prices=[self.life.prices.get(identity,0) for identity,_,_ in missing]
   fare=self.plan['fare'] if self.plan['kind']=='portal' else 0
   if min(prices)<=0 or w.own.values.get(8,0)<sum(prices)+(fare+2000 if self.plan['kind']=='portal' else 100):
    self.abort(now,'Не хватает денег на билеты или переход');return False
   self.reason='Ожидает покупку билетов; доступна местная охота';return False
  plan=self.plan;self.reason='Переход к точке прокачки: '+plan['name']
  if plan['kind']=='ticket':
   if now-self.target_started>=120:
    self.abort(now,'Истекло время подготовки билета');return False
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
   if self.mine_approach() and self.approach_clock is None and hasattr(policy.nav,'cancel_pending'):
    policy.nav.cancel_pending()
   goal=policy.nav.nearest(point,3)
   path_status=getattr(policy.nav,'pending_farm_search',None)
   search=path_status(goal) if self.mine_approach() and goal and path_status else None
   if self.approach_expired(now,plan,search):
    self.abort(now,'Подход к переходу не продвигается или истёк срок дороги');return False
   if goal and policy.move_to(goal,now):return True
   self.abort(now,'Нет проверенного маршрута к переходу');return False
  if plan['kind']=='portal':
   npc=npc_near(w,point)
   if not npc:self.abort(now,'Нет видимой портальщицы');return False
   self.send(301,talk_request(npc.identity));self.context={'npc':npc.identity,'stage':'menu','deadline':now+8};return True
  return self.use_visible_event(now,policy,plan)
 def summary(self):return {'state':self.reason,'plan':self.plan,'camp_options':self.hunt_options,'site_camp':self.site_camp,'preferred_model':self.preferred_model,'requests':self.requests,'confirmed_arrivals':self.confirmed,'timeouts':self.timeouts,'mine_door_requests':self.mine_requests,'confirmed_mine_arrivals':self.mine_arrivals,'last_arrival':self.last_arrival,'known_island_portals':len(self.data['island_nodes']),'known_tickets':len(self.data['tickets']),'known_entrances':len(self.data['entrances']),'spawn_regions_are_not_live_mob_positions':True}
