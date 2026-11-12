"""Build a deterministic source-only Windows connection-alpha package."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'releases' / 'piratia' / 'auto-bots-16'
NAME = 'Piratia-Auto-Bots-Alpha16'


def main():
    sources = sorted(ROOT.glob('*.cmd')) + [ROOT / 'README.md', ROOT / 'PROTOCOL.md']
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
        'status': '200-bot combat/city/activity/chat pilot; native serializers and dispatch checked; live Windows validation pending',
        'native_windows_server_tested': False,
        'pure_python_tests_passed': 174,
        'full_python_suite_total': 182,
        'socket_tests_not_rerun_this_release': 8,
        'last_full_network_regression': '24 passed in Alpha 06',
        'current_network_regression': '8 socket tests not rerun; previous run was blocked by sandbox',
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
        'native_action_serialization_compared': ['movement', 'normal attack', 'local speech', 'base attributes', 'NPC talk', 'quest selection', 'quest accept/deliver', 'item pickup', 'item use/equip', 'skill upgrade', 'return to city', 'NPC function selection', 'NPC purchase', 'party invite/accept/refuse/leave', 'stall create/view/buy/close', 'end action', 'world/trade chat'],
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
