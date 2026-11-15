"""Copy only the explicit GM grant script; do not change NPCs, accounts or items."""
from pathlib import Path
import hashlib


def install(selected):
    p = Path(str(selected).strip().strip('"'))
    roots = (p, p/'resource', p.parent, p.parent/'resource')
    resource = next((r for r in roots if (r/'script/MisScript/NpcScript01.lua').is_file()), None)
    if resource is None:
        raise ValueError('Не найдена серверная resource. Укажи папку GameServer или resource.')
    source = Path(__file__).with_name('BubaSwords.lua')
    target = resource/'script/BubaSwords.lua'
    raw = source.read_bytes()
    if target.exists():
        if target.read_bytes() != raw:
            raise ValueError('BubaSwords.lua уже существует и отличается. Файл не перезаписан.')
        return target
    # Exclusive creation: no accidental overwrite of an existing server script.
    with target.open('xb') as stream:
        stream.write(raw)
    if hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(raw).digest():
        raise OSError('Не подтверждено копирование файла.')
    return target


if __name__ == '__main__':
    try:
        print('Установлен:', install(input('Папка GameServer или resource: ')))
        print('Предметы ещё не выданы. Выполни GM-команду из README.md, когда buba в игре.')
    except (OSError, ValueError) as error:
        print('Ошибка:', str(error))
        raise SystemExit(1)
