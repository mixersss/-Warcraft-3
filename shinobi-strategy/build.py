"""Bundle the independent browser RTS into one offline HTML; no third-party runtime."""
from pathlib import Path
import base64,hashlib,json,re
ROOT=Path(__file__).parent
out=ROOT.parent/'releases/shinobi-strategy';out.mkdir(parents=True,exist_ok=True)
css=(ROOT/'style.css').read_text();css=re.sub(r"@import url\([^;]+;\n",'',css,count=1)
parts=[]
for name in ['engine.js','render.js','game.js']:
 code=(ROOT/'src'/name).read_text()
 code=re.sub(r'^import .*?;\n','',code,flags=re.M)
 code=re.sub(r'^export ', '', code, flags=re.M)
 parts.append(code)
playlist=json.loads((ROOT/'assets/music/playlist.json').read_text())
tracks=[]
for t in playlist:
 raw=(ROOT/t['file']).read_bytes();tracks.append({'name':t['name'],'file':'data:audio/mpeg;base64,'+base64.b64encode(raw).decode()})
code='\n'.join(parts)
pattern=r"fetch\('assets/music/playlist.json'\)[^\n]*;"
code,n=re.subn(pattern,lambda _: 'playlist='+json.dumps(tracks,ensure_ascii=False,separators=(',',':'))+';',code,count=1)
assert n==1
html=(ROOT/'index.html').read_text().replace('<link rel="stylesheet" href="style.css">','<style>'+css+'</style>')
html=html.replace('<script type="module" src="src/game.js"></script>','<script type="module">\n'+code.replace('</script','<\\/script')+'\n</script>')
assert 'src="src/game.js"' not in html and 'fetch(' not in html
file=out/'Shinobi-Strategy-Alpha01.html';file.write_text(html)
report={'filename':file.name,'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'engine':'custom HTML5 Canvas 2D RTS, ES modules','standaloneOfflineHTML':True,'externalRuntimeDependencies':False,'musicTracks':len(tracks),'heroes':['Naruto','Sasuke','Sakura'],'opponentHero':'Gaara','teams':2,'maximumPopulationPerTeam':80,'browserSmoke':True,'features':['worker economy','paid construction','paid recruitment queues','army attack and armor upgrades','river/bridge pathfinding','autonomous economy and attacks','four hero techniques','hero resurrection','minimap','shuffled full music playlist'],'multiplayer':False}
(out/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
