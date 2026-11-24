"""Native stock windows and synchronized server/client prices, upgrading City Shops01."""
import argparse,hashlib,json,os,struct,sys,tempfile,re
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
import install as legacy
from render_native import render,pages,SERVICES
from price_tables import patch_binary,patch_text
CATALOG=ROOT/'catalog.json'
SERVER_FILES=[Path(p) for p in ('script/MisScript/NpcScript01.lua','script/MisSdk/NpcSdk.lua','garner/garnernpc.txt','garner/garnerNPC.bin','ItemInfo.txt','ItemInfo.bin')]
MARKER='owner-city-shops-v2.json'
OPEN_ANCHOR=legacy.ANCHOR
OPEN_HOOK=b'elseif item.func == OwnerOpenTrade then\n\t\t\treturn OwnerOpenTrade(character,npc,item.p1,item.p2)\n\t\t'
BUY_ANCHOR=b'function Buy( character, npc, trade, itemtype, index1, index2, count )'
BUY_HOOK=b'\n\tif trade.owner_native_shop ~= nil then\n\t\treturn OwnerNativeBuy(character,npc,trade,itemtype,index1,index2,count)\n\tend'

def catalog():
 data=json.loads(CATALOG.read_bytes())
 if any(data==json.loads((ROOT/name).read_bytes()) for name in ('catalog-alpha47.json','catalog-alpha48.json','catalog-alpha50.json')):return data
 expected={'apparel':'OwnerClothes','fairies':'OwnerFairies','forge':'OwnerForge','tickets':'OwnerTickets','boosts':'OwnerBoosts','equipment':'OwnerEquipment'}
 if data.get('catalog_revision',0)>=56:expected.update(jewellery='OwnerJewellery',progress='OwnerProgress')
 if data.get('version')!=2 or {s['key'] for s in data.get('shops',[])}!=set(expected):raise ValueError('Неизвестный каталог магазинов')
 seen=set()
 for shop in data['shops']:
  if shop['function']!=expected[shop['key']]:raise ValueError('Не совпадает функция НПС')
  for item in shop['items']:
   if (type(item['id']) is not int or not 1<=item['id']<=65535 or item['id'] in seen
       or type(item['kind']) is not int or type(item['price']) is not int
       or item['price'] not in (1,500,1000,2000,5000,10000,20000,25000,50000,100000,200000,300000,450000,900000,1800000,2500000)):
    raise ValueError('Неверный предмет или цена магазина')
   seen.add(item['id'])
 expected_overrides=({1000:(31,4000,2000,'Blurry Blueprint'),4915:(41,8000,4000,'Withered Root')} if data.get('catalog_revision',0)>=56 else {1000:(31,3000,1500,'Blurry Blueprint'),4915:(41,5000,2500,'Withered Root')})
 if data.get('catalog_revision',0)>=56:
  expected_overrides.update({i:(31,0,0,str(28+4*(i-3088))+' Slot Inventory') for i in range(3088,3094)})
 if len(data.get('price_overrides',[]))!=len(expected_overrides):raise ValueError('Неполные цены выкупа')
 for item in data['price_overrides']:
  if (item.get('kind'),item.get('price'),item.get('npc_buyback'),item.get('name'))!=expected_overrides.get(item.get('id')):raise ValueError('Неизвестная дополнительная цена выкупа')
 return data
def offers(cat):return {i['id']:i for i in [*(i for s in cat['shops'] for i in s['items']),*cat.get('price_overrides',[])]}
def digest(raw):return hashlib.sha256(raw).hexdigest()

def verify_progression_sources(root,cat):
 if cat.get('catalog_revision',0)<56:return
 if not (root/'CharacterInfo.txt').is_file():raise ValueError('Для точного выпадения камней нужен серверный CharacterInfo.txt')
 wanted=set(cat['owner_progression']['gem_ids']);seen=set()
 for line in (root/'ItemInfo.txt').read_bytes().splitlines():
  fields=line.split(b'\t')
  if len(fields)>22 and fields[0].strip().isdigit() and int(fields[0]) in wanted:
   identity=int(fields[0])
   if int(fields[10])!=49 or int(fields[20])!=1:raise ValueError('Для выпадения по одному камню нужен неизменённый тип49 и стак1: '+str(identity))
   seen.add(identity)
 if seen!=wanted:raise ValueError('В серверной таблице отсутствуют выбранные камни')
 if cat.get('catalog_revision',0)>=57:
  blueprint=[l.split(b'\t') for l in (root/'ItemInfo.txt').read_bytes().splitlines() if l.split(b'\t',1)[0].strip()==b'1000']
  if len(blueprint)!=1 or int(blueprint[0][10])!=31 or int(blueprint[0][20])!=99:raise ValueError('Для наземных Пачкулей нужен исходный тип31/стак99 у1000')
 raw=(root/'ItemInfo.bin').read_bytes()
 if len(raw)<4 or struct.unpack_from('<I',raw)[0]!=868 or (len(raw)-4)%868:raise ValueError('Неизвестный бинарный формат предметов')
 for pos in range(4,len(raw),868):
  identity=struct.unpack_from('<I',raw,pos+4)[0]
  if identity in wanted and struct.unpack_from('<i',raw,pos+352)[0]!=1:raise ValueError('В ItemInfo.bin изменён стак камня '+str(identity))
  if cat.get('catalog_revision',0)>=57 and identity==1000 and struct.unpack_from('<i',raw,pos+352)[0]!=99:raise ValueError('В ItemInfo.bin изменён стак Пачкули1000')
 binary=root/'CharacterInfo.bin'
 if binary.exists():
  raw=binary.read_bytes()
  if len(raw)<4 or struct.unpack_from('<I',raw)[0]!=968 or (len(raw)-4)%968:raise ValueError('Неизвестный формат CharacterInfo.bin; нужна сверка выпадения камней')
  definitions={}
  for line in (root/'CharacterInfo.txt').read_bytes().splitlines():
   fields=line.split(b'\t')
   if len(fields)>47 and fields[0].strip().isdigit():
    definitions[int(fields[0])]=[(int(i),int(rate)) for i,rate in zip(fields[46].split(b','),fields[47].split(b',')) if int(i)>0 and int(rate)>0]
  for pos in range(4,len(raw),968):
   identity=struct.unpack_from('<I',raw,pos+4)[0];expected=definitions.get(identity)
   if expected is None or [struct.unpack_from('<ii',raw,pos+428+8*i) for i in range(len(expected))]!=expected:
    raise ValueError('CharacterInfo.txt и .bin расходятся: '+str(identity)+'. Сначала синхронизируй таблицы мобов.')

def implementation_digest(cat,compat=False):
 return digest(render(cat,compat=compat)+OPEN_HOOK+BUY_HOOK+(ROOT/'price_tables.py').read_bytes())

def make_overlay(cat,report):
 rows=[]
 for shop,identity,point in zip(cat['shops'],report['npc_ids'],report.get('positions_m',legacy.DEFAULT_POINTS)):
  mapping={str(item):number for number,panels in enumerate(pages(shop),1) for panel in panels for item in panel}
  handlers=['OwnerOpenTrade']+([name for _,name in SERVICES] if shop['key']=='forge' else [])
  rows.append({'key':'garner:owner-v2:'+str(identity),'source_id':identity,'map':'garner','name':shop['name'],
   'model':17,'position':[v*100+50 for v in point],'region':'Argent City','script_function':shop['function'],
   'script_found':True,'services':['trade']+(['forge','repair'] if shop['key']=='forge' else []),
   'mission_source_ids':[],'menu_handlers':handlers,'offers':[i['id'] for i in shop['items']],
   'verified_shop_binding':True,'conditions_not_evaluated':True,'source_kind':'owner-native-shops-v2',
   'menu_pages':mapping,**({'menu_labels':{str(n):section['label'] for n,section in enumerate(shop['sections'],1)}} if shop.get('sections') else {}),'live_server_seen':False})
 return {'version':2,'catalog_revision':cat.get('catalog_revision',50 if cat.get('price_overrides') else 48),'owner_progression':cat.get('owner_progression'),'fresh_fairies':True,'npcs':rows,'prices':{str(i):v['price'] for i,v in offers(cat).items()},
         'names':{str(i['id']):i['name_ru'] for s in cat['shops'] for i in s['items']},'catalog_sha256':digest(CATALOG.read_bytes()),
         **({'world_expansion':True} if report.get('world_expansion') is True else {})}

def locate_client(selected):
 p=Path(selected).expanduser()
 for root in (p,p.parent,p.parent.parent):
  for rel in ('scripts/table/iteminfo.bin','scripts/table/ItemInfo.bin'):
   if (root/rel).is_file():return root/rel
 if p.is_file() and p.name.casefold()=='iteminfo.bin':return p
 raise ValueError('Не найден клиентский scripts/table/iteminfo.bin. Здесь нужна папка ИГРЫ с Game.exe (например C:\\Games\\Пиратия Online), а не серверная resource.')

def block_span(raw,version=1):
 begin=('-- OWNER_CITY_SHOPS_V%d_BEGIN'%version).encode();end=('-- OWNER_CITY_SHOPS_V%d_END'%version).encode()
 if raw.count(begin)!=1 or raw.count(end)!=1:raise ValueError('Не найден единственный блок предыдущего патча')
 a=raw.index(begin);b=raw.index(end)+len(end)
 if b<=a:raise ValueError('Повреждены границы предыдущего блока магазинов')
 return a,b

def legacy_block_span(raw):return block_span(raw,1)

def strip_block(raw,version):
 a,b=block_span(raw,version)
 if raw[b:b+2]==b'\r\n':b+=2
 elif raw[b:b+1]==b'\n':b+=1
 return raw[:a]+raw[b:]

def strip_legacy(raw):
 a,b=legacy_block_span(raw)
 if raw[b:b+2]==b'\r\n':b+=2
 elif raw[b:b+1]==b'\n':b+=1
 return raw[:a]+raw[b:]

def configure_actors(outputs,report,cat):
 """Move only our forge actor and append one merchant; preserve all other rows."""
 if cat.get('catalog_revision',0)<55:return outputs,report
 import base64,zlib
 text,binary=SERVER_FILES[2:4];rows,records=legacy.validate_npcs(outputs[text],outputs[binary])
 safety=json.loads((ROOT.parent/'city-safety.json').read_bytes());mask=zlib.decompress(base64.b64decode(safety['safe_zlib']))
 ox,oy=safety['origin'];width,height=safety['width'],safety['height']
 ids=list(report['npc_ids']);own=set(ids);newlines=[];updated={};positions=[]
 for index,shop in enumerate(cat['shops']):
  x,y=shop['position_m'];cx,cy=x-ox,y-oy
  if not any(0<=cx+dx<width and 0<=cy+dy<height and mask[(cy+dy)*width+cx+dx] for dx in range(-2,3) for dy in range(-2,3) if dx*dx+dy*dy<=4):raise ValueError('Нет безопасного подхода к новой точке магазина')
  position=(x*100+50,y*100+50);positions.append([x,y])
  for identity,row in rows.items():
   if identity not in own and sum((a-b)**2 for a,b in zip(map(int,row[5].split(b',')),position))<10000:
    raise ValueError('Новая точка магазина занята другим НПС')
  if index<len(ids):
   identity=ids[index];row=list(rows[identity]);record=bytearray(next(r for r in records if struct.unpack_from('<I',r,4)[0]==identity))
  else:
   identity=max(rows)+1
   while identity in ids:identity+=1
   ids.append(identity);row=list(rows[18]);record=bytearray(next(r for r in records if struct.unpack_from('<I',r,4)[0]==18))
   name=shop['name'].encode('ascii');function=shop['function'].encode('ascii')
   if len(name)>=40 or len(function)>=16:raise ValueError('Слишком длинное имя торговца')
   struct.pack_into('<I',record,4,identity);struct.pack_into('<I',record,100,identity)
   record[8:48]=name.ljust(40,b'\0');record[108:236]=name.ljust(128,b'\0')
   record[394:410]=function.ljust(16,b'\0');record[410:426]=b'0'.ljust(16,b'\0')
   row[0]=str(identity).encode();row[1]=name;row[11]=function;row[12]=b'0'
  struct.pack_into('<iiiiI',record,244,*position,*position,180)
  row[5]=row[6]=f'{position[0]},{position[1]}'.encode();row[7]=b'180'
  updated[identity]=bytes(record)
  encoded=b'\t'.join(row)
  if identity in rows:
   # Preserve every byte of unrelated table rows, including line endings.
   pattern=rb'(?m)^'+str(identity).encode()+rb'\t[^\r\n]*'
   if len(re.findall(pattern,outputs[text]))!=1:raise ValueError('Неоднозначная строка НПС')
   outputs[text]=re.sub(pattern,lambda _:encoded,outputs[text])
  else:newlines.append(encoded)
 nl=b'\r\n' if b'\r\n' in outputs[text] else b'\n'
 if newlines:outputs[text]+=nl+nl.join(newlines)+nl
 outputs[binary]=outputs[binary][:4]+b''.join(updated.get(struct.unpack_from('<I',r,4)[0],r) for r in records)+b''.join(updated[i] for i in ids if i not in rows)
 legacy.validate_npcs(outputs[text],outputs[binary])
 report.update(npc_ids=ids,positions_m=positions,shops=[{k:s[k] for k in ('key','name','function')} for s in cat['shops']])
 return outputs,report

def plan_server(root,cat=None):
 cat=cat or catalog();originals={p:(root/p).read_bytes() for p in SERVER_FILES};v1=root/'owner-city-shops-v1.json'
 if b'OWNER_CITY_SHOPS_V2_BEGIN' in originals[SERVER_FILES[0]]:
  marker=root/MARKER
  if not marker.exists():raise ValueError('Есть блок02 без контрольной записи; нужна проверка')
  previous=json.loads(marker.read_bytes());match=None
  for label,path,compat in [('Alpha47',ROOT/'catalog-alpha47.json',True),('Alpha48',ROOT/'catalog-alpha48.json',False),('Alpha50',ROOT/'catalog-alpha50.json',False),('Alpha55',ROOT/'catalog-alpha55.json',False),('Alpha56',ROOT/'catalog-alpha56.json',False),('Alpha57',ROOT/'catalog-alpha57.json',False),('Alpha58',ROOT/'catalog-alpha58.json',False),('Alpha59',ROOT/'catalog-alpha59.json',False)]:
   oldcat=json.loads(path.read_bytes())
   if previous.get('catalog_sha256')==digest(path.read_bytes()) and previous.get('implementation_sha256')==implementation_digest(oldcat,compat=compat):match=(label,oldcat,compat);break
  if match is None:
   raise ValueError('Неизвестная версия установленных магазинов02; нужна проверка обновления')
  oldlabel,oldcat,oldcompat=match
  if set(previous['installed_sha256'])!={p.as_posix() for p in SERVER_FILES}:raise ValueError('Неполная контрольная запись02')
  a,b=block_span(originals[SERVER_FILES[0]],2)
  if originals[SERVER_FILES[0]][a:b].replace(b'\r\n',b'\n')!=render(oldcat,compat=oldcompat).rstrip(b'\n'):
   raise ValueError('Изменён сам блок магазинов02 в NpcScript01.lua; обновление остановлено')
  sdk=originals[SERVER_FILES[1]].replace(b'\r\n',b'\n')
  if sdk.count(OPEN_HOOK+OPEN_ANCHOR)!=1 or sdk.count(BUY_ANCHOR+BUY_HOOK)!=1:
   raise ValueError('Изменены обработчики магазинов02 в NpcSdk.lua; нужна проверка')
  rows,_=legacy.validate_npcs(originals[SERVER_FILES[2]],originals[SERVER_FILES[3]])
  if len(previous['npc_ids'])!=len(oldcat['shops']) or len(set(previous['npc_ids']))!=len(oldcat['shops']):raise ValueError('Не подтверждены прежние НПС02')
  oldpoints=previous.get('positions_m',legacy.DEFAULT_POINTS)
  for shop,identity,point in zip(oldcat['shops'],previous['npc_ids'],oldpoints):
   row=rows[identity];pos=[v*100+50 for v in point]
   if (row[11].strip()!=shop['function'].encode() or row[1].strip()!=shop['name'].encode() or int(row[3])!=17
       or list(map(int,row[5].split(b',')))!=pos or list(map(int,row[6].split(b',')))!=pos):raise ValueError('Изменена привязка НПС02')
  outputs=dict(originals);nl=b'\r\n' if b'\r\n' in originals[SERVER_FILES[0]] else b'\n'
  outputs[SERVER_FILES[0]]=strip_block(originals[SERVER_FILES[0]],2)+nl+render(cat).replace(b'\n',nl)
  for path,patcher in ((Path('ItemInfo.txt'),patch_text),(Path('ItemInfo.bin'),patch_binary)):outputs[path]=patcher(originals[path],offers(cat))
  report=dict(previous,version=2,catalog_sha256=digest(CATALOG.read_bytes()),implementation_sha256=implementation_digest(cat),
              item_count=sum(len(s['items']) for s in cat['shops']),upgraded_from=oldlabel,
              preserved_changed_files=[p.as_posix() for p in SERVER_FILES if digest(originals[p])!=previous['installed_sha256'][p.as_posix()]])
  outputs,report=configure_actors(outputs,report,cat)
  return originals,outputs,report
 if v1.exists():
  previous=json.loads(v1.read_bytes())
  required={p.as_posix() for p in SERVER_FILES[:4]}
  if set(previous['installed_sha256'])!=required:raise ValueError('Неполная контрольная запись предыдущей установки')
  oldcat=json.loads((ROOT.parent/'catalog.json').read_bytes())
  if previous.get('catalog_sha256')!=digest((ROOT.parent/'catalog.json').read_bytes()):
   raise ValueError('Неизвестный каталог предыдущего патча; нужна проверка обновления')
  script_raw=originals[SERVER_FILES[0]];a,b=legacy_block_span(script_raw)
  expected=legacy.render(oldcat).rstrip(b'\n')
  if script_raw[a:b].replace(b'\r\n',b'\n')!=expected:
   raise ValueError('Изменён сам блок старых магазинов в NpcScript01.lua. Автоматическое обновление остановлено; сохрани файл для проверки.')
  changed=[p.as_posix() for p in SERVER_FILES[:4] if digest(originals[p])!=previous['installed_sha256'][p.as_posix()]]
  outputs={p:originals[p] for p in SERVER_FILES[:4]};report={k:previous[k] for k in ('center_m','positions_m','npc_ids','shops')}
  report['preserved_changed_files']=changed
  if len(report['npc_ids'])!=5 or len(set(report['npc_ids']))!=5:raise ValueError('Не подтверждены пять прежних НПС')
  rows,records=legacy.validate_npcs(outputs[SERVER_FILES[2]],outputs[SERVER_FILES[3]])
  for shop,identity,point in zip(cat['shops'],report['npc_ids'],report.get('positions_m',legacy.DEFAULT_POINTS)):
   row=rows[identity];position=[v*100+50 for v in point]
   if (row[11].strip()!=shop['function'].encode() or row[1].strip()!=shop['name'].encode()
       or int(row[3])!=17 or int(row[7])!=180
       or list(map(int,row[5].split(b',')))!=position or list(map(int,row[6].split(b',')))!=position):
    raise ValueError('Не совпадают пять НПС предыдущего патча')
 else:
  _,outputs,report=legacy.plan(root,legacy.DEFAULT_CENTER)
 script,sdk=SERVER_FILES[:2]
 nl=b'\r\n' if b'\r\n' in outputs[script] else b'\n'
 outputs[script]=strip_legacy(outputs[script])+nl+render(cat).replace(b'\n',nl)
 sdkraw=outputs[sdk];sdknl=b'\r\n' if b'\r\n' in sdkraw else b'\n';oldhook=legacy.HOOK.replace(b'\n',sdknl)
 if sdkraw.count(oldhook)!=1 or sdkraw.count(oldhook+OPEN_ANCHOR)!=1:
  raise ValueError('Изменена ветка старого магазина в NpcSdk.lua; нужна проверка обновления')
 sdkraw=sdkraw.replace(oldhook,b'')
 if sdkraw.count(OPEN_ANCHOR)!=1 or sdkraw.count(BUY_ANCHOR)!=1:raise ValueError('Другая версия NpcSdk.lua; нужна проверка')
 outputs[sdk]=sdkraw.replace(OPEN_ANCHOR,OPEN_HOOK.replace(b'\n',sdknl)+OPEN_ANCHOR).replace(BUY_ANCHOR,BUY_ANCHOR+BUY_HOOK.replace(b'\n',sdknl))
 items=offers(cat)
 outputs[Path('ItemInfo.txt')]=patch_text(originals[Path('ItemInfo.txt')],items)
 outputs[Path('ItemInfo.bin')]=patch_binary(originals[Path('ItemInfo.bin')],items)
 report.update(version=2,catalog_sha256=digest(CATALOG.read_bytes()),implementation_sha256=implementation_digest(cat),native_trade_windows=True,prices_scope='global selected item prices; client synchronized; other item fields unchanged',
               item_count=sum(len(s['items']) for s in cat['shops']),positions_m=[list(p) for p in legacy.DEFAULT_POINTS])
 outputs,report=configure_actors(outputs,report,cat)
 return originals,outputs,report

def atomic(path,raw):
 descriptor,name=tempfile.mkstemp(prefix=path.name+'.shop2-',suffix='.tmp',dir=path.parent)
 try:
  with os.fdopen(descriptor,'wb') as stream:stream.write(raw)
  os.replace(name,path)
 finally:Path(name).unlink(missing_ok=True)

def apply_files(changes,backup):
 backup.mkdir(parents=True,exist_ok=False);old={p:p.read_bytes() if p.exists() else None for p in changes}
 for index,(p,raw) in enumerate(old.items()):
  if raw is None:continue
  saved=backup/(str(index)+'-'+p.name);saved.write_bytes(raw)
  if saved.read_bytes()!=raw:raise OSError('Не подтверждена резервная копия')
 (backup/'restore-index.json').write_text(json.dumps([{'path':str(p),'backup':str(index)+'-'+p.name if old[p] is not None else None} for index,p in enumerate(old)],ensure_ascii=False,indent=2))
 written=[]
 try:
  for p,raw in changes.items():atomic(p,raw);written.append(p)
 except BaseException:
  for p in reversed(written):
   if old[p] is None:p.unlink(missing_ok=True)
   else:atomic(p,old[p])
  raise
 return old

def install(server,client,apply=False,bot_assets=None):
 root=legacy.locate(server);clientfile=locate_client(client);cat=catalog();items=offers(cat);marker=root/MARKER
 verify_progression_sources(root,cat)
 craft_changes={};craft_report=None
 if cat.get('catalog_revision',0)>=58:
  from forge_success import plan as forge_plan
  craft_changes,craft_report=forge_plan(root)
 clientraw=clientfile.read_bytes();clientoutput=patch_binary(clientraw,items)
 if marker.exists() and json.loads(marker.read_bytes()).get('catalog_sha256')==digest(CATALOG.read_bytes()):
  previous=json.loads(marker.read_bytes())
  if previous.get('implementation_sha256')!=implementation_digest(cat):raise ValueError('Изменилась версия обработчиков магазинов; нужна проверка обновления')
  if not all(digest((root/p).read_bytes())==h for p,h in previous['installed_sha256'].items()):raise ValueError('После нового патча изменились серверные файлы; нужна проверка')
  if clientoutput==clientraw:
   assets=Path(bot_assets) if bot_assets else ROOT.parents[1]/'assets'
   overlay=assets/'owner-city-shops.json'
   matches=False
   try:matches=overlay.exists() and json.loads(overlay.read_bytes())==make_overlay(cat,previous)
   except (OSError,ValueError):pass
   craft_matches=not craft_report or previous.get('forge_success',{}).get('installed_sha256')==craft_report['installed_sha256']
   if (not (assets/'world-npcs.json').exists() or matches) and not craft_changes and craft_matches:
    return dict(previous,already_installed=True)
  serveroutputs={};report=dict(previous)
 else:
  _,serveroutputs,report=plan_server(root,cat)
 changes={root/p:raw for p,raw in serveroutputs.items()};changes[clientfile]=clientoutput
 changes.update(craft_changes)
 if craft_report:report['forge_success']=craft_report
 assets=Path(bot_assets) if bot_assets else ROOT.parents[1]/'assets'
 if cat.get('catalog_revision',0)>=56 and (root.parent/'GameServer.cfg').exists():
  import importlib.util
  module_path=assets.parent/'src/configure_dungeon_maps.py'
  if not module_path.exists():raise ValueError('Нужен полный комплект Alpha56 с утилитой настройки карт')
  spec=importlib.util.spec_from_file_location('owner56_maps',module_path);maps=importlib.util.module_from_spec(spec);spec.loader.exec_module(maps)
  _,map_changes,map_report=maps.plan(root.parent)
  changes.update(map_changes);report['dungeon_maps']=map_report
 if cat.get('catalog_revision',0)>=57:
  if (root.parent/'GameServer.cfg').exists():
   from loot_protection import plan as protection_plan
   protection_changes,protection_report=protection_plan(root.parent,changes)
   changes.update(protection_changes);report['loot_protection']=protection_report
  else:
   report['loot_protection']={'requires_manual_configuration':True,'setting':'item_prot_time = 1','warning':'Zero means permanent protection; configure all active GameServer processes.'}
 if (assets/'world-npcs.json').exists():
  changes[assets/'owner-city-shops.json']=(json.dumps(make_overlay(cat,report),ensure_ascii=False,indent=2)+'\n').encode()
  report['bot_knowledge_updated']=True
 report.update(applied=False,client_path=str(clientfile),client_sha256=digest(clientoutput))
 if not apply:return report
 changes={path:raw for path,raw in changes.items() if not path.exists() or path.read_bytes()!=raw}
 stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f');backup=root/'owner-city-shops-backups'/('v2-'+stamp)
 old=apply_files(changes,backup)
 previous_marker=marker.read_bytes() if marker.exists() else None
 try:
  report.update(applied=True,backup=str(backup),installed_sha256={p.as_posix():digest((root/p).read_bytes()) for p in SERVER_FILES})
  atomic(marker,(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode())
 except BaseException:
  for path,raw in old.items():
   if raw is None:path.unlink(missing_ok=True)
   else:atomic(path,raw)
  if previous_marker is None:marker.unlink(missing_ok=True)
  else:atomic(marker,previous_marker)
  raise
 return report

def install_client(selected,apply=False):
 p=locate_client(selected);raw=p.read_bytes();output=patch_binary(raw,offers(catalog()))
 if output==raw:return {'already_installed':True,'path':str(p)}
 if apply:
  stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f');apply_files({p:output},p.parent/('owner-shop-prices-backup-'+stamp))
 return {'applied':apply,'path':str(p),'sha256':digest(output)}

def main():
 if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('server',nargs='?');p.add_argument('--client');p.add_argument('--client-only',action='store_true');p.add_argument('--apply',action='store_true');a=p.parse_args()
 try:
  if a.apply and sys.platform=='win32':
   import subprocess
   listing=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True,errors='replace').casefold()
   if '"game.exe"' in listing or (not a.client_only and '"gameserver.exe"' in listing):raise ValueError('Сначала закрой клиент Game.exe и останови GameServer.exe')
  if a.client_only:
   result=install_client(a.client or a.server or input('Папка клиента: ').strip().strip('"'),a.apply)
  else:
   server=a.server or input('Папка GameServer или resource: ').strip().strip('"')
   server=legacy.locate(server)
   print('Найдена серверная resource: '+str(server))
   client=a.client or input('Папка ИГРЫ с Game.exe и scripts (НЕ серверная resource): ').strip().strip('"')
   result=install(server,client,a.apply)
  print(json.dumps(result,ensure_ascii=False,indent=2));print('Готово. Запусти сервер и клиент заново.' if a.apply else 'Предпросмотр: файлы не изменены.')
 except (OSError,ValueError,KeyError,struct.error) as error:print('Ошибка: '+str(error));return 1
 return 0
if __name__=='__main__':raise SystemExit(main())
