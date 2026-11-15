"""Native stock windows and synchronized server/client prices, upgrading City Shops01."""
import argparse,hashlib,json,os,struct,sys,tempfile
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
 data=json.loads(CATALOG.read_text());expected={'apparel':'OwnerClothes','fairies':'OwnerFairies','forge':'OwnerForge','tickets':'OwnerTickets','boosts':'OwnerBoosts'}
 if data.get('version')!=2 or {s['key'] for s in data.get('shops',[])}!=set(expected):raise ValueError('Неизвестный каталог магазинов')
 seen=set()
 for shop in data['shops']:
  if shop['function']!=expected[shop['key']]:raise ValueError('Не совпадает функция НПС')
  for item in shop['items']:
   if (type(item['id']) is not int or not 1<=item['id']<=65535 or item['id'] in seen
       or type(item['kind']) is not int or type(item['price']) is not int
       or item['price'] not in (500,1000,2000,5000,10000,20000,50000,300000)):
    raise ValueError('Неверный предмет или цена магазина')
   seen.add(item['id'])
 for item in data.get('price_overrides',[]):
  if item!={'id':1000,'kind':31,'price':1000,'npc_buyback':500,'name_ru':'Чертеж Пачкули','name_en':'Blurry Blueprint','name':'Blurry Blueprint','stack':99}:raise ValueError('Неизвестная дополнительная цена выкупа')
 return data
def offers(cat):return {i['id']:i for i in [*(i for s in cat['shops'] for i in s['items']),*cat.get('price_overrides',[])]}
def digest(raw):return hashlib.sha256(raw).hexdigest()

def implementation_digest(cat,compat=False):
 return digest(render(cat,compat=compat)+OPEN_HOOK+BUY_HOOK+(ROOT/'price_tables.py').read_bytes())

def make_overlay(cat,report):
 rows=[]
 for shop,identity,point in zip(cat['shops'],report['npc_ids'],legacy.DEFAULT_POINTS):
  mapping={str(item):number for number,panels in enumerate(pages(shop),1) for panel in panels for item in panel}
  handlers=['OwnerOpenTrade']+([name for _,name in SERVICES] if shop['key']=='forge' else [])
  rows.append({'key':'garner:owner-v2:'+str(identity),'source_id':identity,'map':'garner','name':shop['name'],
   'model':17,'position':[v*100+50 for v in point],'region':'Argent City','script_function':shop['function'],
   'script_found':True,'services':['trade']+(['forge','repair'] if shop['key']=='forge' else []),
   'mission_source_ids':[],'menu_handlers':handlers,'offers':[i['id'] for i in shop['items']],
   'verified_shop_binding':True,'conditions_not_evaluated':True,'source_kind':'owner-native-shops-v2',
   'menu_pages':mapping,'live_server_seen':False})
 return {'version':2,'catalog_revision':50 if cat.get('price_overrides') else 48,'fresh_fairies':True,'npcs':rows,'prices':{str(i):v['price'] for i,v in offers(cat).items()},
         'names':{str(i['id']):i['name_ru'] for s in cat['shops'] for i in s['items']},'catalog_sha256':digest(CATALOG.read_bytes())}

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

def plan_server(root,cat=None):
 cat=cat or catalog();originals={p:(root/p).read_bytes() for p in SERVER_FILES};v1=root/'owner-city-shops-v1.json'
 if b'OWNER_CITY_SHOPS_V2_BEGIN' in originals[SERVER_FILES[0]]:
  marker=root/MARKER
  if not marker.exists():raise ValueError('Есть блок02 без контрольной записи; нужна проверка')
  previous=json.loads(marker.read_text());match=None
  for label,path,compat in [('Alpha47',ROOT/'catalog-alpha47.json',True),('Alpha48',ROOT/'catalog-alpha48.json',False)]:
   oldcat=json.loads(path.read_text())
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
  if len(previous['npc_ids'])!=5 or len(set(previous['npc_ids']))!=5:raise ValueError('Не подтверждены пять НПС02')
  for shop,identity,point in zip(cat['shops'],previous['npc_ids'],legacy.DEFAULT_POINTS):
   row=rows[identity];pos=[v*100+50 for v in point]
   if (row[11].strip()!=shop['function'].encode() or row[1].strip()!=shop['name'].encode() or int(row[3])!=17
       or list(map(int,row[5].split(b',')))!=pos or list(map(int,row[6].split(b',')))!=pos):raise ValueError('Изменена привязка НПС02')
  outputs=dict(originals);nl=b'\r\n' if b'\r\n' in originals[SERVER_FILES[0]] else b'\n'
  outputs[SERVER_FILES[0]]=strip_block(originals[SERVER_FILES[0]],2)+nl+render(cat).replace(b'\n',nl)
  for path,patcher in ((Path('ItemInfo.txt'),patch_text),(Path('ItemInfo.bin'),patch_binary)):outputs[path]=patcher(originals[path],offers(cat))
  report=dict(previous,version=2,catalog_sha256=digest(CATALOG.read_bytes()),implementation_sha256=implementation_digest(cat),
              item_count=sum(len(s['items']) for s in cat['shops']),upgraded_from=oldlabel,
              preserved_changed_files=[p.as_posix() for p in SERVER_FILES if digest(originals[p])!=previous['installed_sha256'][p.as_posix()]])
  return originals,outputs,report
 if v1.exists():
  previous=json.loads(v1.read_text())
  required={p.as_posix() for p in SERVER_FILES[:4]}
  if set(previous['installed_sha256'])!=required:raise ValueError('Неполная контрольная запись предыдущей установки')
  oldcat=json.loads((ROOT.parent/'catalog.json').read_text())
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
  for shop,identity,point in zip(cat['shops'],report['npc_ids'],legacy.DEFAULT_POINTS):
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
 clientraw=clientfile.read_bytes();clientoutput=patch_binary(clientraw,items)
 if marker.exists() and json.loads(marker.read_text()).get('catalog_sha256')==digest(CATALOG.read_bytes()):
  previous=json.loads(marker.read_text())
  if previous.get('implementation_sha256')!=implementation_digest(cat):raise ValueError('Изменилась версия обработчиков магазинов; нужна проверка обновления')
  if not all(digest((root/p).read_bytes())==h for p,h in previous['installed_sha256'].items()):raise ValueError('После нового патча изменились серверные файлы; нужна проверка')
  if clientoutput==clientraw:
   assets=Path(bot_assets) if bot_assets else ROOT.parents[1]/'assets'
   overlay=assets/'owner-city-shops.json'
   matches=False
   try:matches=overlay.exists() and json.loads(overlay.read_text())==make_overlay(cat,previous)
   except (OSError,ValueError):pass
   if not (assets/'world-npcs.json').exists() or matches:
    return dict(previous,already_installed=True)
  serveroutputs={};report=dict(previous)
 else:
  _,serveroutputs,report=plan_server(root,cat)
 changes={root/p:raw for p,raw in serveroutputs.items()};changes[clientfile]=clientoutput
 assets=Path(bot_assets) if bot_assets else ROOT.parents[1]/'assets'
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
