"""Read-only full monster knowledge; spawn regions are not live monster positions."""
import json
import math
from functools import lru_cache
from pathlib import Path


class MobKnowledge:
    def __init__(self,path):
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        self.monsters={int(k):v for k,v in data['monsters'].items()}
        self.by_map={}
        for model,record in self.monsters.items():
            for location in record['locations']:
                self.by_map.setdefault(location['map'],{}).setdefault(model,[]).append(location)

    def get(self,model):return self.monsters.get(model)

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
