"""Package Alpha90 bots with the revision 60 server verification tools."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent
OUT=REPO/'releases/piratia/complete-90-fix2';NAME='Piratia-Alpha90-Complete-Fix2'

def main():
 OUT.mkdir(parents=True,exist_ok=True);target=OUT/(NAME+'.zip');files={}
 with zipfile.ZipFile(REPO/'releases/piratia/auto-bots-90-fix2/Piratia-Auto-Bots-Alpha90-Fix2.zip') as bots:
  for name in bots.namelist():files[NAME+'/'+name.split('/',1)[1]]=bots.read(name)
 for relative in ('README.md','AGENTS.md','knowledge/OWNER-EXECUTION.md','knowledge/SERVER-SHOPS-REQUEST.md'):
  files[NAME+'/'+relative]=(REPO/'piratia-bots'/relative).read_bytes()
 for source in sorted(ROOT.rglob('*')):
  if source.is_file() and '__pycache__' not in source.parts and source.suffix in ('.py','.lua','.json','.cmd','.md','.sqlite3','.csv','.html'):
   raw=source.read_bytes()
   if source.suffix=='.cmd':raw=raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
   files[NAME+'/server-shops/'+source.relative_to(ROOT).as_posix()]=raw
 for command,inner in [('INSTALL-SERVER-SHOPS','Install-City-Shops'),('UPDATE-CLIENT-PRICES','Update-Client-Prices'),('INSTALL-WORLD-EXPANSION','Install-World-Expansion'),('RETIRE-ALPHA90-LEGACY','Retire-World-Legacy-IDs')]:
  files[NAME+'/'+command+'.cmd']=('@echo off\r\ncall "%~dp0server-shops\\'+inner+'.cmd"\r\n').encode()
 files[NAME+'/OPEN-ITEM-DATABASE.cmd']=b'@echo off\r\nstart "" "%~dp0server-shops\\native\\item-database.html"\r\n'
 files[NAME+'/START-HERE.md']=(REPO/'piratia-bots/knowledge/ALPHA90.md').read_bytes()
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
  for name,raw in sorted(files.items()):
   info=zipfile.ZipInfo(name,date_time=(2026,11,15,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,raw)
 manifest={'artifact':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,
  'cumulative_bots':'Alpha56 includes Alpha54 and prior fixes','bot_checks':902,'native_patch_checks':39,'legacy_installer_regressions':12,
  'runtime_limit':400,'fixed_authorised_expansion':{'from':300,'to':400,'new':100,'preserve_old_prefix':True,'native_creation_verified':False},
  'player_guide':{'builds':8,'skill_books':74,'history_definitions':426,'initial_walkthrough_steps':19,'external_complete_guides_verified':False,'formats':['html','md','pdf']},
  'dialogue':{'intent_count':136,'authored_examples':680,'authored_conversation_lines':836,'scene_lines':144,'item_fact_lines':5424,'total_unique_lines':6402,'personalities':12,'external_llm':False},
  'current_fix':{'solo_progression':True,'verified55_shop_preflight':True,'fairy_possession_native_state_confirmation':True,'personal_junior_case_resolved':False,'patchouli_bank_deposits_disabled':True,'patchouli_bank_recovery':True,'material_minimum_stall_stack':10,'gold_csv_report':True,'dungeon_config_tool':True,'stable_junior_preference_no_downgrade':True,'fairy_savings_protected':True,'curated_stall_goods':482,'dropped_gear20plus_types':400,'income_source_model_count':468,'paid_native_repair':True,'broken_gear_replacement':True,'escape_fallback_seconds':60,'same_area_resync_cooldown_seconds':600,'one_owned_emergency_ticket_after_class_level10':True,'independent_native_ping_service':True,'fairy_food_goal_every_bot':True,'fairy_food_stock_target':6,'verified_shop_knowledge_restore':True,'useful_trade_items':1629,'drop_backed_items':515,'argent_stall_capacity':60,'all_stalls_or_disconnects_fixed_live':False},
  'server_shops':6,'catalog_items':716,'price_records':718,'shop_counts':{'apparel':506,'fairies':49,'forge':43,'tickets':44,'boosts':13,'equipment':61},
  'native_trade_windows':18,'standard_city_ticket_price':500,'expert_fairy_possession_item':609,'expert_fairy_possession_price':300000,
  'patchouli_player_price':None,'patchouli_npc_price_changed':True,'patchouli_npc_buyback':1500,'patchouli_base_price':3000,'treant_root_npc_buyback':2500,'new_paid_fairies_start_zero_stats':True,'old_fairy_stats_reset':False,
  'independent_random_activity_order_each_cycle':True,'one_fairy_stat_per_actor':True,'fairy_stats':['STR','STA','CON','DEX'],
  'database_ids':5424,'server_ids':5193,'client_ids':5421,'client_update_required':True,
  'price_scope':'718 prices globally synchronized:716 shop goods plus blueprint1000base3000/1500NPCbuyback and root4915base5000/2500NPCbuyback; all other fields unchanged',
  'owner_positions_m':[[2247,2777],[2247,2779],[2197,2703],[2247,2783],[2247,2784],[2192,2710]],'server_patch_automatically_installed':False,
  'v1_and_alpha47_upgrade_reuse_existing_npcs':True,'raw_server_resources_bundled':False,'private_bot_data_bundled':False,'windows_server_validation':False,
  'quest_translation':'postponed by owner','weapon_forging_automation':False,'automatic_craft_production':False,
  'contents_sha256':{name.split('/',1)[1]:hashlib.sha256(raw).hexdigest() for name,raw in sorted(files.items())}}
 cat=json.loads((ROOT/'native/catalog.json').read_text())
 manifest.update(cumulative_bots='Alpha56 includes Alpha55 and previous releases',server_shops=len(cat['shops']),catalog_items=sum(len(s['items']) for s in cat['shops']),price_records=sum(len(s['items']) for s in cat['shops'])+len(cat['price_overrides']),shop_counts={s['key']:len(s['items']) for s in cat['shops']},native_trade_windows=0,owner_positions_m=[s['position_m'] for s in cat['shops']],patchouli_npc_buyback=2000,patchouli_base_price=4000,treant_root_npc_buyback=4000,price_scope='852 selected global price records; eight drop gems removed from NPC stock; six free extenders have zero NPC resale value; other fields preserved',current_fix={'native_profession_levels':[9,40],'bags_to':48,'stall_level':3,'native_stall_goods':18,'gem_ids':cat['owner_progression']['gem_ids'],'gem_chance_total':.03,'gem_rate_multiplier_independent':True,'gem_npc_stock_removed':True,'console_decoupled':True,'backlog_before_decisions':True,'maps_configured_when_cfg_found':True,'live_windows_verified':False},known_issues=['Native Windows validation and full400fleet load remain pending; no guarantee every physically closed cell is recovered.'])
 import sys
 sys.path.insert(0,str(ROOT/'native'))
 from render_native import pages
 manifest['native_trade_windows']=sum(len(pages(s)) for s in cat['shops'])
 manifest.update(cumulative_bots='Alpha57 includes Alpha56 and all previous releases',bot_checks=909,native_patch_checks=45,alpha57={'possession_real_cost':True,'blueprint1000_every_mob':True,'ground_protection_seconds':1,'protection_scope':'all ground loot in configured GameServer processes','idle_recovery_seconds':60,'unproductive_travel_recovery_seconds':180,'native_cooldowns_unchanged':True,'live_windows_verified':False},next_update='Alpha58: 30% gem sellers, actual gem purchases/forging/apparel, boosters and wider reachable XP destinations')
 manifest.update(cumulative_bots='Alpha58 includes Alpha57 and all previous releases',bot_checks=929,native_patch_checks=49,weapon_forging_automation=True,automatic_craft_production='Native operations on owned equipment; retired upgraded items may be sold, no bulk production guarantee',alpha58={'gem_seller_roles':120,'population':400,'argent_stall_capacity':120,'native_forge_modes':[1,2,3,4,5],'normal_and_refining_combinations':True,'valid_operation_success':1.0,'native_created_socket_cap':2,'gem_cap':9,'fusion_upgrade_cap':15,'native_materials_and_gold':True,'island_routes':56,'native_tickets':43,'native_entrances':119,'live_windows_verified':False},next_update=None)
 manifest.update(cumulative_bots='Alpha59 includes Alpha58 and all previous releases',bot_checks=936,native_patch_checks=51,alpha59={'classic_combat_spell_compatibility':True,'missing_spell_failure_reported':True,'stall_closure_state':99,'closure_resync_after_seconds':60,'live_windows_verified':False},next_update=None)
 manifest.update(cumulative_bots='Alpha60 includes Alpha59 and all previous releases',bot_checks=953,native_patch_checks=55,alpha60={'source_rectangle_scouting':True,'normal_player_exp_scale_floor':100,'configured_exp_rate_unchanged':True,'critical_foreign_weapon_trips':True,'ticket_plan_before_purchase':True,'native_xp_receipts':True,'fairy_growth_restored':True,'preventive_weapon_repair_threshold':1/3,'live_windows_verified':False},next_update=None)
 manifest.update(cumulative_bots='Alpha61 includes Alpha60 and all previous releases',bot_checks=971,native_patch_checks=55,minimum_server_revision=60,alpha61={'ground_camps_only':True,'required_coral_first':True,'repair_quote_backoff':True,'hunting_coordinates_in_reports':True,'server_patch_changed':False,'live_windows_verified':False})
 manifest.update(cumulative_bots='Alpha73 includes Alpha72 and previous releases',bot_checks=995,alpha73={'server_patch_changed':False,'verified_shop_restore_included':True,'live_windows_verified':False})
 manifest.update(cumulative_bots='Alpha74 includes Alpha73 and previous releases',bot_checks=1003,alpha74={'server_patch_changed':False,'startup_spawn_placements':3503,'live_windows_verified':False})
 manifest.update(cumulative_bots='Alpha75 includes Alpha74 and previous releases',bot_checks=1010,alpha75={'server_patch_changed':False,'live_windows_verified':False})
 manifest.update(cumulative_bots='Alpha76 includes Alpha75 and previous releases',bot_checks=1017,alpha76={'server_patch_changed':False,'live_windows_verified':False})
 manifest.update(cumulative_bots='Alpha77 includes Alpha76 and previous releases',bot_checks=1021,alpha77={'server_patch_changed':False,'live_windows_verified':False})
 manifest.update(cumulative_bots='Alpha78 includes Alpha77 and previous releases',bot_checks=1023,alpha78={'server_patch_changed':False,'live_windows_verified':False})
 manifest.update(cumulative_bots='Alpha79 includes Alpha78 and previous releases',bot_checks=1029,alpha79={'server_patch_changed':False,'live_windows_verified':False})
 manifest.update(cumulative_bots='Alpha80 includes Alpha79 and previous releases',bot_checks=1036,alpha80={'server_patch_changed':False,'live_windows_verified':False})
 manifest.update(cumulative_bots='Alpha81 includes Alpha80 and previous releases',bot_checks=1039,alpha81={'server_patch_changed':False,'live_windows_verified':False})
 manifest.update(cumulative_bots='Alpha82 includes Alpha81 and previous releases',bot_checks=1043,alpha82={'server_patch_changed':False,'live_windows_verified':False})
 manifest.update(cumulative_bots='Alpha83 includes Alpha82 and previous releases',bot_checks=1047,alpha83={'server_patch_changed':False,'live_windows_verified':False})
 manifest.update(cumulative_bots='Alpha84 includes Alpha83 and previous releases',bot_checks=1053,alpha84={'server_patch_changed':False,'live_windows_verified':False})
 manifest.update(cumulative_bots='Alpha85 includes Alpha84 and previous releases',bot_checks=1057,alpha85={'server_patch_changed':False,'live_windows_verified':False})
 manifest.update(cumulative_bots='Alpha89 includes Alpha88 and previous releases',bot_checks=1070,alpha89={'server_patch_changed':False,'live_windows_verified':False})
 manifest.update(cumulative_bots='Alpha90 includes Alpha89 and previous releases',bot_checks=1072,native_patch_checks=61,alpha90={'world_expansion_installer':True,'installer_fix':2,'live_windows_verified':False})
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(OUT/'README.md').write_bytes((REPO/'piratia-bots/knowledge/ALPHA90.md').read_bytes())
 print(target);print(manifest['sha256'])
if __name__=='__main__':main()
