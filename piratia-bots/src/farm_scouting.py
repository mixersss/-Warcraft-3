"""Dry camp points from exact server placements and source spawn rectangles."""
import math

def scout_points(nav,locations,fallback,limit=96):
    points=list(dict.fromkeys(tuple(p) for p in fallback));extra=[];fixed=[]
    allowed=getattr(nav,'combat_allowed',lambda p:True)
    for area in locations:
        if area.get('conditions_not_evaluated'):continue
        lo,hi=area['rectangle_cm']
        if lo == hi:
            point=tuple(lo)
            if allowed(point) and (nav.land_component(point) if hasattr(nav,'land_component') else nav.nearest(point,0)):
                fixed.append(point)
            continue
        width,height=hi[0]-lo[0],hi[1]-lo[1]
        if width<0 or height<0:continue
        # At most~96 candidates per area, close enough for native eyesight.
        step=max(1200,int(math.ceil(math.sqrt(max(1,width*height)/80)/100))*100)
        xs=list(range(lo[0]+100,hi[0],step)) or [(lo[0]+hi[0])//2]
        ys=list(range(lo[1]+100,hi[1],step)) or [(lo[1]+hi[1])//2]
        for x in xs:
            for y in ys:
                q=nav.nearest((x,y),2)
                if (q and lo[0]<=q[0]<=hi[0] and lo[1]<=q[1]<=hi[1]
                        and allowed(q) and (not hasattr(nav,'land_component') or nav.land_component(q))):
                    extra.append(tuple(q))
    extra=list(dict.fromkeys(extra))
    if len(extra)>limit:
        extra=[extra[int(i*len(extra)/limit)] for i in range(limit)]
    return list(dict.fromkeys(fixed+points+extra))
