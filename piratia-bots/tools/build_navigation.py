"""Derive the numerical Argent walkability crop from the owner's garner.blk."""
import argparse
import base64
import json
import struct
import zlib
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('block_file',type=Path)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    raw = args.block_file.read_bytes()
    width,height = struct.unpack_from('<II',raw)
    if (width,height)!=(8192,8192) or len(raw)!=8+width*height//8:
        parser.error('Expected the supplied 8192x8192 classic garner.blk')
    ox,oy,w,h = 1900,2400,550,500

    def blocked(x,y):
        return bool(raw[8+y*(width//8)+x//8] & (1 << (7-x%8)))

    cells = bytearray()
    for y in range(oy,oy+h):
        for x in range(ox,ox+w):
            # Paths use 100cm cell centres (+50cm), i.e. odd 50cm-grid indices.
            cells.append(int(not any(blocked(x*2+1+dx,y*2+1+dy)
                                     for dx in (-1,0,1) for dy in (-1,0,1))))

    def nearest(x,y):
        points = ((x+dx,y+dy) for dx in range(-12,13) for dy in range(-12,13))
        for a,b in sorted(points,key=lambda p:(p[0]-x)**2+(p[1]-y)**2):
            if ox<=a<ox+w and oy<=b<oy+h and cells[(b-oy)*w+a-ox]:
                return [a*100+50,b*100+50]
        raise ValueError('No clear waypoint')

    data = {'map':'garner','origin':[ox,oy],'width':w,'height':h,'cell_cm':100,
            'source':'derived from supplied garner.blk; 3x3 50cm clearance samples',
            'walkable_zlib':base64.b64encode(zlib.compress(cells,9)).decode(),
            'waypoints':[nearest(x,y) for x,y in ((2140,2740),(2130,2690),(2190,2640),(2240,2640))]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,separators=(',',':')))
    print('Derived numerical navigation crop only; no original map assets copied.')


if __name__=='__main__':
    main()
