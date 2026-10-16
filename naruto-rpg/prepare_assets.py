from pathlib import Path
import json,struct,hashlib,re,shutil
ROOT=Path(__file__).parent;EX=Path('/workspace/naruto-bots/extracted')
names=json.loads((EX/'recovered-names.json').read_text());lookup={k.lower():v for k,v in names.items()};reverse={}
for name,index in names.items():reverse.setdefault(index,name)
units=json.load(open('/workspace/naruto-map-review/war3map.w3u.json'));abilities=json.load(open('/workspace/naruto-map-review/war3map.w3a.json'))
heroids=['H002','H003','H004','H007','H005','H006','H00D','H00B','H00J','H008','H00A','H009']
source=Path('/workspace/naruto-map-review/script-readable.j').read_text()
funcs={m[1]:m[2] for m in re.finditer(r'^function (\w+) takes[^\n]*\n(.*?)^endfunction',source,re.M|re.S)}
soundvars={m[1]:m[2].replace('\\\\','\\') for m in re.finditer(r'set (\w+)=CreateSound\("((?:\\.|[^"\\])*)"',source)}
def closure(fn,depth=0,seen=None):
 seen=set() if seen is None else seen
 if fn in seen or fn not in funcs or depth>6:return ''
 seen.add(fn);body=funcs[fn]
 return body+'\n'+'\n'.join(closure(k,depth+1,seen) for k in set(re.findall(r'\b(\w+)\(',body)) if k in funcs)
conds={};actions={}
for tr,fn in re.findall(r'TriggerAddCondition\((\w+),Condition\(function (\w+)\)\)',source):conds.setdefault(tr,[]).append(fn)
for tr,fn in re.findall(r'TriggerAddAction\((\w+),function (\w+)\)',source):actions.setdefault(tr,[]).append(fn)
spell_sounds={}
for tr,fns in conds.items():
 condition='\n'.join(closure(fn) for fn in fns);ids=set(re.findall(r"GetSpellAbilityId\(\)==\s*'(.{4})'",condition))
 body='\n'.join(closure(fn) for fn in actions.get(tr,[]))
 variables=set(re.findall(r'(?:PlaySoundBJ|PlaySoundOnUnitBJ|StartSound)\((\w+)',body))
 sounds={soundvars[k] for k in variables if k in soundvars}
 for raw in ids:spell_sounds.setdefault(raw,set()).update(sounds)
selected=set();models={};all_audio={i for name,i in names.items() if name.lower().endswith(('.mp3','.wav'))}
for i in range(461):
 data=(EX/f'{i:04d}.bin').read_bytes()
 if data[:4]!=b'MDLX':continue
 selected.add(i);animations=[];textures=[];pos=4
 while pos+8<=len(data):
  tag=data[pos:pos+4];size=struct.unpack_from('<I',data,pos+4)[0];chunk=data[pos+8:pos+8+size];pos+=8+size
  if tag==b'SEQS':
   for off in range(0,len(chunk),132):animations.append(chunk[off:off+80].split(b'\0')[0].decode('latin1'))
  if tag==b'TEXS':
   for off in range(0,len(chunk),268):
    name=chunk[off+4:off+264].split(b'\0')[0].decode('latin1');textures.append(name)
    if name.lower() in lookup:selected.add(lookup[name.lower()])
 models[i]={'path':reverse[i],'animations':animations,'textures':textures}
selected.update(all_audio)
# Portrait for the first playable summoned companion.
selected.add(lookup['icon_gamabunta_portrait.blp'])
heroes=[]
for h,raw in enumerate(heroids):
 f=units[raw]['fields'];model=f['umdl'].replace('.mdl','.mdx');index=lookup[model.lower()];skills=[]
 for key in [f.get('uico','')]:
  if key.lower() in lookup:selected.add(lookup[key.lower()])
 for skill in f['uhab'].split(','):
  obj=abilities[skill];af=obj['fields']
  for key in ['aart','arar']:
   val=af.get(key,'')
   if val.lower() in lookup:selected.add(lookup[val.lower()])
  skills.append({'source_id':skill,'name':af.get('anam',skill),'base_ability':obj['base'],'levels':af.get('alev',3),'description':af.get('arut',af.get('aub1','')),'animation_tags':af.get('aani','spell'),'source_trigger_sound_paths':sorted(spell_sounds.get(skill,set())),'runtime_recreated':False})
 aliases=[f['unam'].split()[-1].lower()]
 if h==0:aliases+=['rasengan']
 if h==1:aliases+=['chidori','sharingan']
 voice=sorted({name for name,i in names.items() if i in all_audio and any(alias in name.lower() for alias in aliases)})
 heroes.append({'slot':h,'id':f'R{h:03X}','source_id':raw,'name':f['unam'],'model':models[index]['path'],'icon':f['uico'],'scale':f.get('usca',.9),'animations':models[index]['animations'],'voice_paths':voice,'skills':skills})
manifest=[]
for i in sorted(selected):
 data=(EX/f'{i:04d}.bin').read_bytes();name=reverse[i]
 # Store imports by original path; filenames, texture references and bytes remain unchanged.
 target=ROOT/'assets'/name.replace('\\','/');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 manifest.append({'source_index':i,'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
(ROOT/'src/heroes.json').write_text(json.dumps(heroes,ensure_ascii=False,indent=2))
(ROOT/'src/skills-catalog.json').write_text(json.dumps({'heroes':heroes,'shared_innate_skills':[{'id':k,'data':abilities[k]} for k in ['A00F','A012']],'note':'All source skill definitions inventoried; mechanics are not yet recreated in the foundation test.'},ensure_ascii=False,indent=2))
(ROOT/'src/asset-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(ROOT/'src/model-animations.json').write_text(json.dumps(list(models.values()),ensure_ascii=False,indent=2))
(ROOT/'src/all-original-audio.json').write_text(json.dumps([{'path':reverse[i],'source_index':i} for i in sorted(all_audio)],ensure_ascii=False,indent=2))
print('Imported',len(models),'models,',len(selected)-len(models)-len(all_audio),'textures/icons,',len(all_audio),'audio files; animation sequences',sum(len(m['animations']) for m in models.values()))
print('Inventoried',len(heroes),'heroes,',sum(len(h['skills']) for h in heroes),'learnable skill slots and 2 shared innate abilities. Recreated mechanics: 0 (foundation test).')
