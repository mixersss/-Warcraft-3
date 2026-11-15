"""Restore ONLY bot supplier knowledge from a verified already-installed native patch."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def restore(resource,assets):
    native=ROOT/'server-shops/native'
    # Installed complete bundle places server-shops beside src/; source checkout uses sibling.
    if not native.exists():native=ROOT.parent/'piratia-city-shops/native'
    if not (native/'installer.py').is_file():raise ValueError('Для проверки серверного патча нужен полный комплект Piratia-Alpha52-Complete с папкой server-shops.')
    sys.path.insert(0,str(native))
    import installer
    server=installer.legacy.locate(resource);marker=server/installer.MARKER
    if not marker.exists():raise ValueError('Не найдена установленная серверная часть. Запусти INSTALL-SERVER-SHOPS.cmd; аккаунты и data не меняются.')
    previous=json.loads(marker.read_text());cat=installer.catalog()
    if (previous.get('catalog_sha256')!=installer.digest(installer.CATALOG.read_bytes()) or
        previous.get('implementation_sha256')!=installer.implementation_digest(cat)):
        raise ValueError('Серверный патч другой версии. Сначала обнови его через INSTALL-SERVER-SHOPS.cmd.')
    expected={p.as_posix() for p in installer.SERVER_FILES}
    if set(previous.get('installed_sha256',{}))!=expected:raise ValueError('Неполный журнал серверной установки')
    for name,digest in previous['installed_sha256'].items():
        if installer.digest((server/name).read_bytes())!=digest:raise ValueError('Серверные ресурсы изменились после патча; нужна проверка установщиком.')
    assets=Path(assets)
    if not (assets/'world-npcs.json').exists():raise ValueError('Не найдена папка assets ботов')
    raw=(json.dumps(installer.make_overlay(cat,previous),ensure_ascii=False,indent=2)+'\n').encode()
    target=assets/'owner-city-shops.json'
    if target.exists() and target.read_bytes()!=raw:
        backup=assets/'owner-city-shops.before-restore.json'
        if not backup.exists():backup.write_bytes(target.read_bytes())
    installer.atomic(target,raw)
    return {'restored':True,'shop_count':5,'catalog_revision':50,'server_unchanged':True,'restart_bots_required':True}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('resource',nargs='?');args=parser.parse_args()
    print('Останови ботов. Серверные файлы, клиент и data не изменяются.')
    selected=args.resource or input('Папка серверной resource: ').strip().strip('"')
    try:print(json.dumps(restore(selected,ROOT/'assets'),ensure_ascii=False,indent=2))
    except (OSError,ValueError,KeyError) as error:print('Ошибка:',str(error));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
