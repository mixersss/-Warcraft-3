"""Build a deterministic source-only Windows connection-alpha package."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'releases' / 'piratia' / 'auto-bots-23'
NAME = 'Piratia-Auto-Bots-Alpha23'


def main():
    sources = sorted(ROOT.glob('*.cmd')) + [ROOT / 'README.md', ROOT / 'PROTOCOL.md', ROOT / 'AGENTS.md']
    sources += sorted((ROOT / 'src').glob('*.py'))
    sources += sorted((ROOT / 'src').glob('*.ps1'))
    sources += sorted((ROOT / 'tests').glob('test_*.py'))
    sources += sorted((ROOT / 'tests').glob('test_*.ps1'))
    sources += sorted((ROOT / 'tests' / 'fixtures').glob('*.json'))
    sources += sorted((ROOT / 'assets').glob('*.json'))
    OUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT / f'{NAME}.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sources:
            info = zipfile.ZipInfo(f'{NAME}/{source.relative_to(ROOT).as_posix()}',
                                   date_time=(2026, 11, 11, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            data = source.read_bytes()
            if source.suffix == '.cmd':
                data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            archive.writestr(info, data)
    artifact = OUT / f'{NAME}.zip'
    manifest = {
        'artifact': artifact.name,
        'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
        'status': 'Spatial patch reservations, NPC admission, checked native turn routes, bounded decision rate and recovery food; live Windows validation pending',
        'native_windows_server_tested': False,
        'decision_frequency_max_hz': 4,
        'npc_destination_capacity': 2,
        'optional_npc_population_fraction': .1,
        'spatial_hunt_density_radius_cm': 2500,
        'native_route_preserves_astar_turns': True,
        'nested_partial_data_copy_rejected': True,
        'windows_session_guard_live_tested': False,
        'pure_python_tests_passed': 290,
        'full_python_suite_total': 298,
        'full_python_suite_passed': None,
        'socket_tests_not_rerun_this_release': 8,
        'last_full_network_regression': '240 passed in Alpha 20 including 8 local socket integration tests',
        'current_network_regression': '8 socket tests not rerun for Alpha23; transport unchanged from Alpha20 full240; Alpha21 full rerun was interrupted',
        'default_bot_count': 200,
        'default_mode': 'mixed',
        'cohort_tactics_at_200': {'farm':80,'hybrid':120},
        'hybrid_phase_seconds': [240,480],
        'finite_dialogue_scripts': 50,
        'dialogue_advances_on_real_peer_echo': True,
        'first_profession_in_both_tactics': True,
        'exclusive_target_cohort_tested': 200,
        'live_target_distribution_verified': False,
        'default_duration_seconds': 7200,
        'three_city_spawn_and_trainer_routes_verified': True,
        'chat_phrase_count': 589,
        'new_chat_phrases': 200,
        'live_two_hundred_connections_tested': False,
        'advanced_profession_requests_implemented': True,
        'advanced_profession_full_chains_implemented': False,
        'player_item_exchange_implemented': False,
        'story_chain': [200,203,204],
        'combat_skill_book_catalog_count': 83,
        'owned_chest_ids': [436,985,986,987,988],
        'native_action_serialization_compared': ['movement', 'normal attack', 'local speech', 'base attributes', 'NPC talk', 'quest selection', 'quest accept/deliver', 'item pickup', 'item use/equip', 'skill upgrade', 'return to city', 'NPC function selection', 'NPC purchase', 'NPC sale', 'party invite/accept/refuse/leave', 'stall create/view/buy/close', 'end action', 'world/trade chat'],
        'native_world_writers_captured': ['base info', 'look', 'append-look (4 slots)', 'skillbag', 'skill state', 'event', 'attribute range', 'initial kitbag with boat/instance', 'kitbag delta'],
        'powershell_state_regression': 'passed with PowerShell 7.4.6 on Linux; idempotent populations 1/10/30/60/100/200, rejection 0/201, credential preservation',
        'population_validation': 'both PowerShell helpers and Python launcher aligned: 1..200' ,
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
        'population_target': 400,
        'maximum_enabled_bots': 200,
        'four_hundred_live_connections_tested': False,
        'stall_session_seconds': 2400,
        'stall_live_population_fraction': .10,
        'voluntary_rest_live_population_fraction': .10,
        'stall_city_caps_at_200': {'garner':15,'magicsea':3,'darkblue':2},
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
        'level_viewer': 'Show-Bot-Levels.cmd',
        'starter_monster_native_level': 3,
        'starter_character_levels': [1,2,3],
        'starter_map': 'garner',
        'native_damage_prefix_verified': True,
        'npc_junk_whitelist_count': 38,
        'npc_sale_requires_bag_and_gold': True,
        'spawn_counts_modified': False,
        'beginner_farm_point_cap_per_species': 64,
        'no_progress_farm_focus_seconds': [120,180],
        'market_catalog_tradeable_item_count': 1575,
        'stall_data_writer_captured': 'GameServer 0x4637e0, plain and five instance attributes',
        'live_stall_transactions_tested': False,
        'black_market_npc_barter_implemented': False,
        'prices_are_pilot_references': True,
        'free_inventory_or_gold_grants': False,
        'chat_ai': 'local rules only',
        'runtime': 'Python >=3.9; standard library only',
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    (OUT / 'README.md').write_bytes((ROOT / 'README.md').read_bytes())
    print(artifact)
    print(manifest['sha256'])


if __name__ == '__main__':
    main()
