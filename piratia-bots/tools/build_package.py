"""Build a deterministic source-only Windows connection-alpha package."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'releases' / 'piratia' / 'auto-bots-12'
NAME = 'Piratia-Auto-Bots-Alpha12'


def main():
    sources = sorted(ROOT.glob('Start*.cmd')) + [ROOT / 'README.md', ROOT / 'PROTOCOL.md']
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
        'status': 'exclusive mob targets, balanced farm zones, bounded stuck/no-damage recovery; 15 quests + 15 farm with shared first-profession priority; live verification pending',
        'native_windows_server_tested': False,
        'pure_python_tests_passed': 102,
        'full_python_suite_total': 110,
        'socket_tests_not_rerun_this_release': 8,
        'last_full_network_regression': '24 passed in Alpha 06',
        'current_network_regression': '8 socket tests not rerun; previous run was blocked by sandbox',
        'default_bot_count': 30,
        'default_mode': 'mixed',
        'cohort_tactics_at_30': {'quests':15,'farm':15},
        'first_profession_in_both_tactics': True,
        'exclusive_target_and_zone_cohort_tested': 30,
        'live_target_distribution_verified': False,
        'default_duration_seconds': 3600,
        'three_city_spawn_and_trainer_routes_verified': True,
        'chat_phrase_count': 107,
        'live_thirty_connections_tested': False,
        'native_action_serialization_compared': ['movement', 'normal attack', 'local speech', 'base attributes', 'NPC talk', 'quest selection', 'quest accept/deliver', 'item pickup', 'item use/equip', 'skill upgrade', 'return to city'],
        'native_world_writers_captured': ['base info', 'look', 'append-look (4 slots)', 'skillbag', 'skill state', 'event', 'attribute range', 'initial kitbag with boat/instance', 'kitbag delta'],
        'powershell_state_regression': 'passed with PowerShell 7.4.6 on Linux; idempotent populations 1/10/30/60, rejection 0/61, credential preservation',
        'fix01': 'secondary-password helper population limit aligned with launcher: 1..60' ,
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
        'maximum_enabled_bots': 60,
        'four_hundred_live_connections_tested': False,
        'chat_ai': 'local rules only',
        'runtime': 'Python >=3.9; standard library only',
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    (OUT / 'README.md').write_bytes((ROOT / 'README.md').read_bytes())
    print(artifact)
    print(manifest['sha256'])


if __name__ == '__main__':
    main()
