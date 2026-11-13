"""Bounded A* over a derived walkability crop from the owner's garner.blk."""
import base64
import heapq
import threading
import time
from collections import OrderedDict
from route_search import Search,RoutePending
from functools import lru_cache
import json
import math
import zlib
from pathlib import Path


class Navigation:
    def __init__(self, path):
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        self.local = threading.local()
        self.map = data.get('map','garner')
        self.origin = tuple(data['origin'])
        self.width, self.height = data['width'], data['height']
        if not 1 <= self.width <= 4096 or not 1 <= self.height <= 4096:
            raise ValueError('Invalid navigation crop size')
        self.cells = zlib.decompress(base64.b64decode(data['walkable_zlib']))
        if len(self.cells) != self.width * self.height:
            raise ValueError('Incomplete navigation crop')
        self.waypoints = [tuple(p) for p in data['waypoints']]

    def cell(self, position):
        return position[0] // 100 - self.origin[0], position[1] // 100 - self.origin[1]

    def position(self, cell):
        return (cell[0] + self.origin[0]) * 100 + 50, (cell[1] + self.origin[1]) * 100 + 50

    def free(self, cell):
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height and self.cells[y*self.width+x] == 1 and cell not in getattr(getattr(self,'local',None),'blocked_cells',())

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

    def path(self, start, end, limit=25000):
        key=(self.cell(start),self.cell(end),limit,tuple(sorted(getattr(getattr(self,'local',None),'blocked_cells',()))))
        cached = self._runtime_path(key) if getattr(self,'incremental',False) and getattr(self.local,'active',False) else self._path(*key)
        result = list(cached)
        if result:
            result[0] = tuple(start)
        return result

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

    def enable_incremental(self):
        self.incremental=True;self.local=threading.local()
        self.completed=OrderedDict();self.cache_lock=threading.Lock()

    def begin_turn(self,expansions=512):
        local=self.local
        if not hasattr(local,'searches'):
            local.searches=OrderedDict();local.yields=local.expansions=local.finished=0
        local.remaining=expansions;local.turn_expanded=0;local.deadline=None;local.active=True

    def end_turn(self):self.local.active=False

    def cancel_pending(self):
        if getattr(self,'incremental',False) and hasattr(self.local,'searches'):self.local.searches.clear()

    def planning_stats(self):
        if not getattr(self,'incremental',False):return {}
        l=self.local
        return {'yields':getattr(l,'yields',0),'expanded_nodes':getattr(l,'expansions',0),
                'completed_searches':getattr(l,'finished',0),'pending_searches':len(getattr(l,'searches',{}))}

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

    def _runtime_path(self,key):
        with self.cache_lock:
            if key in self.completed:
                self.completed.move_to_end(key);return self.completed[key]
        local=self.local
        if key not in local.searches and local.searches:
            # Finish the existing bounded job before accepting a changed goal.
            # Random candidate ties must not discard half-built searches forever.
            self._runtime_path(next(iter(local.searches)))
        if key not in local.searches:
            start,goal,limit=key[:3]
            if not self.free(start) or not self.free(goal):return ()
            direct=self.direct(start,goal)
            if direct:return self._remember(key,direct)
            local.searches[key]=Search(start,goal)
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
        local.finished+=1;local.searches.pop(key,None)
        return self._remember(key,result)

    def _remember(self,key,result):
        with self.cache_lock:
            self.completed[key]=result;self.completed.move_to_end(key)
            while len(self.completed)>512:self.completed.popitem(last=False)
        return result

    @lru_cache(maxsize=256)
    def _path(self,start_cell,goal,limit,blocked=()):
        if not self.free(start_cell) or not self.free(goal):return ()
        return self.direct(start_cell,goal) or Search(start_cell,goal).advance(self,limit,lambda:None)
