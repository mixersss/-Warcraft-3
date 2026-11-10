"""Self-contained browser fighting game: embed source, CSS and13 full MP3s."""
from pathlib import Path
import re,json,base64,hashlib,zipfile
ROOT=Path(__file__).parent;OUT=ROOT.parent/'releases/shinobi-fighter';OUT.mkdir(parents=True,exist_ok=True)
code='\n'.join(re.sub(r'^export ','',re.sub(r'^import .*?;\n','',(ROOT/'src'/n).read_text(),flags=re.M),flags=re.M) for n in ['roster.js','appearance.js','voice-cues.js','voices.js','techniques.js','combat.js','vfx.js','art.js','app.js'])
tracks=[]
for t in json.loads((ROOT/'assets/music/playlist.json').read_text()):tracks.append({'name':t['name'],'file':'data:audio/mpeg;base64,'+base64.b64encode((ROOT/t['file']).read_bytes()).decode()})
code,n=re.subn(r"fetch\('assets/music/playlist.json'\)[^\n]*;",lambda _: 'playlist='+json.dumps(tracks,ensure_ascii=False,separators=(',',':'))+';',code,count=1);assert n==1
voice_manifest=json.loads((ROOT/'assets/voices/manifest.json').read_text())
for voice in voice_manifest:
 data=(ROOT/voice['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==voice['sha256']
 code=code.replace(voice['file'],'data:audio/mpeg;base64,'+base64.b64encode(data).decode())
html=(ROOT/'index.html').read_text().replace('<link rel="stylesheet" href="style.css">','<style>'+(ROOT/'style.css').read_text()+'</style>').replace('<script type="module" src="src/app.js"></script>','<script type="module">'+code.replace('</script','<\\/script')+'</script>')
assert 'fetch(' not in html and 'import {' not in html
p=OUT/'Shinobi-Clash-Alpha03.html';p.write_text(html)
with zipfile.ZipFile(OUT/'Shinobi-Clash-Alpha03.zip','w',zipfile.ZIP_DEFLATED) as z:
 z.write(p,p.name);z.writestr('Как играть.txt','Распакуй архив и открой Shinobi-Clash-Alpha03.html в Chrome или Edge.\nСтрелки — ходьба, Пробел — прыжок, Shift — рывок, A — рука, D — нога, ↓ — присесть, U — сильный, I — фирменная атака, L — блок.\nQ/W/E/R — техники только по перезарядке, без маны и шкалы ульты. P — пауза.\n16 бойцов и13 полных музыкальных треков находятся внутри файла.\n')
report={'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'fighters':16,'techniques':64,'musicTracks':13,'sourceVoiceClips':len(voice_manifest),'voiceSkillBindings':64,'punchKey':'A','kickKey':'D','crouchKey':'ArrowDown','standaloneHTML':True,'engine':'independent Canvas2D fighter','roundsToWin':2,'networkMultiplayer':False,'originalWarcraftModelsUsed':False,'sourceSkillAdaptation':True,'manaRemoved':True,'allFourSkillsCooldownOnly':True,'cloneLifetimeSeconds':6,'summonsHaveHPAndCanBeKilled':True,'voiceVolume':0.65,'referenceOutfitPass':16}
(OUT/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
