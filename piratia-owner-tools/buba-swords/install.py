"""Copy only the explicit GM grant script; do not change NPCs, accounts or items."""
from pathlib import Path
import hashlib


def install(selected):
    p = Path(str(selected).strip().strip('"'))
    roots = (p, p/'resource', p.parent, p.parent/'resource')
    resource = next((r for r in roots if (r/'script/MisScript/NpcScript01.lua').is_file()), None)
    if resource is None:
        raise ValueError('Не найдена серверная resource. Укажи папку GameServer или resource.')
    changes = {}
    for name in ('BubaSwords.lua', 'BubaLevel35.lua'):
        raw = Path(__file__).with_name(name).read_bytes()
        target = resource/'script'/name
        if target.exists():
            if target.read_bytes() != raw:
                raise ValueError(name+' уже существует и отличается. Файл не перезаписан.')
        else:
            changes[target] = raw
    written = []
    try:
        for target, raw in changes.items():
            with target.open('xb') as stream:
                stream.write(raw)
            written.append(target)
            if hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(raw).digest():
                raise OSError('Не подтверждено копирование файла.')
    except BaseException:
        for target in written:
            target.unlink()
        raise
    return resource/'script/BubaSwords.lua'


if __name__ == '__main__':
    try:
        print('Установлены BubaSwords.lua и BubaLevel35.lua:', install(input('Папка GameServer или resource: ')).parent)
        print('Предметы ещё не выданы. Выполни GM-команду из README.md, когда buba в игре.')
    except (OSError, ValueError) as error:
        print('Ошибка:', str(error))
        raise SystemExit(1)
