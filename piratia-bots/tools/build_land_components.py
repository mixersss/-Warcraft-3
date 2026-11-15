"""Build-only scipy: fast rejection of disconnected land, without changing masks."""
import base64,hashlib,json,zlib
from pathlib import Path
import numpy as np
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[1]
for path in sorted((ROOT/'assets').glob('*-navigation.json')):
    data=json.loads(path.read_text())
    if 'walkable_zlib' not in data:continue
    name=path.name
    raw=zlib.decompress(base64.b64decode(data['walkable_zlib']));cells=np.frombuffer(raw,np.uint8).reshape(data['height'],data['width'])
    labels,count=label(cells);sizes=np.bincount(labels.ravel());large=np.flatnonzero(sizes>=256);large=large[large!=0]
    width=1 if len(large)<=255 else 2
    if len(large)>65535:raise ValueError('Too many land components')
    table=np.zeros(count+1,dtype=np.uint8 if width==1 else '<u2');table[large]=np.arange(1,len(large)+1)
    packed=table[labels].tobytes();data.update(land_component_labels_zlib=base64.b64encode(zlib.compress(packed,9)).decode(),
        land_component_label_width=width,land_component_source_sha256=hashlib.sha256(raw).hexdigest(),
        land_component_labels_sha256=hashlib.sha256(packed).hexdigest(),land_component_count=len(large))
    path.write_text(json.dumps(data,separators=(',',':'))+'\n')
    print(name,':',len(large),'large components,',width,'bytes/label; existing masks untouched')
