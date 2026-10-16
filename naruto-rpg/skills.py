"""First ten independent techniques. Original icons/models/audio; new balance and logic."""
import json
from pathlib import Path
ROOT=Path(__file__).parent
# Checked-in runtime data, rather than original protected object definitions.
SKILLS=json.loads((ROOT/'src/playable-skills.json').read_text())
HERO_SKILLS={0:','.join(s['id'] for s in SKILLS[:5]),1:','.join(s['id'] for s in SKILLS[5:])}
def ability_data():
 out=[]
 for j,row in enumerate(SKILLS):
  pos=j%5;changes=[('anam',3,row['name']),('aher',0,1),('aite',0,0),('alev',0,row['ranks']),('arlv',0,row['required_level']),('alsk',0,row['level_skip']),('aart',3,row['icon']),('arar',3,row['icon']),('ahky',3,row['key']),('arhk',3,row['key']),('abpx',0,pos if pos<4 else 1),('abpy',0,2 if pos<4 else 1),('arpx',0,pos%4),('arpy',0,pos//4),('aret',3,row['name']),('arut',3,row['description']),('aani',3,row['animation']),('areq',3,''),('arac',3,'human'),('acat',3,''),('aeat',3,'')]
  for n in range(1,row['ranks']+1):
   changes += [('atp1',3,row['name']+f' [ур. {n}]',n,0),('aub1',3,row['rank_descriptions'][n-1],n,0),('amcs',0,row['mana'][n-1],n,0),('acdn',2,row['cooldown'],n,0),('aran',2,row['range'],n,0),('atar',3,row['targets'],n,0)]
   for field,kind,column,values in row['fields']:changes.append((field,kind,values[min(n-1,len(values)-1)],n,column))
  out.append((row['base'],row['id'],changes))
 # Sharingan's bounded temporary passive bonuses; removed on expiration/death/reselection.
 for base,raw,fields in [('AEev','Rsev',[('Eev1',2,1,[.15,.20,.25])]),('AOcr','Rscr',[('Ocr1',2,1,[15.,20.,25.]),('Ocr2',2,2,[1.5,1.75,2.]),('Ocr3',2,3,[0.,0.,0.]),('Ocr4',2,4,[0.,0.,0.]),('Ocr5',0,5,[0,0,0])]),('Aamk','Rsag',[('Iagi',0,1,[6,10,14]),('Iint',0,2,[0,0,0]),('Istr',0,3,[0,0,0])])]:
  mods=[('anam',3,'Sharingan: '+raw),('aher',0,0),('aite',0,0),('alev',0,3),('abpx',0,0),('abpy',0,-11)]
  for field,kind,col,values in fields:
   for n,v in enumerate(values,1):mods.append((field,kind,v,n,col))
  out.append((base,raw,mods))
 return out

def summon_units():
 out=[]
 for n in range(1,4):
  out.append(('hkni','rt0'+str(n),[('unam',3,'Гамабунта'),('umdl',3,'Gamabunta_2.mdl'),('uico',3,'Icon_Gamabunta_Portrait.blp'),('usca',1,2.0+.25*n),('uhpm',0,1000+600*n),('ua1b',0,35+25*n),('ua1d',0,1),('ua1s',0,3),('ua1c',2,1.5),('ua1r',0,180),('umvs',0,300),('ucol',2,48.),('udef',0,2+2*n),('ufoo',0,0),('uabi',3,''),('ureq',3,''),('upgr',3,''),('uacq',2,800.)]))
 return out
