import re,json,hashlib
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Trace source spell art, buff art, visual units, helper abilities and explicitly enabled/started trigger actions.')
parser.add_argument('script',type=Path);parser.add_argument('abilities',type=Path);parser.add_argument('units',type=Path);parser.add_argument('buffs',type=Path);parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
source=args.script.read_text();abilities=json.loads(args.abilities.read_text());units=json.loads(args.units.read_text());buffs=json.loads(args.buffs.read_text())
funcs={m[1]:{'body':m[2],'line':source[:m.start()].count('\n')+1} for m in re.finditer(r'^function (\w+) takes[^\n]*\n(.*?)^endfunction',source,re.M|re.S)}
conds={};actions={};events={}
for tr,fn in re.findall(r'TriggerAddCondition\((\w+),Condition\(function (\w+)\)\)',source):conds.setdefault(tr,[]).append(fn)
for tr,fn in re.findall(r'TriggerAddAction\((\w+),function (\w+)\)',source):actions.setdefault(tr,[]).append(fn)
def closure(roots,triggers=False,limit=300):
 seen=set();todo=list(roots)
 while todo:
  fn=todo.pop()
  if fn in seen or fn not in funcs:continue
  seen.add(fn);assert len(seen)<limit,(roots,fn)
  body=funcs[fn]['body'];todo+=re.findall(r'\b(\w+)\(',body)+re.findall(r'\bfunction (\w+)',body)
  if triggers:
   for tr in re.findall(r'(?:TriggerExecute|ConditionalTriggerExecute|EnableTrigger)\((\w+)\)',body):todo+=actions.get(tr,[])
 return seen
rootmap={}
for tr,fns in conds.items():
 body='\n'.join(funcs[f]['body'] for f in closure(fns))
 for raw in re.findall(r"GetSpellAbilityId\(\)==\s*'(.{4})'",body):rootmap.setdefault(raw,[]).append(tr)
visual_fields={'amat','acat','aeat','atat','asat','aani','amsp','amho','Ncl1','Ncl4','Ncl5','alig','aefs','aefl','ata0','ata1','ata2','acap','acat'}
report=[]
for h in json.load(open(str(Path(__file__).parent/'src/skills-catalog.json')))['heroes']:
 for skill in h['skills']:
  raw=skill['source_id'];roots=[f for tr in rootmap.get(raw,[]) for f in actions.get(tr,[])]
  fs=closure(roots,True)
  records=[];unitids=set();extraAbilities=set()
  for fn in sorted(fs,key=lambda f:funcs[f]['line']):
   body=funcs[fn]['body'];lines=[]
   for offset,line in enumerate(body.splitlines()):
    if re.search(r'CreateNUnits|AddSpecialEffect|SetUnitAnimation|SetUnitScale|SetUnitTimeScale|SetUnitVertexColor|SetUnitFlyHeight|UnitAddAbility|SetUnitAbilityLevel',line):
     lines.append({'line':funcs[fn]['line']+offset+1,'operation':line})
    unitids.update(re.findall(r"CreateNUnits\w*\([^\n]*?'(.{4})'",line))
    extraAbilities.update(re.findall(r"(?:UnitAddAbility\([^\n]*?,|SetUnitAbilityLevelSwapped\()'(.{4})'",line))
   if lines:records.append({'function':fn,'operations':lines})
  art=[v for v in abilities.get(raw,{}).get('mods',[]) if v['id'] in visual_fields]
  buffids={v['value'] for v in abilities.get(raw,{}).get('mods',[]) if v['id']=='abuf'}
  unitart={k:{v['id']:v['value'] for v in units.get(k,{}).get('mods',[]) if v['id'] in ('umdl','usca','uclr','uclg','uclb','uabi','umvh','umvt')} for k in sorted(unitids)}
  buffart={k:{v['id']:v['value'] for v in buffs.get(k,{}).get('mods',[])} for l in sorted(buffids) for k in l.split(',') if k}
  report.append({'hero':h['slot'],'name':skill['name'],'sourceId':raw,'base':skill['base_ability'],'abilityArt':art,'buffArt':buffart,'triggerVisualUnits':unitart,'triggerVisualOperations':records,'extraAbilityIds':sorted(extraAbilities),'helperAbilityArt':{k:[v for v in abilities.get(k,{}).get('mods',[]) if v['id'] in visual_fields or v['id']=='abuf'] for k in sorted(extraAbilities)}})
args.out.write_text(json.dumps({'sourceScriptSha256':hashlib.sha256(source.encode()).hexdigest(),'method':'Source W3A/W3U/W3H plus spell-trigger conditions, action/helper calls and explicitly enabled/started triggers. Static tracing cannot resolve all dynamic unit variables or pre-enabled periodic triggers.','skills':report},ensure_ascii=False,indent=2))
print(f'Audited {len(report)} source skill slots; saved {args.out}')
