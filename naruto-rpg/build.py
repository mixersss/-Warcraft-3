"""Fresh 1.26 foundation: new scenario, retained original imports and generated visual helpers."""
from pathlib import Path
import json,math,struct,hashlib
from presentation import combat,misc,scenery
from skills import VISUALS,SKILLS,HERO_SKILLS,ability_data,summon_units,buff_data,normalize_abilities
from classic_formats import i,f,s,objects,archive
ROOT=Path(__file__).parent;SIZE=256;HALF=16384;BOUND=16320
HEROES=json.loads((ROOT/'src/heroes.json').read_text());ASSETS=json.loads((ROOT/'src/asset-manifest.json').read_text());AUDIO=json.loads((ROOT/'src/all-original-audio.json').read_text())
GENERATED=json.loads((ROOT/'src/generated-assets.json').read_text())
BASE=[(-15936,14400),(-7744,14400),(-15936,9536),(-7744,9536)]
NAME='SHINOBI STORY ALPHA 12'
DESC='Наруто RPG: четыре команды по три героя. Страна Волн, вопросы Ибики, Лес смерти, арены, поиск Джирайи в бочках, вторжение, Акацуки и погоня за Саске. Русские задания; боты участвуют в сюжете. -help: команды.'
def positions():return [(BASE[p//3][0],BASE[p//3][1]+(p%3-1)*128) for p in range(12)]
def info():
 d=i(25,1,6061)+s(NAME)+s('mixersss; imported assets from ShikamaruShadow map')+s(DESC)+s('1-12; 4 teams x 3')
 d+=f(-BOUND,-BOUND,BOUND,BOUND,-BOUND,BOUND,BOUND,-BOUND)+i(0,0,0,0,SIZE,SIZE,0x60)+b'X'
 d+=i(-1)+s('')+s(DESC)+s(NAME)+s('Warcraft III TFT 1.26; сюжетная альфа')
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
  entries.append(('Hpal',h['id'],[('unam',3,h['name']),('upro',3,h['name']),('upru',0,1),('umdl',3,h['model'].replace('.mdx','.mdl')),('uico',3,h['icon']),('usca',1,float(h['scale'])),('uhab',3,HERO_SKILLS.get(h['slot'],'')),('uabi',3,'AInv,Rjtr,Rlog'),('uhpm',0,1000),('umpm',0,1000),('umpi',0,1000),('umpr',2,8.),('umvs',0,320),('ucol',2,24.),('ua1b',0,20),('ua1d',0,1),('ua1s',0,3),('ua1c',2,1.4),('ua1r',0,128),('upgr',3,''),('ureq',3,'')]))
 for slot,raw,model in [(0,'Rnfm','Naruto.mdl'),(1,'Rsfm','SasukeCursed.mdl'),(7,'Rkfm','units\\creeps\\WhiteWolf\\WhiteWolf.mdl'),(9,'Rgfm','Shukaku.mdl')]:
  base=list(entries[slot][2]);overrides={'unam':{0:'Наруто — Кьюби',1:'Саске — проклятая печать',7:'Киба — звериная форма',9:'Гаара — Сюкаку'}[slot],'umdl':model,'ua1b':45,'ua1c':1.1,'umvs':360}
  base=[(key,kind,overrides.get(key,value)) for key,kind,value in base]
  if slot==0:base += [('uani',3,'alternate')]
  if slot==7:base += [('usca',1,1.2)]
  if slot==9:base += [('usca',1,1.3)]
  entries.append(('Hpal',raw,base))
 # Tenten must really attack at range for native Barrage to work.
 for slot in range(12):entries[slot][2].extend(combat(slot))
 from story import unit_entries
 entries.extend(unit_entries())
 entries.extend(__import__('campaign').units())
 entries.extend(summon_units())
 entries.extend(__import__('npc_source').entries('units'))
 entries.append(('hfoo','rdum',[('unam',3,'Тренировочный противник'),('uhpm',0,50000),('uhpr',2,30.),('uaen',0,0),('umvs',0,0),('uabi',3,''),('upgr',3,''),('ureq',3,'')]))
 for _,_,mods in entries:
  mods.extend([('usnd',3,''),('ucs2',3,'')])
  if not any(m[0]=='ucs1' for m in mods):mods.append(('ucs1',3,'WoodHeavyBash'))
  mods[:]=list({k:(k,t,v) for k,t,v in mods}.values())
 return objects(entries)
def preview():
 raw=(ROOT/'src/location/original-war3map.w3e').read_bytes()
 n=struct.unpack_from('<i',raw,13)[0];off=17+n*4
 cliffs=struct.unpack_from('<i',raw,off)[0];off+=4+cliffs*4+16
 w=256;d=bytearray(struct.pack('<BBBHHBHHHHBB',0,0,2,0,0,0,0,0,w,w,24,0))
 palette=[(116,91,62),(115,94,64),(108,105,97),(125,121,108),(142,139,123),(99,94,87),(59,91,42),(120,119,108),(67,98,45)]
 for py in range(w):
  for px in range(w):
   tile=raw[off+(py*257+px)*7+4]&15
   color=palette[tile%len(palette)]
   for xx,yy in BASE:
    if abs(px-(xx+HALF)/128)<2 and abs(py-(yy+HALF)/128)<2:color=(245,215,50)
   d+=bytes(reversed(color))
 return bytes(d)
def q(x):return json.dumps(x,ensure_ascii=False)
def script():
 data=[];voice_indices={row['path'].lower():j for j,row in enumerate(AUDIO)}
 for j,row in enumerate(AUDIO):data.append(f'    set AudioPath[{j}]={q(row["path"])}')
 for j,row in enumerate(json.loads((ROOT/'src/audio-settings.json').read_text())):
  data.append(f'    set AudioDuration[{j}]={row["duration_ms"]}')
  data.append(f'    set AudioEAX[{j}]={q(row["eax"])}')
 for j,row in enumerate(json.loads((ROOT/'src/chapter-music.json').read_text())):
  data.append(f"    set PlaylistAudio[{j}]={row['audio_index']}")
  data.append(f"    set PlaylistDuration[{j}]={row['duration_ms']/1000.}")
 for p,h in enumerate(HEROES):
  data += [f"    set RosterHeroType[{p}]='{h['id']}'",f"    set HeroType[{p}]='{h['id']}'",f'    set HeroName[{p}]={q(h["name"])}',f'    set SpawnX[{p}]={positions()[p][0]}.',f'    set SpawnY[{p}]={positions()[p][1]}.',f'    set AnimCount[{p}]={len(h["animations"])}',f'    set VoiceCount[{p}]={len(h["voice_paths"])}',f'    set SkillCount[{p}]={len(h["skills"])}']
  assert len(h['animations'])<64 and len(h['voice_paths'])<64
  for k,name in enumerate(h['animations']):data.append(f'    set AnimName[{p*64+k}]={q(name)}')
  for k,name in enumerate(h['voice_paths']):data.append(f'    set VoiceIndex[{p*64+k}]={voice_indices[name.lower()]}')
  for k,row in enumerate(h['skills']):data.append(f'    set SkillName[{p*5+k}]={q(row["name"])}')
 skillbodies=[[] for _ in range(12)]
 for row in SKILLS:
  j=row['index'];body=skillbodies[row['hero']]
  anims=HEROES[row['hero']]['animations'];tokens=row['animation'].lower().replace(',',' ').split()
  anim=next((k for k,name in enumerate(anims) if all(t in name.lower().split() for t in tokens)), -1)
  profile=next(p for p in VISUALS['skills'] if p['index']==j)
  formindex=-1;formscale=1.
  formmodels={0:'Naruto.mdx',1:'SasukeCursed.mdx',9:'Shukaku.mdx'}
  if row['hero'] in formmodels:
   metadata=json.loads((ROOT/'src/model-visual-metadata.json').read_text())
   seqs=next(m['sequences'] for m in metadata if m['path']==formmodels[row['hero']])
   desired='Spell slam Alternate' if row['hero']==0 else ('Spell slam' if row['hero']==1 and row['slot'] in (2,3) else 'Spell')
   formindex=next(n for n,a in enumerate(seqs) if a['name'].lower()==desired.lower())
   formscale=seqs[formindex]['seconds']/profile['channelSeconds'] if profile['channelSeconds'] else 1.
  values={'SkillFormAnimation':formindex,'SkillFormPoseScale':formscale,'SkillHold':profile['channelSeconds'],'SkillPoseScale':profile['sequencePlaybackScale'],'PlayableSkill':"'"+row['id']+"'",'SkillRanks':row['ranks'],'SkillRequired':row['required_level'],'SkillSkip':row['level_skip'],'SkillAudio':row['audio_index'],'SkillOrder':q(row['order']),'SkillTarget':row['target_mode'],'SkillCooldown':float(row['cooldown']),'SkillPassive':str(row.get('passive',False)).lower(),'SkillMorph':str(row['base']=='AEme').lower(),'SkillToggle':str(row['base']=='ANms').lower(),'SkillHeal':str(row.get('heal',False)).lower(),'SkillAnimation':anim,'RosterMechanic':row.get('mechanic',0),'RosterRadius':float(row.get('radius',0.)),'RosterDuration':float(row.get('duration',0.)),'RosterVisual':q(row.get('effect','')),'RosterProfile':row.get('profile',0),'RosterPetSlot':row.get('companion_slot',0)}
  for key,value in values.items():body.append(f'    set {key}[{j}]={value}')
  for n,mana in enumerate(row['mana']):
   body.append(f'    set SkillMana[{j*4+n}]={float(mana)}')
   body.append(f"    set RosterPower[{j*4+n}]={float(row.get('damage',[0.]*row['ranks'])[n])}")
   body.append(f"    set RosterBurn[{j*4+n}]={float(row.get('burn',[0.]*row['ranks'])[n])}")
   summon=row.get('summon','')
   if summon:
    raw=summon if len(summon)==4 else summon+str(n+1)
    body.append(f"    set RosterPetType[{j*4+n}]='{raw}'")
 skillfunctions=[]
 for h,body in enumerate(skillbodies):skillfunctions.append(f'function SkillsData{h} takes nothing returns nothing\n'+'\n'.join(body)+'\nendfunction')
 dispatch=['function SkillsLoadData takes nothing returns nothing']
 for h in range(12):dispatch += [('    if' if h==0 else '    elseif')+f' SkillDataCursor=={h} then',f'        call SkillsData{h}()']
 dispatch += ['    endif','    set SkillDataCursor=SkillDataCursor+1','    if SkillDataCursor>=12 then','        set SkillDataReady=true','        call PauseTimer(SkillDataClock)','        call DestroyTimer(SkillDataClock)','        set SkillDataClock=null','    endif','endfunction']
 skillfunctions.append('\n'.join(dispatch))
 skills=(ROOT/'src/skills.j').read_text().replace('// ROSTER_RUNTIME',(ROOT/'src/common-skills.j').read_text()+'\n'+(ROOT/'src/visuals.j').read_text()+'\n'+(ROOT/'src/roster.j').read_text()).replace('// GENERATED_SKILL_FUNCTIONS','\n'.join(skillfunctions)).replace('// GENERATED_SKILLS','    set SkillDataClock=CreateTimer()\n    call TimerStart(SkillDataClock,.05,true,function SkillsLoadData)')
 from story import generated_data
 code=(ROOT/'src/foundation.j').read_text().replace('// NPC_SOURCE_GLOBALS',(ROOT/'src/npc-source-globals.j').read_text()).replace('// GENERATED_DATA','\n'.join(data)+generated_data()+__import__('campaign').generated()+__import__('npc_source').generated()).replace('// TREE_RUNTIME',(ROOT/'src/tree-jump.j').read_text()).replace('// SKILLS_RUNTIME',skills).replace('// STORY_RUNTIME',(ROOT/'src/npc-source-runtime.j').read_text()+'\n'+__import__('npc_source').initialize()+'\n'+(ROOT/'src/npc-ai.j').read_text()+'\n'+(ROOT/'src/story.j').read_text().replace('// NEXT_CHAPTER_RUNTIME',(ROOT/'src/stage-hud.j').read_text()+'\n'+(ROOT/'src/exam.j').read_text()+'\n'+(ROOT/'src/campaign-cameras.j').read_text()+'\n'+(ROOT/'src/campaign.j').read_text()))
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
 for row in GENERATED:
  files[row['path']]=(ROOT/row['file']).read_bytes()
  assert len(files[row['path']])==row['bytes'] and hashlib.sha256(files[row['path']]).hexdigest()==row['sha256']
 files.update({'war3map.w3i':info(),'war3map.w3e':terrain(),'war3map.wpm':pathing(),'war3map.w3u':unit_data(),'war3map.w3a':objects(normalize_abilities(ability_data()+__import__('story').ability_entries()+__import__('campaign').abilities())+__import__('npc_source').entries('abilities'),True),'war3map.w3t':objects(__import__('story').item_entries()+__import__('loot').items()+__import__('story').scroll_entries()),'war3map.w3b':objects([]),'war3map.w3h':objects(buff_data()+__import__('npc_source').entries('buffs')),'war3map.w3q':objects([],True),'war3map.j':script().encode('utf8'),'war3mapMisc.txt':misc(),'war3map.doo':b'W3do'+i(8,11,0,0,0),'war3mapUnits.doo':b'W3do'+i(8,11,0),'war3map.w3r':i(5,0),'war3map.w3c':i(0,0),'war3map.w3s':i(1,0),'war3map.shd':bytes(SIZE*4*SIZE*4),'war3mapPreview.tga':preview(),'war3mapMap.tga':preview()})
 for name in ['war3map.w3e','war3map.wpm','war3map.doo','war3map.w3b','war3map.w3d']:
  files[name]=(ROOT/'src/location'/('original-'+name)).read_bytes()
 files['war3map.w3b']=scenery()
 files['war3map.doo']=(ROOT/'src/location/render-war3map.doo').read_bytes()
 files['war3map.wts']=(ROOT/'src/npc-original.wts').read_bytes()
 imported=[name for name in files if name in {x['path'] for x in ASSETS+GENERATED}]
 files['war3map.imp']=i(1,len(imported))+b''.join(b'\x0d'+s(name) for name in imported)
 mapdir=ROOT/'dist/map';mapdir.mkdir(parents=True,exist_ok=True)
 for old in mapdir.iterdir():
  if old.is_file():old.unlink()
 for name,data in files.items():
  if name not in imported: (mapdir/name).write_bytes(data)
 out=ROOT/'dist/Shinobi_Story_Alpha_12.w3x';out.write_bytes(archive(files,NAME))
 assert out.stat().st_size<8*1024*1024,'Classic 8 MiB limit'
 report={'filename':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'newMetadataAndScript':True,'copiedOriginalScenarioOrObjects':'terrain/scenery, source-native NPC object records, WTS and spell-action closure; fresh campaign control and metadata','importedAssets':len(ASSETS)+len(GENERATED),'originalImportedAssets':len(ASSETS),'generatedAssets':len(GENERATED),'models':67+len(GENERATED),'audioFiles':174,'musicTracks':9,'animationsInModels':442,'teams':4,'slots':12,'inventoriedLearnableSkills':58,'inventoriedInnateSkills':2,'recreatedSkillMechanics':58,'skillImplementation':'playable roster remains adapted; NPC and level-60 clone spell actions imported from source','playableHeroesWithSkills':12,'sectorSize':4096,'originalNinjasPerTeam':14,'nativeTreeJumpTargeting':True,'mentorDepartureSeconds':330,'originalLootTypes':7,'recreatedInnateSkills':1,'nativeVisibleTrees':3377,'auditedActiveSkillAnimations':52,'sourceVisualSlotsAudited':58,'modelsWithSequenceAndAttachmentAudit':67,'visualActorTypes':len(VISUALS['visualUnits']),'boundedVisualActorCapacity':256,'realChannelCastPoses':True,'nativeImpactSounds':True,'musicMode':'source chapter mapping; forest HeavyViolence loop','experienceProfile':'source native factors and quiz/Jiraiya rewards; independent battle encounters','stage':'12 source NPC combat, original invasion deployment and invasion-only shops','commonKawarimiForAllHeroes':True,'stageTimerHUD':True,'questionBankSize':16,'questionsPerExam':5,'questionSeconds':15,'forestExamSeconds':1320,'towerOpensAfterSeconds':1200,'examGenin':85,'campaignObjectives':22,'parallelCloneEncounters':8,'jiraiyaBarrels':20,'jiraiyaSearchSeconds':150,'invasionStreams':8,'invasionWaveSeconds':45,'cinematics':'simplified fades/camera transitions; not identical to original','npcTechniques':'source-native spell objects and callbacks, original level-60 clone skill sets; adapted bot targeting/scheduling','shopsOnlyDuringInvasion':True,'sourceLeafDefenders':140,'sourceAnbuDefenders':102,'sourceVillageMedics':6,'sourceVillageShops':4,'sourceNPCSpellObjects':len(__import__('npc_source').DATA['abilities']),'sourceNPCFunctions':len(json.loads((ROOT/'src/npc-source-audit.json').read_text())['sourceFunctions']),'fullOriginalScenarioIdentical':False,'engineTested':False}
 (ROOT/'dist/build-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':build()
