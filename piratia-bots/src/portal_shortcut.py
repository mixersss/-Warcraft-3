"""Paid, source-verified same-map portal shortcuts; native dialogs and arrival only."""
import math
from city_travel import CityTravel
from adventure import talk_request
from route_search import RoutePending


def route_length(points):return sum(math.dist(a,b) for a,b in zip(points,points[1:]))


class PortalShortcut(CityTravel):
    def __init__(self,world,send,portals):
        super().__init__(world,send,1,{},portals)
        self.plan=None;self.goal=None;self.next_check=0;self.last_check=None
        self.savings_seconds=0;self.arrival_origin=None

    @property
    def busy(self):return self.plan is not None

    def abort(self,now,problem='сокращённый переход не подтверждён'):
        super().abort(now,problem)
        self.plan=None;self.goal=None;self.next_check=now+60

    def consider(self,goal,now,policy):
        if self.plan:return self.resume(now,policy)
        if now<self.next_check or not self.portals:return False
        key=(self.world.map,tuple(goal))
        if key!=self.last_check:self.last_check=key;self.next_check=now
        own=self.world.own;origin=own.position
        if math.dist(origin,goal)<10000:return False
        if any(getattr(f,'context',None) or getattr(f,'pending',None) for f in
               (policy.adventure,policy.town,policy.career,policy.story,policy.vendor,policy.party,policy.market) if f):return False
        speed=max(100,min(own.values.get(44,480),3000))
        options=[]
        for node in self.portals['nodes']:
            if node['map']!=self.world.map or self.failed_portals.get(tuple(node['position']),0)>now:continue
            for edge in node['routes']:
                if edge['map']!=self.world.map:continue
                fee=0 if own.values.get(0,0)<=edge['free_through_level'] else edge['fare']
                if own.values.get(8,0)<fee+100:continue
                estimate=math.dist(origin,node['position'])+math.dist(edge['arrival_cm'],goal)+20*speed
                if estimate+10*speed<math.dist(origin,goal):options.append((estimate,node,edge))
        if not options:self.next_check=now+30;return False
        _,node,edge=min(options,key=lambda r:r[0])
        start=policy.nav.nearest(node['position'],2);arrival=policy.nav.nearest(edge['arrival_cm'],6)
        if not start or not arrival:self.next_check=now+30;return False
        try:
            with policy.nav.background_work(True):
                before=policy.nav.path(origin,start);after=policy.nav.path(arrival,goal)
                via=(route_length(before)+route_length(after))/speed+20 if before and after else math.inf
                lower_bound=math.dist(origin,goal)/speed
                # A checked portal route faster than even a straight walk
                # cannot lose to any ground route. Avoid a futile long search.
                direct=None if via+10<lower_bound else policy.nav.path(origin,goal)
        except RoutePending:return False # Foreground walking keeps its own budget.
        if not before or not after:self.next_check=now+30;return False
        via=(route_length(before)+route_length(after))/speed+20
        walking=lower_bound if direct is None else route_length(direct)/speed if direct else math.inf
        if walking-via<10:self.next_check=now+30;return False
        self.savings_seconds=round(walking-via,1) if math.isfinite(walking) else None
        self.plan=node,edge;self.portal=node;self.goal=tuple(goal)
        self.target=edge['map'];self.trip_started=now;self.last_position=origin;self.last_progress=now
        self.reason='сокращает путь через '+node['name']
        return self.resume(now,policy)

    def resume(self,now,policy):
        if not self.plan:return False
        node,edge=self.plan;own=self.world.own
        if self.context:
            if self.context[1]=='map' and self.arrival_origin is None:self.arrival_origin=own.position
            if (self.context[1]=='map' and self.arrival_origin is not None
                    and math.dist(own.position,self.arrival_origin)>1000
                    and self.world.map==edge['map'] and math.dist(own.position,edge['arrival_cm'])<=600):
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

    def observe(self,command,payload,now):
        used=super().observe(command,payload,now)
        if used and self.context and self.context[1]=='map':self.arrival_origin=self.world.own.position
        return used

    def on_map(self,now):
        if self.plan:
            edge=self.plan[1]
            if self.world.map!=edge['map'] or math.dist(self.world.own.position,edge['arrival_cm'])>600:
                self.abort(now,'прибытие не совпало с проверенной точкой');return
        super().on_map(now)
        self.plan=None;self.goal=None;self.arrival_origin=None;self.next_check=now+60

    def summary(self):
        result=super().summary()
        result.update(goal=self.goal,estimated_saved_seconds=self.savings_seconds,
                      arrival_confirmed_only_by_server=True)
        return result
