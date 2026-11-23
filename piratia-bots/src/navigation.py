"""Bounded A* over numerical ground grids derived from owner map resources."""
import base64
import heapq
import threading
import time
from collections import OrderedDict
from collections import deque
from contextlib import contextmanager
from route_search import Search,RoutePending
from functools import lru_cache
import json
import math
import zlib
import hashlib
import struct
from pathlib import Path


class Navigation:
    def __init__(self, path):
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        self.local = threading.local()
        self.map = data.get('map','garner')
        self.geometry_revision=data.get('geometry_revision','legacy-blk')
        self.connected_bits=(zlib.decompress(base64.b64decode(data['connected_ground_zlib']))
                             if 'connected_ground_zlib' in data else None)
        self.origin = tuple(data['origin'])
        self.width, self.height = data['width'], data['height']
        if not 1 <= self.width <= 4096 or not 1 <= self.height <= 4096:
            raise ValueError('Invalid navigation crop size')
        self.cells = zlib.decompress(base64.b64decode(data['walkable_zlib']))
        if len(self.cells) != self.width * self.height:
            raise ValueError('Incomplete navigation crop')
        self.recovery_cells=(zlib.decompress(base64.b64decode(data['recovery_walkable_zlib']))
                             if 'recovery_walkable_zlib' in data else None)
        if self.recovery_cells is not None and len(self.recovery_cells)!=len(self.cells):
            raise ValueError('Incomplete physical recovery grid')
        self.recovery_bits=(zlib.decompress(base64.b64decode(data['recovery50_free_zlib']))
                            if 'recovery50_free_zlib' in data else None)
        self.safe_recovery_bits=(zlib.decompress(base64.b64decode(data['recovery50_dry_zlib']))
                                 if 'recovery50_dry_zlib' in data else None)
        if self.safe_recovery_bits is not None and len(self.safe_recovery_bits)!=(self.width*self.height*4+7)//8:
            raise ValueError('Incomplete dry recovery grid')
        if self.recovery_bits is not None and len(self.recovery_bits)!=(self.width*self.height*4+7)//8:
            raise ValueError('Incomplete 50cm recovery grid')
        self.combat_bits=(zlib.decompress(base64.b64decode(data['combat_no_fight_zlib']))
                          if 'combat_no_fight_zlib' in data else None)
        if self.combat_bits is not None and len(self.combat_bits)!=(self.width*self.height+7)//8:
            raise ValueError('Incomplete no-fight grid')
        self.combat_zone_revision=data.get('combat_zone_revision','unknown')
        self.waypoints = [tuple(p) for p in data['waypoints']]
        self.land_labels=None;self.land_label_width=0;self.land_source_cells=self.cells
        if data.get('land_component_labels_zlib'):
            labels=zlib.decompress(base64.b64decode(data['land_component_labels_zlib']))
            width=data.get('land_component_label_width',0)
            if (width in (1,2) and len(labels)==self.width*self.height*width
                and data.get('land_component_source_sha256')==hashlib.sha256(self.cells).hexdigest()
                and data.get('land_component_labels_sha256')==hashlib.sha256(labels).hexdigest()):
                self.land_labels=labels;self.land_label_width=width
        if self.connected_bits is not None and len(self.connected_bits)!=(self.width*self.height+7)//8:
            raise ValueError('Incomplete connected ground grid')

    def needs_recovery(self,position,ignore_temporary=False):
        cell=self.cell(position)
        if ignore_temporary:
            x,y=cell
            if not (0<=x<self.width and 0<=y<self.height and self.cells[y*self.width+x]==1):return True
        elif not self.free(cell):return True
        bits=getattr(self,'connected_bits',None)
        if bits is None:return False
        index=cell[1]*self.width+cell[0]
        return not bool(bits[index//8]&(1<<(7-index%8)))

    def cell(self, position):
        return position[0] // 100 - self.origin[0], position[1] // 100 - self.origin[1]

    def position(self, cell):
        return (cell[0] + self.origin[0]) * 100 + 50, (cell[1] + self.origin[1]) * 100 + 50

    def free(self, cell):
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height and self.cells[y*self.width+x] == 1 and cell not in getattr(getattr(self,'local',None),'blocked_cells',())

    def combat_allowed(self,position):
        if position is None:return False
        bits=getattr(self,'combat_bits',None)
        if bits is None:return True # Legacy/unknown maps retain server-stall recovery.
        x,y=self.cell(position)
        if not (0<=x<self.width and 0<=y<self.height):return False
        index=y*self.width+x
        return not bool(bits[index//8]&(1<<(7-index%8)))

    def expire_obstacles(self,now):
        local=getattr(self,'local',None)
        if local is None or not getattr(local,'blocked_cells',None):return
        keep={cell:until for cell,until in local.obstacles.items() if until>now}
        if len(keep)!=len(local.obstacles):
            local.obstacles=keep;local.blocked_cells=frozenset(keep)
            if hasattr(local,'searches'):local.searches.clear()

    def avoid_cell(self,cell,now,seconds=30):
        """Short per-worker avoidance after an unrequested server movement stop.

        Never edit shared map cells or infer a whole lake from a single collision.
        """
        x,y=cell
        if not (0<=x<self.width and 0<=y<self.height and self.cells[y*self.width+x]==1):return False
        if not hasattr(self,'local'):self.local=threading.local()
        local=self.local
        self.expire_obstacles(now)
        rows=getattr(local,'obstacles',{});rows[cell]=now+seconds
        while len(rows)>64:rows.pop(next(iter(rows)))
        local.obstacles=rows;local.blocked_cells=frozenset(rows)
        if hasattr(local,'searches'):local.searches.clear()
        return True

    def nearest(self, position, radius=6):
        x,y = self.cell(position)
        if self.free((x,y)):return self.position((x,y))
        cells = ((x+dx,y+dy) for dx in range(-radius,radius+1) for dy in range(-radius,radius+1))
        for cell in sorted(cells,key=lambda c:(c[0]-x)**2+(c[1]-y)**2):
            if self.free(cell):
                return self.position(cell)
        return None

    def recovery_cell(self,position):
        scale=2 if getattr(self,'recovery_bits',None) is not None else 1
        step=100//scale
        return position[0]//step-self.origin[0]*scale,position[1]//step-self.origin[1]*scale

    def recovery_path(self,position,blocked=(),radius=24,limit=4096,static=False):
        """Exit an occupied excluded shore cell; never use this for normal travel.

        Original client/server hard obstacles and native land/bridge permissions
        still apply. Stop at the first reachable dry cell; do not cross a pond
        as a shortcut. Server movement remains authoritative.
        """
        physical=getattr(self,'recovery_cells',None)
        bits=getattr(self,'safe_recovery_bits',None) or getattr(self,'recovery_bits',None)
        if physical is None and bits is None:return []
        scale=2 if bits is not None else 1;step=100//scale
        width,height=self.width*scale,self.height*scale
        start=self.recovery_cell(position);blocked=set(blocked);radius*=scale
        raw_bits=getattr(self,'recovery_bits',None)
        start_index=start[1]*width+start[0]
        occupied_physical=(raw_bits is not None and 0<=start[0]<width and 0<=start[1]<height
                           and bool(raw_bits[start_index//8]&(1<<(7-start_index%8))))
        def free(c):
            x,y=c
            if not (0<=x<width and 0<=y<height) or (c!=start and c in blocked):return False
            index=y*width+x
            # The server may already have stopped us on the excluded edge of
            # a shore. Permit ONLY that occupied, physically clear origin; every
            # subsequent cell must still be dry. Never centre deeper into it.
            if c==start and occupied_physical:return True
            return bool(bits[index//8]&(1<<(7-index%8))) if bits is not None else physical[index]==1
        needs_recovery=(lambda point:self.needs_recovery(point,ignore_temporary=True)) if static else self.needs_recovery
        if not free(start) or not needs_recovery(position):return []
        parents={start:None};queue=deque([start]);goal=None
        while queue and len(parents)<=limit:
            current=queue.popleft()
            point=((current[0]+self.origin[0]*scale)*step+step//2,
                   (current[1]+self.origin[1]*scale)*step+step//2)
            if current!=start and not needs_recovery(point):goal=current;break
            x,y=current
            for dx,dy in ((0,-1),(-1,0),(1,0),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)):
                cell=x+dx,y+dy
                if (cell in parents or max(abs(cell[0]-start[0]),abs(cell[1]-start[1]))>radius
                        or not free(cell)):continue
                if dx and dy and (not free((x+dx,y)) or not free((x,y+dy))):continue
                parents[cell]=current;queue.append(cell)
                if len(parents)>=limit:break
        if goal is None:return []
        cells=[]
        while goal is not None:cells.append(goal);goal=parents[goal]
        points=[tuple(position)]
        for cell in reversed(cells):
            if cell==start and occupied_physical:continue
            point=((cell[0]+self.origin[0]*scale)*step+step//2,
                   (cell[1]+self.origin[1]*scale)*step+step//2)
            if point!=points[-1]:points.append(point)
        return points[:32]

    def path(self, start, end, limit=25000):
        a,b=self.land_component(start),self.land_component(end)
        if a and b and a!=b:
            local=getattr(self,'local',None)
            if local is not None:local.component_rejections=getattr(local,'component_rejections',0)+1
            return []
        key=(self.cell(start),self.cell(end),limit,tuple(sorted(getattr(getattr(self,'local',None),'blocked_cells',()))),getattr(getattr(self,'local',None),'lane','foreground'))
        cached = self._runtime_path(key) if getattr(self,'incremental',False) and getattr(self.local,'active',False) else self._path(*key)
        result = list(cached)
        if result:
            result[0] = tuple(start)
        return result

    def land_component(self,position):
        labels=getattr(self,'land_labels',None)
        if labels is None or self.cells is not getattr(self,'land_source_cells',self.cells):return None
        x,y=self.cell(position)
        if not (0<=x<self.width and 0<=y<self.height):return 0
        index=y*self.width+x
        return labels[index] if self.land_label_width==1 else struct.unpack_from('<H',labels,index*2)[0]

    def shore_exit(self,position,blocked=(),maximum_cm=250):
        """Bounded native escape attempt from an already occupied shore edge.

        No global passability change. Hard obstacles and diagonal corners are
        checked on the original 50cm grid; the endpoint must be connected dry
        ground. Only the server can accept the short move through the margin.
        """
        raw=getattr(self,'recovery_bits',None);dry=getattr(self,'safe_recovery_bits',None)
        if raw is None or dry is None or not self.needs_recovery(position):return []
        width,height=self.width*2,self.height*2;start=self.recovery_cell(position);blocked=set(blocked)
        def free(cell):
            x,y=cell
            if not (0<=x<width and 0<=y<height) or (cell!=start and cell in blocked):return False
            i=y*width+x;return bool(raw[i//8]&(1<<(7-i%8)))
        if not free(start):return []
        parents={start:None};queue=deque([start]);goal=None
        while queue and len(parents)<256:
            cell=queue.popleft();point=((cell[0]+self.origin[0]*2)*50+25,(cell[1]+self.origin[1]*2)*50+25)
            if math.dist(position,point)>maximum_cm:continue
            if cell!=start and not self.needs_recovery(point):goal=cell;break
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)):
                other=cell[0]+dx,cell[1]+dy
                if other in parents or not free(other):continue
                if dx and dy and (not free((cell[0]+dx,cell[1])) or not free((cell[0],cell[1]+dy))):continue
                parents[other]=cell;queue.append(other)
        if goal is None:return []
        points=[]
        while goal!=start:
            points.append(((goal[0]+self.origin[0]*2)*50+25,(goal[1]+self.origin[1]*2)*50+25));goal=parents[goal]
        route=[tuple(position),*reversed(points)]
        return route if sum(math.dist(a,b) for a,b in zip(route,route[1:]))<=maximum_cm else []

    def segment(self,start,end):
        """Native routes contain turns, not every A* grid cell (maximum 32)."""
        if self.cell(start)!=self.cell(end):
            endpoint=self.position(self.cell(end))
            if self.line_clear(start,endpoint):return [tuple(start),endpoint]
        path=self.path(start,end)
        if len(path)<3:return path
        # Keep the first centred cell: arbitrary sub-cell start positions must
        # not change the angle of a checked diagonal around a wall.
        turns=[path[0]]
        for i in range(1,len(path)-1):
            before=(path[i][0]-path[i-1][0],path[i][1]-path[i-1][1])
            after=(path[i+1][0]-path[i][0],path[i+1][1]-path[i][1])
            if before!=after:turns.append(path[i])
        turns.append(path[-1])
        return turns[:32]

    def line_clear(self,start,end):
        """Supercover of the actual segment, including both sides of corners."""
        x,y=self.cell(start);gx,gy=self.cell(end)
        dx,dy=end[0]-start[0],end[1]-start[1]
        sx=1 if dx>0 else -1;sy=1 if dy>0 else -1
        tx=(((x+(1 if dx>0 else 0)+self.origin[0])*100-start[0])/dx) if dx else math.inf
        ty=(((y+(1 if dy>0 else 0)+self.origin[1])*100-start[1])/dy) if dy else math.inf
        step_x=100/abs(dx) if dx else math.inf;step_y=100/abs(dy) if dy else math.inf
        if not self.free((x,y)):return False
        while (x,y)!=(gx,gy):
            if abs(tx-ty)<1e-12:
                if not self.free((x+sx,y)) or not self.free((x,y+sy)):return False
                x+=sx;y+=sy;tx+=step_x;ty+=step_y
            elif tx<ty:x+=sx;tx+=step_x
            else:y+=sy;ty+=step_y
            if not self.free((x,y)):return False
        return True

    def movement_segment(self,start,end,max_distance=2400):
        """Send a short checked prefix, preserving the rest of a cached route.

        A 32-turn packet can otherwise span most of a map. Short prefixes let
        the controller react to visible mobs and actual server corrections in
        seconds; they do not change passability or permit shoreline shortcuts.
        """
        route=self.segment(start,end)
        if len(route)<2:return route
        result=[route[0]];remaining=max_distance
        for point in route[1:]:
            origin=result[-1];length=math.dist(origin,point)
            if length<=remaining:
                result.append(point);remaining-=length
                if remaining<1:break
            else:
                fraction=remaining/length
                cut=tuple(round(a+(b-a)*fraction) for a,b in zip(origin,point))
                if cut!=origin and self.line_clear(origin,cut):result.append(cut)
                break
        return result

    def enable_incremental(self):
        self.incremental=True;self.local=threading.local()
        self.completed=OrderedDict();self.corridors=OrderedDict();self.cache_lock=threading.Lock()

    def begin_turn(self,expansions=512):
        local=self.local
        if not hasattr(local,'searches'):
            local.searches=OrderedDict();local.yields=local.expansions=local.finished=0
        local.remaining=expansions;local.background_remaining=128
        local.turn_expanded=0;local.deadline=None;local.active=True;local.lane='foreground'

    @contextmanager
    def background_work(self,reserve_foreground=False):
        local=getattr(self,'local',None)
        if not getattr(local,'active',False):
            yield
            return
        old_lane=local.lane;old_remaining=local.remaining
        outer_deadline=local.deadline
        allowance=min(old_remaining,local.background_remaining) if reserve_foreground else old_remaining
        local.lane='background';local.remaining=allowance
        if reserve_foreground:
            deadline=time.thread_time()+.0015
            local.deadline=min(outer_deadline,deadline) if outer_deadline is not None else deadline
        try:yield
        finally:
            used=allowance-local.remaining
            if reserve_foreground:local.background_remaining-=used
            local.remaining=max(0,old_remaining-used)
            if reserve_foreground:local.deadline=outer_deadline
            local.lane=old_lane

    def end_turn(self):self.local.active=False

    def cancel_pending(self,goal=None):
        if getattr(self,'incremental',False) and hasattr(self.local,'searches'):
            if goal is None:self.local.searches.clear()
            else:
                cell=self.cell(goal)
                for key in list(self.local.searches):
                    if key[1]==cell and key[4]=='foreground':self.local.searches.pop(key)

    def pending_farm_search(self,goal):
        local=getattr(self,'local',None)
        cell=self.cell(goal)
        return next(((key,len(search.closed)) for key,search in getattr(local,'searches',{}).items()
                     if key[1]==cell and key[4]=='foreground'),None)

    def camp_route_ready(self,start,goal):
        """Check already calculated paths without starting another A* job."""
        if not getattr(self,'incremental',False):return False
        blocked=tuple(sorted(getattr(self.local,'blocked_cells',())))
        key=(self.cell(start),self.cell(goal),25000,blocked,'foreground')
        with self.cache_lock:
            result=self.completed.get(key[:4])
        if result is not None:return len(result)>1
        route=self._reuse_corridor(key)
        if not route:return False
        self._remember(key,route)
        return True

    def planning_stats(self):
        if not getattr(self,'incremental',False):return {}
        l=self.local
        return {'geometry_revision':getattr(self,'geometry_revision','legacy-blk'),
                'impossible_land_routes_rejected_without_search':getattr(l,'component_rejections',0),
                'yields':getattr(l,'yields',0),'expanded_nodes':getattr(l,'expansions',0),
                'completed_searches':getattr(l,'finished',0),'pending_searches':len(getattr(l,'searches',{})),
                'shared_route_hits':getattr(l,'shared_route_hits',0),
                'pending_jobs':[{'start':list(self.position(k[0])),'goal':list(self.position(k[1])),
                                 'known_cells':len(s.costs),'expanded_cells':len(s.closed),'open_nodes':len(s.queue),
                                 'heuristic_weight':s.weight,'lane':k[4]} for k,s in getattr(l,'searches',{}).items()]}

    def direct(self,start,goal):
        """Checked grid line: every diagonal also requires both side cells free."""
        dx,dy=goal[0]-start[0],goal[1]-start[1];steps=max(abs(dx),abs(dy))
        route=[];previous=None
        for i in range(steps+1):
            cell=(start[0]+round(dx*i/steps),start[1]+round(dy*i/steps)) if steps else start
            if not self.free(cell):return ()
            if previous and cell[0]!=previous[0] and cell[1]!=previous[1]:
                if not self.free((cell[0],previous[1])) or not self.free((previous[0],cell[1])):return ()
            route.append(self.position(cell));previous=cell
        return tuple(route)

    def _new_search(self,start,goal):
        x,y=self.position(start)
        westbound_argent=(getattr(self,'map',None)=='garner' and 208000<=x<=237000 and 260000<=y<=288000
                          and start[0]-goal[0]>=180)
        # Checked dry grid edges are symmetric. Searching from the west
        # reaches the narrow Argent approaches without exhausting the budget.
        a,b=(goal,start) if westbound_argent else (start,goal)
        return Search(a,b,heuristic_weight=4)

    def _runtime_path(self,key):
        route_key=key[:4]
        with self.cache_lock:
            if route_key in self.completed:
                self.completed.move_to_end(route_key);return self.completed[route_key]
        local=self.local
        reused=self._reuse_corridor(key)
        if reused:
            local.shared_route_hits=getattr(local,'shared_route_hits',0)+1
            for previous in list(local.searches):
                if previous[4]==key[4]:local.searches.pop(previous,None)
            return self._remember(key,reused)
        if key not in local.searches:
            start,goal,_=key[:3]
            if not self.free(start) or not self.free(goal):return ()
            direct=self.direct(start,goal)
            if direct:return self._remember(key,direct)
            other=route_key+('background' if key[4]=='foreground' else 'foreground',)
            if other in local.searches and key[4]=='background':
                # Advance the existing route while retaining this caller's slice.
                return self._runtime_path(other)
            previous=next((old for old in local.searches if old[4]==key[4]),None)
            # Only another expensive route waits for the current search. A
            # straight combat approach can proceed without finishing that job.
            if previous is not None:self._runtime_path(previous)
            local.searches[key]=local.searches.pop(other,None) or self._new_search(start,goal)
            while len(local.searches)>2:local.searches.popitem(last=False)
        search=local.searches[key];local.searches.move_to_end(key)
        def spend():
            # Start the clock at actual search work, and count this thread's
            # CPU time: waiting for other bots/GIL must not consume its slice.
            if local.deadline is None:local.deadline=time.thread_time()+.006
            if local.remaining<=0 or (local.turn_expanded>=32 and time.thread_time()>=local.deadline):
                local.yields+=1;raise RoutePending()
            local.remaining-=1;local.expansions+=1;local.turn_expanded+=1
        result=search.advance(self,key[2],spend)
        if search.goal==key[0]:result=result[::-1]
        local.finished+=1;local.searches.pop(key,None)
        return self._remember(key,result)

    def _reuse_corridor(self,key):
        """Join a checked long route and check any final leg to a nearby goal."""
        goal_key=(key[1],key[3])
        with self.cache_lock:
            routes=tuple(self.corridors.get(goal_key,()))
            cached=tuple((entry,paths[-1]) for entry,paths in self.corridors.items()) if not routes and math.dist(key[0],key[1])>=50 else ()
        if not self.free(key[0]) or not self.free(key[1]):return ()
        choices=[(route,()) for route in routes]
        nearby=[(cell,route) for (cell,obstacles),route in cached
                if obstacles==key[3] and math.dist(cell,key[1])<=16]
        for cell,route in sorted(nearby,key=lambda row:math.dist(row[0],key[1]))[:4]:
            tail=self.direct(cell,key[1])
            if tail:choices.append((route,tail[1:]))
        if not choices:return ()
        start=self.position(key[0]);candidates={}
        for route,tail in choices:
            for index in range(0,len(route),4):
                point=route[index];dist=math.dist(start,point)
                if dist>1600:continue
                remaining=len(route)-index+len(tail)
                old=candidates.get(point)
                if old is None or remaining<old[1]:candidates[point]=(dist,remaining,index,route,tail)
        for _,_,index,route,tail in sorted(candidates.values(),key=lambda row:row[0])[:16]:
            prefix=self.direct(key[0],self.cell(route[index]))
            if prefix:
                # Joining a corridor may cross its later suffix. Erase the
                # resulting loop, retaining only already checked grid edges.
                result=[];seen={}
                for point in prefix+route[index+1:]+tail:
                    if point in seen:
                        cut=seen[point]
                        for old in result[cut+1:]:seen.pop(old,None)
                        del result[cut+1:]
                    else:seen[point]=len(result);result.append(point)
                return tuple(result)
        return ()

    def _remember(self,key,result):
        with self.cache_lock:
            route_key=key[:4]
            self.completed[route_key]=result;self.completed.move_to_end(route_key)
            while len(self.completed)>512:self.completed.popitem(last=False)
            if len(result)>1:
                goal_key=(key[1],key[3]);routes=self.corridors.setdefault(goal_key,[])
                if not routes or routes[-1]!=result:routes.append(result)
                del routes[:-4]
                self.corridors.move_to_end(goal_key)
                while len(self.corridors)>128:self.corridors.popitem(last=False)
        return result

    @lru_cache(maxsize=256)
    def _path(self,start_cell,goal,limit,blocked=(),lane='foreground'):
        if not self.free(start_cell) or not self.free(goal):return ()
        direct=self.direct(start_cell,goal)
        if direct:return direct
        search=self._new_search(start_cell,goal)
        result=search.advance(self,limit,lambda:None)
        return result[::-1] if search.goal==start_cell else result
