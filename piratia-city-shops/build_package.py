"""Combine cumulative Alpha51 bots and the owner-priced native NPC patch."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent
OUT=REPO/'releases/piratia/complete-51';NAME='Piratia-Alpha51-Complete'

def main():
 OUT.mkdir(parents=True,exist_ok=True);target=OUT/(NAME+'.zip');files={}
 with zipfile.ZipFile(REPO/'releases/piratia/auto-bots-51/Piratia-Auto-Bots-Alpha51.zip') as bots:
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
 files[NAME+'/START-HERE.md']=(REPO/'piratia-bots/knowledge/ALPHA51-INSTALL.md').read_bytes()
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
  for name,raw in sorted(files.items()):
   info=zipfile.ZipInfo(name,date_time=(2026,11,15,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,raw)
 manifest={'artifact':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,
  'cumulative_bots':'Alpha51 includes Alpha50 and prior fixes','bot_checks':803,'native_patch_checks':25,'legacy_installer_regressions':12,
  'runtime_limit':400,'fixed_authorised_expansion':{'from':300,'to':400,'new':100,'preserve_old_prefix':True,'native_creation_verified':False},
  'player_guide':{'builds':8,'skill_books':74,'history_definitions':426,'initial_walkthrough_steps':19,'external_complete_guides_verified':False,'formats':['html','md','pdf']},
  'dialogue':{'intent_count':132,'authored_examples':660,'authored_conversation_lines':264,'item_fact_lines':5424,'total_unique_lines':5688,'personalities':12,'external_llm':False},
  'server_shops':5,'catalog_items':645,'price_records':646,'shop_counts':{'apparel':506,'fairies':39,'forge':43,'tickets':44,'boosts':13},
  'native_trade_windows':12,'standard_city_ticket_price':500,'expert_fairy_possession_item':609,'expert_fairy_possession_price':300000,
  'patchouli_player_price':None,'patchouli_npc_price_changed':True,'patchouli_npc_buyback':500,'patchouli_base_price':1000,'new_paid_fairies_start_zero_stats':True,'old_fairy_stats_reset':False,
  'independent_random_activity_order_each_cycle':True,'one_fairy_stat_per_actor':True,'fairy_stats':['STR','STA','CON','DEX'],
  'database_ids':5424,'server_ids':5193,'client_ids':5421,'client_update_required':True,
  'price_scope':'646 price records globally synchronized:645 shop goods plus blueprint1000base1000 for native500NPCbuyback; all other fields unchanged',
  'owner_positions_m':[[2247,2777],[2247,2779],[2247,2781],[2247,2783],[2247,2784]],'server_patch_automatically_installed':False,
  'v1_and_alpha47_upgrade_reuse_existing_npcs':True,'raw_server_resources_bundled':False,'private_bot_data_bundled':False,'windows_server_validation':False,
  'quest_translation':'postponed by owner','weapon_forging_automation':False,'automatic_craft_production':False,
  'contents_sha256':{name.split('/',1)[1]:hashlib.sha256(raw).hexdigest() for name,raw in sorted(files.items())}}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(OUT/'README.md').write_bytes((ROOT/'native/README.md').read_bytes())
 print(target);print(manifest['sha256'])
if __name__=='__main__':main()
