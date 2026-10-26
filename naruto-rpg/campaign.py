"""Independent full-story chapter runtime data; source correspondence is explicit in campaign-source.json."""
import json
from pathlib import Path
ROOT=Path(__file__).parent
DATA=json.loads((ROOT/'src/campaign-source.json').read_text())
MODELS=[('Хирузен Сарутоби','Sandaime.mdl',90000,160),('Какаши','KakashiNew.mdl',30000,120),('Майто Гай','Gai.mdl',30000,140),('Итачи','Itachi.mdl',55000,170),('Кисамэ','Kisame.mdl',60000,180),('Дзиробо','Jiroubu.mdl',30000,140),('Кидомару','Kidoumaru.mdl',26000,110),('Сакон','Sakon.mdl',30000,130),('Тауюя','Tayuya.mdl',26000,110),('Кимимаро','Kimimaro.mdl',40000,170),('Саске — проклятая печать','SasukeCursed.mdl',60000,180),('Кабуто','Kabuto.mdl',65000,170),('Манда','Manda.mdl',120000,220),('Орочимару','Orochimaru.mdl',100000,210),('Джирайя','Jiraiya.mdl',20000,130),('Ниндзя Звука','SoundJounin.mdl',2200,65),('Ниндзя Песка','SandJounin.mdl',2400,65),('Ниндзя Листа','LeafJounin.mdl',2600,70),('Бочка','Buildings\\Other\\BarrelsUnit0\\BarrelsUnit0.mdl',120,0),('Валун','Doodads\\Terrain\\RockChunks\\RockChunks0.mdl',5000,0)]
MODELS += [('Двойник: '+name,model,5000,70) for name,fn,a,b,model in DATA['cloneRooms']]
MODELS += [('Наруто — сюжетный персонаж','Naruto.mdl',50000,160)]
MODELS += [('Асумa','AsumaNew.mdl',20000,149),('Куренай','KurenaiNew.mdl',20000,149),('Анко','Anko.mdl',20000,149),('Медик Листа','LeafJounin.mdl',3000,0),('Джирайя','Jiraiya.mdl',60000,349),('АНБУ','ANBU_2.mdl',5000,149),('Баки','SandJounin.mdl',10000,149),('Трёхголовая змея','Manda.mdl',30000,499),('Какаши — Акацуки','KakashiNew.mdl',10000,299),('Гай — Акацуки','Gai.mdl',10000,299),('Укон','Sakon.mdl',60000,349)]
def raw(n):return ('C' if 20<=n<=27 else 'c')+format(n,'03X')
def units():
 out=[]
 for n,(name,model,hp,damage) in enumerate(MODELS):
  native=__import__('npc_source').body(n,name)
  if native:
   if n in (17,32,34):
    base,rawid,mods=native
    # Match the hfoo-based invading ninjas: native20+6d3 bounty, not zero.
    mods=list({m[0]:m for m in mods+[('ubba',0,20),('ubdi',0,6),('ubsi',0,3)]}.values())
    native=(base,rawid,mods)
   patch=json.loads((ROOT/'src/mentor-balance46.json').read_text()).get(str(n),{})
   if patch:
    base,rawid,mods=native
    mods=list({m[0]:m for m in list(mods)+[(key,0,value)for key,value in patch.items()]}.values())
    native=(base,rawid,mods)
   hp48=json.loads((ROOT/'src/balance48.json').read_text())['npcHPOverrides'].get(str(n))
   if hp48 is not None:
    base,rawid,mods=native
    native=(base,rawid,list({m[0]:m for m in list(mods)+[('uhpm',0,hp48)]}.values()))
   out.append(native)
   continue
  scale=.8 if n!=12 else 1.2
  mods=[('unam',3,name),('umdl',3,model),('uico',3,'ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp'),('usca',1,scale),('uhpm',0,hp),('uhpr',2,0.),('ua1b',0,damage),('ua1d',0,1),('ua1s',0,3),('ua1c',2,1.5),('ua1r',0,140),('umvs',0,310),('ucol',2,24.),('udef',0,6),('umpm',0,3000),('umpi',0,3000),('umpr',2,10.),('uabi',3,'Cbol,Cwav,Cstm'),('uaen',0,1),('usnd',3,''),('ucs1',3,'WoodHeavyBash'),('ucs2',3,''),('ulev',0,10),('ufoo',0,0),('upgr',3,''),('ureq',3,''),('ubba',0,0),('ubdi',0,0),('ubsi',0,0)]
  if n in (0,18,19):mods.extend([('umvs',0,0),('uabi',3,''),('uaen',0,0 if n>=18 else 1),('ucol',2,16.)])
  if n==18:mods.extend([('usca',1,2.),('uhpm',0,100),('uico',3,'ReplaceableTextures\\CommandButtons\\BTNBarrel.blp')])
  if n==32:mods.extend([('uabi',3,'Cmed'),('uaen',0,0)])
  if n==14:mods.extend([('uabi',3,'Avul'),('uaen',0,0)])
  if n in (6,8,15,16):mods.extend([('ua1w',3,'missile'),('ua1r',0,550),('ua1m',3,'Kunai.mdl'),('ua1z',0,1100)])
  seed=json.loads((ROOT/'src/campaign-npc-seeds.json').read_text()).get(str(n),{})
  mods=[(k,t,seed.get(k,v)) for k,t,v in mods]
  mods=list({m[0]:m for m in mods}.values())
  if n==28:
   # The absent-player Naruto fallback must be a real hero for native level60.
   mods += [('upro',3,'Наруто'),('uhab',3,''),('upra',3,'STR'),('ustr',0,20),('uagi',0,20),('uint',0,20),('ustp',2,2.),('uagp',2,1.),('uinp',2,1.5)]
  out.append(('Hpal'if n==28 else'hfoo',raw(n),mods))
 final=json.loads((ROOT/'src/balance48.json').read_text())['finalOrochimaru']
 base,_,mods=next(row for row in out if row[1]==raw(final['kind']))
 out.append((base,final['unitId'],[(k,t,final['hp']if k=='uhpm'else v)for k,t,v in mods]))
 for f in json.loads((ROOT/'src/village-fountains-source.json').read_text())['fountains']:
  mods=[(m['id'],m['variableType'],m['value'].replace('\\\\','\\')if m['id']=='umdl'else m['value'])for m in f['effectiveModifications']]
  mods.extend([('unam',3,'Фонтан силы'if f['doubleHealth']else'Фонтан восстановления'),('uabi',3,('Crg2'if f['doubleHealth']else'ACnr')+',ANre,Avul')])
  out.append(('nfnp',f['newId'],list({m[0]:m for m in mods}.values())))
 return out

def abilities():
 out=[('ACnr','Crg2',[('anam',3,'Исходное восстановление здоровья x2'),('aher',0,0),('alev',0,1),('Oar1',2,.02,1,1),('areq',3,''),('aefs',3,''),('aefl',3,'')])]
 for base,rawid,name,order,mods in [
 ('Ahea','Cmed','Медицинская техника','heal',[('Hea1',2,350.,1,1),('aran',2,650.,1,0),('atar',3,'friend,ground,air,organic',1,0)]),
 ('AHtb','Cbol','Направленная техника','thunderbolt',[('Htb1',2,350.,1,1),('amat',3,'Kunai.mdl')]),
 ('AOsh','Cwav','Удар чакры','shockwave',[('Osh1',2,250.,1,1),('amat',3,'WindAttack.mdl')]),
 ('AOws','Cstm','Удар по области','stomp',[('Wrs1',2,250.,1,1)])]:
  out.append((base,rawid,[('anam',3,name),('aher',0,0),('aite',0,0),('alev',0,1),('areq',3,''),('amcs',0,100,1,0),('acdn',2,8.,1,0),('adur',2,1.,1,0),('ahdu',2,.6,1,0),('aani',3,'spell'),('aefs',3,''),('aefl',3,'')]+mods))
 return out

def generated():
 lines=[]
 nav=json.loads((ROOT/'src/campaign-navigation.json').read_text())
 animations=json.loads((ROOT/'src/model-animations.json').read_text())
 for n,row in enumerate(MODELS):
  model=row[1].replace('.mdl','.mdx'); seq=next((x['animations'] for x in animations if x['path'].lower()==model.lower()),[])
  cast=next((i for i,a in enumerate(seq) if (a if isinstance(a,str) else a['name']).lower().startswith('spell')),next((i for i,a in enumerate(seq) if 'attack' in (a if isinstance(a,str) else a['name']).lower()),0))
  lines += [f"    set CampaignUnit[{n}]='{raw(n)}'",f'    set CampaignAnimation[{n}]={cast}']
 for stage,seats in json.loads((ROOT/'src/arena-stands-source.json').read_text())['stages'].items():
  for p,seat in enumerate(seats):
   n=p+(12 if int(stage)==11 else 0)
   lines.extend([f"    set ArenaSeatX[{n}]={float(seat['x'])}",f"    set ArenaSeatY[{n}]={float(seat['y'])}"])
 for wave in json.loads((ROOT/'src/invasion-waves-source.json').read_text())['lanes']:
  for key in ['origin','destination','kind','role','period','delay']:
   value=float(wave[key])if key in ['period','delay']else wave[key]
   lines.append(f"    set CampaignWave{key.title()}[{wave['lane']}]={value}")
 for st in DATA['stages']:
  n=st['id'];p=nav[str(n)];bounds=p['bounds']
  vals={'CampaignName':st['name'],'CampaignIntro':st['intro'],'CampaignMusic':-1 if st['music'] is None else st['music'],'CampaignLimit':float(st['seconds']),'CampaignX':float(p['spawn'][0]),'CampaignY':float(p['spawn'][1]),'CampaignTX':float(p['target'][0]),'CampaignTY':float(p['target'][1]),'CampaignMinX':float(bounds[0]),'CampaignMinY':float(bounds[1]),'CampaignMaxX':float(bounds[2]),'CampaignMaxY':float(bounds[3])}
  for key,value in vals.items():lines.append(f'    set {key}[{n}]='+json.dumps(value,ensure_ascii=False))
 for j,p in enumerate(nav['barrels']):lines += [f'    set CampaignBarrelX[{j}]={float(p[0])}',f'    set CampaignBarrelY[{j}]={float(p[1])}']
 layout=json.loads((ROOT/'src/invasion20-layout.json').read_text())
 for j,pos in enumerate(layout['defenders']):lines += [f'    set CampaignDefenderX[{j}]={float(pos[0])}',f'    set CampaignDefenderY[{j}]={float(pos[1])}']
 for row in layout['reserves']:
  j=row['kind'];pos=row['position'];lines += [f'    set CampaignReserveX[{j}]={float(pos[0])}',f'    set CampaignReserveY[{j}]={float(pos[1])}']
 for j,pos in enumerate(layout['waveSpawns']):lines += [f'    set CampaignWaveSpawnX[{j}]={float(pos[0])}',f'    set CampaignWaveSpawnY[{j}]={float(pos[1])}']
 for j,p in enumerate(nav['routes']):lines += [f'    set CampaignRouteX[{j}]={float(p[0])}',f'    set CampaignRouteY[{j}]={float(p[1])}']
 for j,(p,kind) in enumerate(zip(nav['five'],[5,6,8,7,9])):lines += [f'    set CampaignFiveX[{j}]={float(p[0])}',f'    set CampaignFiveY[{j}]={float(p[1])}',f'    set CampaignFiveType[{j}]={kind}']
 invasion=json.loads((ROOT/'src/invasion-source.json').read_text())
 for key,name in [('leafDefenders','Leaf'),('anbuDefenders','Anbu')]:
  for n,row in enumerate(invasion[key]):
   for suffix,field in [('X','x'),('Y','y'),('Facing','facing')]:lines.append(f'    set Campaign{name}{suffix}[{n}]={float(row[field])}')
 for n,row in enumerate(invasion['villageShops']):lines.extend([f"    set StoryShopX[{n}]={row['x']}",f"    set StoryShopY[{n}]={row['y']}"])
 for n,b in enumerate(invasion['medicRegions'].values()):lines.extend([f'    set CampaignMedicX[{n}]={(b[0]+b[2])/2}',f'    set CampaignMedicY[{n}]={(b[1]+b[3])/2}'])
 for n,key in enumerate(['SL','UJ','WQ','YQ','FM','DP','VM']):
  b=invasion['deploymentRegions'][key];lines.extend([f'    set CampaignSupportX[{n}]={(b[0]+b[2])/2}',f'    set CampaignSupportY[{n}]={(b[1]+b[3])/2}'])
 return '\n'+'\n'.join(lines)
