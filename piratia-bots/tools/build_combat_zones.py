"""Add numerical native no-fight masks without changing walking/recovery geometry."""
import argparse
import base64
import hashlib
import json
import struct
import zlib
from pathlib import Path
from build_world_navigation import MapFile
ROOT=Path(__file__).resolve().parents[1]
REVISION='alpha40-native-no-fight-v1'


def attach(path,mask):
    import numpy as np
    data=json.loads(path.read_text())
    if mask.shape!=(data['height'],data['width']):raise ValueError('Combat mask dimensions do not match navigation')
    data['combat_no_fight_zlib']=base64.b64encode(zlib.compress(np.packbits(mask).tobytes(),9)).decode()
    data['combat_zone_revision']=REVISION
    path.write_text(json.dumps(data,separators=(',',':'))+'\n')


def build(client_maps,resource):
    import numpy as np
    catalog_path=ROOT/'assets/world-navigation.json';catalog=json.loads(catalog_path.read_text())
    regions_path=ROOT/'assets/regions.json';regions=json.loads(regions_path.read_text())
    for name,info in catalog['maps'].items():
        m=MapFile((client_maps/(name+'.map')).read_bytes())
        raw=(resource/name/(name+'.atr')).read_bytes();aw,ah=struct.unpack_from('<II',raw)
        if not (m.width<=aw<=4096 and m.height<=ah<=4096 and len(raw)==8+3*aw*ah):raise ValueError('Invalid server ATR')
        attrs=np.frombuffer(raw,dtype=np.uint8,offset=8).reshape(ah,aw,3)
        # Unloaded client sections stay unknown and cannot be chosen for combat.
        mask=np.ones((m.height,m.width),dtype=bool)
        for i,off in enumerate(m.offsets):
            if not off:continue
            x=i%(m.width//m.sx)*m.sx;y=i//(m.width//m.sx)*m.sy
            tiles=np.frombuffer(m.raw,dtype=np.uint8,count=m.sx*m.sy*15,offset=off).reshape(m.sy,m.sx,15)
            mask[y:y+m.sy,x:x+m.sx]=((tiles[:,:,8]&2)!=0)|((attrs[y:y+m.sy,x:x+m.sx,0]&2)!=0)
        attach(ROOT/'assets'/info['navigation'],mask)
        if name in regions:
            for record in regions[name]['farms'].values():
                record['points']=[p for p in record['points']
                                  if 0<=p[0]//100<m.width and 0<=p[1]//100<m.height
                                  and not mask[p[1]//100,p[0]//100]]
            info['farm_points_filtered_for_combat']=True
        if name=='garner':attach(ROOT/'assets/argent-navigation.json',mask[2400:2900,1900:2450])
        info['combat_forbidden_or_unknown_tiles']=int(mask.sum())
        info['combat_attribute_sha256']=hashlib.sha256(raw).hexdigest()
        print(name,int(mask.sum()),'no-fight/unknown tiles',flush=True)
    catalog['combat_zone_revision']=REVISION
    catalog['combat_policy']='native NOT_FIGHT bit0x0002 from client and server; independent from walkability'
    catalog['alpha40_combat_farm_points']={k:sum(len(x['points']) for x in v['farms'].values()) for k,v in regions.items()}
    regions_path.write_text(json.dumps(regions,ensure_ascii=False,separators=(',',':'))+'\n')
    catalog_path.write_text(json.dumps(catalog,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('client_maps',type=Path);p.add_argument('resource',type=Path)
    args=p.parse_args();build(args.client_maps,args.resource)
