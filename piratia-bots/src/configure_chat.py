"""Set chat intensity without changing bot accounts, gameplay, rates or server."""
import argparse,json,os,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=['quiet','normal','lively']);args=p.parse_args()
    choice=args.mode
    if choice is None:
        print('1 — тихо; 2 — обычно; 3 — оживлённо. Настройка действует после перезапуска ботов.')
        choice={'1':'quiet','2':'normal','3':'lively'}.get(input('Режим [2]: ').strip() or '2')
    if choice is None:raise ValueError('Неизвестный режим')
    target=ROOT/'assets/dialogue-settings.json';data=json.loads(target.read_text(encoding='utf8'));data['intensity']=choice
    fd,path=tempfile.mkstemp(prefix='dialogue-',suffix='.tmp',dir=target.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
        os.replace(path,target)
    finally:Path(path).unlink(missing_ok=True)
    print('Сохранено:',choice,'— игра ботов не приостанавливается из-за чата.')
if __name__=='__main__':main()
