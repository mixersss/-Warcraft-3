"""Build a deterministic source-only Windows connection-alpha package."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'releases' / 'piratia' / 'auto-bots-05'
NAME = 'Piratia-Auto-Bots-Alpha05'


def main():
    sources = [ROOT / 'Start-Bot.cmd', ROOT / 'README.md', ROOT / 'PROTOCOL.md']
    sources += sorted((ROOT / 'src').glob('*.py'))
    sources += sorted((ROOT / 'src').glob('*.ps1'))
    sources += sorted((ROOT / 'tests').glob('test_*.py'))
    sources += sorted((ROOT / 'tests').glob('test_*.ps1'))
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
        'status': 'automatic account/character creation and headless connection alpha; gameplay AI not implemented',
        'native_windows_server_tested': False,
        'automated_tests': 20,
        'powershell_state_regression': 'passed with PowerShell 7.4.6 on Linux; old ArgumentException reproduced',
        'windows_sql_dpapi_runtime_tested': False,
        'owner_confirmed_previous_release': {'account_creation': True, 'login': True, 'character_creation': True},
        'begin_play_format': 'classic character-name string, native client 0x51a4d0',
        'native_character_look_compared': True,
        'creation_appearance': {'type': 1, 'hair': 2000, 'face': 2554, 'source': 'native client character creator tables'},
        'native_gate_crypto_compared': ['3DES encrypt/decrypt', 'B encrypt/decrypt',
                                       'Noise encrypt/decrypt with evolving state'],
        'runtime': 'Python >=3.9; standard library only',
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    (OUT / 'README.md').write_bytes((ROOT / 'README.md').read_bytes())
    print(artifact)
    print(manifest['sha256'])


if __name__ == '__main__':
    main()
