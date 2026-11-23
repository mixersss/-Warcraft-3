"""Paid, source-verified same-map portal shortcuts; native dialogs and arrival only."""
import math
import struct
from city_travel import CityTravel
from adventure import talk_request
from classic_wire import Reader, ProtocolError
from town import function_request
from route_search import RoutePending


def route_length(points):return sum(math.dist(a,b) for a,b in zip(points,points[1:]))


class PortalShortcut(CityTravel):
    def __init__(self,world,send,portals,travel_data=None):
        super().__init__(world,send,1,{},portals)
        self.plan=None;self.goal=None;self.next_check=0;self.last_check=None
        self.savings_seconds=0;self.arrival_origin=None
        data=travel_data or {}
        self.nodes=[*(portals or {}).get('nodes',()),*data.get('island_nodes',())]
        self.tickets=data.get('tickets',())
        self.ticket=None;self.failed_tickets={};self.gold_before=None

    @property
    def busy(self):return self.plan is not None or self.ticket is not None

    def abort(self,now,problem='сокращённый переход не подтверждён'):
        super().abort(now,problem)
        if self.ticket:self.failed_tickets[self.ticket[0]]=now+300
        self.plan=None;self.ticket=None;self.goal=None;self.next_check=now+60
        self.arrival_origin=None;self.gold_before=None

    def ticket_count(self,identity):
        return sum(item.count for item in self.world.bag.values() if item.identity==identity and item.valid)

    def landing(self,nav,point):
        p=tuple(point)
        if not hasattr(nav,'needs_recovery') or not nav.needs_recovery(p,ignore_temporary=True):
            return nav.nearest(p,1)
        path=nav.recovery_path(p,radius=6,static=True)
        return path[-1] if path and route_length(path)<=550 else None

    def consider(self,goal,now,policy):
        if self.busy:return self.resume(now,policy)
        key=self.world.map,tuple(goal)
        if key==self.last_check and now<self.next_check:return False
        self.last_check=key
        own=self.world.own;origin=own.position
        straight=math.dist(origin,goal)
        if straight<6000:return False
        if any(getattr(f,'context',None) or getattr(f,'pending',None) for f in
               (policy.adventure,policy.town,policy.career,policy.story,policy.vendor,policy.party,policy.market) if f):return False
        speed=max(100,min(own.values.get(44,480),3000))
        component=getattr(getattr(policy,'nav',None),'land_component',None)
        origin_component=component(origin) if component else None
        goal_component=component(goal) if component else None
        separated=bool(origin_component and goal_component and origin_component!=goal_component)
        options=[]
        for node in self.nodes:
            if node['map']!=self.world.map or self.failed_portals.get(tuple(node['position']),0)>now:continue
            for edge in node['routes']:
                if edge['map']!=self.world.map:continue
                fee=0 if own.values.get(0,0)<=edge.get('free_through_level',-1) else edge['fare']
                if own.values.get(8,0)<fee+100:continue
                approach=math.dist(origin,node['position'])
                estimate=(approach+math.dist(edge['arrival_cm'],goal))/speed+20
                if separated and not self.ticket_count(4602):continue
                options.append((estimate,node,edge,(edge['arrival_cm'],),20))
        if (self.tickets and self.world.bag_ready and not self.world.bag_disabled
                and not getattr(policy,'pending_action',None)
                and all(own.values.get(a,0)>=own.values.get(b,1) for a,b in ((1,31),(2,32)))):
            for ticket in self.tickets:
                identity=ticket['item_id']
                if (ticket['map']!=self.world.map or own.values.get(0,0)<ticket['minimum_level']
                        or self.failed_tickets.get(identity,0)>now or not self.ticket_count(identity)):
                    continue
                points=ticket['points']
                # Keep a way home before transferring to separated land.
                if separated and identity!=4602 and not self.ticket_count(4602):continue
                estimate=max(math.dist(p,goal) for p in points)/speed+8
                options.append((estimate,None,ticket,points,8))
        if not options:self.next_check=now+20;return False
        chosen=None;walking=math.inf if separated else None;waiting=False
        for estimate,node,record,points,overhead in sorted(options,key=lambda row:row[0]):
            if chosen and estimate>=chosen[0]:break
            landings=[self.landing(policy.nav,point) for point in points]
            if not all(landings):continue
            try:
                with policy.nav.background_work(True):
                    if walking is None and estimate>=straight/speed:
                        direct=policy.nav.path(origin,goal)
                        if not direct:continue
                        walking=route_length(direct)/speed
                    if walking is not None and estimate>walking:
                        break
                    start=policy.nav.nearest(node['position'],2) if node else origin
                    before=policy.nav.path(origin,start) if start else []
                    if not before:continue
                    after=[policy.nav.path(landing,goal) for landing in landings]
                    if not all(after):continue
                    total=(route_length(before)+max(map(route_length,after)))/speed+overhead
                    if separated:
                        saved=math.inf
                    elif total+10<straight/speed:
                        saved=straight/speed-total
                    else:
                        if walking is None:
                            direct=policy.nav.path(origin,goal)
                            if not direct:continue
                            walking=route_length(direct)/speed
                        saved=walking-total
            except RoutePending:
                waiting=True
                break
            if saved>=10:chosen=total,saved,node,record
        if not chosen:
            if not waiting:self.next_check=now+20
            return False
        _,saved,node,record=chosen
        self.savings_seconds=round(saved,1) if math.isfinite(saved) else None;self.goal=tuple(goal)
        if node is None:
            from hunter import action_header
            identity=record['item_id']
            slot=next(slot for slot,item in self.world.bag.items() if item.identity==identity and item.valid)
            self.ticket=identity,record['points'],self.ticket_count(identity),now+20
            self.arrival_origin=origin;self.target=self.world.map
            self.reason='сокращает путь билетом '+record['name']
            self.requests+=1
            policy.emit(action_header(self.world.own_id,policy.sequence,11)+struct.pack('>hh',slot,-1))
            return True
        self.plan=node,record;self.portal=node;self.target=record['map']
        self.trip_started=now;self.last_position=origin;self.last_progress=now
        self.reason='сокращает путь через '+node['name']
        return self.resume(now,policy)

    def resume(self,now,policy):
        if self.ticket:
            item,points,before,deadline=self.ticket
            w=self.world
            if (w.map==self.target and w.bag_ready and not w.bag_disabled
                    and self.ticket_count(item)<before and math.dist(w.own.position,self.arrival_origin)>1000
                    and any(math.dist(w.own.position,p)<=600 for p in points)):
                self.ticket=None;self.target=None;self.goal=None;self.arrival_origin=None
                self.arrivals+=1;self.next_check=now+30;self.reason='прибытие по билету подтверждено'
                return False
            if now>=deadline:self.abort(now,'нет подтверждения билета или высадки');return False
            return True
        if not self.plan:return False
        node,edge=self.plan;own=self.world.own
        if self.context:
            if self.context[1]=='map' and self.arrival_origin is None:self.arrival_origin=own.position
            if (self.context[1]=='map' and self.arrival_origin is not None
                    and math.dist(own.position,self.arrival_origin)>1000
                    and self.world.map==edge['map'] and math.dist(own.position,edge['arrival_cm'])<=600
                    and self.fare_confirmed()):
                self.on_map(now);return False
            if now>=self.context[2]:self.abort(now,'нет ответа на сокращённый переход');return False
            return True
        if math.dist(own.position,self.last_position)>=100:
            self.last_position=own.position;self.last_progress=now
        if now-self.last_progress>35:self.abort(now,'нет движения к портальщице');return False
        npc=next((e for e in self.world.entities.values() if e.control in (2,3)
                  and math.dist(e.position,node['position'])<350),None)
        if npc and math.dist(own.position,npc.position)<=220:
            self.send(301,talk_request(npc.identity));self.requests+=1
            self.context=npc.identity,'menu',now+8;return True
        point=policy.nav.nearest(node['position'],2)
        if point and policy.move_to(point,now,use_portals=False):return True
        self.abort(now,'нет проверенного подхода к портальщице');return False

    def fare_confirmed(self):
        edge=self.plan[1]
        fee=0 if self.world.own.values.get(0,0)<=edge.get('free_through_level',-1) else edge['fare']
        return fee==0 or (self.gold_before is not None and self.world.own.values.get(8,0)<=self.gold_before-fee)

    def observe(self,command,payload,now):
        if command!=802 or not self.context or not self.plan:return False
        r=Reader(payload);source,page=r.long(),r.byte();r.string_bytes();count=r.byte()
        if count>64:raise ProtocolError('Too many teleporter functions')
        labels=[r.string() for _ in range(count)]
        npc,stage,_=self.context
        if source!=npc:return False
        edge=self.plan[1]
        wanted=edge['label'] if stage=='menu' else 'Teleport'
        self.last_menu=[label[:160] for label in labels]
        if wanted not in labels:self.abort(now,'нет выбранного перехода в меню');return True
        if stage=='confirm':
            own=self.world.own
            fee=0 if own.values.get(0,0)<=edge.get('free_through_level',-1) else edge['fare']
            self.gold_before=own.values.get(8,0)
            if self.gold_before<fee:self.abort(now,'не хватает золота для перехода');return True
            self.arrival_origin=own.position
        if stage in ('menu','confirm'):
            self.send(301,function_request(npc,page,labels.index(wanted)));self.requests+=1
            self.context=npc,('confirm' if stage=='menu' else 'map'),now+(8 if stage=='menu' else 20)
        return True

    def on_map(self,now):
        if self.ticket:return # Reconcile the native bag after entry.
        if self.plan:
            edge=self.plan[1]
            if self.world.map!=edge['map'] or math.dist(self.world.own.position,edge['arrival_cm'])>600:
                self.abort(now,'прибытие не совпало с проверенной точкой');return
            if not self.context or self.context[1]!='map' or not self.fare_confirmed():return
        super().on_map(now)
        self.plan=None;self.goal=None;self.arrival_origin=None;self.next_check=now+30

    def summary(self):
        result=super().summary()
        result.update(goal=self.goal,estimated_saved_seconds=self.savings_seconds,
                      ticket_pending=self.ticket[0] if self.ticket else None,
                      arrival_confirmed_only_by_server=True)
        return result
