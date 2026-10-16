"""Fresh 1.26 foundation: new metadata/script/objects; original models/audio only."""
from pathlib import Path
import json,math,struct,hashlib
from skills import SKILLS,HERO_SKILLS,ability_data,summon_units
from classic_formats import i,f,s,objects,archive
ROOT=Path(__file__).parent;SIZE=96;HALF=6144;BOUND=5888
HEROES=json.loads((ROOT/'src/heroes.json').read_text());ASSETS=json.loads((ROOT/'src/asset-manifest.json').read_text());AUDIO=json.loads((ROOT/'src/all-original-audio.json').read_text())
BASE=[(-3900,-3900),(3900,-3900),(3900,3900),(-3900,3900)]
NAME='SHINOBI SKILLS ALPHA 05'
DESC='Новая основа RPG для Warcraft III 1.26. Четыре команды по три героя. Первые 10 техник Наруто и Саске: клоны, призывы, формы и боевые навыки. Тренировочная альфа; сюжет пока не подключён.'
def positions():return [(BASE[p//3][0]+(p%3-1)*250,BASE[p//3][1]) for p in range(12)]
def info():
 d=i(25,1,6061)+s(NAME)+s('mixersss; imported assets from ShikamaruShadow map')+s(DESC)+s('1-12; 4 teams x 3')
 d+=f(-BOUND,-BOUND,BOUND,BOUND,-BOUND,BOUND,BOUND,-BOUND)+i(2,2,2,2,SIZE-4,SIZE-4,0x60)+b'L'
 d+=i(-1)+s('')+s(DESC)+s(NAME)+s('Resource and animation test')
 d+=i(2)+s('')+s('')+s('')+s('')+i(0)+f(3000,5000,.5)+bytes([0,0,0,255])+i(0)+s('Default')+b'L'+bytes([255]*4)
 d+=i(12)
 for p,(x,y) in enumerate(positions()):d+=i(p,1,1,1)+s(HEROES[p]['name'])+f(x,y)+i(0,7<<(p//3*3))
 d+=i(4)
 for t in range(4):d+=i(11,7<<(t*3))+s(f'Отряд {t+1}')
 return d+i(0,0,0,0)
def texture(x,y):
 if any((x-a)**2+(y-b)**2<1100**2 for a,b in BASE):return 3
 if abs(x-y)<220 or abs(x+y)<220:return 2
 if x*x+y*y<950**2:return 3
 return 1 if (int(x//480)+int(y//480))%7==0 else 0
def terrain():
 d=bytearray(b'W3E!'+i(11)+b'L'+i(1,4)+b'LgrsLgrdLdrtLrok'+i(2)+b'CLdiCLgr'+i(SIZE+1,SIZE+1)+f(-HALF,-HALF))
 for y in range(SIZE+1):
  for x in range(SIZE+1):
   edge=x<2 or y<2 or x>SIZE-2 or y>SIZE-2
   d+=struct.pack('<HHBBB',8192,8192,texture(x*128-HALF,y*128-HALF)|(128 if edge else 0),(x*7+y*3)%4,2)
 return bytes(d)
def pathing():
 w=SIZE*4
 return b'MP3W'+i(0,w,w)+bytes(14 if x<8 or y<8 or x>=w-8 or y>=w-8 else 8 for y in range(w) for x in range(w))
def unit_data():
 entries=[]
 for h in HEROES:
  entries.append(('Hpal',h['id'],[('unam',3,h['name']),('upro',3,h['name']),('upru',0,1),('umdl',3,h['model'].replace('.mdx','.mdl')),('uico',3,h['icon']),('usca',1,float(h['scale'])),('uhab',3,HERO_SKILLS.get(h['slot'],'')),('uabi',3,'AInv'),('uhpm',0,1000),('umpm',0,1000),('umpi',0,1000),('umpr',2,8.),('umvs',0,320),('ucol',2,24.),('ua1b',0,20),('ua1d',0,1),('ua1s',0,3),('ua1c',2,1.4),('ua1r',0,128),('upgr',3,''),('ureq',3,'')]))
 for slot,raw,model in [(0,'Rnfm','Naruto.mdl'),(1,'Rsfm','SasukeCursed.mdl')]:
  base=list(entries[slot][2]);overrides={'unam':'Наруто — Кьюби' if slot==0 else 'Саске — проклятая печать','umdl':model,'ua1b':45,'ua1c':1.1,'umvs':360}
  base=[(key,kind,overrides.get(key,value)) for key,kind,value in base]
  if slot==0:base += [('uani',3,'alternate')]
  entries.append(('Hpal',raw,base))
 entries.extend(summon_units())
 entries.append(('hfoo','rdum',[('unam',3,'Тренировочный противник'),('uhpm',0,50000),('uhpr',2,30.),('uaen',0,0),('umvs',0,0),('uabi',3,''),('upgr',3,''),('ureq',3,'')]))
 return objects(entries)
def preview():
 w=256;d=bytearray(struct.pack('<BBBHHBHHHHBB',0,0,2,0,0,0,0,0,w,w,24,0));palette=[(48,88,43),(65,90,48),(115,91,64),(145,147,132)];teams=[(245,60,60),(65,130,245),(185,90,240),(245,210,45)]
 for py in range(w):
  for px in range(w):
   x,y=(px/w*2-1)*HALF,(py/w*2-1)*HALF;color=palette[texture(x,y)]
   for t,(xx,yy) in enumerate(BASE):
    if (x-xx)**2+(y-yy)**2<400**2:color=teams[t]
   d+=bytes(reversed(color))
 return bytes(d)
def q(x):return json.dumps(x,ensure_ascii=False)
def script():
 data=[];voice_indices={row['path'].lower():j for j,row in enumerate(AUDIO)}
 for j,row in enumerate(AUDIO):data.append(f'    set AudioPath[{j}]={q(row["path"])}')
 for j,row in enumerate(json.loads((ROOT/'src/audio-settings.json').read_text())):
  data.append(f'    set AudioDuration[{j}]={row["duration_ms"]}')
  data.append(f'    set AudioEAX[{j}]={q(row["eax"])}')
 for p,h in enumerate(HEROES):
  data += [f"    set HeroType[{p}]='{h['id']}'",f'    set HeroName[{p}]={q(h["name"])}',f'    set SpawnX[{p}]={positions()[p][0]}.',f'    set SpawnY[{p}]={positions()[p][1]}.',f'    set AnimCount[{p}]={len(h["animations"])}',f'    set VoiceCount[{p}]={len(h["voice_paths"])}',f'    set SkillCount[{p}]={len(h["skills"])}']
  assert len(h['animations'])<64 and len(h['voice_paths'])<64
  for k,name in enumerate(h['animations']):data.append(f'    set AnimName[{p*64+k}]={q(name)}')
  for k,name in enumerate(h['voice_paths']):data.append(f'    set VoiceIndex[{p*64+k}]={voice_indices[name.lower()]}')
  for k,row in enumerate(h['skills']):data.append(f'    set SkillName[{p*5+k}]={q(row["name"])}')
 skilldata=[]
 orders=['','mirrorimage','waterelemental','thunderbolt','metamorphosis','breathoffire','roar','chainlightning','thunderbolt','metamorphosis']
 targets=[0,0,0,1,0,2,0,1,1,0]
 for j,row in enumerate(SKILLS):
  skilldata += [f"    set PlayableSkill[{j}]='{row['id']}'",f"    set SkillRanks[{j}]={row['ranks']}",f"    set SkillRequired[{j}]={row['required_level']}",f"    set SkillSkip[{j}]={row['level_skip']}",f"    set SkillAudio[{j}]={row['audio_index']}",f"    set SkillOrder[{j}]={q(orders[j])}",f"    set SkillTarget[{j}]={targets[j]}",f"    set SkillCooldown[{j}]={float(row['cooldown'])}"]
  for n,mana in enumerate(row['mana']):skilldata.append(f'    set SkillMana[{j*4+n}]={float(mana)}')
 skills=(ROOT/'src/skills.j').read_text().replace('// GENERATED_SKILLS','\n'.join(skilldata))
 code=(ROOT/'src/foundation.j').read_text().replace('// GENERATED_DATA','\n'.join(data)).replace('// SKILLS_RUNTIME',skills)
 lines=['function config takes nothing returns nothing',f'    call SetMapName({q(NAME)})',f'    call SetMapDescription({q(DESC)})','    call SetPlayers(12)','    call SetTeams(4)','    call SetGamePlacement(MAP_PLACEMENT_TEAMS_TOGETHER)']
 for p,(x,y) in enumerate(positions()):
  lines += [f'    call DefineStartLocation({p},{x}.,{y}.)',f'    call SetPlayerStartLocation(Player({p}),{p})',f'    call ForcePlayerStartLocation(Player({p}),{p})',f'    call SetPlayerColor(Player({p}),ConvertPlayerColor({p}))',f'    call SetPlayerRacePreference(Player({p}),RACE_PREF_HUMAN)',f'    call SetPlayerRaceSelectable(Player({p}),false)',f'    call SetPlayerController(Player({p}),MAP_CONTROL_USER)',f'    call SetPlayerTeam(Player({p}),{p//3})',f'    call SetPlayerState(Player({p}),PLAYER_STATE_ALLIED_VICTORY,1)',f'    call SetStartLocPrioCount({p},2)']
  n=0
  for other in range(p//3*3,p//3*3+3):
   if p!=other:
    lines += [f'    call SetPlayerAllianceStateAllyBJ(Player({p}),Player({other}),true)',f'    call SetPlayerAllianceStateVisionBJ(Player({p}),Player({other}),true)',f'    call SetStartLocPrio({p},{n},{other},MAP_LOC_PRIO_HIGH)'];n+=1
 return code+'\n'+'\n'.join(lines)+'\nendfunction\n'
def build():
 files={row['path']:(ROOT/'assets'/row['path'].replace('\\','/')).read_bytes() for row in ASSETS}
 for row in ASSETS:assert hashlib.sha256(files[row['path']]).hexdigest()==row['sha256']
 files.update({'war3map.w3i':info(),'war3map.w3e':terrain(),'war3map.wpm':pathing(),'war3map.w3u':unit_data(),'war3map.w3a':objects(ability_data(),True),'war3map.w3t':objects([]),'war3map.w3b':objects([]),'war3map.w3h':objects([],True),'war3map.w3q':objects([],True),'war3map.j':script().encode('utf8'),'war3mapMisc.txt':b'[Misc]\nMaxHeroLevel=30\nMaxUnitSpeed=480\n','war3map.doo':b'W3do'+i(8,11,0,0,0),'war3mapUnits.doo':b'W3do'+i(8,11,0),'war3map.w3r':i(5,0),'war3map.w3c':i(0,0),'war3map.w3s':i(1,0),'war3map.shd':bytes(SIZE*4*SIZE*4),'war3mapPreview.tga':preview(),'war3mapMap.tga':preview()})
 imported=[name for name in files if name in {x['path'] for x in ASSETS}]
 files['war3map.imp']=i(1,len(imported))+b''.join(b'\x0d'+s(name) for name in imported)
 mapdir=ROOT/'dist/map';mapdir.mkdir(exist_ok=True)
 for old in mapdir.iterdir():
  if old.is_file():old.unlink()
 for name,data in files.items():
  if name not in imported: (mapdir/name).write_bytes(data)
 out=ROOT/'dist/Shinobi_Skills_Alpha_05.w3x';out.write_bytes(archive(files,NAME))
 assert out.stat().st_size<8*1024*1024,'Classic 8 MiB limit'
 report={'filename':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'newMetadataAndScript':True,'copiedOriginalScenarioOrObjects':False,'importedAssets':len(ASSETS),'models':67,'audioFiles':174,'animationsInModels':442,'teams':4,'slots':12,'inventoriedLearnableSkills':58,'inventoriedInnateSkills':2,'recreatedSkillMechanics':10,'skillImplementation':'new independent adaptations, not original script','playableHeroesWithSkills':2,'sectorSize':4096,'stage':'Ten-technique training alpha; story and other heroes skills pending','engineTested':False}
 (ROOT/'dist/build-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':build()
