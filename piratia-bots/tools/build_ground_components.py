import sys,json,base64,zlib
from pathlib import Path
import numpy as np
from scipy.ndimage import label
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_world_navigation import project
import argparse
p=argparse.ArgumentParser(description='Add connected-ground and water-safe physical egress masks; build-time numpy/scipy only')
p.add_argument('client_map',type=Path);p.add_argument('server_resource',type=Path);args=p.parse_args()
root=Path(__file__).resolve().parents[1]/'assets';regions=json.loads((root/'regions.json').read_text())
for name,region in regions.items():
 p=root/region['navigation'];data=json.loads(p.read_text());a=np.frombuffer(zlib.decompress(base64.b64decode(data['walkable_zlib'])),np.uint8).reshape(data['height'],data['width'])
 labels,_=label(a);sizes=np.bincount(labels.ravel());main=int(np.argmax(sizes[1:])+1)
 for pos in region['spawns']:
  x,y=pos[0]//100-data['origin'][0],pos[1]//100-data['origin'][1]
  # Spawn hints may themselves be excluded; core is the largest ground component.
  if labels[y,x] and labels[y,x]!=main:raise ValueError('Spawn not in main component')
 _,_,safe=project((args.client_map/(name+'.map')).read_bytes(),
   (args.server_resource/name/(name+'.blk')).read_bytes(),
   (args.server_resource/name/(name+'.atr')).read_bytes(),True,True)
 ox,oy=data['origin'];safe=safe[oy*2:(oy+data['height'])*2,ox*2:(ox+data['width'])*2]
 data['connected_ground_zlib']=base64.b64encode(zlib.compress(np.packbits((labels!=0)&(sizes[labels]>=256)).tobytes(),9)).decode()
 data['recovery50_dry_zlib']=base64.b64encode(zlib.compress(np.packbits(safe).tobytes(),9)).decode()
 data['connected_ground_policy']='cardinal ground components of at least256 cells; recovery respects original collision, native land/bridge and conservative water exclusions'
 p.write_text(json.dumps(data,separators=(',',':'))+'\n')
 print(name,'core',int(sizes[main]),flush=True)
