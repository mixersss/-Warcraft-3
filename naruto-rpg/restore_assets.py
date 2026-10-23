"""Restore original imports from a checked-in release, verifying every SHA-256."""
from pathlib import Path
import argparse,json,hashlib
from mpq_tools import StormArchive
ROOT=Path(__file__).parent
parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path);parser.add_argument('--output',type=Path,default=ROOT/'assets');args=parser.parse_args()
manifest=json.loads((ROOT/'src/asset-manifest.json').read_text())
def valid(row):
 p=args.output/row['path'].replace('\\','/')
 return p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
missing=[r for r in manifest if not valid(r)]
if missing:
 report=Path('/workspace/-Warcraft-3/releases/shinobi-new/build-report.json');release=report.parent
 name=json.loads(report.read_text())['filename'] if report.exists() else ''
 candidates=[args.archive] if args.archive else [release/'Shinobi_Story_Alpha_25.w3x',release/name,release/'Shinobi_Skills_Alpha_05a.w3x']
 archive=next((p for p in candidates if p and p.is_file()),None)
 assert archive,'No release archive available; supply --archive PATH'
 source=StormArchive(archive)
 try:
  for row in missing:
   data=source.read(row['path']);assert hashlib.sha256(data).hexdigest()==row['sha256'],row['path']
   target=args.output/row['path'].replace('\\','/');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 finally:source.close()
assert all(valid(r) for r in manifest)
print(f'Verified {len(manifest)} original assets; restored {len(missing)}')
