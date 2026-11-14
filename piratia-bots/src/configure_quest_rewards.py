"""Set ordinary quest XP/gold multipliers in the actual server dispatcher, with backups.

Byte-oriented edits preserve the owner's Lua encoding and unrelated server code.
No original server scripts, account files or SQL are bundled or accessed.
"""
import argparse,datetime,hashlib,os,re,sys,tempfile
from pathlib import Path

class PatchError(ValueError):pass

def branch(data,name):
    pattern=rb'(?m)^([ \t]*)(?:elseif|if)[ \t]+actions\[i\]\.func[ \t]*==[ \t]*'+name.encode()+rb'[ \t]+then[ \t]*\r?$'
    matches=list(re.finditer(pattern,data))
    if len(matches)!=1:raise PatchError('Нужна ровно одна ветка '+name+'; файл не изменён.')
    match=matches[0];indent=match[1]
    following=re.search(rb'(?m)^'+re.escape(indent)+rb'(?:elseif\b|else\b|end\b)',data[match.end():])
    if not following:raise PatchError('Не найдена граница ветки '+name+'.')
    finish=match.end()+following.start()
    body=data[match.end():finish]
    if len(body)>8000 or len(re.findall(rb'\blocal\s+ret\s*=\s*'+name.encode()+rb'\s*\(',body))!=1:
        raise PatchError('Неизвестный обработчик '+name+'; файл не изменён.')
    return match,finish,body

def patch(data,experience=9,gold=5):
    if any(type(x) is not int or not 1<=x<=100 for x in (experience,gold)):
        raise PatchError('Множители должны быть целыми числами от1до100.')
    newline=b'\r\n' if b'\r\n' in data else b'\n'
    edits=[]
    for name,rate in (('AddExp',experience),('AddMoney',gold)):
        match,finish,body=branch(data,name)
        # Refuse unknown additional actions instead of deleting custom quest logic.
        stripped=re.sub(rb'--[^\r\n]*',b'',body)
        stripped=re.sub(rb'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',b'""',stripped)
        calls=set(m.decode('ascii') for m in re.findall(rb'\b([A-Za-z_][A-Za-z_0-9.]*)\s*\(',stripped))
        if calls-{'PRINT','SystemNotice','Notice','GetExpState','AddExp','AddMoney','math.floor'}:
            raise PatchError('Ветка '+name+' содержит дополнительные функции; автоматическая правка отменена.')
        # Supported pre-existing rate edits may change arithmetic, but not global state.
        assignments=re.findall(rb'(?m)^\s*([^\r\n=]+?)\s*(?<![<>=~])=(?!=)',stripped)
        if any(not lhs.strip().startswith(b'local ') and lhs.strip() not in (b'actions[i].p1',b'actions[i].p2') for lhs in assignments):
            raise PatchError('Неизвестные изменения состояния в '+name+'; автоматическая правка отменена.')
        indent=match[1]+b'\t'
        lines=[f'-- PIRATIA_QUEST_RATES_V1 {name} x{rate}'.encode()]
        if name=='AddExp':
            lines.extend((b'local piratia_quest_bonus = GetExpState(character) / 100',
              f'local ret = AddExp(character, npc, math.floor(actions[i].p1 * piratia_quest_bonus * {rate}), math.floor(actions[i].p2 * piratia_quest_bonus * {rate}))'.encode()))
        else:lines.append(f'local ret = AddMoney(character, npc, math.floor(actions[i].p1 * {rate}))'.encode())
        lines.extend((b'if ret ~= LUA_TRUE then',b'\treturn LUA_FALSE',b'end'))
        replacement=newline+newline.join(indent+line for line in lines)+newline
        start=match.end()-(data[match.end()-1:match.end()]==b'\r')
        edits.append((start,finish,replacement))
    for start,finish,replacement in sorted(edits,reverse=True):data=data[:start]+replacement+data[finish:]
    return data

def discover(selected):
    selected=Path(selected).expanduser().resolve()
    if selected.is_file() and selected.suffix.lower()!='.lua':selected=selected.parent
    if selected.is_file():paths=[selected]
    elif selected.is_dir():
        paths=[]
        for directory,folders,files in os.walk(selected,followlinks=False):
            folders[:]=[n for n in folders if n.casefold() not in
                ('.git','data','node_modules','venv','.venv','backups','backup','logs','log')]
            for name in files:
                if name.lower().endswith('.lua'):paths.append(Path(directory)/name)
                if len(paths)>4000:raise PatchError('Слишком большая папка: укажи папку GameServer или resource.')
    else:raise PatchError('Такой папки или Lua-файла нет.')
    candidates=[]
    for path in paths:
        if path.is_symlink() or path.suffix.lower()!='.lua' or path.stat().st_size>4*1024*1024:continue
        try:path.resolve().relative_to(selected if selected.is_dir() else selected.parent)
        except ValueError:continue
        data=path.read_bytes()
        if all(re.search(rb'actions\[i\]\.func\s*==\s*'+name+rb'\b',data) for name in (b'AddExp',b'AddMoney')):
            candidates.append(path)
    if len(candidates)!=1:
        if not candidates:raise PatchError('Обработчик наград не найден. Укажи папку серверной части с resource/script, не клиента.')
        raise PatchError('Найдено несколько копий; укажи папку нужного GameServer:\n'+'\n'.join(map(str,candidates)))
    return candidates[0]

def apply(path,experience=9,gold=5):
    path=Path(path);original=path.read_bytes();updated=patch(original,experience,gold)
    if updated==original:return None
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    digest=hashlib.sha256(original).hexdigest()[:12]
    backup=path.with_name(path.name+f'.quest-rates-{stamp}-{digest}.bak')
    with backup.open('xb') as stream:
        stream.write(original);stream.flush();os.fsync(stream.fileno())
    if backup.read_bytes()!=original:raise PatchError('Не удалось проверить резервную копию; исходный файл не изменён.')
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix=path.name+'.',suffix='.tmp',delete=False) as stream:
            temporary=Path(stream.name);stream.write(updated);stream.flush();os.fsync(stream.fileno())
        if path.read_bytes()!=original:raise PatchError('Файл успел измениться другим процессом; правка отменена. Повтори после остановки сервера.')
        os.replace(temporary,path);temporary=None
    finally:
        if temporary:temporary.unlink(missing_ok=True)
    return backup

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path',nargs='?');parser.add_argument('--exp',type=int,default=9);parser.add_argument('--gold',type=int,default=5)
    args=parser.parse_args()
    selected=args.path or input('Вставь полный путь к папке сервера/GameServer: ').strip().strip('"')
    try:
        target=discover(selected);print('Найден обработчик: '+str(target))
        backup=apply(target,args.exp,args.gold)
        print('Резервная копия: '+str(backup) if backup else 'Эти множители уже установлены; файл не изменён.')
        print(f'Обычный опыт за квесты: x{args.exp}; золото за квесты: x{args.gold}.')
        print('Перезапусти GameServer, чтобы загрузить правку. Опыт мирных навыков и дроп не менялись.')
    except (OSError,PatchError) as error:
        print('Ошибка: '+str(error));return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
