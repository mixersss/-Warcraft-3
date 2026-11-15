"""Add missing mine/Abaddon maps to existing GameServer configs, with backups."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re

REQUIRED = ('eastgoaf', 'hell', 'hell2', 'hell3', 'hell4', 'hell5')
MAP = re.compile(rb'(?mi)^[ \t]*map[ \t]*=[ \t]*([a-zA-Z0-9_]+)[ \t]*(?=\r?$)')


def plan(selected):
    selected = Path(str(selected).strip().strip('"'))
    roots = (selected, selected.parent, selected.parent.parent)
    game = next((p for p in roots if (p / 'GameServer.cfg').is_file()), None)
    if game is None:
        raise ValueError('Нужна папка GameServer, в которой находится GameServer.cfg.')
    files = [game / 'GameServer.cfg']
    files += sorted(p for p in game.glob('GameServer*.cfg') if re.fullmatch(r'GameServer[0-9]+\.cfg',p.name))
    contents = {p: p.read_bytes() for p in files}
    loaded = {}
    for path, raw in contents.items():
        for match in MAP.finditer(raw):
            name = match[1].decode('ascii').lower()
            if name in loaded:
                raise ValueError('Одна карта прописана в нескольких конфигурациях: ' + name)
            loaded[name] = path
    if 'garner' not in loaded:
        raise ValueError('Не найдена существующая конфигурация Аргента.')
    missing = [name for name in REQUIRED if name not in loaded]
    resource = game / 'resource'
    for name in missing:
        folder = resource / name
        for relative in (name+'.blk', name+'.atr', 'ctrl.lua', 'entry.lua'):
            if not (folder / relative).is_file():
                raise ValueError('Нет ресурса карты: ' + name + '/' + relative)
    target = loaded['garner']
    raw = contents[target]
    matches = list(MAP.finditer(raw))
    if len(matches)+len(missing) > 100:
        raise ValueError('Превышен предел карт одного процесса.')
    changes = {}
    if missing:
        last = matches[-1]
        newline = b'\r\n' if b'\r\n' in raw else b'\n'
        addition = newline + newline.join(b'map = '+name.encode('ascii') for name in missing)
        changes[target] = raw[:last.end()]+addition+raw[last.end():]
    return contents, changes, {'added_maps': missing, 'already_configured': [name for name in REQUIRED if name in loaded],
                               'game_processes_added': 0, 'live_map_loading_verified': False}


def configure(selected, apply=False):
    originals, changes, report = plan(selected)
    if not apply or not changes:
        return dict(report, applied=False)
    # Stage all bytes before writing; credentials stay only in local config backups.
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backups = {}
    for path in changes:
        backup = path.with_name(path.name+'.before-dungeons-'+stamp+'.backup')
        with backup.open('xb') as stream:
            stream.write(originals[path])
        if backup.read_bytes() != originals[path]:
            raise OSError('Не подтверждена резервная копия конфигурации.')
        backups[path] = backup
    written = []
    try:
        for path, raw in changes.items():
            temporary = path.with_name(path.name+'.dungeons.tmp')
            with temporary.open('xb') as stream:
                stream.write(raw)
            temporary.replace(path)
            written.append(path)
    except BaseException:
        for path in written:
            path.write_bytes(originals[path])
        raise
    finally:
        for path in changes:
            path.with_name(path.name+'.dungeons.tmp').unlink(missing_ok=True)
    return dict(report, applied=True, backups=[p.name for p in backups.values()])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('game', nargs='?')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print('Останови GameServer перед изменением. База данных и условия входа в подземелья сохраняются.')
    try:
        selected = args.game or input('Папка GameServer (где GameServer.cfg): ')
        print(json.dumps(configure(selected, args.apply), ensure_ascii=False, indent=2))
        print('После запуска проверь в логе GameServer строки map [eastgoaf] ok! и map [hell...] ok!')
        print('Наличие map в cfg ещё не подтверждает загрузку. Плата, расписание и квестовые условия входа действуют.')
    except (OSError, ValueError) as error:
        print('Ошибка:', str(error))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
