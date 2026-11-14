"""Rebuild private source-backed knowledge locally; never execute or upload server Lua."""
import argparse,os,sys,tempfile
from pathlib import Path
from audit_mechanics import locate
from mechanics import MechanicsKnowledge

def learn(resource,destination,builder):
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    descriptor,name=tempfile.mkstemp(dir=destination.parent,prefix='mechanics-',suffix='.tmp');os.close(descriptor)
    temporary=Path(name)
    try:
        builder(Path(resource),temporary)
        verified=MechanicsKnowledge(temporary)
        os.replace(temporary,destination)
        return verified.summary()
    finally:temporary.unlink(missing_ok=True)

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    root=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',nargs='?');a=p.parse_args()
    selected=a.path or input('Папка GameServer или его resource: ').strip().strip('"')
    sys.path.insert(0,str(root/'tools'))
    from build_mechanics import project
    try:
        resource=locate(selected);output=root/'data'/'knowledge'/'mechanics.json'
        summary=learn(resource,output,project)
        print('Личная база знаний обновлена: '+str(output))
        print(f"Lua-файлов:{summary['lua_files']}; функций:{summary['named_functions']}; требуют повторной сверки:{summary['requires_reaudit']}.")
        print('Перезапусти ботов, чтобы загрузить её. Серверные Lua и данные персонажей не изменены и никуда не отправлены.')
    except (OSError,ValueError,KeyError,TypeError) as error:
        print('Не удалось обновить знания: '+str(error));return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
