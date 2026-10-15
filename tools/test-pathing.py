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
    # Closing only a 1800x1800 square around the intended gate must seal
    # that fortress. An extra exit anywhere else would fail this assertion.
    length = math.hypot(cx,cy)
    gx,gy = cx-cx/length*2300, cy-cy/length*2300
    # The 900-unit corridor has a clear center and solid side walls. Its exit
    # is near the arena, rather than immediately beside the bases.
    for along in range(2400,3101,100):
        half_width=560+(along-2300)*0.4
        for side in (-half_width,0,half_width):
            x=cx-cx/length*along-cy/length*side
            y=cy-cy/length*along+cx/length*side
            assert (cell(x,y) in blocked)==(side!=0), ('Tunnel side/center',team,along,side)
    for along, half_width in [(2400,600),(3100,880)]:
        for side in range(-int(half_width)+160,int(half_width)-159,64):
            x=cx-cx/length*along-cy/length*side
            y=cy-cy/length*along+cx/length*side
            assert cell(x,y) in accessible, ('Wide gate cross-section blocked',team,along,side)
    for sx,sy in [(-5050,-5100),(-5050,-2450),(-2500,-5000)]:
        for _ in range(team):sx,sy=-sy,sx
        assert cell(sx,sy) in accessible, ('Fortress shop unreachable',team,sx,sy)
    ex,ey=cx-cx/length*3300,cy-cy/length*3300
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
