"""Compare the knowledge snapshot to selected server resources; never export Lua content."""
import argparse,hashlib,json,sys
from pathlib import Path

def locate(selected):
    selected=Path(selected).expanduser()
    if selected.is_file():selected=selected.parent
    for root in (selected/'resource',selected,selected.parent/'resource'):
        if (root/'script').is_dir():return root
    raise ValueError('Не найдена папка resource/script. Укажи серверную папку, не папку клиента.')

def audit(root,data):
    root=Path(root).resolve();records=[]
    expected={path:info['sha256'] for path,info in data['source_files'].items()}
    expected.update(data['source_tables'])
    for relative,digest in expected.items():
        path=(root/relative).resolve()
        try:path.relative_to(root)
        except ValueError:raise ValueError('Недопустимый путь исходника в справочнике')
        if not path.is_file():records.append({'path':relative,'state':'missing'});continue
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        records.append({'path':relative,'state':'same' if actual==digest else 'changed','sha256':actual})
    changed={r['path'] for r in records if r['state']!='same'}
    extra=sorted(p.relative_to(root).as_posix() for p in root.rglob('*.lua')
                 if p.relative_to(root).as_posix() not in data['source_files'])
    functions={f['key']:f for f in data['functions']}
    affected=[c['id'] for c in data['cards'] if
              (changed or extra) and (c.get('review_status') in ('reviewed_rules','requires_reaudit') or
              any(functions[key]['path'] in changed for key in c['evidence']))]
    return {'files':records,'matching':sum(r['state']=='same' for r in records),
            'changed':sum(r['state']=='changed' for r in records),'missing':sum(r['state']=='missing' for r in records),
            'additional_lua_files':extra,'source_snapshot_matches':not changed and not extra,'mechanics_requiring_source_review':affected,
            'native_engine_audited':False,'file_contents_exported':False}

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',nargs='?');p.add_argument('--output',type=Path)
    a=p.parse_args();base=Path(__file__).resolve().parents[1]
    selected=a.path or input('Полный путь к папке GameServer или resource: ').strip().strip('"')
    try:
        root=locate(selected);data=json.loads((base/'assets/mechanics.json').read_text());report=audit(root,data)
        print(f"Совпадают:{report['matching']}; изменены:{report['changed']}; отсутствуют:{report['missing']}; новых Lua:{len(report['additional_lua_files'])}.")
        print('Правила для сверки: '+(', '.join(report['mechanics_requiring_source_review']) or 'нет изменений в опорных Lua-файлах'))
        print('Это сравнение файлов, а не проверка исполнения внутри GameServer.')
        output=a.output or base/'server-mechanics-audit.json';output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print('Отчёт: '+str(output))
    except (OSError,ValueError) as error:print('Ошибка: '+str(error));return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
