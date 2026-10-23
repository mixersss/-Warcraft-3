"""Inventory all roster slots against source data and bundled MDX sequences (not engine playback)."""
import json,struct
from pathlib import Path
ROOT=Path(__file__).parent
rows=json.loads((ROOT/'src/playable-skills.json').read_text())
heroes=json.loads((ROOT/'src/heroes.json').read_text())
source=json.loads((ROOT/'src/skills-catalog.json').read_text())['heroes']
source_lists={r['hero']:r['sourceSkills'] for r in json.loads((ROOT/'src/source-skill-audit.json').read_text())['heroes']}
assets={r['path'].lower():r for r in json.loads((ROOT/'src/asset-manifest.json').read_text())}
def sequences(path):
 data=(ROOT/'assets'/path).read_bytes();assert data[:4]==b'MDLX'
 at=4
 while at<len(data):
  tag=data[at:at+4];size=struct.unpack_from('<I',data,at+4)[0];body=data[at+8:at+8+size];at+=8+size
  if tag==b'SEQS':
   assert size%132==0
   return [body[n:n+80].split(b'\0',1)[0].decode() for n in range(0,size,132)]
 raise AssertionError('Missing model animations: '+path)
report=[]
for h in heroes:
 model_sequences=sequences(h['model'])
 assert model_sequences==h['animations']
 skills=[r for r in rows if r['hero']==h['slot']]
 assert [r['source_id'] for r in skills]==source_lists[h['slot']]
 orders=[]
 for r in skills:
  assert len(r['rank_descriptions'])==r['ranks']==len(r['mana'])
  for field,kind,column,values in r['fields']:
   assert len(values) in (1,r['ranks']),(r['id'],field)
   if field in ('Eev1','Ocr4'):assert all(0<=v<=.75 for v in values)
   if kind==3:
    for value in values:
     for model in str(value).split(','):
      if model.lower().endswith(('.mdl','.mdx')) and not model.lower().startswith(('units\\','abilities\\','objects\\','doodads\\')):
       assert model.lower().removesuffix('.mdl').removesuffix('.mdx')+'.mdx' in assets,(r['id'],model)
  tokens=r['animation'].lower().replace(',',' ').split()
  matching=[(n,name) for n,name in enumerate(model_sequences) if all(t in name.lower().split() for t in tokens)]
  if not r['passive']:
   assert matching and 'alternate' not in matching[0][1].lower(),r['id']
   assert r['order'] and r['order'] not in orders,(h['name'],r['order'])
   orders.append(r['order'])
  report.append({'hero':h['name'],'id':r['id'],'sourceId':r['source_id'],'name':r['name'],'ranks':r['ranks'],'passive':r['passive'],'model':h['model'],'animation':None if r['passive'] else matching[0][1],'animationIndex':None if r['passive'] else matching[0][0],'sourceAnimationTags':r['animation'] if h['slot']in(3,6)else source[h['slot']]['skills'][r['slot']]['animation_tags'],'mechanic':r.get('mechanic',0),'nativeBase':r['base'],'enginePlaybackChecked':False})
assert len(report)==58
result={'slots':58,'heroes':12,'activeAnimations':sum(not r['passive']for r in rows),'sourceSlotListsMatch':True,'allRankFieldsChecked':True,'modelSequencesReadFromBundledMDX':True,'enginePlaytest':False,'mechanicalEquivalenceToOriginal':False,'skills':report}
(ROOT/'dist/skill-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('PASS: 58 source slots, 54 active normal-model MDX sequences, every rank field, evasion caps and distinct per-hero cast orders; engine playback not tested.')
