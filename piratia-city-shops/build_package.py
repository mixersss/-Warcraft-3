"""Combine cumulative Alpha48 bots and the owner-priced native NPC patch."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent
OUT=REPO/'releases/piratia/complete-48';NAME='Piratia-Alpha48-Complete'

def main():
 OUT.mkdir(parents=True,exist_ok=True);target=OUT/(NAME+'.zip');files={}
 with zipfile.ZipFile(REPO/'releases/piratia/auto-bots-48/Piratia-Auto-Bots-Alpha48.zip') as bots:
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
 files[NAME+'/START-HERE.md']='''# Alpha48 — один полный комплект

1. Останови ботов, GameServer и клиент Game.exe. Сделай копию своей data.
2. Скопируй содержимое комплекта поверх папки ботов, сохраняя data.
3. ОБЯЗАТЕЛЬНО запусти INSTALL-SERVER-SHOPS.cmd, даже если ставил47/Fix01.
   Сервер: C:\\PKO138 + Tools\\[1] GameServer\\resource
   Клиент: C:\\Games\\Пиратия Online
   Это разные папки. Вложенная серверная script/MisScript тоже распознаётся.
4. Дождись «Готово», запусти сервер, клиент и затем ботов через Start-World.cmd.

Старые пять НПС обновляются без дублей. Их точки:
2247,2777;2247,2779;2247,2781;2247,2783;2247,2784.
Установщик сохраняет резервные копии и обновляет справочник ботов.
Без шага3боты не начнут закупку фей в старом магазине47со смешанными статами.

В этом выпуске: случайный порядок занятий для каждого бота и каждого цикла;
кач/исторические задания/Пачкули/мирные профессии/покупки/торговля. Бой и обмен
с сервером завершаются перед сменой занятия. Боты покупают фею второго поколения
или Джуниора и развивают только одну стату: сила, дух, телосложение или точность.
Покупают только её фрукт, кормят фею, пополняют еду, нужные билеты и НЯ.
Нормальные городские билеты4602/4603/4604снова по500G. Expert Fairy Possession609
у Fairies and Food стоит300000G. Новые оплаченные феи начинают с0статов/роста;
старые феи и их статы не сбрасываются.

Чертёж Пачкули1000в ларьках и предложениях ботов стоит500G за штуку.
Цена этого предмета в ItemInfo и выплата НПС не меняются. Периодический фарм
выбирает безопасные доступные источники с учётом вероятности и расстояния.
Ларьки готовятся с15уровня после класса и реального изучения навыка торговли.
Ботам нужны заработанные деньги, очки жизни и товар; мгновенных80готовых ларьков
у популяции новичков обещать нельзя. Торговля/покупки подтверждаются сервером.
Часть товара остаётся в сумке для продажи, а не уходит целиком в банк.

В магазинах645позиций:506аппарелей/крыльев,39товаров фей/книга609,
43материала форжа,44билета,13усилителей. Обычные окна Trade с иконками;
аппарели разделены на8наборов Trade / Trade - part 2…8.
Цены выбранных645ID меняются на сервере И клиенте и действуют у всех обычных
НПС для этих ID. Другие поля ItemInfo сохраняются. Для остальных игроков есть
UPDATE-CLIENT-PRICES.cmd. Не заменяй клиентский ItemInfo серверным.

OPEN-ITEM-DATABASE.cmd — русская база5424предметов с поиском; CSV/SQLite рядом.
Подробности: README.md и server-shops/native/README.md.

Сохраняются аккаунты, персонажи, data, заработанные статы/вещи, SQL, рейты
и награды за квесты. Перевод квестов отложен по просьбе владельца.
Ковка оружия и снаряжения — следующий этап; автомат производства пока не включён.
Проверки:722ботов,23нового установщика/Lua,12предыдущего установщика.
Покупки/рост фей/ларьки на живом Windows-сервере ещё требуют проверки в игре.
'''.encode('utf8')
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
  for name,raw in sorted(files.items()):
   info=zipfile.ZipInfo(name,date_time=(2026,11,15,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,raw)
 manifest={'artifact':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,
  'cumulative_bots':'Alpha48 includes all prior bot fixes','bot_checks':722,'native_patch_checks':23,'legacy_installer_regressions':12,
  'server_shops':5,'catalog_items':645,'shop_counts':{'apparel':506,'fairies':39,'forge':43,'tickets':44,'boosts':13},
  'native_trade_windows':12,'standard_city_ticket_price':500,'expert_fairy_possession_item':609,'expert_fairy_possession_price':300000,
  'patchouli_player_price':500,'patchouli_npc_price_changed':False,'new_paid_fairies_start_zero_stats':True,'old_fairy_stats_reset':False,
  'independent_random_activity_order_each_cycle':True,'one_fairy_stat_per_actor':True,'fairy_stats':['STR','STA','CON','DEX'],
  'database_ids':5424,'server_ids':5193,'client_ids':5421,'client_update_required':True,
  'price_scope':'Selected 645 IDs globally in server/client ItemInfo; other fields unchanged; blueprint1000 price unchanged',
  'owner_positions_m':[[2247,2777],[2247,2779],[2247,2781],[2247,2783],[2247,2784]],'server_patch_automatically_installed':False,
  'v1_and_alpha47_upgrade_reuse_existing_npcs':True,'raw_server_resources_bundled':False,'private_bot_data_bundled':False,'windows_server_validation':False,
  'quest_translation':'postponed by owner','weapon_forging_automation':False,'automatic_craft_production':False,
  'contents_sha256':{name.split('/',1)[1]:hashlib.sha256(raw).hexdigest() for name,raw in sorted(files.items())}}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(OUT/'README.md').write_bytes((ROOT/'native/README.md').read_bytes())
 print(target);print(manifest['sha256'])
if __name__=='__main__':main()
