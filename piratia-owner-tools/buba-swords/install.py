"""Copy only the explicit GM grant script; do not change NPCs, accounts or items."""
from pathlib import Path
import hashlib
import json
import os
import tempfile
from datetime import datetime


def install(selected):
    p = Path(str(selected).strip().strip('"'))
    roots = (p, p/'resource', p.parent, p.parent/'resource')
    resource = next((r for r in roots if (r/'script/MisScript/NpcScript01.lua').is_file()), None)
    if resource is None:
        raise ValueError('Не найдена серверная resource. Укажи папку GameServer или resource.')
    previous = json.loads(Path(__file__).with_name('previous-script-sha256.json').read_text())
    changes = {}
    for name in ('BubaSwords.lua', 'BubaLevel35.lua', 'BubaNPC.lua'):
        raw = Path(__file__).with_name(name).read_bytes()
        target = resource/'script'/name
        if target.exists():
            if target.read_bytes() != raw:
                if hashlib.sha256(target.read_bytes()).hexdigest() not in previous.get(name, []):
                    raise ValueError(name+' содержит неизвестные изменения. Файл не перезаписан.')
                changes[target] = raw
        else:
            changes[target] = raw
    originals = {p:p.read_bytes() if p.exists() else None for p in changes}
    for target, raw in originals.items():
        if raw is not None:
            backup = target.with_name(target.name+'.before-fix03-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.backup')
            with backup.open('xb') as stream:stream.write(raw)
            if backup.read_bytes()!=raw:raise OSError('Не подтверждена резервная копия.')
    written = []
    try:
        for target, raw in changes.items():
            fd,temporary=tempfile.mkstemp(dir=target.parent,prefix=target.name+'.',suffix='.tmp')
            try:
                with os.fdopen(fd,'wb') as stream:stream.write(raw)
                os.replace(temporary,target)
            finally:Path(temporary).unlink(missing_ok=True)
            written.append(target)
            if hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(raw).digest():
                raise OSError('Не подтверждено копирование файла.')
    except BaseException:
        for target in written:
            if originals[target] is None:target.unlink()
            else:target.write_bytes(originals[target])
        raise
    return resource/'script/BubaSwords.lua'


if __name__ == '__main__':
    try:
        print('Установлены три скрипта Fix03:', install(input('Папка GameServer или resource: ')).parent)
        print('Предметы ещё не выданы. Введи &lua dofile(GetResPath("script/BubaNPC.lua")), затем поговори с НПС за buba.')
    except (OSError, ValueError) as error:
        print('Ошибка:', str(error))
        raise SystemExit(1)
