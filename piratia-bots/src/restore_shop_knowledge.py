"""Restore ONLY bot supplier knowledge from a verified already-installed native patch."""
import argparse,json,sys,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def verify_shop_actors(installer, current, catalog, receipt):
    """Verify the actors the bots actually use in both resource formats."""
    text, binary = installer.SERVER_FILES[2:4]
    rows = installer.legacy.npc_rows(current[text])
    ids = list(receipt.get('npc_ids', []))
    positions = list(receipt.get('positions_m', installer.legacy.DEFAULT_POINTS))
    shops = list(catalog['shops'])
    if receipt.get('world_expansion') and type(receipt.get('world_supply_npc_id')) is int:
        from world_expansion import LOCATION
        ids.append(receipt['world_supply_npc_id']);positions.append(LOCATION)
        shops.append({'function':'ForgeSupply','name':'Forge Supply'})
    if len(ids)!=len(shops) or len(set(ids))!=len(shops) or len(positions)!=len(shops):
        raise ValueError('Неполный список НПС в журнале установки.')
    wanted = set(ids)
    for shop, identity, position in zip(shops, ids, positions):
        row = rows.get(identity)
        point = b','.join(str(value*100+50).encode() for value in position)
        if (row is None or row[11].strip()!=shop['function'].encode()
                or row[1].strip()!=shop['name'].encode() or int(row[3])!=17
                or row[5].strip()!=point or row[6].strip()!=point):
            raise ValueError(f'garnernpc.txt: изменилась привязка НПС {identity} ({shop["name"]}).')
    records = [record for record in installer.legacy.binary_rows(current[binary])
               if struct.unpack_from('<I',record,4)[0] in wanted]
    if {struct.unpack_from('<I',record,4)[0] for record in records}!=wanted or len(records)!=len(ids):
        raise ValueError('garnerNPC.bin: отсутствует или повторяется запись торговца.')
    try:
        installer.legacy.validate_npcs(
            b'\n'.join(b'\t'.join(rows[identity]) for identity in ids),
            struct.pack('<I',428)+b''.join(records))
    except ValueError as error:
        raise ValueError(f'garnerNPC.bin: {error}') from error


def verify_shop_script(installer,current,catalog,receipt):
    npc_file=installer.SERVER_FILES[0]
    npc=current[npc_file].replace(b'\r\n',b'\n')
    a,b=installer.block_span(npc,2)
    owned=installer.render(catalog).rstrip(b'\n')
    variants={owned}
    known_world=set()
    if receipt.get('world_expansion') and catalog.get('catalog_revision',0)>=60:
        from native_gems import VANILLA, enable_script
        from world_expansion import START, END, world_script
        world=world_script().rstrip(b'\n')
        enabled=enable_script(owned+b'\n'+world)
        start=enabled.index(START)
        variants.add(enabled[:start].rstrip(b'\n'))
        known_world={world, enabled[start:]}
        roll=re.compile(rb'(?m)^    if math\.random\(1,100\)>3 then return end\n'
                        rb'    Owner56GemStats\.rolls=Owner56GemStats\.rolls\+1\n'
                        rb'    Owner57GroundDrop\(dead,Owner56GemIDs\[math\.random\(1,8\)\],1\)')
        known_world.add(roll.sub(lambda _:VANILLA,world))
        known_world.add(world.replace(b'Owner56GemIDs[math.random(1,8)]',b'ground_stones[math.random(1,8)]')
                        .replace(b'local replaced={[1000]=true}\n',
                                 b'local replaced={[1000]=true}\nfor _,id in ipairs(ground_stones) do replaced[id]=true end\n'))
    if npc[a:b] not in variants:
        raise ValueError('NpcScript01.lua: изменён блок работы торговцев.')
    outside=npc[:a]+npc[b:]
    if known_world and outside.count(START)==outside.count(END)==1:
        start=outside.index(START)
        end=outside.index(END,start)+len(END)
        if outside[start:end] in known_world:
            outside=outside[:start]+outside[end:]
    public=set(re.findall(rb'(?m)^function\s+(Owner\w*)\s*\(',owned))
    external=set(re.findall(rb'(?m)^\s*function\s+(Owner\w*)\s*\(',outside))
    # The expansion owns the drop hook; it does not serve NPC trade.
    if (public & external)-{b'Owner56GroundGem'} or re.search(rb'(?m)^\s*OwnerNativeShops\s*[=\[]',outside):
        raise ValueError('NpcScript01.lua: найдено стороннее переопределение торговцев.')


def verify_shop_sdk(installer, raw):
    sdk=raw.replace(b'\r\n',b'\n')
    if sdk.count(installer.OPEN_HOOK)!=1 or sdk.count(installer.BUY_HOOK)!=1 or sdk.count(installer.BUY_ANCHOR+installer.BUY_HOOK)!=1:
        raise ValueError('NpcSdk.lua: изменены обработчики покупки или меню.')


def verify_changed_resources(installer, current, changed, cat, receipt):
    script, sdk, text, binary, items_text, items_bin = installer.SERVER_FILES
    if script in changed:
        verify_shop_script(installer,current,cat,receipt)
    if sdk in changed:
        verify_shop_sdk(installer,current[sdk])
    if {text,binary}.intersection(changed):
        verify_shop_actors(installer,current,cat,receipt)
    expected = installer.offers(cat)
    if receipt.get('world_expansion') and type(receipt.get('world_supply_npc_id')) is int:
        from world_expansion import SUPPLIES, item_text
        known=item_text(current[items_text],set(SUPPLIES))
        expected.update({i:{'id':i,'kind':int(known[i][10]),'price':price} for i,price in SUPPLIES.items()})
    for path, verify in ((items_text,installer.patch_text),(items_bin,installer.patch_binary)):
        if path not in changed:
            continue
        try:
            if verify(current[path],expected)!=current[path]:
                raise ValueError('изменилась цена предмета из каталога торговцев')
        except ValueError as error:
            raise ValueError(f'{path.name}: {error}.') from error


def restore(resource,assets):
    native=ROOT/'server-shops/native'
    # Installed complete bundle places server-shops beside src/; source checkout uses sibling.
    if not native.exists():native=ROOT.parent/'piratia-city-shops/native'
    if not (native/'installer.py').is_file():raise ValueError('Для проверки серверного патча нужен полный комплект Piratia-Alpha73-Complete с папкой server-shops.')
    sys.path.insert(0,str(native))
    import installer
    server=installer.legacy.locate(resource);marker=server/installer.MARKER
    if not marker.exists():raise ValueError('Не найдена установленная серверная часть. Запусти INSTALL-SERVER-SHOPS.cmd; аккаунты и data не меняются.')
    previous=json.loads(marker.read_bytes());cat=None;catalog_sha=None
    for path in (installer.CATALOG,native/'catalog-alpha55.json',native/'catalog-alpha50.json',native/'catalog-alpha48.json'):
        if not path.exists():continue
        candidate=json.loads(path.read_bytes());sha=installer.digest(path.read_bytes())
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
    current={path:(server/path).read_bytes() for path in installer.SERVER_FILES}
    changed=[path for path,raw in current.items()
             if installer.digest(raw)!=previous['installed_sha256'][path.as_posix()]]
    verify_changed_resources(installer,current,changed,cat,previous)
    assets=Path(assets)
    if not (assets/'world-npcs.json').exists():raise ValueError('Не найдена папка assets ботов')
    overlay=installer.make_overlay(cat,previous);overlay['catalog_sha256']=catalog_sha
    raw=(json.dumps(overlay,ensure_ascii=False,indent=2)+'\n').encode()
    target=assets/'owner-city-shops.json'
    if target.exists() and target.read_bytes()!=raw:
        backup=assets/'owner-city-shops.before-restore.json'
        if not backup.exists():backup.write_bytes(target.read_bytes())
    installer.atomic(target,raw)
    return {'restored':True,'shop_count':len(overlay['npcs']),'catalog_revision':overlay['catalog_revision'],'verified_changed_files':[path.as_posix() for path in changed], 'outside_lua_edits_preserved':[path.as_posix() for path in changed if path.suffix=='.lua'],'server_unchanged':True,'restart_bots_required':True}

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
        location=json.loads(saved.read_bytes()).get('resource')
        if isinstance(location,str):candidates=[Path(location),*candidates]
    except (OSError,ValueError,TypeError,AttributeError):pass
    for path in dict.fromkeys(map(Path,candidates)):
        if not (path/'owner-city-shops-v2.json').is_file():continue
        try:
            result=restore(path,assets)
            ready=result['catalog_revision']>=minimum_revision
            if ready:
                from diagnostic_io import write_snapshot
                write_snapshot(saved,{'resource':str(path.resolve())})
            return dict(result,ready=ready,problem='' if ready else 'Нужно обновить серверные магазины через INSTALL-SERVER-SHOPS.cmd')
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
