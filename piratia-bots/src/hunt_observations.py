"""Shared, local atlas of locations where bots observed earned combat XP."""
import json
import threading
import time

from diagnostic_io import write_snapshot

MAX_CELLS = 2048
INACTIVE_SECONDS = 7 * 86400


class HuntObservations:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.cells = {}
        self.recent_deaths = {}
        self.points_by_map = {}
        self.dirty = False
        self.next_save = 0
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if data.get('version') != 1:
                return
            cutoff = time.time()-INACTIVE_SECONDS
            for name, model, x, y, count, last in data['cells'][:MAX_CELLS]:
                if (isinstance(name, str) and all(type(n) is int for n in (model,x,y,count,last))
                        and 0 < model < 100000 and 0 <= x < 409600 and 0 <= y < 409600
                        and count in (1,2) and last >= cutoff):
                    self.cells[self.key(name,model,(x,y))] = ((x,y),count,last)
        except (OSError, ValueError, TypeError, AttributeError, KeyError):
            pass

    @staticmethod
    def key(name,model,point):
        return name, model, point[0]//1500, point[1]//1500

    def record(self,name,model,point,identity):
        key = self.key(name,model,point)
        proof = name, identity
        with self.lock:
            now = time.monotonic()
            if self.recent_deaths.get(proof,0) > now:
                return
            self.recent_deaths.pop(proof,None)
            self.recent_deaths[proof] = now+20
            if len(self.recent_deaths)>256:
                del self.recent_deaths[next(iter(self.recent_deaths))]
            previous = self.cells.pop(key, None)
            count = min(2,previous[1]+1) if previous else 1
            self.cells[key] = (previous[0] if previous else point,count,int(time.time()))
            if previous and count == 2 and previous[1] == 1:
                self.points_by_map.pop(name,None)
            if len(self.cells)>MAX_CELLS:
                oldest=next(iter(self.cells))
                del self.cells[oldest]
                self.points_by_map.pop(oldest[0],None)
            self.dirty = True

    def points(self,name):
        with self.lock:
            points = self.points_by_map.get(name)
            if points is None:
                index = {}
                for (map_name,model,_,_), (point,count,_) in self.cells.items():
                    if map_name == name and count == 2:
                        index.setdefault(model,[]).append(point)
                points = {model:tuple(locations) for model,locations in index.items()}
                self.points_by_map[name] = points
            return points

    def save(self,now):
        with self.lock:
            if not self.dirty or now < self.next_save:
                return
            self.next_save = now+60
            self.dirty = False
            cells = [[name,model,*point,count,last] for (name,model,_,_), (point,count,last) in self.cells.items()]
        if not write_snapshot(self.path,{'version':1,'cells':cells}):
            with self.lock:
                self.dirty = True
