"""Derive ground navigation from private client .map and server .blk files.

Build-time numpy only. Outputs numeric grids/audit; never copies original assets.
Format: MPMapDef.h SNewFileTile (780627), MPTile.h, CompCommand.h.
"""
import argparse
import base64
import hashlib
import json
import struct
import zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HEADER=struct.Struct('<5I')
TILE=struct.Struct('<IBhbHB4B')
LAND=1
BRIDGE=8


class MapFile:
    def __init__(self,raw):
        if len(raw)<HEADER.size:raise ValueError('Incomplete map header')
        flag,self.width,self.height,self.sx,self.sy=HEADER.unpack_from(raw)
        if flag!=780627:raise ValueError('Unsupported map version')
        if not (1<=self.width<=4096 and 1<=self.height<=4096 and
                1<=self.sx<=64 and 1<=self.sy<=64 and
                self.width%self.sx==0 and self.height%self.sy==0):
            raise ValueError('Invalid map dimensions')
        count=(self.width//self.sx)*(self.height//self.sy)
        first=HEADER.size+4*count
        if len(raw)<first:raise ValueError('Incomplete section table')
        self.offsets=struct.unpack_from('<'+str(count)+'I',raw,HEADER.size)
        size=self.sx*self.sy*TILE.size
        ranges=sorted((off,off+size) for off in self.offsets if off)
        if any(a<first or b>len(raw) for a,b in ranges):raise ValueError('Section outside map')
        if any(a[1]>b[0] for a,b in zip(ranges,ranges[1:])):raise ValueError('Overlapping map sections')
        self.raw=raw

    def tile(self,x,y):
        if not (0<=x<self.width and 0<=y<self.height):raise ValueError('Tile outside map')
        off=self.offsets[(y//self.sy)*(self.width//self.sx)+x//self.sx]
        if not off:return None
        values=TILE.unpack_from(self.raw,off+TILE.size*((y%self.sy)*self.sx+x%self.sx))
        return {'height_cm':values[3]*10,'region':values[4],'blocks':values[6:]}


def project(map_file,block_raw,attr_raw=None):
    import numpy as np
    m=MapFile(map_file);w,h=m.width,m.height
    height=np.zeros((h,w),dtype=np.int16);region=np.zeros((h,w),dtype=np.uint16)
    client=np.ones((h*2,w*2),dtype=bool);valid=np.zeros((h,w),dtype=bool)
    for i,off in enumerate(m.offsets):
        if not off:continue
        x=i%(w//m.sx)*m.sx;y=i//(w//m.sx)*m.sy
        data=np.frombuffer(m.raw,dtype=np.uint8,count=m.sx*m.sy*15,offset=off).reshape(m.sy,m.sx,15)
        height[y:y+m.sy,x:x+m.sx]=data[:,:,7].view(np.int8).astype(np.int16)*10
        region[y:y+m.sy,x:x+m.sx]=data[:,:,8].astype(np.uint16)+(data[:,:,9].astype(np.uint16)<<8)
        valid[y:y+m.sy,x:x+m.sx]=True
        for n,(dx,dy) in enumerate(((0,0),(1,0),(0,1),(1,1))):
            client[y*2+dy:(y+m.sy)*2+dy:2,x*2+dx:(x+m.sx)*2+dx:2]=(data[:,:,11+n]&128)!=0
    if len(block_raw)<8:raise ValueError('Incomplete server block header')
    bw,bh=struct.unpack_from('<II',block_raw)
    if not (bw%8==0 and bw>=w*2 and bh>=h*2 and bw<=8192 and bh<=8192 and len(block_raw)==8+bw*bh//8):
        raise ValueError('Invalid server block dimensions/length')
    server=np.unpackbits(np.frombuffer(block_raw,dtype=np.uint8,offset=8)).reshape(bh,bw)[:h*2,:w*2].astype(bool)
    server_region=region
    attr_differences=ground_differences=0
    if attr_raw is not None:
        if len(attr_raw)<8:raise ValueError('Incomplete server attribute header')
        aw,ah=struct.unpack_from('<II',attr_raw)
        if not (w<=aw<=4096 and h<=ah<=4096 and len(attr_raw)==8+aw*ah*3):
            raise ValueError('Invalid server attribute dimensions/length')
        attrs=np.frombuffer(attr_raw,dtype=np.uint8,offset=8).reshape(ah,aw,3)[:h,:w]
        server_region=attrs[:,:,0].astype(np.uint16)+(attrs[:,:,1].astype(np.uint16)<<8)
        attr_differences=int(((server_region!=region)&valid).sum())
        ground_differences=int(((((server_region&(LAND|BRIDGE))!=0)!=((region&(LAND|BRIDGE))!=0))&valid).sum())
    # Underwater terrain vertices are excluded conservatively up to the shore.
    # Bridges use their explicit native region bit, not guessed model names.
    wet=height<0
    water=wet.copy()
    water[:-1,:]|=wet[1:,:];water[:,:-1]|=wet[:,1:];water[:-1,:-1]|=wet[1:,1:]
    water&=((region&BRIDGE)==0)|((server_region&BRIDGE)==0)
    forbidden=~valid|((region&(LAND|BRIDGE))==0)|((server_region&(LAND|BRIDGE))==0)|water
    blocked=client|server|np.repeat(np.repeat(forbidden,2,axis=0),2,axis=1)
    padded=np.pad(blocked,1,constant_values=True)
    clear=np.ones((h,w),dtype=bool)
    # A cell's centre is the odd 50cm index. Retain the established 3x3 clearance.
    for dy in (-1,0,1):
        for dx in (-1,0,1):clear&=~padded[2+dy:2*h+dy+1:2,2+dx:2*w+dx+1:2]
    audit={'width':w,'height':h,'present_tiles':int(valid.sum()),
           'underwater_vertices':int((wet&valid).sum()),'water_excluded_tiles':int((water&valid).sum()),
           'bridge_tiles':int(((region&BRIDGE)!=0).sum()),
           'server_attributes_checked':attr_raw is not None,
           'client_server_region_differences':attr_differences,
           'client_server_ground_eligibility_differences':ground_differences,
           'block_comparison_scope':'present client sections only',
           'client_server_block_differences_50cm':int(((client!=server)&np.repeat(np.repeat(valid,2,axis=0),2,axis=1)).sum()),
           'walkable_tiles':int(clear.sum()),'client_map_sha256':hashlib.sha256(map_file).hexdigest(),
           'server_block_sha256':hashlib.sha256(block_raw).hexdigest()}
    if attr_raw is not None:audit['server_attribute_sha256']=hashlib.sha256(attr_raw).hexdigest()
    return clear.astype(np.uint8),audit


def encode(name,cells,waypoints=(),origin=(0,0)):
    return {'map':name,'origin':list(origin),'width':cells.shape[1],'height':cells.shape[0],'cell_cm':100,
            'geometry_revision':'alpha38-client-ground-v1',
            'source':'client 780627 .map collision + server .blk + native land/bridge flags; conservative underwater terrain exclusion; 3x3 50cm clearance',
            'walkable_zlib':base64.b64encode(zlib.compress(cells.tobytes(),9)).decode(),'waypoints':list(waypoints)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('client_map',type=Path);p.add_argument('server_resource',type=Path)
    args=p.parse_args();catalog={'maps':{},'client_only_maps':[],'native_windows_verified':False,
        'water_policy':'exclude tiles touching negative terrain vertices except explicit bridge regions; conservative shore clearance',
        'format_sources':[
          'https://github.com/mothannakhzaleh/TalesOfPirateDX9/blob/main/sources/Libraries/Util/include/MPMapDef.h',
          'https://github.com/mothannakhzaleh/TalesOfPirateDX9/blob/main/sources/Engine/include/MPTile.h',
          'https://github.com/mothannakhzaleh/TalesOfPirateDX9/blob/main/sources/Libraries/common/include/CompCommand.h']}
    for path in sorted(args.client_map.glob('*.map')):
        name=path.stem;server=args.server_resource/name/(name+'.blk')
        if not server.exists():catalog['client_only_maps'].append(name);continue
        attributes=args.server_resource/name/(name+'.atr')
        if not attributes.exists():raise ValueError('Server attributes missing: '+name)
        cells,audit=project(path.read_bytes(),server.read_bytes(),attributes.read_bytes())
        target=ROOT/'assets'/(name+'-navigation.json')
        old=json.loads(target.read_text()) if target.exists() else {}
        waypoints=[]
        for point in old.get('waypoints',[]):
            x,y=point[0]//100,point[1]//100
            if 0<=x<cells.shape[1] and 0<=y<cells.shape[0] and cells[y,x]:waypoints.append(point)
        target.write_text(json.dumps(encode(name,cells,waypoints),separators=(',',':'))+'\n')
        if name=='garner':
            crop=cells[2400:2900,1900:2450]
            argent=ROOT/'assets/argent-navigation.json';previous=json.loads(argent.read_text())
            points=[q for q in previous['waypoints'] if crop[q[1]//100-2400,q[0]//100-1900]]
            argent.write_text(json.dumps(encode(name,crop,points,(1900,2400)),separators=(',',':'))+'\n')
        audit['navigation']=target.name;catalog['maps'][name]=audit
        print(name,audit['walkable_tiles'],'walkable;',audit['water_excluded_tiles'],'water exclusions',flush=True)
    (ROOT/'assets/world-navigation.json').write_text(json.dumps(catalog,indent=2)+'\n')


if __name__=='__main__':main()
