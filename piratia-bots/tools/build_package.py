"""Build a deterministic source-only Windows connection-alpha package."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'releases' / 'piratia' / 'auto-bots-91'
NAME = 'Piratia-Auto-Bots-Alpha91'


def main():
    sources = sorted(ROOT.glob('*.cmd')) + [ROOT / 'README.md', ROOT / 'PROTOCOL.md', ROOT / 'AGENTS.md']
    sources += [ROOT / 'tools' / 'build_junk.py', ROOT / 'tools' / 'build_merchants.py', ROOT / 'tools' / 'build_world_navigation.py', ROOT / 'tools' / 'recheck_farm_points.py', ROOT / 'tools' / 'build_world_mobs.py', ROOT / 'tools' / 'build_portals.py', ROOT / 'tools' / 'build_items.py', ROOT / 'tools' / 'build_combat_zones.py', ROOT / 'tools' / 'build_combat_skills.py', ROOT / 'tools' / 'build_life_items.py', ROOT / 'tools' / 'build_npc_knowledge.py', ROOT / 'tools' / 'build_market.py', ROOT / 'tools' / 'build_story.py', ROOT / 'tools' / 'build_quest_rewards_package.py']
    sources += [ROOT / 'tools/lua_inventory.py', ROOT / 'tools/build_mechanics.py', ROOT / 'knowledge/mechanics-evidence-lock.json', ROOT / 'knowledge/MECHANICS-COVERAGE.md']
    sources += [ROOT / 'tools/build_ground_components.py', ROOT / 'knowledge/fleet-alpha44-audit.json', ROOT / 'knowledge/fleet-alpha47-audit.json', ROOT / 'knowledge/ALPHA49.md', ROOT / 'knowledge/SERVER-SHOPS-REQUEST.md']
    sources += [ROOT/'tools/build_dialogue_data.py',ROOT/'tools/build_land_components.py',ROOT/'knowledge/ALPHA50.md',ROOT/'knowledge/ALPHA50-INSTALL.md',ROOT/'knowledge/DIALOGUE50.md',ROOT/'knowledge/dialogue-data-audit.json',ROOT/'knowledge/dialogue-benchmark.json',ROOT/'knowledge/fleet-alpha49-audit.json']
    sources += [ROOT/'tools/build_player_guide.py',ROOT/'tools/build_story_reference.py',ROOT/'knowledge/ALPHA51.md',ROOT/'knowledge/ALPHA51-INSTALL.md',ROOT/'knowledge/guide-sources.json']
    sources += [ROOT/'tools/dialogue52_lines.py',ROOT/'tools/dialogue52_scenes.py',ROOT/'tools/build_useful_loot.py',ROOT/'knowledge/ALPHA52.md',ROOT/'knowledge/ALPHA52-INSTALL.md',ROOT/'knowledge/fleet-alpha51-audit.json']
    sources += [ROOT/'knowledge/ALPHA53.md',ROOT/'knowledge/ALPHA53-INSTALL.md']
    sources += [ROOT/'tools/build_stall_policy.py',ROOT/'knowledge/ALPHA54.md',ROOT/'knowledge/ALPHA54-INSTALL.md']
    sources += [ROOT/'knowledge/ALPHA55.md',ROOT/'knowledge/ALPHA55-INSTALL.md',ROOT/'knowledge/FAIRY-POSSESSION55.md',ROOT/'knowledge/fleet-alpha54-audit.json']
    sources += [ROOT/'knowledge/ALPHA56.md',ROOT/'knowledge/ALPHA56-INSTALL.md',ROOT/'knowledge/fleet-alpha55-audit.json']
    sources += [ROOT/'knowledge/ALPHA57.md',ROOT/'knowledge/ALPHA57-INSTALL.md',ROOT/'knowledge/ALPHA57-58-PLAN.md']
    sources += [ROOT/'knowledge/ALPHA58.md',ROOT/'knowledge/ALPHA58-INSTALL.md',ROOT/'tools/build_travel58.py']
    sources += [ROOT/'knowledge/ALPHA59.md',ROOT/'knowledge/ALPHA59-INSTALL.md',ROOT/'knowledge/fleet-alpha58-audit.json']
    sources += [ROOT/'knowledge/ALPHA60.md',ROOT/'knowledge/ALPHA60-INSTALL.md',ROOT/'knowledge/fleet-alpha59-audit.json']
    sources += [ROOT/'knowledge/ALPHA61.md',ROOT/'knowledge/ALPHA61-INSTALL.md',ROOT/'knowledge/fleet-alpha60-audit.json']
    sources += [ROOT / 'knowledge/ALPHA62.md',ROOT / 'knowledge/ALPHA63.md',ROOT / 'knowledge/ALPHA64.md',ROOT / 'knowledge/ALPHA65.md',ROOT / 'knowledge/ALPHA66.md',ROOT / 'knowledge/ALPHA67.md',ROOT / 'knowledge/ALPHA68.md',ROOT / 'knowledge/ALPHA69.md',ROOT / 'knowledge/ALPHA70.md',ROOT / 'knowledge/ALPHA71.md',ROOT / 'knowledge/ALPHA72.md',ROOT / 'knowledge/ALPHA73.md',ROOT / 'knowledge/ALPHA73-MAP-AUDIT.md',ROOT / 'knowledge/ALPHA74.md',ROOT / 'knowledge/ALPHA75.md',ROOT / 'knowledge/ALPHA76.md',ROOT / 'knowledge/ALPHA77.md',ROOT / 'knowledge/ALPHA78.md',ROOT / 'knowledge/ALPHA79.md',ROOT / 'knowledge/ALPHA80.md',ROOT / 'knowledge/ALPHA81.md',ROOT / 'knowledge/ALPHA82.md',ROOT / 'knowledge/ALPHA83.md',ROOT / 'knowledge/ALPHA84.md',ROOT / 'knowledge/ALPHA85.md',ROOT / 'knowledge/ALPHA86.md',ROOT / 'knowledge/ALPHA87.md',ROOT / 'knowledge/ALPHA88.md',ROOT / 'knowledge/ALPHA89.md',ROOT / 'knowledge/ALPHA90.md']
    sources += [ROOT/'knowledge/ALPHA91.md',ROOT/'knowledge/ALPHA91-ANALYSIS.md',ROOT/'knowledge/fleet-alpha90-fix9-audit.json',ROOT/'knowledge/level-source-coverage91.json',ROOT/'knowledge/camp-cache-benchmark91.json']
    sources += sorted((ROOT / 'src').glob('*.py'))
    sources += sorted((ROOT / 'src').glob('*.ps1'))
    sources += sorted((ROOT / 'tests').glob('test_*.py'))
    sources += sorted((ROOT / 'tests').glob('test_*.ps1'))
    sources += sorted((ROOT / 'tests' / 'fixtures').glob('*.json'))
    sources += sorted((ROOT / 'assets').glob('*.json'))
    sources += [ROOT / 'knowledge' / 'sources-local.json', ROOT / 'knowledge' / 'OWNER-GOAL-500.md', ROOT / 'knowledge' / 'OWNER-EXECUTION.md', ROOT / 'knowledge' / 'IMPLEMENTATION.md', ROOT / 'knowledge' / 'navigation-audit.json', ROOT / 'knowledge' / 'pond-navigation-alpha38.png']
    OUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT / f'{NAME}.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sources:
            info = zipfile.ZipInfo(f'{NAME}/{source.relative_to(ROOT).as_posix()}',
                                   date_time=(2026, 11, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            data = source.read_bytes()
            if source.suffix == '.cmd':
                data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            archive.writestr(info, data)
        for source in sorted((ROOT.parent/'releases/piratia/guides-51').iterdir()):
            if source.suffix=='.zip':continue
            info=zipfile.ZipInfo(f'{NAME}/guides/{source.name}',date_time=(2026,11,15,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,source.read_bytes())
    artifact = OUT / f'{NAME}.zip'
    manifest = {
        'artifact': artifact.name,
        'alpha55': {'bot_tests':876,'native_tests':29,'legacy_tests':12,'gold_csv_report':True,'auto_party_waiting':False,'progression_cycle_share':[.77,.82],'patchouli_npc_buyback':1500,'treant_root_npc_buyback':2500,'private_junior_case_resolved':False,'live_fleet_verified':False},
        'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
        'mechanics_knowledge': {'lua_files':242,'named_functions':4135,'reviewed_source_cards':22,'indexed_only_cards':6,'all_mechanics_understood':False,'new_native_operations_enabled':False,'local_learner':'Learn-Mechanics.cmd','finder':'Find-Mechanic.cmd','audit':'Audit-Mechanics.cmd'},
        'fleet_alpha44_reaudit': {'connected':300,'first_profession':172,'novices':128,'no_xp_over_30min':246,'full_bags':3,'needs_geometric_recovery':40,'dry_checked_exits':24,'no_exit_but_owned_ticket':6,'no_exit_or_ticket':10,'live46_fix_verified':False},
        'stuck_city_ticket': {'owned_only':[4602,4603,4604],'full_hp_sp_required':True,'native_arrival_and_consumption_required':True},
        'native_owner_shops_v2': {'optional_installed_overlay':True,'ordinary_trade_stock':True,'catalog_items':716,'berry_aliases':{'nya':3844,'zya':3845},'baseline_static_npcs':521,'with_installed_native_shops':527,'live_windows_verified':False},
        'owner_economy_alpha48': {'random_independent_activity_order_each_cycle':True,'cycle_seconds':1800,'phase_duration_variation':.15,'finish_fights_and_transactions_before_switch':True,'blueprint1000_player_price':None,'blueprint1000_npc_price_changed':True,'blueprint1000_npc_buyback':500,'source_drop_species':22,'second_generation_or_junior_only':True,'fairy_stats':['STR','STA','CON','DEX'],'one_fruit_stat_per_fairy':True,'normal_ticket_price':500,'expert_possession_item609_price':300000,'fresh_paid_fairies_start_zero_stats':True,'old_fairy_stats_reset':False,'stalls_from_level':15,'stall_skill_and_life_points_required':True,'keep_six_stall_offers_before_banking':True,'life_profession_learning_enabled':True,'automatic_craft_production_enabled':False,'weapon_forging_automation_enabled':False,'quest_translation':'postponed by owner'},
        'current_alpha50': {'dialogue_intents':132,'dialogue_examples':660,'authored_conversation_lines':264,'distinct_item_fact_lines':5424,'unique_reply_lines':5688,'personalities':12,'context_channels':['local','world','trade','private'],'memory_turns':16,'context_limit_per_client':32,'npc_patchouli_buyback':500,'patchouli_base_price':1000,'class_funding_plain_patchouli_allowed':True,'treasure_items':[684,682,2445],'new_map_min_level':15,'new_map_max_level':40,'native_coral_energy_action':23,'shore_probe_max_cm':250,'land_component_grids':30,'progress_watchdog_seconds':45,'protocol_reconnect_limit':3,'new_native_live_validation':False},
        'current_alpha51': {'runtime_limit':400,'fixed_growth':[300,400],'preserved_old_bots':300,'build_skill_guides':8,'near_term_book_purchase_limit':2,'guide_history_definition_rows':426,'guide_initial_walkthrough_steps':19,'guide_skill_book_rows':74,'external_complete_guides_verified':False,'live400_creation_verified':False},
        'hunt_party_alpha49': {'world_echo_then_private_reply_then_native_team':True,'maximum_level_gap':3,'maximum_meeting_seconds':90,'unproductive_team_seconds':120,'maximum_movement_prefix_cm':2400,'recruitment_cash_gate':2000,'ordinary_chat_cash_gate':20000,'live_verified':False},
        'current_alpha52': {'network_background_ping_pump':True,'max_queued_packets':4096,'max_queued_payload_bytes':2097152,'diagnostic_write_failure_nonfatal':True,'fairy_goal_all_bots':True,'fairy_food_stock_target':6,'restore_verified_shop_knowledge_cmd':'RESTORE-BOT-SHOPS.cmd','dialogue_intents':136,'authored_examples':680,'authored_conversation_lines':836,'scene_lines':144,'distinct_item_fact_lines':5424,'unique_reply_lines':6402,'useful_trade_items':1629,'drop_backed_items':515,'argent_stall_capacity':120,'live_windows_validation':False},
        'current_alpha53':{'paid_native_repair_source_audited':True,'live_repair_verified':False,'escape_fallback_seconds':60,'same_area_resync_cooldown_seconds':600,'proactive_owned_ticket_min_level':10,'population_unchanged':400},
        'current_alpha54':{'stable_junior_preference_no_downgrade':True,'fairy_savings_protected':True,'affordable_pet_bypasses_xp_watchdog':True,'verified_missing_overlay_bootstrap':True,'curated_stall_goods':482,'drop_gear_level20plus':400,'source_monster_definitions':468,'live_windows_purchase_verified':False},
        'status':'Alpha55 prioritizes earned solo XP, verified55 supplier knowledge, fairy casts/training, real bank Patchouli recovery, stacks and equipment savings. Includes54. Personal Junior case and full live fleet validation remain pending.',
        'previous_status_alpha53':'Alpha53 adds paid native repair, broken-gear replacement, confirmed-escape movement waiting, one-minute owned-ticket/native-position-resync fallback and proactive earned ticket procurement. All52 changes included; live Windows fleet recovery unverified.',
        'previous_status_alpha52':'Alpha52 decouples native ping servicing, bounds queued events, caches unchanged equipment decisions, preserves state during diagnostic file locks, restores verified supplier knowledge, prioritizes fairy food, contextualizes LFG replies and adds finite nearby scenes and useful real loot markets. No claim every idle/disconnect case resolved on owner server.',
        'previous_status_alpha51': 'Alpha51 adds eight owner/server-derived skill plans, a standalone original Russian history/skills guide, and resumable300to400 expansion preserving the old300; complete external community guides not verified. Includes Alpha50: global NPC Patchouli500G buyback/novice fare funding, ordinary dropped-gear and NP markets, real parchment/Caribbean map/ticket digging, essential role weapons, caster cooldown and native coral-energy updates, native-progress watchdog, bounded shoreline attempts, disconnected-land rejection, bounded protocol recovery diagnostics, isolated four-channel dialogue with132 intents/12 profiles/5688distinct reply lines including5424item facts. Prior source mechanics knowledge/roles/builds/fairies/stalls/bank/LFG preserved. Old data/accounts/rates/rewards untouched. Live Windows behavior and all fleet recovery not proven; quest translation, ship/PvP/weapon-forging/production automation remain deferred',
        'junk_classification_policy': 'broad audited common trophy drops and plant ingredients; no general price cap; valuable/quest/modified item protections retained',
        'first_profession_objective_npc_review': 'reconnect, audited item quantity/observed target deaths, or180s fallback; NPC remains authoritative',
        'garner_verified_merchants': 19,
        'garner_merchants_include_mines_and_field_shops': True,
        'unavailable_trade_function_selects_alternative': True,
        'npc_not_ready_returns_to_farming': True,
        'optional_planning_cannot_monopolize_decision': True,
        'background_planning_node_slice_when_nearby_work': 128,
        'foreground_and_background_search_jobs_are_independent': True,
        'nonurgent_sale_yields_to_active_class_farming': True,
        'reports_distinguish_actual_profession_from_planned_class': True,
        'attribute_refusal_retry_seconds': 300,
        'route_search_heuristic_weight': 4,
        'route_search_closed_cells_not_reexpanded': True,
        'shared_destination_corridor_limit': 128,
        'shared_corridors_per_destination': 4,
        'shared_route_join_checked_on_grid': True,
        'merchant_approach_within_centimetres': 220,
        'unreachable_merchant_goals_try_alternatives_without_cooldown': True,
        'bot78_screenshot_position_movement_replay_passed': True,
        'nearby_origin_corridor_replay_count': 200,
        'unexpected_server_stop_replans_route': True,
        'our_endaction_stop_is_not_obstacle': True,
        'temporary_obstacle_seconds': 30,
        'temporary_obstacle_limit_per_worker': 64,
        'temporary_obstacles_are_worker_local': True,
        'movement_wait_uses_server_accepted_route_duration': True,
        'visible_first_profession_kills_precede_optional_loot_and_shopping': True,
        'find_bot_by_public_nickname': 'Find-Bot.cmd; tags from Alpha34+ reports; no data or credentials read',
        'pond_shoreline_from_owner_atr_confirmed': False,
        'original_navigation_grid_changed': True,
        'navigation_geometry_revision': 'alpha39-ground-recovery-v1',
        'paired_client_server_navigation_maps': 29,
        'combat_zone_revision': 'alpha40-native-no-fight-v1',
        'native_no_fight_bit': 2,
        'combat_zone_maps': 29,
        'combat_masks_change_walking_grid': False,
        'protected_monsters_skipped_before_attack': True,
        'protected_targets_release_without_species_blacklist': True,
        'protected_queued_attacks_discarded': True,
        'firing_position_must_allow_combat': True,
        'combined_native_immune_bits_release_target': True,
        'help_requests_do_not_pin_to_protected_targets': True,
        'full_dual_sword_or_two_handed_loadout_choice_implemented': False,
        'basic_whole_loadout_comparison_implemented': True,
        'two_owned_sword_plan_with_exact_slot_native_confirmation': True,
        'unverified_force_left_operand_used': False,
        'monster_xp_column_zero_based': 90,
        'levelup_cumulative_xp_preserved': True,
        'xp_per_minute_and_no_gain_duration_in_fleet_and_diagnostics': True,
        'completed_fight_counter_probe_repeated_without_new_result': False,
        'unfamiliar_probe_prefers_nearby_viable_camp': True,
        'fixed_authorised_expansion': {'from':300,'to':400,'new':100},
        'previous_authorised_expansion': {'from':200,'to':300,'new':100},
        'growth_ledger': 'data/population-growth-400.json',
        'growth_backup_before_mutation': 'data/backups/before-growth-400',
        'old200_and_native_confirmed_new_accounts_and_characters_protected': True,
        'missing_protected_sql_account_recreated': False,
        'new_profiles_balance_compatible_class_deficits_without_changing_old_roles': True,
        'repeated_world_launch_adds_more_than400': False,
        'live400_connections_verified': False,
        'live300_connections_verified': False,
        'known_static_npc_placements': 521,
        'all_runtime_npc_source_tables': 29,
        'maps_with_static_npc_placements': 20,
        'npc_model_definitions': 131,
        'npc_models_without_verified_static_coordinates': 30,
        'dynamic_npc_spawns_exhaustively_known': False,
        'all_known_npc_services_automated': False,
        'npc_knowledge_shared_by_all_workers': True,
        'npc_finder': 'Find-NPC.cmd',
        'shop_lookup_across_three_home_cities': True,
        'shopping_reserves_roundtrip_fare_and_100gold': True,
        'accessory_goals_keep_marine_corals': True,
        'owner_build_variant_count': 8,
        'build_variants_persist_separately_from_roles': 'data/bot-builds.json',
        'only_future_unspent_stat_points_affected': True,
        'old_earned_stats_reset': False,
        'native_observed_speed_target': 210,
        'observed_speed_excludes_temporary_buffs': False,
        'native_level_xp_divisor_20vs12': 2.6,
        'current_level_xp_observations_separate_from_lifetime': True,
        'ordinary_low_level_hunt_yields_to_viable_near_level_band': True,
        'required_low_level_quest_targets_preserved': True,
        'owner_execution_tracker': 'knowledge/OWNER-EXECUTION.md',
        'native50cm_egress_grid_for_occupied_excluded_cells': True,
        'reported_offmesh_positions_replayed': 17,
        'offmesh_recovery_moves_fabricated_positions': False,
        'stale_quest_combat_flag_reset_each_decision': True,
        'mandatory_profession_npc_admission_limit_removed': True,
        'pending_native_promotion_conditions_inspected': True,
        'teacher_retry_delay_allows_productive_hunting': True,
        'known_monster_definitions': 608,
        'monster_types_with_located_source_spawns': 426,
        'monster_types_without_verified_coordinates': 182,
        'maximum_known_monster_level': 300,
        'spawn_source_tables': 29,
        'normal_monster_spawn_regions_including_conditional_literals': 7725,
        'script_conditions_or_expression_spawns_evaluated': False,
        'level45_farm_selection_cap_removed': True,
        'observed_results_and_distance_affect_hunt_selection': True,
        'verified_portal_npcs': 4,
        'active_verified_portal_routes': 9,
        'same_map_shortcut_compares_checked_approach_and_arrival_routes': True,
        'portal_arrival_requires_native_state': True,
        'conditional_unverified_portals_enabled': False,
        'bows_in_native_left_weapon_slot_supported': True,
        'shields_scored_by_defence': True,
        'replacement_gear_requires_bag_space_and_native_confirmation': True,
        'all_four_first_profession_weapon_cases_passed': True,
        'latest_owner_alpha38_fleet_actual_professions': {'novice':188,'hunter':11,'swordsman':1},
        'latest_owner_alpha38_snapshot_proves_all_classes_completed': False,
        'client_only_maps_not_enabled': ['darkhouse','prisonisland'],
        'server_attribute_masks_checked': True,
        'underwater_terrain_exclusion_except_explicit_bridges': True,
        'farm_points_rechecked_on_ground_connected_to_home': True,
        'additional_map_navigation_loaded_on_demand': True,
        'complete_dungeon_ai_or_all_teleports_implemented': False,
        'field_merchants_by_home_map': {'garner':19,'magicsea':7,'darkblue':11},
        'coral_purchase_and_renewal_recorded_as_requirement': True,
        'coral_purchase_and_renewal_implemented': True,
        'coral_supply_scope': 'verified sellers;3city shopping plans through confirmed known portals; real owned replacements/server charge confirmation',
        'targeted_combat_skill_ids': [81,82,85,86,90,91,96,97,99,213,214,216,224],
        'full_skill_rotation_and_party_healing_implemented': False,
        'native_activated_skills_sp_cooldown_weapon_coral_gates': True,
        'native_look_energy_and_skillbag_energy_preserved_without_layout_change': True,
        'queued_spell_keeps_selected_skill_id': True,
        'native_item_allowed_bodies_column': 23,
        'equipment_catalog_entries': 1673,
        'pending_wardrobe_drained_before_new_hunt': True,
        'class_chest_open10_gear_requires15_respected': True,
        'live_first_profession_completion_verified': False,
        'npc_sale_cooldown_seconds': 0,
        'vendor_task_pause_seconds': 0,
        'vendor_productive_route_absolute_time_limit_removed': True,
        'full_bag_does_not_block_quest_combat': True,
        'report_character_tags_without_names': True,
        'shared_active_quest_targets': True,
        'ordinary_busy_target_fallback': True,
        'competitive_active_quest_drop_pickup': 'native requests only; server ownership and inventory confirmation required; bounded retries',
        'post_first_profession_development_regression_passed': True,
        'all_life_professions_and_fast_travel_routes_implemented': False,
        'first_profession_priority_level': 9,
        'farm_until_real_fare_available': True,
        'sell_safe_junk_before_class_letter_if_bag_full': True,
        'small_junk_stacks_can_be_sold_when_less_than_two_free_slots': True,
        'plain_junk_reserve_units': 0,
        'sell_visit_clears_all_safe_junk_stacks': True,
        'five_stack_visit_cap_removed': True,
        'small_junk_quantity_start_threshold_removed': True,
        'alternative_city_merchants_on_busy_site': False,
        'ordinary_merchant_admission_limit_removed': True,
        'fleet_reports_include_coordinates': True,
        'owner_target_bots': 500,
        'runtime_capacity_bots': 400,
        'quest_ingredients_and_modified_items_preserved': True,
        'commit_full_journal_resync_after_seconds': 2,
        'unchanged_journal_is_not_success': True,
        'dead_target_released_before_npc_travel': True,
        'missing_journal_retries_seconds': 30,
        'new_class_selection': 'least represented compatible target, random ties; verified novices may rebalance only before a profession quest is started',
        'requires_saved_population_by_default': True,
        'explicit_new_population_flag': '--allow-new-bots',
        'account_state_format_changed': False,
        'existing_professions_and_started_quests_preserved': True,
        'remote_class_travel_router_tests': ['garner to darkblue, native menu/map confirmation/referral acceptance', 'garner to magicsea, native menu/map confirmation/referral acceptance'],
        'server_quest_and_newbie_chest_issue_fixed': False,
        'server_issue_status': 'Owner MissionScript01 and NpcScript01 match prior audited SHA256 and parse as Lua; Senna has four class referrals and mission pages28/29; current SDK/loader/new-character initialization and actual startup evidence still needed',
        'server_rates_modified': False,
        'live_x2_leveling_rate_verified': False,
        'native_windows_server_tested': False,
        'planning_budget_clock': 'thread CPU, started at first search work',
        'minimum_search_pops_if_budget_allows': 32,
        'console_final_state_interval_seconds': 30,
        'visible_opportunity_after_seconds': 20,
        'no_xp_trial_after_seconds': 90,
        'owner_alpha24_snapshot': {'reports':200,'level4':37,'level5':126,'level6':37,'planning':150,'xp_gained':84,'level_gained':16,'positive_hp':200,'revival_requests':68},
        'offline_report_route_replay': {'destinations':147,'reachable':146,'offmesh_origins':1,'unfinished':0},
        'ground_sitting_native_client_capture_passed': True,
        'ground_sitting_server_branch_disassembled': True,
        'ground_sitting_live_windows_tested': False,
        'runtime_astar_slice_pop_limit': 512,
        'runtime_astar_deadline_check_ms': 6,
        'death_handled_before_navigation': True,
        'in_range_old_route_stop_before_attack': True,
        'starter_exclusive_search_seconds': 90,
        'decision_frequency_max_hz': 4,
        'npc_destination_capacity': 2,
        'npc_destination_capacity_applies_to': 'optional visits only; mandatory profession visits unlimited',
        'optional_npc_population_fraction': .1,
        'spatial_hunt_density_radius_cm': 2500,
        'native_route_preserves_astar_turns': True,
        'nested_partial_data_copy_rejected': True,
        'windows_session_guard_live_tested': False,
        'pure_python_tests_passed': 852,
        'full_python_suite_total': 876,
        'full_python_suite_passed': 876,
        'socket_tests_not_rerun_this_release': 0,
        'last_full_network_regression': '876 passed in Alpha55 including 8 legacy socket integrations and 4 dedicated background-network socket tests',
        'current_network_regression': '8 legacy simulated-server socket tests and 4 dedicated background-pump socket tests; owner Windows server not tested',
        'default_bot_count': 400,
        'default_mode': 'mixed',
        'cohort_tactics_at_200': {'farm':80,'hybrid':120},
        'hybrid_phase_seconds': [240,480],
        'finite_dialogue_scripts': 50,
        'dialogue_advances_on_real_peer_echo': True,
        'first_profession_in_both_tactics': True,
        'exclusive_target_cohort_tested': 200,
        'live_target_distribution_verified': False,
        'default_duration_seconds': 0,
        'three_city_spawn_and_trainer_routes_verified': True,
        'chat_phrase_count': 589,
        'new_chat_phrases': 200,
        'live_two_hundred_connections_tested': False,
        'advanced_profession_requests_implemented': True,
        'advanced_profession_full_chains_implemented': False,
        'player_item_exchange_implemented': False,
        'story_chain': [200,203,204],
        'combat_skill_book_catalog_count': 83,
        'owned_chest_ids': [436,437,438,439,440,441,442,443,985,986,987,988],
        'native_action_serialization_compared': ['movement', 'normal attack', 'local speech', 'base attributes', 'NPC talk', 'quest selection', 'quest accept/deliver', 'item pickup', 'item use/equip', 'skill upgrade', 'return to city', 'NPC function selection', 'NPC purchase', 'NPC sale', 'party invite/accept/refuse/leave', 'stall create/view/buy/close', 'end action', 'world/trade chat'],
        'native_world_writers_captured': ['base info', 'look', 'append-look (4 slots)', 'skillbag', 'skill state', 'event', 'attribute range', 'initial kitbag with boat/instance', 'kitbag delta'],
        'powershell_state_regression': 'passed with PowerShell 7.4.6 on Linux; idempotent populations 1/10/30/60/100/200/300, rejection0/301, credential/PIN/backup preservation, protected account creation refused; runtime PS syntax parsed',
        'population_validation': 'both PowerShell helpers and Python launcher aligned: 1..300; Start-World grows saved200 to fixed300' ,
        'windows_sql_dpapi_runtime_tested': False,
        'owner_confirmed_previous_release': {'account_creation': True, 'login': True, 'character_creation': True, 'map_entry': True, 'movement_and_combat_alpha08': True, 'alpha11_fix01_spawn_and_initial_quest_movement':True, 'hunting_and_chat_alpha09': True},
        'begin_play_format': 'classic character-name string, native client 0x51a4d0',
        'secondary_password_setup': 'command 346 with uppercase MD5 string; only if login flag says absent',
        'native_character_look_compared': [1,2,3,4],
        'native_journal_writer_captured': True,
        'live_quest_completion_tested': False,
        'instances_implemented': False,
        'creation_appearance': {'type': 1, 'hair': 2000, 'face': 2554, 'source': 'native client character creator tables'},
        'native_gate_crypto_compared': ['3DES encrypt/decrypt', 'B encrypt/decrypt',
                                       'Noise encrypt/decrypt with evolving state'],
        'population_target': 500,
        'maximum_enabled_bots': 300,
        'four_hundred_live_connections_tested': False,
        'stall_session_seconds': 3600,
        'stall_live_population_fraction': None,
        'argent_target_stalls': 60,
        'stall_minimum_level': 15,
        'voluntary_rest_live_population_fraction': .10,
        'stall_city_caps_at_200': {'garner':80,'magicsea':3,'darkblue':2},
        'preferred_home_cities_at_200': {'garner':150,'magicsea':25,'darkblue':25},
        'npc_city_transfer_live_tested': False,
        'local_chat_shared_seconds': 2,
        'world_chat_shared_seconds': 120,
        'trade_chat_shared_seconds': 180,
        'explicit_nearby_help_seconds': 120,
        'live_combat_fix_verified': False,
        'skill_update_dispatch_fixed': [510,531],
        'attribute_request_is_increment': True,
        'native_attribute_increment_verified': True,
        'deferred_action_stop_queue': True,
        'private_owner_reports_packaged': False,
        'continuous_world_launcher': 'Start-World.cmd',
        'combined_attack_ignores_intermediate_move_stop': True,
        'normal_attack_preserved_while_target_hp_decreases': True,
        'movement_segment_early_cancel_removed': True,
        'two_hundred_acknowledged_fight_policy_simulation': 'passed; offline only',
        'owner_alpha18_population': {'connected':200,'zero_attack_requests':116,'waiting_action':73},
        'network_reconnect_attempts_finite_unstable_sessions': 3,
        'continuous_network_recovery': True,
        'continuous_recovery_backoff_seconds': [5,15,30,120],
        'history_max_entries': 20,
        'collect_all_earned_monster_loot': True,
        'pickup_requires_inventory_gain_and_ground_removal': True,
        'starter_monster_model': 103,
        'adaptive_hunting_profiles': 6,
        'starter_species_is_initial_trial_only': True,
        'novice_empty_plan_fallback_tested_profiles': 6,
        'unfamiliar_trial_every_third_completed_fight': True,
        'xp_after_death_settlement_seconds': 2,
        'revival_retry_batches_continue_after_backoff': True,
        'revival_first_delay_seconds': 4,
        'revival_retry_seconds': 15,
        'city_leisure': 'checked walking routes and brief stops',
        'bench_sitting_implemented': False,
        'runtime_unsolicited_speech_is_contextual': True,
        'random_scripted_bot_dialogues_enabled': False,
        'stable_personality_profiles': 6,
        'learning_uses_observed_hp_time_xp_gold': True,
        'learning_persistence': 'data/hunt-learning-NNN.json',
        'bot_help_requires_real_chat_request_echo': True,
        'human_party_requests': True,
        'human_friend_requests': True,
        'private_replies': True,
        'native_friend_private_serializers_verified': True,
        'contacts_live_windows_tested': False,
        'level_viewer': 'Show-Bot-Levels-And-Gold.cmd',
        'starter_monster_native_level': 3,
        'starter_character_levels': [1,2,3],
        'starter_map': 'garner',
        'native_damage_prefix_verified': True,
        'npc_junk_whitelist_count': len(json.loads((ROOT / 'assets' / 'junk-items.json').read_text())['items']),
        'npc_sale_requires_bag_and_gold': True,
        'spawn_counts_modified': False,
        'beginner_farm_point_cap_per_species': 64,
        'no_progress_farm_focus_seconds': [120,180],
        'market_catalog_tradeable_item_count': 1586,
        'stall_data_writer_captured': 'GameServer 0x4637e0, plain and five instance attributes',
        'live_stall_transactions_tested': False,
        'black_market_npc_barter_implemented': False,
        'prices_are_pilot_references': True,
        'bounded_prices_learn_from_confirmed_transactions': True,
        'history_journals_projected': 19,
        'later_history_exhaustively_supported': False,
        'basic_visible_confirmed_party_healing': True,
        'bank_actions_public_source_based': [26,27],
        'personal_trade_server_envelope': 811,
        'personal_trade_subcommands': list(range(812,820)),
        'own_trade_lock_has_no_server_echo': True,
        'bank_and_personal_trade_owner_binary_capture_this_release': False,
        'live_bank_or_personal_trade_windows_verified': False,
        'fountain_exact_object_location_verified': False,
        'city_pitches_use_verified_spawns_banks_and_guards': True,
        'sale_phrase_combinations_for_short_facts': 4800,
        'thirty_personalities_deferred': True,
        'quest_rewards_configurator': {'experience':9,'gold':5,'automatic_backup':True,'idempotent':True,'server_scripts_bundled':False},
        'free_inventory_or_gold_grants': False,
        'chat_ai': 'local rules only',
        'runtime': 'Python >=3.9; standard library only',
    }
    manifest.update(alpha56={'bot_tests':902,'native_tests':39,'legacy_tests':12,'native_profession_levels':[9,40],'bag_capacity':48,'stall_skill_level':3,'native_stall_goods':18,'gem_total_chance':.03,'gem_rate_independent':True,'gem_npc_stock_removed':True,'patchouli_npc_buyback':2000,'treant_root_npc_buyback':4000,'focused_loot':[1000,4915,684,860,861,862,863,864,865,866,1012],'live_windows_verified':False},status='Alpha56: owner NPC professions/bags/perpetual corals/jewellery, earned ground gem economy, static dungeon loading, focused XP and bounded network catchup; includes prior releases.',native_owner_shops_v2={'ordinary_trade_stock':True,'catalog_items':844,'with_installed_native_shops':529,'live_windows_verified':False},free_inventory_or_gold_grants='Only owner-authorized public bag expansions and profession/stall packages; no free gold, existing items/stats untouched',junk_classification_policy='New pickups limited to Patchouli/root/NP/eight selected gems; old safe junk can be sold; owned useful items protected')
    manifest.update(alpha57={'bot_tests':909,'native_tests':45,'blueprint_every_mob':True,'ground_protection_seconds':1,'possession_real_cost':True,'native_reaction_seconds':[.15,.21],'idle_recovery_seconds':60,'unproductive_travel_recovery_seconds':180,'live_windows_verified':False},status='Alpha57 cumulative: native Possession satiety fix, ground loot protection and universal blueprints, responsive farming and emergency recovery; Alpha58 forging/economy pending.')
    manifest.update(alpha58={'bot_tests':929,'native_tests':49,'legacy_tests':12,'gem_sellers':120,'native_forge_modes':[1,2,3,4,5],'normal_and_refining_combinations':True,'success_for_valid_operations':1.0,'normal_gem_cap':9,'created_socket_cap':2,'fusion_upgrade_cap':15,'island_portal_nodes':8,'island_routes':56,'native_tickets':43,'map_entrances':119,'live_windows_verified':False},status='Alpha58 cumulative: paid native crafting, gem market roles, source-backed island/ticket/event travel and native EXP consumables; includes Alpha57 stability/Possession fixes.')
    manifest.update(alpha59={'bot_tests':936,'native_tests':51,'legacy_tests':12,'classic_combat_spell_compatibility':True,'stall_state_id':99,'closure_resync_after_seconds':60,'live_windows_verified':False},status='Alpha59 cumulative: classic missing-core-spell fallback and bounded stall closure recovery; Alpha58 forging/economy preserved.')
    manifest.update(alpha60={'bot_tests':953,'native_tests':55,'legacy_tests':12,'critical_foreign_combat_supplies':True,'prepurchase_travel_planning':True,'source_rectangle_scouting':True,'normal_player_exp_scale_floor':100,'configured_exp_rate_unchanged':True,'native_xp_receipts':True,'fairy_growth_restored':True,'preventive_weapon_repair_threshold':1/3,'live_windows_verified':False},status='Alpha60 cumulative: source-backed scouting, mandatory staff/tickets, continuous native XP, restored fairy growth and preventive repair; includes previous releases.')
    manifest.update(alpha61={'bot_tests':971,'native_tests':55,'legacy_tests':12,'minimum_server_revision':60,'ground_camps_only':True,'required_coral_first':True,'prequote_repair_backoff':True,'hunting_coordinates_in_reports':True,'live_windows_verified':False},status='Alpha61 cumulative: land hunting, required coral priority, food/staff deadlock and repair/supply loops; native60 unchanged.')
    manifest.update(alpha62={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha62 limits ticket and merchant detours and preserves local hunting.')
    manifest.update(alpha63={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha63 reconciles pending merchant operations before optional task gates.')
    manifest.update(alpha64={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha64 prioritizes closer valid camps after prolonged absence of XP.')
    manifest.update(alpha65={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha65 preserves advancing camp searches and reserves foreground search work.')
    manifest.update(alpha66={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha66 defers optional city trips after confirmed hunting-site arrival.')
    manifest.update(alpha67={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha67 verifies hunting camp connectivity at each possible arrival.')
    manifest.update(alpha68={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha68 protects local hunting routes from optional city travel.')
    manifest.update(alpha69={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha69 protects hunting between routes when no XP is being earned.')
    manifest.update(alpha70={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha70 preserves working class weapons during equipment changes.')
    manifest.update(alpha71={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha71 earns essential supply gold from weak mobs and prioritizes Patchouli.')
    manifest.update(alpha72={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha72 recovers using verified mine exits and bounded shoreline routes.')
    manifest.update(alpha73={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha73 prioritizes in-range attacks and verifies recovery from ticket arrivals.')
    manifest.update(alpha74={'minimum_server_revision':60,'startup_spawn_placements':3503,'live_windows_verified':False},
                    status='Alpha74 imports startup spawns and resumes hunting after essential errands.')
    manifest.update(alpha75={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha75 keeps nearby combat ahead of optional journeys and tracks native progress independently.')
    manifest.update(alpha76={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha76 wakes combat decisions from world events and uses checked short movement with native attacks.')
    manifest.update(alpha77={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha77 compares owned tickets and portal landings against the current goal, and reacts to native damage sources.')
    manifest.update(alpha78={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha78 includes mine doors in walking alternatives and uses progress-aware entrance approaches.')
    manifest.update(alpha79={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha79 retains selected mine routes and prioritizes immediate native defensive attacks.')
    manifest.update(alpha80={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha80 applies a shared lower level limit to ordinary hunts.')
    manifest.update(alpha81={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha81 replans wounded retreats after a server movement stop.')
    manifest.update(alpha82={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha82 stages westbound Argent walks, spreads mine camps and buys ripe fairy fruit locally.')
    manifest.update(alpha83={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha83 removes shared Argent stop points and reuses checked routes to neighboring camps.')
    manifest.update(alpha84={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha84 learns delayed rewards and ranks combat and travel on comparable XP rates.')
    manifest.update(alpha85={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha85 indexes known mobs by level and distributes bots across distinct camp and transport choices.')
    manifest.update(alpha86={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha86 recovers exhausted farm paths, excludes Abandoned Mine 1, and buys nearby Strive amplifiers.')
    manifest.update(alpha87={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha87 follows precomputed land camps after confirmed travel landings and imports static server placements.')
    manifest.update(alpha88={'minimum_server_revision':60,'max_hunt_level_above':3,'live_windows_verified':False},
                    status='Alpha88 enforces the same upper level limit from camp selection to live attacks.')
    manifest.update(alpha89={'minimum_server_revision':60,'live_windows_verified':False},
                    status='Alpha89 keeps trivial aggro from diverting XP hunts and reports weak attack reasons.')
    manifest.update(alpha90={'minimum_server_revision':60,'world_expansion_installer':True,'installer_fix':3,'live_windows_verified':False},
                    status='Alpha90 Fix3 restores normal gems, adds forge combinations and curates normal monster loot.')
    manifest.update(alpha91={'bot_tests':1095,'native_tests':67,'legacy_tests':12,'runtime_limit':400,'gem_seller_roles':200,'seller_shift_seconds':[600,900],'healing_food_prices_updated':True,'fairy_and_booster_confirmation_nonblocking':True,'real_inventory_and_native_progress_required':True,'private_reports_bundled':False,'live_windows_verified':False}, status='Alpha91 repairs XP/maintenance/trade starvation, improves HP/SP recovery, and audits portal/ticket escape limits.')
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    (OUT / 'README.md').write_bytes((ROOT / 'knowledge/ALPHA91.md').read_bytes())
    print(artifact)
    print(manifest['sha256'])


if __name__ == '__main__':
    main()
