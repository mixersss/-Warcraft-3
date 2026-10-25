"""Eight pre-encoded full songs; build does not need the original uploaded files."""
from pathlib import Path
import json,hashlib,struct
ROOT=Path(__file__).resolve().parents[1]
def tracks():return json.loads((ROOT/'map/music.json').read_text())['tracks']
def files():
 result={}
 for r in tracks():
  data=(ROOT/r['file']).read_bytes()
  assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
  result[r['path']]=data
 return result
def imports():return struct.pack('<ii',1,len(tracks()))+b''.join(b'\x0d'+r['path'].encode('ascii')+b'\0'for r in tracks())
def runtime():
 data=[]
 for i,r in enumerate(tracks()):data.extend([f'    set FFMusicPath[{i}]='+json.dumps(r['path']),f'    set FFMusicSeconds[{i}]={r["durationMs"]/1000.}'])
 return (ROOT/'map/music.j').read_text().replace('    // PLAYLIST_DATA','\n'.join(data))
