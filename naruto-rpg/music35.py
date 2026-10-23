"""Exact music bytes from the user's3.5 source, overlaid without changing older model/voice assets."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).parent

def catalog():return json.loads((ROOT/'src/music35-source.json').read_text())['tracks']+json.loads((ROOT/'src/extra35-assets.json').read_text())
def effective_manifest(original):
 overrides={r['path'].lower():r for r in catalog()}
 oldpaths={r['path'].lower()for r in original}
 return [dict(r,bytes=overrides[r['path'].lower()]['bytes'],sha256=overrides[r['path'].lower()]['sha256'])if r['path'].lower()in overrides else r for r in original]+[r for r in catalog()if r['path'].lower()not in oldpaths]
def files():
 result={}
 for r in catalog():
  data=(ROOT/r['file']).read_bytes();assert len(data)==r['bytes']and hashlib.sha256(data).hexdigest()==r['sha256'],r['path'];result[r['path']]=data
 return result
