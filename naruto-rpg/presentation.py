"""Explicit, Classic-compatible combat art and source first-chapter XP constants."""
import json
from pathlib import Path
ROOT=Path(__file__).parent
RANGED={2:('Shurikens.mdl',700),5:('Kunai.mdl',700),6:('Shurikens.mdl',700),9:('gaars sand.mdl',700),11:('WindAttack.mdl',700)}
def combat(slot):
 mods=[('ua1c',2,2.),('ua1w',3,'normal'),('udp1',2,.4),('ubs1',2,.55),('ucs1',3,'RockHeavyBash' if slot in (4,8) else 'WoodHeavyBash')]
 if slot in RANGED:
  model,distance=RANGED[slot]
  mods=[('ua1c',2,1.93),('ua1w',3,'missile'),('ua1r',0,distance),('ua1m',3,model),('ua1z',0,1400),('udp1',2,.5),('ubs1',2,.8),('ucs1',3,'WoodLightBash')]
 return mods

def misc():
 return ('[Misc]\nMaxHeroLevel=60\nMaxUnitLevel=100\nHeroFactorXP=90,90,70,70,70,70,70,50,40,40,40,40,40,40,40,40,40,40,30\nHeroExpRange=2000.0\nMaxUnitSpeed=480\n').encode()

def scenery():
 from classic_formats import objects
 data=json.loads((ROOT/'src/location/scenery-objects.json').read_text())
 original=[];custom=[]
 for table,out in [('originalTable',original),('customTable',custom)]:
  for row in data[table]['objects']:
   mods=[(m['id'],m['variableType'],m['value']) for m in row['modifications']]
   if row['oldId'] in ('LTlt','CTtc'):
    file='Doodads\\Terrain\\LordaeronTree\\LordaeronTree' if row['oldId']=='LTlt' else 'Doodads\\Terrain\\AshenvaleTree\\AshenvaleTree'
    patch={'bfil':(3,file),'bvar':(0,10),'btxi':(0,31 if row['oldId']=='LTlt' else 32),'btxf':(3,'ReplaceableTextures\\LordaeronTree\\LordaeronSummerTree' if row['oldId']=='LTlt' else 'ReplaceableTextures\\AshenvaleTree\\AshenTree'),'bmis':(1,.8),'bmas':(1,1.2),'bmap':(1,0.),'bmar':(1,0.),'bvcr':(0,255),'bvcg':(0,255),'bvcb':(0,255)}
    mods=[m for m in mods if m[0] not in patch]+[(k,t,v) for k,(t,v) in patch.items()]
   out.append((row['oldId'],row['newId'],mods))
 return objects(custom,original_entries=original)
