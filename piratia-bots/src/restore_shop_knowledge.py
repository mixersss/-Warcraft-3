"""Restore ONLY bot supplier knowledge from a verified already-installed native patch."""
import argparse,json,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def restore(resource,assets):
    native=ROOT/'server-shops/native'
    # Installed complete bundle places server-shops beside src/; source checkout uses sibling.
    if not native.exists():native=ROOT.parent/'piratia-city-shops/native'
    if not (native/'installer.py').is_file():raise ValueError('Для проверки серверного патча нужен полный комплект Piratia-Alpha62-Complete с папкой server-shops.')
    sys.path.insert(0,str(native))
    import installer
    server=installer.legacy.locate(resource);marker=server/installer.MARKER
    if not marker.exists():raise ValueError('Не найдена установленная серверная часть. Запусти INSTALL-SERVER-SHOPS.cmd; аккаунты и data не меняются.')
    previous=json.loads(marker.read_text());cat=None;catalog_sha=None
    for path in (installer.CATALOG,native/'catalog-alpha55.json',native/'catalog-alpha50.json',native/'catalog-alpha48.json'):
        if not path.exists():continue
        candidate=json.loads(path.read_text());sha=installer.digest(path.read_bytes())
        if previous.get('catalog_sha256')==sha and previous.get('implementation_sha256')==installer.implementation_digest(candidate):cat=candidate;catalog_sha=sha;break
    if cat is None:
        raise ValueError('Серверный патч другой версии. Сначала обнови его через INSTALL-SERVER-SHOPS.cmd.')
    if cat.get('catalog_revision',0)>=58:
        craft=previous.get('forge_success',{})
        path=server/'script/calculate/forge.lua'
        if not craft.get('installed_sha256') or not path.is_file() or installer.digest(path.read_bytes())!=craft['installed_sha256']:
            raise ValueError('Изменена серверная ковка или отсутствует её контрольная запись; запусти INSTALL-SERVER-SHOPS.cmd.')
    expected={p.as_posix() for p in installer.SERVER_FILES}
    if set(previous.get('installed_sha256',{}))!=expected:raise ValueError('Неполный журнал серверной установки')
    changed=[name for name,digest in previous['installed_sha256'].items() if installer.digest((server/name).read_bytes())!=digest]
    if changed:
        lua_names={p.as_posix() for p in installer.SERVER_FILES[:2]}
        if set(changed)-lua_names:raise ValueError('Изменились НПС или таблицы предметов после патча; нужна проверка установщиком.')
        npc=(server/installer.SERVER_FILES[0]).read_bytes().replace(b'\r\n',b'\n')
        a,b=installer.block_span(npc,2);owned=installer.render(cat).rstrip(b'\n')
        if npc[a:b]!=owned:raise ValueError('Изменён сам блок новых магазинов; восстановление остановлено.')
        outside=npc[:a]+npc[b:]
        if re.search(rb'function\s+Owner\w*\s*\(',outside):raise ValueError('Обнаружено внешнее переопределение функций магазинов.')
        sdk=(server/installer.SERVER_FILES[1]).read_bytes().replace(b'\r\n',b'\n')
        if sdk.count(installer.OPEN_HOOK)!=1 or sdk.count(installer.BUY_HOOK)!=1 or sdk.count(installer.BUY_ANCHOR+installer.BUY_HOOK)!=1:
            raise ValueError('Изменены точки подключения покупки/меню магазинов.')
    assets=Path(assets)
    if not (assets/'world-npcs.json').exists():raise ValueError('Не найдена папка assets ботов')
    overlay=installer.make_overlay(cat,previous);overlay['catalog_sha256']=catalog_sha
    raw=(json.dumps(overlay,ensure_ascii=False,indent=2)+'\n').encode()
    target=assets/'owner-city-shops.json'
    if target.exists() and target.read_bytes()!=raw:
        backup=assets/'owner-city-shops.before-restore.json'
        if not backup.exists():backup.write_bytes(target.read_bytes())
    installer.atomic(target,raw)
    return {'restored':True,'shop_count':len(overlay['npcs']),'catalog_revision':overlay['catalog_revision'],'outside_lua_edits_preserved':changed,'server_unchanged':True,'restart_bots_required':True}

def ensure_shop_knowledge(assets,candidates=None,minimum_revision=48):
    """Before starting workers, recover a missing overlay from a few known roots only."""
    from owner_shops import read_overlay
    assets=Path(assets)
    try:
        current=read_overlay(assets)
        if current and current.get('fresh_fairies') and current.get('catalog_revision',0)>=minimum_revision:return {'ready':True,'restored':False}
    except (OSError,ValueError,TypeError,KeyError,AttributeError):pass
    if candidates is None:
        parent=assets.parent.parent
        candidates=[parent/'[1] GameServer/resource',parent/'GameServer/resource',
                    Path(r'C:\PKO138 + Tools\[1] GameServer\resource'),Path(r'C:\PKO138+Tools\[1] GameServer\resource')]
    problems=[]
    saved=assets.parent/'data/server-source.json'
    try:
        location=json.loads(saved.read_text()).get('resource')
        if isinstance(location,str):candidates=[Path(location),*candidates]
    except (OSError,ValueError,TypeError,AttributeError):pass
    for path in dict.fromkeys(map(Path,candidates)):
        if not (path/'owner-city-shops-v2.json').is_file():continue
        try:
            result=restore(path,assets)
            return dict(result,ready=result['catalog_revision']>=minimum_revision,problem='' if result['catalog_revision']>=minimum_revision else 'Нужно обновить серверные магазины через INSTALL-SERVER-SHOPS.cmd')
        except (OSError,ValueError,KeyError) as error:problems.append(str(error))
    return {'ready':False,'restored':False,'problem':problems[-1] if problems else 'Справочник магазинов отсутствует; RESTORE-BOT-SHOPS.cmd с серверной resource'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('resource',nargs='?');args=parser.parse_args()
    print('Останови ботов. Серверные файлы, клиент и data не изменяются.')
    selected=args.resource or input('Папка серверной resource: ').strip().strip('"')
    try:print(json.dumps(restore(selected,ROOT/'assets'),ensure_ascii=False,indent=2))
    except (OSError,ValueError,KeyError) as error:print('Ошибка:',str(error));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
