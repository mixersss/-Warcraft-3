"""Check the produced WPM using flood fill, independently of wall generation."""
from collections import deque
from pathlib import Path
import math
import struct

data = (Path(__file__).resolve().parents[1]/'build/map/war3map.wpm').read_bytes()
magic, version, width, height = struct.unpack_from('<4sIII', data)
assert magic == b'MP3W' and version == 0 and (width, height) == (384, 384)
blocked = {n for n, flags in enumerate(data[16:]) if flags & 2}


def cell(x, y):
    return int((y+6144)//32)*width + int((x+6144)//32)


def reached(start, barriers):
    visited = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        x, y = current % width, current // width
        for dx, dy in ((0,1),(1,0),(0,-1),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)):
            nx, ny = x+dx, y+dy
            nxt = ny*width+nx
            if 0 <= nx < width and 0 <= ny < height and nxt not in barriers and nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    return visited


center = cell(0, 0)
accessible = reached(center, blocked)
first = [(-4700,-3600),(-4200,-4700),(-3100,-4200)]
for team, (cx, cy) in enumerate([(-3904,-3904),(3904,-3904),(3904,3904),(-3904,3904)]):
    # Every base and spawn area connects to the arena through its one gate.
    homes = []
    for x,y in first:
        for _ in range(team): x,y=-y,x
        homes.append((x,y))
        for sx,sy in [(x,y),(x-90,y+220),(x,y+220),(x+90,y+220),(x,y-240),(x*0.82,y*0.82)]:
            assert cell(sx,sy) in accessible, ('Unreachable base/spawn/hero/tower',team,sx,sy)
    # Bastion footprint is away from the barracks, spawns, existing towers,
    # heroes and shops. Include a conservative 192x192 footprint in flood fill.
    bastions=[]
    for bx,by in [(-5100,-3900),(-4600,-5100),(-3400,-4600)]:
        for _ in range(team): bx,by=-by,bx
        bastions.append((bx,by))
        for dx in (-96,0,96):
            for dy in (-96,0,96): assert cell(bx+dx,by+dy) in accessible
    obstacles=set(blocked)
    for bx,by in bastions:
        for py in range(height):
            wy=(py+0.5)*32-6144
            if abs(wy-by)>96: continue
            for px in range(width):
                wx=(px+0.5)*32-6144
                if abs(wx-bx)<=96: obstacles.add(py*width+px)
    siege_routes=reached(center,obstacles)
    for x,y in homes:
        for sx,sy in [(x,y),(x-90,y+220),(x,y+220),(x+90,y+220),(x,y-240),(x*0.82,y*0.82)]:
            assert cell(sx,sy) in siege_routes,('Bastion blocks base, spawn, hero or guard tower',team,sx,sy)
    # Closing only a 1800x1800 square around the intended gate must seal
    # that fortress. An extra exit anywhere else would fail this assertion.
    length = math.hypot(cx,cy)
    gx,gy = cx-cx/length*2300, cy-cy/length*2300
    # The 1600-unit corridor has a clear center and solid side walls. Its exit
    # is near the arena, rather than immediately beside the bases.
    for along in range(2400,3801,100):
        half_width=560+(along-2300)*0.4
        for side in (-half_width,0,half_width):
            x=cx-cx/length*along-cy/length*side
            y=cy-cy/length*along+cx/length*side
            assert (cell(x,y) in blocked)==(side!=0), ('Tunnel side/center',team,along,side)
    for along, half_width in [(2400,600),(3800,1160)]:
        for side in range(-int(half_width)+160,int(half_width)-159,64):
            x=cx-cx/length*along-cy/length*side
            y=cy-cy/length*along+cx/length*side
            assert cell(x,y) in accessible, ('Wide gate cross-section blocked',team,along,side)
    for sx,sy in [(-5200+slot*288,-5488) for slot in range(5)]:
        for _ in range(team):sx,sy=-sy,sx
        assert cell(sx,sy) in accessible, ('Fortress shop unreachable',team,sx,sy)
    ex,ey=cx-cx/length*4000,cy-cy/length*4000
    assert cell(ex,ey) in accessible and math.hypot(ex,ey)<2300
    closure = set(blocked)
    for py in range(height):
        wy=(py+0.5)*32-6144
        if abs(wy-gy) > 900: continue
        for px in range(width):
            wx=(px+0.5)*32-6144
            if abs(wx-gx) <= 900: closure.add(py*width+px)
    sealed = reached(cell(*homes[0]), closure)
    assert center not in sealed, ('Fortress has a second exit',team)
    for x,y in homes: assert cell(x,y) in sealed, ('All three bases must share the enclosure',team)
print('PASS: WPM flood fill: 12 bases/spawns connect to arena; closing each single gate seals exactly that team fortress.')

# Removing the central arena must disconnect every team from every other team.
# This proves no route can skirt a radial wall via the outer map edge.
without_center=set(blocked)
for py in range(height):
    wy=(py+0.5)*32-6144
    for px in range(width):
        wx=(px+0.5)*32-6144
        if wx*wx+wy*wy<=1500**2: without_center.add(py*width+px)
for team in range(4):
    x,y=first[0]
    for _ in range(team):x,y=-y,x
    connected=reached(cell(x,y),without_center)
    for other in range(4):
        ox,oy=first[0]
        for _ in range(other):ox,oy=-oy,ox
        assert (cell(ox,oy) in connected)==(other==team),('Route bypasses central arena',team,other)
# Ground and flying pathing share the radial dividers.
for along in range(1550,5800,64):
    for x,y in [(0,along),(0,-along),(along,0),(-along,0)]:
        assert data[16+cell(x,y)]&6==6
print('PASS: Every inter-team path crosses the central arena; no outer ground/flying bypass.')
for team in range(4):
    sx,sy=-3760,-5488
    for _ in range(team):sx,sy=-sy,sx
    for dx in [-96,0,96]:
        for dy in [-96,0,96]:assert cell(sx+dx,sy+dy) in accessible,('Supreme shop access',team)
for sx,sy in [(0,-640),(-160,-640),(160,-640)]:assert cell(sx,sy) in accessible
print('PASS: New supreme shops and central potion shop are reachable.')
for team in range(4):
    for sx,sy in [(-5200+slot*288,-5488) for slot in range(6,9)]:
        for _ in range(team): sx,sy=-sy,sx
        for dx in [-96,0,96]:
            for dy in [-96,0,96]: assert cell(sx+dx,sy+dy) in accessible,('Book shop access',team,sx,sy)
        for hx,hy in first:
            for _ in range(team): hx,hy=-hy,hx
            assert math.hypot(sx-hx,sy-hy)>250,'Book shop must not overlap barracks'
print('PASS: All twelve book-shop sites have clear footprints and connect to their fortress.')

market_obstacles=set(blocked)
markets=[]
for team in range(4):
 for slot in range(10):
  sx,sy=-5200+slot*288,-5488
  for _ in range(team):sx,sy=-sy,sx
  markets.append((sx,sy))
  for py in range(max(0,int((sy+6144-96)//32)),min(height,int((sy+6144+96)//32)+1)):
   for px in range(max(0,int((sx+6144-96)//32)),min(width,int((sx+6144+96)//32)+1)):
    market_obstacles.add(py*width+px)
market_routes=reached(center,market_obstacles)
for team in range(4):
 for slot in range(10):
  sx,sy=-5200+slot*288,-5488+192
  for _ in range(team):sx,sy=-sy,sx
  assert cell(sx,sy) in market_routes,('Shop front blocked',team,slot)
 for hx,hy in first:
  for _ in range(team):hx,hy=-hy,hx
  for n in range(23):
   across=(n%3-1)*90;forward=220+(n//3)*90
   dx,dy=[(across,forward),(-forward,across),(-across,-forward),(forward,-across)][team]
   assert cell(hx+dx,hy+dy) in market_routes,('Expanded wave spawn blocked by market',team,n)
print('PASS: All ten market-row fronts per fortress and all 23 upgraded wave sites per barracks remain connected with conservative shop footprints.')
