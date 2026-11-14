"""Spaced dry city pitches around known centres, guards and banks, not one ring."""
import math

def city_pitches(map_name,home,nav,npcs,spawns=(),limit=100):
    rows=list(npcs.by_map.get(map_name,()))
    city=[n for n in rows if math.dist(home,n['position'])<=15000]
    anchors=[tuple(home)]+[tuple(p) for p in spawns]
    anchors.extend(tuple(n['position']) for n in city if 'bank' in n['services'] or 'guard' in n['name'].casefold())
    anchors=list(dict.fromkeys(anchors));result=[]
    # Round-robin anchors keep each zone represented even if the first has ample space.
    for radius in (700,1200,1700,2200,2700,3200,3700,4200):
        for i in range(16):
            angle=math.tau*i/16
            for anchor in anchors:
                raw=(round(anchor[0]+radius*math.cos(angle)),round(anchor[1]+radius*math.sin(angle)))
                point=nav.nearest(raw,2)
                if point is None or math.dist(point,raw)>300:continue
                if nav.combat_allowed(point):continue # City business stays inside known no-fight zones.
                if any(math.dist(point,p)<450 for p in result):continue
                if any(math.dist(point,n['position'])<450 for n in city):continue
                result.append(tuple(point))
                if len(result)>=limit:return result
    return result
