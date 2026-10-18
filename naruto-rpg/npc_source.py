"""Source-native NPC objects and isolated source spell callbacks; no source scenario triggers."""
from pathlib import Path
import json
ROOT=Path(__file__).parent
DATA=json.loads((ROOT/'src/npc-native-source.json').read_text())
ASSETS={r['path'].lower()for r in json.loads((ROOT/'src/asset-manifest.json').read_text())}
def icon(field,value):
 if field in ['uico','aart','arar','fart'] and isinstance(value,str) and value.lower().endswith('.blp') and value.lower()not in ASSETS and not value.lower().startswith(('replaceabletextures\\','ui\\')):
  return 'ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp'
 return value
def entries(key):
 out=[]
 for o in DATA[key]:
  mods=[]
  for m in o['modifications']:
   row=(m['id'],m['variableType'],icon(m['id'],m['value']))
   if key=='abilities':row+=(m['levelOrVariation'],m['dataPointer'])
   mods.append(row)
  if key=='units':
   mods.extend([('usnd',3,''),('ucs1',3,'WoodHeavyBash'),('ucs2',3,'')])
   mods=list({m[0]:m for m in mods}.values())
  out.append((o['oldId'],o['newId'],mods))
 return out

def body(kind,name):
 row=DATA['profiles'].get(str(kind))
 if not row:return None
 o=row['body'];mods=[(m['id'],m['variableType'],icon(m['id'],m['value']))for m in o['modifications']]
 mods.extend([('unam',3,name),('uabi',3,','.join(row['skills'])),('usnd',3,''),('ucs1',3,'WoodHeavyBash'),('ucs2',3,'')])
 return o['oldId'],o['newId'],list({m[0]:m for m in mods}.values())

ORDERS={'AHtb':('thunderbolt',1),'ANsb':('thunderbolt',1),'ANfb':('thunderbolt',1),'ANbf':('breathoffire',2),'ANbr':('battleroar',0),'ANbl':('blink',2),'AHtc':('thunderclap',0),'AHwe':('waterelemental',0),'AOmi':('mirrorimage',0),'ANst':('stampede',2),'ANc3':('clusterrockets',2),'AHdr':('drain',3),'AEmb':('manaburn',1),'AOcl':('chainlightning',1),'AEsh':('shadowstrike',1),'AUsl':('sleep',1),'ACcr':('cripple',1),'ACwb':('web',1),'AUim':('impale',2),'AUin':('inferno',2),'Aenw':('ensnare',1),'AOwk':('windwalk',0),'AOw2':('stomp',0),'ANms':('manashieldon',0),'AEfk':('fanofknives',0),'AEer':('entanglingroots',1),'Acyc':('cyclone',1),'Arsg':('spiritbeast',0),'ANsi':('silence',2),'AEme':('metamorphosis',0),'AOsh':('shockwave',2)}
def get(o,key,rank,default):
 mods=[m for m in o['modifications']if m['id']==key and m['levelOrVariation']in(0,rank)]
 return mods[-1]['value']if mods else default

def generated():
 objects={o['newId']:o for o in DATA['abilities']};lines=[]
 for n,role in enumerate([4,3,5,7,8,9,10,11]):lines.append(f"    set NPCSourceTypeDummy[{n+20}]='R{role:03X}'")
 for kind,p in DATA['profiles'].items():
  n=int(kind);active=0;init=[]
  for raw,rank in p['skills'].items():
   init.extend([f"    call UnitAddAbility(u,'{raw}')",f"    call SetUnitAbilityLevel(u,'{raw}',{rank})"])
   o=objects.get(raw)
   if not o or (o['oldId']not in ORDERS and o['oldId']!='ANcl'):continue
   if o['oldId']=='ANcl':
    order=str(get(o,'Ncl6',rank,'channel'));mode=int(get(o,'Ncl2',rank,0))
   else:
    order,mode=ORDERS[o['oldId']]
   if raw in ['A012','A00F']:continue
   if raw=='A02D':mode=4
   assert active<8,(kind,active)
   i=n*8+active;active+=1
   hold=max(1.,float(get(o,'acas',rank,.5))+.3)
   if o['oldId']in ['ANst','AHdr','AOw2']:hold=max(hold,float(get(o,'adur',rank,3.)))
   channel_guard=o['oldId']=='ANcl' and float(get(o,'Ncl1',rank,0.))>30.
   if o['oldId']=='ANcl':hold=max(hold,float(get(o,'Ncl1',rank,1.)))
   radius=float(get(o,'aare',rank,250.))
   if o['oldId']in ['AHwe','Arsg','AOmi','ANbr','ANms','AEme']or raw=='A029':radius=1100.
   vals={'NPCChannelGuard':str(channel_guard).lower(),'NPCRank':str(rank),'NPCOrderId':str(852600 if o['oldId']=='Arsg'else 0),'NPCAbility':"'"+raw+"'",'NPCOrder':json.dumps(order),'NPCTarget':str(mode),'NPCRange':str(float(get(o,'aran',rank,700.))),'NPCRadius':str(radius),'NPCCost':str(float(get(o,'amcs',rank,100.))),'NPCCooldown':str(float(get(o,'acdn',rank,8.))),'NPCHold':str(hold)}
   for a,v in vals.items():lines.append(f'    set {a}[{i}]={v}')
  lines.append(f'    set NPCSpellCount[{n}]={active}')
 return '\n'+'\n'.join(lines)

def initialize():
 lines=['function NPCInitialize takes unit u, integer kind returns nothing','    call NPCSourceBind(u,kind)','    call NPCBindAliases(u,kind)']
 for kind,p in DATA['profiles'].items():
  lines.append('    if kind=='+kind+' then')
  for raw,rank in p['skills'].items():
   if kind=='8' and raw=='S02B':continue
   lines.extend([f"        call UnitAddAbility(u,'{raw}')",f"        call SetUnitAbilityLevel(u,'{raw}',{rank})"])
  if kind=='8':lines.append("        call UnitRemoveAbility(u,'S02B')")
  lines.append('    endif')
 lines.extend([
  '    if kind==11 and CampaignStage==26 then',
  "        call UnitAddAbility(u,'AInv')",
  "        call UnitAddItemByIdSwapped('Nlra',u)",
  "        call UnitAddItemByIdSwapped('Nlsh',u)",
  "        call UnitAddItemByIdSwapped('Nnot',u)",
  "        call UnitAddItemByIdSwapped('Nlku',u)",
  "        call UnitAddItemByIdSwapped('Nnot',u)",
  "        call UnitAddItemByIdSwapped('Nlra',u)",
  '    endif','endfunction'])
 return '\n'.join(lines)
