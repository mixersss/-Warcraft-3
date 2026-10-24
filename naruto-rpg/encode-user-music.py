"""Re-encode uploaded full songs from a supplied directory; build uses the checked-in outputs."""
from pathlib import Path
import argparse,hashlib,json,subprocess
ROOT=Path(__file__).parent
parser=argparse.ArgumentParser();parser.add_argument('--inputs',type=Path,required=True);args=parser.parse_args()
p=ROOT/'src/user-music.json';data=json.loads(p.read_text())
for r in data['tracks']:
 matches=[f for f in args.inputs.rglob(r['originalName'])if f.is_file()and hashlib.sha256(f.read_bytes()).hexdigest()==r['sourceSha256']]
 assert len(matches)==1,r['originalName']
 target=ROOT/r['file'];target.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(matches[0]),'-map','0:a:0','-vn','-sn','-dn','-map_metadata','-1','-ac','1','-ar','22050','-c:a','libmp3lame','-b:a','24k','-write_xing','0','-id3v2_version','0',str(target)],check=True)
 raw=target.read_bytes();probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(target)]))
 r.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),duration_ms=round(float(probe['format']['duration'])*1000))
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
