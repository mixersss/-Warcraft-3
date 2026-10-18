"""Full roster of independent techniques. Original icons/models/audio; new balance and logic."""
import json
from pathlib import Path
ROOT=Path(__file__).parent
# Checked-in runtime data, rather than original protected object definitions.
VISUALS=json.loads((ROOT/'src/skill-visuals.json').read_text())
SKILLS=json.loads((ROOT/'src/playable-skills.json').read_text())
HERO_SKILLS={h:','.join(s['id'] for s in SKILLS if s['hero']==h) for h in range(12)}
def ability_data():
 out=[]
 for j,row in enumerate(SKILLS):
  pos=row['slot'];changes=[('anam',3,row['name']),('aher',0,1),('aite',0,0),('alev',0,row['ranks']),('arlv',0,row['required_level']),('alsk',0,row['level_skip']),('aart',3,row['icon']),('arar',3,row['icon']),('ahky',3,row['key']),('arhk',3,row['key']),('abpx',0,pos if pos<4 else 1),('abpy',0,2 if pos<4 else 1),('arpx',0,pos%4),('arpy',0,pos//4),('aret',3,row['name']),('arut',3,row['description']),('aani',3,row['animation']),('areq',3,''),('arac',3,'human'),('acat',3,''),('aeat',3,''),('aefs',3,''),('aefl',3,'')]
  for n in range(1,row['ranks']+1):
   changes += [('atp1',3,row['name']+f' [ур. {n}]',n,0),('aub1',3,row['rank_descriptions'][n-1],n,0),('amcs',0,row['mana'][n-1],n,0),('acdn',2,row.get('cooldowns',[row['cooldown']]*row['ranks'])[n-1],n,0),('aran',2,row['range'],n,0),('atar',3,row['targets'],n,0)]
   for field,kind,column,values in row['fields']:changes.append((field,kind,values[min(n-1,len(values)-1)],n,column))
  out.append((row['base'],row['id'],changes))
 # Sharingan's bounded temporary passive bonuses; removed on expiration/death/reselection.
 for base,raw,fields in [('AEev','Rsev',[('Eev1',2,1,[.15,.20,.25])]),('AOcr','Rscr',[('Ocr1',2,1,[15.,20.,25.]),('Ocr2',2,2,[1.5,1.75,2.]),('Ocr3',2,3,[0.,0.,0.]),('Ocr4',2,4,[0.,0.,0.]),('Ocr5',0,5,[0,0,0])]),('Aamk','Rsag',[('Iagi',0,1,[6,10,14]),('Iint',0,2,[0,0,0]),('Istr',0,3,[0,0,0])])]:
  mods=[('anam',3,'Sharingan: '+raw),('aher',0,0),('aite',0,0),('alev',0,3),('abpx',0,0),('abpy',0,-11)]
  for field,kind,col,values in fields:
   for n,v in enumerate(values,1):mods.append((field,kind,v,n,col))
  out.append((base,raw,mods))
 # Generic temporary bonuses used by Lee, Hyuuga, Kiba and smoke defense.
 for base,raw,fields in [
  ('AEev','Rbev',[('Eev1',2,1,[.10,.15,.20,.25])]),
  ('AOcr','Rbcr',[('Ocr1',2,1,[15.,20.,25.,30.]),('Ocr2',2,2,[1.5,1.7,1.9,2.1]),('Ocr3',2,3,[0.]*4),('Ocr4',2,4,[0.]*4),('Ocr5',0,5,[0]*4)]),
  ('AIat','Rbat',[('Iatt',0,1,[10,20,30,40])]),
  ('AIsx','Rbas',[('Isx1',2,1,[.15,.25,.35,.45])]),
  ('AId1','Rbar',[('Idef',0,1,[3,5,7,9])]),
  ('AIms','Rbms',[('Imvb',0,1,[20,30,40,50])])]:
  mods=[('anam',3,'Temporary: '+raw),('aher',0,0),('aite',0,0),('alev',0,4),('abpx',0,0),('abpy',0,-11)]
  for field,kind,col,values in fields:
   for n,v in enumerate(values,1):mods.append((field,kind,v,n,col))
  out.append((base,raw,mods))
 # Source A02W detection ranges; independent of the temporary combat bonuses.
 sight=[('anam',3,'Бьякуган: обнаружение'),('aher',0,0),('alev',0,4),('abpy',0,-11)]
 for n in range(1,5):sight += [('aran',2,200.+200.*n,n,0),('Det1',0,1,n,1),('atar',3,'enemies,vulnerable',n,0)]
 out.append(('Atru','Rbyg',sight))
 # Hidden native stun applied by an expiring invisible caster; no PauseUnit locks.
 stun=[('anam',3,'Короткое оглушение'),('aher',0,0),('alev',0,4),('abpx',0,0),('abpy',0,-11),('amat',3,''),('aani',3,''),('acat',3,'')]
 for n in range(1,5):stun += [('amcs',0,0,n,0),('acdn',2,0.,n,0),('aran',2,2000.,n,0),('Htb1',2,0.,n,1),('adur',2,.5*n,n,0),('ahdu',2,.25*n,n,0),('amsp',0,10000,n,0),('atar',3,'ground,air,enemy,neutral,organic',n,0)]
 out.append(('ANsb','Rstn',stun))
 micro=[('anam',3,'Микрооглушение Кайтэна'),('aher',0,0),('alev',0,1),('abpy',0,-11),('amat',3,''),('aani',3,''),('amcs',0,0,1,0),('acdn',2,0.,1,0),('aran',2,2000.,1,0),('Htb1',2,0.,1,1),('adur',2,.2,1,0),('ahdu',2,.1,1,0),('atar',3,'ground,air,enemy,neutral,organic',1,0)]
 out.append(('AHtb','Rmic',micro))
 out.append(('AHtb','Rkst',[('anam',3,'Оглушение куная'),('aher',0,0),('alev',0,1),('abpy',0,-11),('amcs',0,0,1,0),('acdn',2,0.,1,0),('aran',2,2000.,1,0),('acas',2,0.,1,0),('Htb1',2,0.,1,1),('adur',2,1.25,1,0),('ahdu',2,.75,1,0),('abuf',3,'Rksb',1,0),('amat',3,''),('aani',3,''),('atar',3,'ground,air,enemy,neutral,organic',1,0)]))
 for _,_,mods in out:
  if not any(m[0]=='aefs' for m in mods):mods.extend([('aefs',3,''),('aefl',3,'')])
 return out

def summon_units():
 out=[]
 for n in range(1,4):
  out.append(('hkni','rt0'+str(n),[('unam',3,'Гамабунта'),('umdl',3,'Gamabunta_2.mdl'),('uico',3,'Icon_Gamabunta_Portrait.blp'),('usca',1,2.0+.25*n),('uhpm',0,1000+600*n),('ua1b',0,35+25*n),('ua1d',0,1),('ua1s',0,3),('ua1c',2,1.5),('ua1r',0,180),('umvs',0,300),('ucol',2,48.),('udef',0,2+2*n),('ufoo',0,0),('uabi',3,''),('ureq',3,''),('upgr',3,''),('uacq',2,800.)]))
 for prefix,name,model,icon,scale,hp,dmg,armor in [
  ('ra0','Акамару','units\\creeps\\WhiteWolf\\WhiteWolf.mdl','Icon_Akamaru_Portrait.blp',.65,600,24,2),
  ('rc0','Карасу','Karasu.mdl','Icon_Kankuro_Karasu.blp',1.,700,35,3),
  ('rk0','Куроари','Kuroari.mdl','Icon_Kankuro_Kuroari.blp',1.,1100,25,6),
  ('rs0','Сансёо','Sanshouo.mdl','Icon_Kankuro_Sanshouo.blp',1.3,1800,40,9),
  ('rz0','Сидзунэ','Shizune.mdl','Icon_Sakura_Shosen.blp',1.,900,15,3)]:
  for n in range(1,2 if prefix=='rz0' else 4):
   out.append(('hfoo',prefix+str(n),[('unam',3,name),('umdl',3,model),('uico',3,icon),('usca',1,scale),('uhpm',0,hp+(n-1)*400),('ua1b',0,dmg+(n-1)*18),('ua1d',0,1),('ua1s',0,3),('ua1c',2,1.4),('ua1r',0,140),('umvs',0,325),('ucol',2,28.),('udef',0,armor+(n-1)*2),('ufoo',0,0),('uabi',3,'ACvs' if prefix=='rc0' else ''),('ureq',3,''),('upgr',3,'')]))
 out.append(('hfoo','rshk',[('unam',3,'Теневые путы'),('uhom',0,1),('umdl',3,'ShikamaruKageMane.mdl'),('uabi',3,'Aloc,Avul'),('uaen',0,0),('umvs',0,0),('umvt',3,'fly'),('umvh',2,0.),('umvf',2,0.),('ucol',2,0.),('usca',1,2.),('ushu',3,''),('ushb',3,''),('usin',0,0),('usid',0,0),('ufoo',0,0)]))
 out.append(('hfoo','rshd',[('unam',3,'Тень'),('ushu',3,''),('ushb',3,''),('umdl',3,'ShinobiShadowStrip.mdl'),('usin',0,0),('usid',0,0),('uhom',0,1),('umvt',3,'fly'),('umvh',2,6.),('umvf',2,6.),('uabi',3,'Aloc,Avul'),('uaen',0,0),('umvs',0,0),('ucol',2,0.),('usca',1,1.),('ufoo',0,0)]))
 out.append(('hfoo','rdst',[('unam',3,'Технический кастер'),('umdl',3,''),('usin',0,0),('usid',0,0),('ucpt',2,0.),('ucbs',2,0.),('uabi',3,'Aloc,Avul,Rstn'),('uaen',0,0),('umvs',0,0),('ucol',2,0.),('usca',1,.01),('umpr',2,0.),('umpm',0,0),('ufoo',0,0)]))
 for entry in VISUALS['visualUnits']:
  out.append(('hfoo',entry['id'],[('unam',3,'Графика техники'),('umdl',3,entry['model']),('uabi',3,'Aloc,Avul'),('uaen',0,0),('umvs',0,0),('umvt',3,'fly'),('umvh',2,0.),('umvf',2,0.),('ucol',2,0.),('usca',1,entry['scale']),('ushu',3,''),('ushb',3,''),('ussc',1,0.),('usin',0,0),('usid',0,0),('utar',3,''),('utyp',3,''),('ufoo',0,0),('ureq',3,''),('upgr',3,'')]))
 return out


def buff_data():
 out=[('BPSE','Rksb',[('fnam',3,'Оглушение кунаем'),('ftip',3,'Оглушение'),('fube',3,'Кунай временно оглушил цель.'),('fart',3,'ReplaceableTextures\\CommandButtons\\BTNStormBolt.blp'),('ftat',3,'Abilities\\Spells\\Human\\Thunderclap\\ThunderclapTarget.mdl'),('fta0',3,'overhead')]),('BEer','Rsmb',[('fnam',3,'Теневое подражание'),('ftip',3,'Теневое подражание'),('fube',3,'Тень удерживает на месте.'),('fart',3,'Icon_Shikamaru_KageMane.BLP'),('ftat',3,''),('fsat',3,''),('feat',3,'')])]

 for base,raw,name,art in [('BUau','Rnav','Джинчурики',''),('Broa','Rshb','Шаринган',''),('BEer','Rgac','Песчаный гроб','gaars sand.mdl'),('BNms','Rgas','Песчаный щит','gaars sand.mdl'),('BEme','Rgam','Сюкаку','')]:
  out.append((base,raw,[('fnam',3,name),('ftip',3,name),('ftat',3,art),('fta0',3,'origin'),('fsat',3,''),('feat',3,'')]))
 return out


def normalize_abilities(entries):
 """Global art/flags must use level zero. Classic ignores fake per-rank model overrides."""
 schema=json.loads((ROOT/'src/classic-skill-schema.json').read_text())['abilityFields']
 normalized=[]
 for base,raw,mods in entries:
  unique={};global_rank_values={}
  for mod in mods:
   field,kind,value=mod[:3];meta=schema[field]
   level,column=mod[3:] if len(mod)==5 else (0,0)
   if meta['repeat']==0:
    if len(mod)==5 and field in global_rank_values and global_rank_values[field]!=value:
     raise ValueError(f'{raw}: conflicting global values for {field}')
    if len(mod)==5:global_rank_values[field]=value
    level,column=0,0
   key=(field,level,column)
   unique[key]=(field,kind,value,level,column)
  normalized.append((base,raw,list(unique.values())))
 return normalized
