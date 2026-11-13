"""Read-only inspection of the supplied classic three-byte ATR grid.

Report raw attributes/regions, without guessing a land/sea bit or editing a map.
"""
import argparse
import hashlib
import json
import mmap
import struct
from collections import Counter
from pathlib import Path


def attr_crop(path,bounds):
    with Path(path).open('rb') as source:
        header=source.read(8)
        if len(header)!=8:raise ValueError('Incomplete ATR header')
        width,height=struct.unpack('<II',header)
        if not (1<=width<=4096 and 1<=height<=4096):raise ValueError('Unsupported ATR dimensions')
        source.seek(0,2)
        if source.tell()!=8+width*height*3:raise ValueError('Expected classic three-byte ATR cells')
        x0,y0,x1,y1=bounds
        if not (0<=x0<x1<=width and 0<=y0<y1<=height):raise ValueError('Crop outside ATR grid')
        counts=Counter()
        with mmap.mmap(source.fileno(),0,access=mmap.ACCESS_READ) as data:
            for y in range(y0,y1):
                for x in range(x0,x1):
                    counts[struct.unpack_from('<HB',data,8+3*(y*width+x))]+=1
        source.seek(0);digest=hashlib.sha256()
        for chunk in iter(lambda:source.read(1048576),b''):digest.update(chunk)
    return {'width':width,'height':height,'bounds':list(bounds),'sha256':digest.hexdigest(),
            'raw_attribute_region_counts':[{'attribute_word':a,'region_byte':r,'tiles':n}
                                            for (a,r),n in sorted(counts.items())],
            'land_sea_semantics_inferred':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('atr',type=Path)
    parser.add_argument('--bounds',nargs=4,type=int,default=[2018,2534,2059,2585])
    args=parser.parse_args()
    print(json.dumps(attr_crop(args.atr,args.bounds),indent=2))


if __name__=='__main__':main()
