"""Read-only checks of the client's Junior possession animation tables/assets."""
import json
from pathlib import Path
import struct


def table_record(path, stride, identity):
    raw = path.read_bytes()
    if len(raw) < 4 or struct.unpack_from('<I', raw)[0] != stride or (len(raw)-4) % stride:
        raise ValueError('Неизвестный формат таблицы: ' + path.name)
    matches = [raw[p:p+stride] for p in range(4, len(raw), stride)
               if struct.unpack_from('<I', raw, p+4)[0] == identity]
    if len(matches) != 1:
        raise ValueError('Не найдена единственная запись ' + str(identity) + ': ' + path.name)
    return matches[0]


def check(client):
    root = Path(str(client).strip().strip('"'))
    tables = root / 'scripts/table'
    state = table_record(tables/'skilleff.bin', 264, 174)
    effect = struct.unpack_from('<H', state, 250)[0]
    animation = table_record(tables/'sceneffectinfo.bin', 208, effect)
    expected = b'futi8.par'
    files = [p for p in root.rglob('*.par') if p.name.casefold() == 'futi8.par']
    return {'client_state_174': True, 'junior_effect_id': effect,
            'expected_effect_id': 534, 'effect_names_futi8': expected in animation.lower(),
            'futi8_par_found': bool(files),
            'effect_locations': [str(p.relative_to(root)) for p in files],
            'server_effect_confirmed': False,
            'note': 'Файлы не изменены. Таблицы/наличие par не доказывают применение навыка сервером.'}


def main():
    print('Проверка анимации Джун: укажи папку ИГРЫ с Game.exe. Файлы не изменяются.')
    try:
        print(json.dumps(check(input('Папка клиента: ')), ensure_ascii=False, indent=2))
    except (OSError, ValueError) as error:
        print('Ошибка:', str(error))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
