"""Combine cumulative bots, native shops and a derived searchable item database."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent
OUT=REPO/'releases/piratia/complete-47-fix01'
NAME='Piratia-Alpha47-Fix01-Complete'

def main():
 OUT.mkdir(parents=True,exist_ok=True);target=OUT/(NAME+'.zip');files={}
 with zipfile.ZipFile(REPO/'releases/piratia/auto-bots-47/Piratia-Auto-Bots-Alpha47.zip') as bots:
  for name in bots.namelist():files[NAME+'/'+name.split('/',1)[1]]=bots.read(name)
 for relative in ('README.md','AGENTS.md','knowledge/OWNER-EXECUTION.md','knowledge/SERVER-SHOPS-REQUEST.md'):
  files[NAME+'/'+relative]=(REPO/'piratia-bots'/relative).read_bytes()
 for source in sorted(ROOT.rglob('*')):
  if source.is_file() and '__pycache__' not in source.parts and source.suffix in ('.py','.lua','.json','.cmd','.md','.sqlite3','.csv','.html'):
   raw=source.read_bytes()
   if source.suffix=='.cmd':raw=raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
   files[NAME+'/server-shops/'+source.relative_to(ROOT).as_posix()]=raw
 for command,inner in [('INSTALL-SERVER-SHOPS','Install-City-Shops'),('UPDATE-CLIENT-PRICES','Update-Client-Prices')]:
  files[NAME+'/'+command+'.cmd']=('@echo off\r\ncall "%~dp0server-shops\\'+inner+'.cmd"\r\n').encode()
 files[NAME+'/OPEN-ITEM-DATABASE.cmd']=b'@echo off\r\nstart "" "%~dp0server-shops\\native\\item-database.html"\r\n'
 files[NAME+'/START-HERE.md']='''# Один комплект: Alpha47 Fix01 и обычные магазины City Shops02

Все предыдущие изменения ботов включены; промежуточные версии не нужны.
Останови ботов, GameServer и клиент Game.exe. Сохрани копию своей data.
Скопируй содержимое комплекта поверх папки ботов, сохранив data.

Запусти INSTALL-SERVER-SHOPS.cmd. Укажи серверную папку GameServer/resource,
затем папку клиента Пиратии, где находится scripts. Установщик обновит оба
комплекта файлов с резервированием и добавит знания новых магазинов ботам.
Это РАЗНЫЕ папки. Например, сервер: C:\\PKO138 + Tools\\[1] GameServer\\resource;
клиент: C:\\Games\\Пиратия Online. Во второй строке нельзя указывать серверную resource.
Вложенные серверные папки script/MisScript распознаются автоматически.
Координаты уже внесены:2247,2777;2247,2779;2247,2781;2247,2783;2247,2784.
Предыдущие пять НПС обновляются без дублей. Запусти сервер, клиент и ботов.

У НПС выбирай Trade: это обычные торговые окна с иконками и покупкой.
506аппарелей/крыльев разделены на8наборов Trade / Trade - part 2…8.
Другие магазины:38товаров для фей,43для форжа,44билета,13усилителей опыта/удачи.
НЯ3844 иЗЯ3845 — у Experience and Luck. У Forge Supplies есть9родных услуг,
включая вставку/объединение/извлечение гемов, сокеты и слияние аппарелей.
Цены материалов5000G, родные цены/условия самих операций сохраняются.

ВАЖНО: обычное окно берёт цены из клиента. Выбранные644ID получают одинаковые
цены в сервере И клиенте. Они действуют у всех обычных НПС для этих ID,
включая родную оценку при продаже. Остальные параметры не меняются.
Для других игроков: UPDATE-CLIENT-PRICES.cmd, указать их клиентскую папку.
Не заменяй клиентский ItemInfo серверным: установщик сохраняет его остальные поля.

OPEN-ITEM-DATABASE.cmd открывает автономную базу5424предметов с русским поиском,
фильтрами и ценами новых магазинов. CSV дляExcel и SQLite лежат в server-shops/native.
Полная инструкция и откат: [server-shops/native/README.md](server-shops/native/README.md).

Аккаунты, персонажи, прогресс, data, SQL, рейты и квестовые награды не меняются.
Fix01 обновляет старые магазины и при изменениях вне нашего проверенного блока,
сохраняя эти изменения. Изменённый блок магазинов или неверные привязки НПС
перезаписываться не будут. Материалы форжа885/890/891 включены по5000G.
Проверки:703ботов,20нового установщика/Lua,12старого установщика.
Проверены копии исходных ресурсов и12родных торговых пакетов со всеми644ID.
Живые покупки и окна на Windows GameServer/Game.exe ещё не проверены.
'''.encode('utf-8')
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
  for name,raw in sorted(files.items()):
   info=zipfile.ZipInfo(name,date_time=(2026,11,15,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,raw)
 manifest={'artifact':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,
   'cumulative_bots':'Alpha47 Fix01 includes Alpha47 and all prior bot fixes; installer paths and conservative V1 migration corrected','bot_checks':703,'native_patch_checks':20,'legacy_installer_regressions':12,
   'server_shops':5,'catalog_items':644,'shop_counts':{'apparel':506,'fairies':38,'forge':43,'tickets':44,'boosts':13},
   'native_trade_windows':12,'native_forge_services':9,'database_ids':5424,'server_ids':5193,'client_ids':5421,'common_ids':5190,'client_only_ids':231,'server_only_ids':3,
   'client_update_required':True,'price_scope':'Selected 644 IDs globally in server and client ItemInfo; other fields unchanged',
   'requires_player_minimap_coordinates':False,'owner_positions_m':[[2247,2777],[2247,2779],[2247,2781],[2247,2783],[2247,2784]],'server_patch_automatically_installed':False,
   'v1_upgrade_reuses_existing_npcs':True,'raw_server_resources_bundled':False,'private_bot_data_bundled':False,'windows_server_validation':False,
   'contents_sha256':{name.split('/',1)[1]:hashlib.sha256(raw).hexdigest() for name,raw in sorted(files.items())}}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(OUT/'README.md').write_bytes((ROOT/'native/README.md').read_bytes())
 print(target);print(manifest['sha256'])
if __name__=='__main__':main()
