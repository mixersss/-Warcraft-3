"""Combine the cumulative bots and original server installer into one download."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent
OUT=REPO/'releases/piratia/complete-46'
NAME='Piratia-Alpha46-Complete'

def main():
 OUT.mkdir(parents=True,exist_ok=True);target=OUT/(NAME+'.zip');files={}
 with zipfile.ZipFile(REPO/'releases/piratia/auto-bots-46/Piratia-Auto-Bots-Alpha46.zip') as bots:
  for name in bots.namelist():files[NAME+'/'+name.split('/',1)[1]]=bots.read(name)
 for relative in ('README.md','AGENTS.md','knowledge/OWNER-EXECUTION.md','knowledge/SERVER-SHOPS-REQUEST.md'):
  files[NAME+'/'+relative]=(REPO/'piratia-bots'/relative).read_bytes()
 for source in sorted(ROOT.rglob('*')):
  if source.is_file() and '__pycache__' not in source.parts and source.suffix in ('.py','.lua','.json','.cmd','.md'):
   raw=source.read_bytes()
   if source.suffix=='.cmd':raw=raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
   files[NAME+'/server-shops/'+source.relative_to(ROOT).as_posix()]=raw
 files[NAME+'/INSTALL-SERVER-SHOPS.cmd']=b'@echo off\r\ncall "%~dp0server-shops\\Install-City-Shops.cmd"\r\n'
 files[NAME+'/START-HERE.md']='''# Один комплект: боты Alpha46 и пять торговцев

Все предыдущие изменения ботов включены; промежуточные версии не нужны.
Останови ботов, сохрани копию своей data и скопируй содержимое комплекта
поверх текущей программы, сохранив data.

Для торговцев останови GameServer и запусти INSTALL-SERVER-SHOPS.cmd.
Укажи серверную папку GameServer или resource. Координаты уже внесены:
2247,2777;2247,2779;2247,2781;2247,2783;2247,2784.
Установщик сохраняет резервные копии. Перезапусти сервер и ботов.
Торговцы продают через страницы диалога. Цены и инструкция:
[server-shops/README.md](server-shops/README.md).

Аккаунты, персонажи, предметы и прогресс не перезаписываются.
Боты:696проверок; серверный установщик:11проверок. Живой Windows-сервер
ещё не проверен. Результат исправления простоев нужно наблюдать после обновления.
'''.encode('utf-8')
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
  for name,raw in sorted(files.items()):
   info=zipfile.ZipInfo(name,date_time=(2026,11,15,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,raw)
 manifest={'artifact':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,
   'cumulative_bots':'Alpha46 includes Alpha45 and all prior bot fixes','bot_checks':696,'server_patch_checks':11,
   'server_shops':5,'catalog_items':632,'requires_player_minimap_coordinates':False,'owner_positions_m':[[2247,2777],[2247,2779],[2247,2781],[2247,2783],[2247,2784]],'server_patch_automatically_installed':False,
   'raw_server_resources_bundled':False,'private_bot_data_bundled':False,'windows_server_validation':False,
   'contents_sha256':{name.split('/',1)[1]:hashlib.sha256(raw).hexdigest() for name,raw in sorted(files.items())}}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(OUT/'README.md').write_bytes((ROOT/'README.md').read_bytes())
 print(target);print(manifest['sha256'])
if __name__=='__main__':main()
