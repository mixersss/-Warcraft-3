"""Read-only full monster knowledge; spawn regions are not live monster positions."""
import json
import math
from functools import lru_cache
from pathlib import Path


class MobKnowledge:
    def __init__(self,path,local_spawns=None):
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        self.monsters={int(k):v for k,v in data['monsters'].items()}
        known = {
            (area['map'], model, tuple(area['rectangle_cm'][0]), tuple(area['rectangle_cm'][1])): area
            for model, record in self.monsters.items() for area in record['locations']
        }
        for overlay in (Path(path).with_name('startup-spawns.json'), local_spawns):
            if overlay is not None:
                self.add_spawns(overlay, known)
        self.by_map={}
        for model,record in self.monsters.items():
            for location in record['locations']:
                self.by_map.setdefault(location['map'],{}).setdefault(model,[]).append(location)

    def add_spawns(self, path, known):
        try:
            data = json.loads(Path(path).read_text(encoding='utf-8'))
            if data.get('version') != 1 or not isinstance(data.get('maps'), dict):
                return
        except (OSError, ValueError, AttributeError):
            return
        for name, rows in data['maps'].items():
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, list) or len(row) != 8:
                    continue
                model,x,y,x2,y2,count,delay,kind = row
                if (not all(type(n) is int for n in row[:7]) or model not in self.monsters
                        or kind not in ('startup', 'table') or count<=0
                        or not (0<=x<=x2<409600 and 0<=y<=y2<409600)):
                    continue
                key = name, model, (x,y), (x2,y2)
                area = dict(map=name, rectangle_cm=[[x,y],[x2,y2]], count=count, respawn_seconds=delay,
                            source_kind='map_startup' if kind=='startup' else 'server_spawn_table')
                previous = known.get(key)
                if previous is None:
                    known[key] = area
                    self.monsters[model]['locations'].append(area)
                elif previous.get('conditions_not_evaluated'):
                    previous.clear()
                    previous.update(area)

    def get(self,model):return self.monsters.get(model)

    @lru_cache(maxsize=512)
    def nearby_ground(self,map_name,point):
        rows=[]
        for model,locations in self.by_map.get(map_name,{}).items():
            if self.monsters[model].get('territory')!=0:continue
            distances=[]
            for area in locations:
                if area.get('conditions_not_evaluated'):continue
                lo,hi=area['rectangle_cm'];near=(max(lo[0],min(hi[0],point[0])),max(lo[1],min(hi[1],point[1])))
                distance=math.dist(point,near)
                if distance<=25000:distances.append(distance)
            if distances:rows.append((model,min(distances)))
        return tuple(rows)

    def nearest(self,model,map_name,position):
        best=None
        for location in self.by_map.get(map_name,{}).get(model,[]):
            lo,hi=location['rectangle_cm']
            point=(max(lo[0],min(hi[0],position[0])),max(lo[1],min(hi[1],position[1])))
            distance=math.dist(position,point)
            if best is None or distance<best['straight_line_cm']:
                best={'map':map_name,'rectangle_cm':location['rectangle_cm'],
                      'nearest_region_point':point,'straight_line_cm':round(distance),
                      'conditions_not_evaluated':location.get('conditions_not_evaluated',False)}
        return best

    def summary(self,map_name,position,level):
        rows=[]
        for model in self.by_map.get(map_name,{}):
            record=self.monsters[model]
            if not max(1,level-9)<=record['level']<=level+3:continue
            nearest=self.nearest(model,map_name,position)
            if nearest:rows.append(dict(model=model,name=record['name'],level=record['level'],
                                        territory=record['territory'],**nearest))
        rows.sort(key=lambda r:r['straight_line_cm'])
        return {'known_monster_types':len(self.monsters),'known_spawn_maps':len(self.by_map),
                'types_with_located_source_spawns':sum(bool(r['locations']) for r in self.monsters.values()),
                'nearby_spawn_regions':rows[:5],'spawn_regions_are_not_live_targets':True}
