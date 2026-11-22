"""Normal NPC purchases and occasional city breaks; money/inventory are server-owned."""
import math,struct
from classic_wire import Reader,ProtocolError
from adventure import talk_request
from owner_shops import npc_near
from coral_supplies import damage_ready,required_links

def function_request(npc,page,index):return struct.pack('>IHBB',npc,303,page,index)
def buy_request(npc,page,index,count):
    if not 0<=page<4 or not 0<=index<128 or not 1<=count<=20:raise ValueError('Invalid purchase')
    return struct.pack('>IHBBBBB',npc,309,1,page,index,0,count)

def trade_page(payload):
    r=Reader(payload);npc,kind,param,count=r.long(),r.byte(),r.long(),r.byte()
    if kind!=1 or count>4:raise ProtocolError('Unsupported NPC shop type')
    offers=[]
    for _ in range(count):
        page,n=r.byte(),r.byte()
        if page>=4 or n>128:raise ProtocolError('Unsupported shop page')
        for index in range(n):offers.append((r.short(),page,index))
    r.end();return npc,offers

class Town:
    def __init__(self,world,life,gear,role,rng,home,rest_directory=None,owner=None):
        self.world,self.life,self.gear,self.role,self.rng=world,life,gear,role,rng
        self.home=home;self.next_break=None;self.rest_until=0;self.rest_arrived=None
        self.next_shop=0;self.context=None;self.pending=None
        self.requests=self.confirmed=self.timeouts=self.breaks=0
        self.target_shop=None;self.wanted=None;self.reason=''
        self.rest_directory=rest_directory;self.owner=owner or str(world.own_id)
        self.work_kills=self.work_quests=0;self.work_baseline=None;self.last_rest=0;self.rest_due=False
        self.rest_goal=None;self.rest_pause_until=0;self.walk_stops=0
        self.npcs=getattr(life,'npcs',None);self.supply_plan=None;self.failed_suppliers={};self.next_supply_check=0;self.knowledge_plans=0
        self.petcare=None
        self.food_visit_requested=False
        self.professions=None
        self.treasure=None
        self.crafting=None
        self.xp_boosters=None
        self.hunt_travel=None
        self.last_purchase_failure=None
        self.visit_started=None;self.visit_key=None;self.approach_timeouts=0
        self.progression_visit=False
        self.trip_purchase=False
    def urgent_coral(self):
        return self.world.own.values.get(4) in (4,16) and not damage_ready(self.world,self.gear)
    def combat_supply_required(self):
        w=self.world;job=w.own.values.get(4)
        if job in (4,16):return self.urgent_coral()
        kinds=(9,) if job in (5,13,14) else (3,4) if job in (2,12) else ()
        if not kinds:return False
        for link in ((9,) if 9 in kinds else (6,9)):
            identity=w.own.equipment.get(link);detail=w.own.equipment_details.get(link,{})
            if (self.gear.types.get(identity) in kinds and detail.get('valid',True)
                    and (detail.get('max_endurance',0)<=0 or detail.get('endurance',0)>0)):return False
        return not any(self.gear.types.get(i.identity) in kinds and self.gear.compatible(w.own,i.identity,i) and i.valid
                       and (i.max_endurance<=0 or i.endurance>0) for i in w.bag.values())
    def note_progress(self,kills,quests):
        if self.work_baseline is None:self.work_baseline=(kills,quests)
        self.work_kills=max(0,kills-self.work_baseline[0]);self.work_quests=max(0,quests-self.work_baseline[1])
        if self.work_kills>=12 or self.work_quests>=2:self.rest_due=True
    def end_rest(self,now):
        if self.rest_directory:self.rest_directory.release(self.owner)
        self.rest_until=0;self.rest_arrived=None;self.rest_due=False;self.last_rest=now
        self.work_baseline=None;self.work_kills=self.work_quests=0
        self.next_break=now+600
        self.rest_goal=None;self.rest_pause_until=0
    def choose_walk_stop(self,now,policy):
        for _ in range(12):
            angle=self.rng.uniform(0,math.tau);radius=self.rng.uniform(600,1600)
            raw=(round(self.home[0]+radius*math.cos(angle)),round(self.home[1]+radius*math.sin(angle)))
            goal=policy.nav.nearest(raw,3)
            if not goal or math.dist(goal,policy.position(now))<350:continue
            if any(e.identity!=self.world.own_id and e.control in (1,2,3) and math.dist(e.position,goal)<250 for e in self.world.entities.values()):continue
            if policy.nav.path(policy.position(now),goal):return goal
        return None
    def equipment_goal(self):
        data=getattr(self.life,'equipment_goals',None);owner=getattr(self.life,'owner_shops',None);w=self.world
        if not data or not owner or owner.get('catalog_revision',0)<55:return None
        free=max(0,(w.bag_capacity or 0)-len(w.bag));owned={i.identity for i in w.bag.values()};choices=[]
        for key,row in data['items'].items():
            identity=int(key)
            if identity in owned or not self.gear.compatible(w.own,identity):continue
            upgrade=self.gear.upgrade(w.own,identity,free)
            price=self.life.prices.get(identity,0)
            if upgrade and price>0:choices.append((row['level'],price,-upgrade[0],identity))
        return min(choices)[3] if choices else None
    def equipment_savings(self):
        goal=self.equipment_goal()
        return self.life.prices.get(goal,0) if goal else 0
    def critical_items(self,map_name=None):
        w=self.world;job=w.own.values.get(4);result=[];shop_map=map_name or w.map
        w.own.required_coral_links=required_links(w)
        if job in (5,13,14) and not (self.gear.types.get(w.own.equipment.get(9))==9 and w.own.equipment_details.get(9,{}).get('valid',True)):
            if not any(self.gear.types.get(i.identity)==9 and self.gear.compatible(w.own,i.identity) and i.valid for i in w.bag.values()):
                staves=[i for shop in self.life.services['shops'].get(shop_map,[]) for i in shop['offers'] if self.gear.types.get(i)==9 and self.gear.compatible(w.own,i)]
                if staves:result.append(min(staves,key=lambda i:(self.life.prices.get(i,10**9),i)))
        if job in (2,12) and not any(self.gear.types.get(w.own.equipment.get(link)) in (3,4) and w.own.equipment_details.get(link,{}).get('valid',True) for link in (6,9)):
            if not any(self.gear.types.get(i.identity) in (3,4) and self.gear.compatible(w.own,i.identity) and i.valid for i in w.bag.values()):
                bows=[i for shop in self.life.services['shops'].get(shop_map,[]) for i in shop['offers'] if self.gear.types.get(i) in (3,4) and self.gear.compatible(w.own,i)]
                if bows:result.append(min(bows,key=lambda i:(self.life.prices.get(i,10**9),i)))
        from skill_plan import SkillPlan
        books=[]
        if self.role:
            books=SkillPlan(w,self.role,self.life).missing_books()
        if job in (4,16):
            for link in sorted(required_links(w),key=lambda n:(n!=7,n)):
                current=w.own.equipment.get(link,0);details=w.own.equipment_details.get(link,{})
                cost=max(1,w.skills.get({5:213,6:216,7:214}[link],{}).get('energy',1))
                if self.gear.types.get(current)==29 and details.get('valid') and details.get('energy',0)>=cost:continue
                if any(self.gear.gear.get(i.identity,{}).get('kind')==29 and link in self.gear.gear[i.identity]['links'] and i.energy>=cost for i in w.bag.values()):continue
                options=[i for shop in self.life.services['shops'].get(shop_map,[]) for i in shop['offers']
                         if self.gear.gear.get(i,{}).get('kind')==29 and link in self.gear.gear[i]['links'] and self.gear.compatible(w.own,i)]
                if options:result.append(min(options,key=lambda i:(self.life.prices.get(i,10**9),i)))
        self.combat_items=set(result)
        for identity in books:
            skill=self.life.books.get(identity,{}).get('skill')
            if (skill==99 and job in (5,13,14) or skill==214 and job in (4,16)) and not w.skills.get(skill,{}).get('level'):
                self.combat_items.add(identity)
        result.extend(books)
        ticket={'garner':4602,'magicsea':4603,'darkblue':4604}.get(w.map)
        self.emergency_ticket=ticket if ticket and job and w.own.values.get(0,0)>=10 and not any(i.identity in (4602,4603,4604) and i.valid for i in w.bag.values()) else None
        if self.emergency_ticket:result.append(self.emergency_ticket)
        if (job and not w.skills.get(241,{}).get('level',0) and w.own.values.get(13,0)>0
                and not any(i.identity==3296 for i in w.bag.values())):
            result.append(3296)
        if self.petcare:result.extend(identity for identity,_,_ in self.petcare.purchase_goals())
        if self.professions:result.extend(identity for identity,_,_ in self.professions.purchase_goals())
        if self.treasure:result.extend(identity for identity,_,_ in self.treasure.purchase_goals())
        if self.crafting:result.extend(identity for identity,_,_ in self.crafting.purchase_goals())
        if self.xp_boosters:result.extend(identity for identity,_,_ in self.xp_boosters.purchase_goals())
        if self.hunt_travel:result.extend(identity for identity,_,_ in self.hunt_travel.purchase_goals())
        goal=self.equipment_goal()
        if goal:result.append(goal)
        if self.petcare and self.petcare.needs_food_visit() and 2312 in result:
            result=[2312]+[i for i in result if i!=2312]
        return result
    def spend_limit(self,identity):
        cash=self.world.own.values.get(8,0)
        reserve=100+(self.supply_plan.get('reserved_travel_gold',0)//2 if self.supply_plan else 0)
        if identity in (817,867,635) and self.life.prices.get(identity)==1:
            reserve=self.supply_plan.get('reserved_travel_gold',0)//2 if self.supply_plan else 0
        from pet_care import PET_IDS
        if self.petcare and identity in PET_IDS:reserve+=max(0,2-self.petcare.count(2312))*self.life.prices.get(2312,0)
        critical=self.critical_items()
        if self.supply_plan and self.supply_plan.get('critical') and self.supply_plan['item']==identity:critical.append(identity)
        essential=identity in self.combat_items or identity in PET_IDS|{1847,2312,227,4602,4603,4604}
        if self.hunt_travel and self.hunt_travel.plan and identity in {i for i,n,r in self.hunt_travel.purchase_goals()}:essential=True
        if self.supply_plan and self.supply_plan.get('critical') and self.supply_plan['item']==identity and self.gear.types.get(identity) in (3,4,9,29):essential=True
        if self.petcare and not essential:reserve+=min(max(0,cash-reserve),self.petcare.savings())
        goal=self.equipment_goal()
        if goal and identity not in critical:reserve+=min(max(0,cash-reserve),self.equipment_savings())
        return max(0,cash-reserve) if identity in critical else min(cash//4,max(0,cash-reserve))
    def choose_want(self):
        w=self.world;cash=w.own.values.get(8,0)
        if not w.bag_ready or w.bag_disabled or cash<1:return None
        free=(w.bag_capacity or 0)-len(w.bag)
        if free<2:return None
        if self.petcare and self.petcare.needs_food_visit() and w.own.values.get(1,0)>w.own.values.get(31,1)*.55:
            goal=next(((i,n) for i,n,_ in self.petcare.purchase_goals() if i==2312),None)
            price=self.life.prices.get(2312,0)
            if goal and price>0 and price<=self.spend_limit(2312):return 2312,min(goal[1],self.spend_limit(2312)//price)
        food=sum(item.count for item in w.bag.values() if item.identity==1847)
        critical=self.critical_items()
        if self.urgent_coral() and (food>=2 or any(self.life.prices.get(i)==1 for i in critical)) and w.own.values.get(1,0)>w.own.values.get(31,1)*.55:
            for identity in critical:
                if self.gear.types.get(identity)==29 and 0<self.life.prices.get(identity,0)<=self.spend_limit(identity):return identity,1
        if food<5 and 0<self.life.prices.get(1847,0)<=self.spend_limit(1847):return 1847,min(10,15-food)
        if cash<120:return None
        for identity in critical:
            if identity in self.combat_items and 0<self.life.prices.get(identity,0)<=self.spend_limit(identity):return identity,1
        ticket=getattr(self,'emergency_ticket',None)
        if ticket and 0<self.life.prices.get(ticket,0)<=self.spend_limit(ticket):return ticket,1
        if self.hunt_travel and self.hunt_travel.plan:
            for identity,count,_ in self.hunt_travel.purchase_goals():
                price=self.life.prices.get(identity,0)
                if 0<price<=self.spend_limit(identity):return identity,min(count,self.spend_limit(identity)//price)
        if self.progression_visit:return None
        if self.petcare:
            for identity,count,_ in self.petcare.purchase_goals():
                price=self.life.prices.get(identity,0)
                if 0<price<=self.spend_limit(identity):return identity,min(count,max(1,self.spend_limit(identity)//price))
        if self.professions:
            for identity,count,_ in self.professions.purchase_goals():
                if 0<self.life.prices.get(identity,0)<=self.spend_limit(identity):return identity,count
        if self.crafting:
            for identity,count,_ in self.crafting.purchase_goals():
                if 0<self.life.prices.get(identity,0)<=self.spend_limit(identity):return identity,min(20,count)
        for identity in self.critical_items():
            if 0<self.life.prices.get(identity,0)<=self.spend_limit(identity):return identity,1
        for identity,book in self.life.books.items():
            if (self.life.can_learn(w,book) and w.own.values.get(7,0)>=book['cost']
                    and not w.skills.get(book['skill'],{}).get('level',0)
                    and not any(i.identity==identity for i in w.bag.values())
                    and 0<self.life.prices.get(identity,0)<=self.spend_limit(identity)):return identity,1
        if self.xp_boosters:
            for identity,count,_ in self.xp_boosters.purchase_goals():
                if 0<self.life.prices.get(identity,0)<=self.spend_limit(identity):return identity,count
        if self.hunt_travel:
            for identity,count,_ in self.hunt_travel.purchase_goals():
                if 0<self.life.prices.get(identity,0)<=self.spend_limit(identity):return identity,count
        owned={i.identity for i in w.bag.values()}
        for shop in self.life.services['shops'].get(w.map,[]):
            for identity in shop['offers']:
                if identity in owned or not self.gear.upgrade(w.own,identity,free):continue
                if 0<self.life.prices.get(identity,0)<=self.spend_limit(identity):return identity,1
        return None
    def plan_supplies(self,now,policy):
        """Use all known city sellers; a source record never bypasses live menus."""
        if not self.npcs or now<self.next_supply_check or self.world.own.values.get(4,0)==0:return None
        self.next_supply_check=now+60
        w=self.world;own=w.own;cash=own.values.get(8,0);free=(w.bag_capacity or 0)-len(w.bag)
        if not w.bag_ready or w.bag_disabled or free<2:return None
        food=sum(i.count for i in w.bag.values() if i.identity==1847)
        # Missing apples must not prohibit discovery of the only usable staff
        # in another city. Without that staff a caster cannot earn more food.
        staff_blocked=(own.values.get(4) in (5,13,14) and self.combat_supply_required()
                       and own.values.get(1,0)>own.values.get(31,1)*.55)
        coral_only=food<5 and not staff_blocked
        if coral_only and not ((food>=2 or self.life.prices.get(867)==1) and self.urgent_coral() and own.values.get(1,0)>own.values.get(31,1)*.55):return None
        portals=getattr(getattr(policy,'travel',None),'portals',None)
        if not isinstance(portals,dict):portals=None
        owned={i.identity for i in w.bag.values()};options=[]
        trip_items={i for i,n,r in self.hunt_travel.purchase_goals()} if self.hunt_travel and self.hunt_travel.plan else set()
        repeated={}
        for feature in (self.crafting,self.xp_boosters,self.hunt_travel):
            if feature:
                for identity,count,_ in feature.purchase_goals():
                    if count>0:repeated[identity]=min(20,count)
        for map_name in ('garner','magicsea','darkblue'):
            fee=0;approach=0
            if map_name!=w.map:
                edges=[(n,e) for n in (portals or {}).get('nodes',[]) if n['map']==w.map
                       for e in n['routes'] if e['map']==map_name]
                if not edges:continue
                node,edge=min(edges,key=lambda ne:math.dist(own.position,ne[0]['position']))
                fee=0 if own.values.get(0,0)<=edge['free_through_level'] else edge['fare']
                # Reserve the paid return journey as well as the next100G of supplies.
                reserve=2*fee+100;approach=math.dist(own.position,node['position'])+9600
                arrival=edge['arrival_cm']
            else:reserve=100;arrival=own.position
            essentials=set(self.critical_items(map_name))
            combat_items=set(self.combat_items)
            for shop in self.npcs.shops(map_name):
                if self.failed_suppliers.get(shop['key'],0)>now:continue
                for identity in shop['offers']:
                    if identity in owned and identity not in combat_items and identity not in repeated:continue
                    if coral_only and not (identity in combat_items and self.gear.types.get(identity)==29):continue
                    price=self.life.prices.get(identity,0)
                    from pet_care import PET_IDS
                    food_reserve=max(0,2-self.petcare.count(2312))*self.life.prices.get(2312,0) if self.petcare and identity in PET_IDS else 0
                    purchase_reserve=0 if map_name==w.map and identity in (817,867,635) and price==1 else reserve
                    if price<=0 or price+purchase_reserve+food_reserve>cash:continue
                    if self.petcare and identity not in PET_IDS|{1847,227,2312,4602,4603,4604}|trip_items and identity not in self.combat_items and price>max(0,cash-reserve-self.petcare.savings()):continue
                    critical=identity in essentials
                    urgent=(identity in combat_items or identity==self.emergency_ticket or identity in trip_items
                            or identity==2312 and self.petcare and self.petcare.needs_food_visit())
                    if self.progression_visit and not urgent:continue
                    if not critical and price>cash//4:continue
                    upgrade=self.gear.upgrade(own,identity,free)
                    if not critical and not upgrade:continue
                    if not critical:
                        change=self.gear.transition(own,identity,free)
                        # A ring or necklace cannot evict a coral required for spells.
                        if change and any(link in getattr(own,'required_coral_links',(5,6,7)) and self.gear.types.get(own.equipment.get(link,0))==29
                                and self.gear.types.get(identity)!=29 for link in own.equipment
                                if own.equipment.get(link)!=change[0].get(link)):
                            continue
                    kind=self.gear.types.get(identity);empty_accessory=False
                    if kind in (25,26):
                        empty_accessory=any(not own.equipment.get(link) for link in self.gear.gear[identity]['links'])
                    gain=upgrade[0] if upgrade else 1
                    priority=-1 if identity==2312 and self.petcare and self.petcare.needs_food_visit() else 0 if critical else 1 if empty_accessory else 2
                    if self.petcare and identity in PET_IDS and not self.petcare.fairy():priority=-1
                    job=own.values.get(4)
                    caster_blocked=(job in (5,13,14) and (not w.skills.get(99,{}).get('level') or self.gear.types.get(own.equipment.get(9))!=9)
                                    or self.urgent_coral())
                    if caster_blocked and identity in combat_items:priority=-2
                    if identity in trip_items:priority=-1
                    travel=approach+math.dist(arrival,shop['position'])
                    score=gain/max(1,price)/(1+travel/12000)
                    options.append(((priority,-score,travel,price,shop['key'],identity),
                        {'map':map_name,'shop':shop,'item':identity,'critical':critical,'reserved_travel_gold':2*fee,
                         'started':now,'price':price,'quantity':repeated.get(identity),'reason':'основное снабжение' if critical else 'заполняет слот украшения' if empty_accessory else 'улучшает экипировку'}))
        self.critical_items() # Remote shop scans must not overwrite current-map essentials.
        if not options:return None
        self.knowledge_plans+=1;return min(options,key=lambda row:row[0])[1]

    def on_map(self,now,was_dead=False):
        plan=self.supply_plan
        self.finish(now,0)
        if plan and not was_dead and plan['map']==self.world.map:
            self.supply_plan=plan;self.next_shop=now

    def count(self,identity):return sum(i.count for i in self.world.bag.values() if i.identity==identity)
    def observe(self,command,payload,now,send):
        if not self.context:return False
        npc,stage,deadline=self.context
        if command==802 and stage=='talk':
            r=Reader(payload);source,page=r.long(),r.byte();r.string_bytes();count=r.byte()
            if count>64:raise ProtocolError('Too many shop functions')
            labels=[r.string() for _ in range(count)]
            if source!=npc:return True
            desired=(self.target_shop or {}).get('menu_pages',{}).get(str(self.wanted[0]),1) if self.wanted else 1
            label=(self.target_shop or {}).get('menu_labels',{}).get(str(desired))
            accepted={label.casefold()} if label else ({'trade','торговля','купить'} if desired==1 else {'trade - part '+str(desired)})
            index=next((i for i,label in enumerate(labels) if label.casefold() in accepted),None)
            if index is None:self.finish(now,180);return True
            send(301,function_request(npc,page,index));self.context=npc,'shop',now+8
            return True
        if command==805 and stage=='shop':
            source,offers=trade_page(payload)
            if source!=npc:return True
            identity,count=self.wanted
            offer=next(((page,index) for model,page,index in offers if model==identity),None)
            price=self.life.prices.get(identity,0);cash=self.world.own.values.get(8,0)
            if price>0:count=min(count,max(0,self.spend_limit(identity)//price))
            reserve=0 if identity in (817,867,635) and price==1 else 100
            if offer and count>0 and price>0 and price*count<=max(0,cash-reserve) and price*count<=self.spend_limit(identity):
                send(308,buy_request(npc,*offer,count));self.requests+=1
                self.pending=identity,self.count(identity),cash,now+12
                self.context=npc,'confirmation',now+12
            else:self.finish(now,180)
            return True
        return command in (801,802,803,805,806,807,808)
    def finish(self,now,delay=120):
        if self.supply_plan and delay>=180:
            self.failed_suppliers[self.supply_plan['shop']['key']]=now+300
            if len(self.failed_suppliers)>128:self.failed_suppliers.pop(next(iter(self.failed_suppliers)))
        self.supply_plan=None
        self.trip_purchase=False
        self.visit_started=None;self.visit_key=None
        self.context=None;self.pending=None;self.target_shop=None;self.wanted=None;self.next_shop=now+delay
    def tick(self,now,policy,safe,dialogue_busy=False,medical=False):
        if self.next_break is None:self.next_break=now+600
        w=self.world
        if self.pending:
            identity,before,cash,deadline=self.pending
            if self.count(identity)>before and w.own.values.get(8,cash)<cash:
                essential=self.progression_visit or identity in getattr(self,'combat_items',()) or (self.petcare and identity==2312)
                self.confirmed+=1;self.finish(now,2 if essential else 60)
            elif now>deadline:
                self.last_purchase_failure={'stage':'confirmation','item':identity,'bag_before':before,'bag_after':self.count(identity),'gold_before':cash,'gold_after':w.own.values.get(8),'time':now}
                self.timeouts+=1;self.finish(now,300)
            return True
        if self.context:
            if now>self.context[2]:
                self.last_purchase_failure={'stage':self.context[1],'item':self.wanted[0] if self.wanted else None,'time':now}
                self.timeouts+=1;self.finish(now,300)
            return True
        if not safe or dialogue_busy:return False
        activity=getattr(policy,'activity',None)
        self.progression_visit=bool(activity and activity.hunting(now) is True)
        food_needed=bool(self.petcare and self.petcare.needs_food_visit())
        trip_items={i for i,_,_ in self.hunt_travel.purchase_goals()} if self.hunt_travel else set()
        if self.progression_visit or self.trip_purchase:
            # Revalidate walking goals after a trip ends. Native menus and
            # payments in flight have already been handled above.
            self.critical_items()
            required=self.combat_items|trip_items|{self.emergency_ticket,1847}
            if food_needed:required.add(2312)
            planned=self.supply_plan['item'] if self.supply_plan else self.wanted[0] if self.wanted else None
            if planned is not None and planned not in required:self.finish(now,0)
        if food_needed and not self.food_visit_requested:
            self.next_shop=min(self.next_shop,now);self.next_supply_check=min(self.next_supply_check,now)
            if self.rest_until:self.end_rest(now)
            if self.wanted and self.wanted[0]!=2312:
                self.wanted=self.target_shop=self.supply_plan=None
        self.food_visit_requested=food_needed
        business=bool(getattr(policy,'economy',None) and policy.economy.business(w,now) is True)
        if (business or self.progression_visit) and self.rest_until:self.end_rest(now)
        if self.rest_until and not medical and not business:
            if self.rest_directory and not self.rest_directory.acquire(self.owner,now):self.end_rest(now);return False
            if now>=self.rest_until:self.end_rest(now);return False
            self.reason='идёт на короткую прогулку по городу'
            if math.dist(policy.position(now),self.home)>1800:
                goal=policy.nav.nearest(self.home,6)
                if not goal or not policy.move_to(goal,now):self.end_rest(now);return False
                return True
            if self.rest_arrived is None:self.rest_arrived=now;self.rest_until=now+self.rng.uniform(40,100);self.breaks+=1
            if now<self.rest_pause_until:
                self.reason='короткая остановка во время прогулки';return True
            if self.rest_goal and math.dist(policy.position(now),self.rest_goal)<200:
                self.walk_stops+=1;self.rest_goal=None;self.rest_pause_until=now+self.rng.uniform(3,8);return True
            if not self.rest_goal:self.rest_goal=self.choose_walk_stop(now,policy)
            if self.rest_goal and policy.move_to(self.rest_goal,now):return True
            self.end_rest(now);return False
        if self.rest_due and not medical and not business and not self.progression_visit and now>=self.next_break:
            if self.rest_directory and not self.rest_directory.acquire(self.owner,now):return False
            self.rest_until=now+180;return True
        if now<self.next_shop:return False
        if self.supply_plan and now-self.supply_plan['started']>300:self.finish(now,180);return False
        if not self.supply_plan and not self.wanted and not medical:
            self.supply_plan=self.plan_supplies(now,policy)
        if self.supply_plan:
            plan=self.supply_plan
            if plan['map']!=w.map:
                travel=getattr(policy,'travel',None)
                self.reason='ищет покупку в другом городе: '+plan['shop']['name']
                if travel and travel.tick(now,policy,safe,dialogue_busy):return True
                return False # No fare/route: keep productive hunting.
            quantity=next((n for i,n,_ in self.petcare.purchase_goals() if i==plan['item']),1) if self.petcare else 1
            quantity=plan.get('quantity') or quantity
            self.wanted=(plan['item'],quantity);self.target_shop=plan['shop']
        if not self.wanted:
            # Healthy beginners must first earn something, not all shop on login.
            hp=w.own.values.get(1,0);maximum=max(1,w.own.values.get(31,1))
            earned=(self.work_kills>=2 or self.work_quests>0 or w.own.values.get(0,1)>=4)
            if not earned and hp>=maximum*.85:return False
            self.wanted=self.choose_want()
            if not self.wanted:self.next_shop=now+120;return False
            shops=[s for s in self.life.services['shops'].get(w.map,[]) if self.wanted[0] in s['offers']]
            if not shops:self.finish(now,300);return False
            self.target_shop=min(shops,key=lambda s:math.dist(policy.position(now),s['position']))
        self.trip_purchase=self.wanted[0] in trip_items
        point=self.target_shop['position']
        key=(w.map,self.wanted[0],tuple(point))
        if self.visit_key!=key:self.visit_key=key;self.visit_started=now
        elif now-self.visit_started>=120:
            # A real menu/payment already in flight is handled above. Bound
            # only the approach; changing console labels must not reset it.
            self.approach_timeouts+=1;self.finish(now,180)
            self.reason='Не дошёл до продавца за120с; откладывает визит и продолжает охоту'
            return False
        self.reason='покупки у городского торговца'
        returner=getattr(policy,'stuck_return',None)
        # Do not consume a reserved return ticket en route to the ticket shop.
        if self.trip_purchase:returner=None
        city_center=self.life.services.get('city_centres',{}).get(w.map,self.home)
        if (returner and math.dist(policy.position(now),point)>8000 and math.dist(point,city_center)<5000
                and returner.tick(now,policy,destination=w.map) is True):
            self.reason=returner.reason;return True
        npc=npc_near(w,point)
        if npc and math.dist(policy.position(now),npc.position)<=220:
            policy.send(301,talk_request(npc.identity));self.context=npc.identity,'talk',now+8;return True
        goal=policy.nav.nearest(npc.position if npc else point,6)
        if goal and policy.move_to(goal,now):return True
        self.finish(now,300);return False
    def summary(self):return {'wanted_item':self.wanted[0] if self.wanted else None,'visit_stage':self.context[1] if self.context else 'approach' if self.wanted else None,'approach_timeouts':self.approach_timeouts,'urgent_coral_supply':self.urgent_coral(),'last_purchase_failure':self.last_purchase_failure,'knowledge_purchase_plans':self.knowledge_plans,'shopping_destination':self.supply_plan['map'] if self.supply_plan else None,'planned_item':self.supply_plan['item'] if self.supply_plan else None,'shopping_goal':self.supply_plan['reason'] if self.supply_plan else None,'purchase_requests':self.requests,'confirmed_purchases':self.confirmed,'timeouts':self.timeouts,'city_breaks':self.breaks,'city_walk_stops':self.walk_stops,'state':self.reason,'rest_due_after_tasks':self.rest_due,'kills_since_break':self.work_kills,'quests_since_break':self.work_quests,'bench_sitting_implemented':False}
