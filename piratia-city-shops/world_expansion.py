"""Install ordinary gem drops, curated loot and an additional Argent shop."""
import argparse
import base64
import hashlib
import json
import re
import struct
import sys
import zlib
from datetime import datetime
from pathlib import Path

import install as city
import personal_forge as forge

ROOT = Path(__file__).resolve().parent
GEMS = dict(zip(range(5609, 5617), (860, 861, 862, 863, 864, 865, 866, 1012)))
TROPHIES = {5618+level-1: (1591, level*1000) for level in range(1, 31)}
LEGACY = dict(zip((*range(6400, 6408), *range(6410, 6440)), (*GEMS, *TROPHIES)))
PRODUCTS = {
    category: {int(i): price for i, price in prices.items()}
    for category, prices in json.loads((ROOT / "supply_products.json").read_bytes()).items()
}
SUPPLIES = {i: price for offers in PRODUCTS.values() for i, price in offers.items()}
WEAPONS = {i: 1_800_000 for i in range(2331, 2345)}
START = b"-- WORLD_EXPANSION_BEGIN"
END = b"-- WORLD_EXPANSION_END"
VENDOR = b"ForgeSupply"
LOCATION = (2260, 2770)

def supply_overlay(identity):
    """The real additional shop, with the same pages as world_script()."""
    import csv
    with (ROOT/'native/item-database.csv').open(encoding='utf-8-sig') as stream:
        names={r['id']:r['name_ru'] for r in csv.DictReader(stream)}
    mapping={};labels={};number=0
    for category,offers in PRODUCTS.items():
        items=list(offers)
        heading={'cooking':'Cooking','manufacturing':'Manufacturing'}[category]
        for start in range(0,len(items),36):
            number+=1
            labels[str(number)]=heading if len(items)<=36 else f'{heading} {start//36+1}'
            mapping.update({str(i):number for i in items[start:start+36]})
    return {'key':'garner:owner-v2:'+str(identity),'source_id':identity,'map':'garner',
            'name':'Forge Supply','model':17,'position':[v*100+50 for v in LOCATION],
            'region':'Argent City','script_function':'ForgeSupply','script_found':True,
            'services':['trade'],'mission_source_ids':[],'menu_handlers':['OwnerOpenTrade'],
            'offers':list(SUPPLIES),'verified_shop_binding':True,'conditions_not_evaluated':True,
            'source_kind':'owner-world-supplies','menu_pages':mapping,'menu_labels':labels,'live_server_seen':False},names


def client_price_records(raw):
    """Existing original client items only; no records or effects are invented."""
    import csv
    existing=table_bin(raw)
    prices=SUPPLIES | WEAPONS | {684:200_000}
    with (ROOT/'native/item-database.csv').open(encoding='utf-8-sig') as stream:
        kinds={int(row['id']):int(row['kind']) for row in csv.DictReader(stream) if row['kind']}
    return {i:{'kind':kinds[i],'price':price} for i,price in prices.items() if i in existing},sorted(set(prices)-existing.keys())


def table_bin(raw):
    size = 868
    if not raw.startswith(struct.pack("<I", size)) or (len(raw)-4) % size:
        raise ValueError("Неизвестный формат ItemInfo.bin.")
    rows = {}
    for offset in range(4, len(raw), size):
        record = raw[offset:offset+size]
        identity = struct.unpack_from("<I", record, 4)[0]
        if identity in rows or identity != struct.unpack_from("<I", record, 108)[0]:
            raise ValueError(f"Неверный ID в ItemInfo.bin: {identity}")
        rows[identity] = record
    return rows


def item_text(raw, relevant_ids):
    rows = {}
    for line in raw.splitlines(keepends=True):
        fields = line.rstrip(b"\r\n").split(b"\t")
        if not fields[0].strip().isdigit():
            continue
        identity = int(fields[0])
        if identity not in relevant_ids:
            continue
        if len(fields) <= 24:
            raise ValueError(f"Неполная запись нужного предмета в ItemInfo.txt: {identity}")
        if identity in rows:
            raise ValueError(f"Повтор предмета в ItemInfo.txt: {identity}")
        rows[identity] = fields
    return rows


def make_item_tables(text, server, client, installed, *, retire_legacy=False):
    aliases = {i: (source, 31, 0, b" (Lv1)") for i, source in GEMS.items()}
    aliases.update({i: (source, 41, 2*price, f" Trophy {price//100}".encode())
                    for i, (source, price) in TROPHIES.items()})
    required = {source for source, _, _, _ in aliases.values()} | SUPPLIES.keys() | WEAPONS.keys() | {684}
    rows = item_text(text, required | aliases.keys() | LEGACY.keys())
    binaries = [table_bin(server), table_bin(client)]
    for table in (rows, *binaries):
        if missing := required - table.keys():
            raise ValueError("В таблице отсутствуют предметы обновления: " + ", ".join(map(str, sorted(missing))))
        for ids in (set(GEMS), set(TROPHIES), set(range(6400, 6408)), set(range(6410, 6440))):
            existing = ids & table.keys()
            if existing and (not installed or existing != ids):
                raise ValueError("Выбранные ID заняты или таблицы обновлены частично.")
    if (set(aliases) & rows.keys()) != (set(aliases) & binaries[0].keys()):
        raise ValueError("Серверные таблицы расходятся по новым ID.")
    if (set(LEGACY) & rows.keys()) != (set(LEGACY) & binaries[0].keys()):
        raise ValueError("Серверные таблицы расходятся по прежним ID.")
    for identity in GEMS.values():
        if int(rows[identity][10]) != 49 or int(rows[identity][20]) != 1:
            raise ValueError(f"Неверный исходный гем {identity}.")
        if any(struct.unpack_from("<h", t[identity], 308)[0] != 49
               or struct.unpack_from("<i", t[identity], 352)[0] != 1 for t in binaries):
            raise ValueError(f"Неверная двоичная запись исходного гема {identity}.")
    all_aliases = aliases | {old: aliases[new] for old, new in LEGACY.items()}
    nl = b"\r\n" if b"\r\n" in text else b"\n"

    def check_identity(identity, name, suffix):
        if not name.endswith(suffix):
            raise ValueError(f"Новый ID {identity} уже занят другим предметом.")

    def text_row(identity, previous=None):
        source, kind, price, suffix = all_aliases[identity]
        row = rows[source].copy()
        if previous is not None:
            check_identity(identity, previous[1], suffix)
        row[0], row[1], row[10], row[20], row[21], row[22] = (
            str(identity).encode(), row[1]+suffix, str(kind).encode(), b"99", b"0", str(price).encode())
        for i, field in enumerate(row):
            if field == b"ItemUse_hexin":
                row[i] = b"0"
        return b"\t".join(row)

    new_ids = TROPHIES.keys()
    if 6400 in rows and not retire_legacy:
        new_ids = (*new_ids, *GEMS)  # keep the migration destination available
    out_text = []
    for line in text.splitlines(keepends=True):
        fields = line.rstrip(b"\r\n").split(b"\t")
        identity = int(fields[0]) if fields[0].strip().isdigit() else None
        if identity in LEGACY and retire_legacy:
            check_identity(identity, fields[1], all_aliases[identity][3])
            continue
        if identity in all_aliases:
            line = text_row(identity, fields)+line[len(line.rstrip(b"\r\n")):]
        out_text.append(line)
    text = b"".join(out_text)
    added = [text_row(identity) for identity in new_ids if identity not in rows]
    if added:
        text += (b"" if text.endswith((b"\r", b"\n")) else nl) + nl.join(added) + nl

    results = []
    for table in binaries:
        def binary_row(identity):
            source, kind, price, suffix = all_aliases[identity]
            record = bytearray(table[source])
            if identity in table:
                previous = table[identity][112:192].split(b"\0", 1)[0]
                check_identity(identity, previous, suffix)
            for offset in (4, 108):
                struct.pack_into("<I", record, offset, identity)
            name = record[112:192].split(b"\0", 1)[0]
            if len(name)+len(suffix) >= 80:
                raise ValueError(f"Слишком длинное имя исходного предмета {source}.")
            record[112:192] = (name+suffix).ljust(80, b"\0")
            struct.pack_into("<h", record, 308, kind)
            struct.pack_into("<i", record, 320, price)
            struct.pack_into("<i", record, 352, 99)
            record[356] = 0
            hook = b"ItemUse_hexin"
            offset = record.find(hook)
            if offset >= 0:
                record[offset:offset+len(hook)] = b"0".ljust(len(hook), b"\0")
            return bytes(record)
        records = []
        for identity, record in table.items():
            if identity in LEGACY and retire_legacy:
                check_identity(identity, record[112:192].split(b"\0", 1)[0], all_aliases[identity][3])
                continue
            records.append(binary_row(identity) if identity in all_aliases else record)
        records.extend(binary_row(identity) for identity in new_ids if identity not in table)
        results.append(struct.pack("<I",868)+b"".join(records))
    from price_tables import patch_binary, patch_text
    prices = {identity: {"kind": int(rows[identity][10]), "price": price}
              for identity, price in (SUPPLIES | WEAPONS | {684: 200_000}).items()}
    return patch_text(text, prices), *(patch_binary(data, prices) for data in results)

def add_vendor(text, binary):
    rows, records = city.validate_npcs(text, binary)
    own = [i for i, row in rows.items() if row[11] == VENDOR]
    x, y = (v*100+50 for v in LOCATION)
    position = f"{x},{y}".encode()
    safety = json.loads((ROOT / "city-safety.json").read_text(encoding="utf-8"))
    dx,dy=(value-origin for value,origin in zip(LOCATION,safety["origin"]))
    mask = zlib.decompress(base64.b64decode(safety["safe_zlib"]))
    if not (0<=dx<safety["width"] and 0<=dy<safety["height"] and mask[dy*safety["width"]+dx]):
        raise ValueError("Клетка продавца не проходит проверку карты.")
    if own:
        if len(own) != 1 or rows[own[0]][5] != position:
            raise ValueError("Запись торговца расходниками перемещена или повторяется.")
        return text, binary
    if any(row[5] == position for row in rows.values()):
        raise ValueError("Клетка рядом с кузницей уже занята.")
    identity = max(rows)+1
    row = list(rows[18])
    record = bytearray(next(r for r in records if struct.unpack_from("<I", r, 4)[0] == 18))
    label = b"Forge Supply"
    for offset in (4, 100):
        struct.pack_into("<I", record, offset, identity)
    record[8:48] = label.ljust(40, b"\0")
    record[108:236] = label.ljust(128, b"\0")
    record[394:410] = VENDOR.ljust(16, b"\0")
    record[410:426] = b"0".ljust(16, b"\0")
    struct.pack_into("<iiiiI", record, 244, x, y, x, y, 180)
    row[0], row[1], row[5], row[6], row[7], row[11], row[12] = (
        str(identity).encode(), label, position, position, b"180", VENDOR, b"0")
    nl = b"\r\n" if b"\r\n" in text else b"\n"
    text = text.rstrip(b"\r\n")+nl+b"\t".join(row)+nl
    binary += record
    city.validate_npcs(text, binary)
    return text, binary


def world_script():
    lines = []
    number = 0
    for heading, offers in (("Cooking", PRODUCTS["cooking"]), ("Manufacturing", PRODUCTS["manufacturing"])):
        items = list(offers)
        for start in range(0, len(items), 36):
            number += 1
            stock = ",".join(map(str, items[start:start+36]))
            label = heading if len(items)<=36 else f"{heading} {start//36+1}"
            lines.append((stock, label, number))
    pages = ",\n".join(
        '    supply_page({},{},{'+stock+'},"forge-supply")' for stock, _, _ in lines)
    options = "\n".join(
        f'    Text(1,"{label}",OwnerOpenTrade,"forge-supply",{number})' for _,label,number in lines)
    return ((ROOT / "world_expansion.lua").read_text(encoding="utf-8")
            .replace("-- SUPPLY_STOCK", pages).replace("-- SUPPLY_OPTIONS", options)).encode("ascii")


def plan(resource, client, encoding="cp1251", bot_assets=None, *, retire_legacy=False, trophy_report=None):
    sys.path.insert(0, str(ROOT / "native"))
    before, after, _ = forge.plan(resource, encoding)
    script = after[forge.SCRIPT]
    if forge.MARKER not in after:
        raise ValueError("Не найден журнал действующей серверной ревизии 60.")
    if not all(token in before[forge.SCRIPT] for token in
               (b"function Owner57GroundDrop", b"function OwnerEquipment", b"OwnerNativeShops")):
        raise ValueError("Нужна установленная серверная ревизия 60 с торговцами и наземными гемами.")
    installed = START in script
    block = world_script()
    nl = b"\r\n" if b"\r\n" in script else b"\n"
    block = block.replace(b"\n", nl).rstrip(b"\r\n")
    if installed:
        if script.count(START) != 1 or script.count(END) != 1:
            raise ValueError("Найден повтор или неполный блок расширения.")
        after[forge.SCRIPT] = re.sub(re.escape(START)+rb"[\s\S]*?"+re.escape(END),
                                    lambda _: block, script)
    else:
        after[forge.SCRIPT] = script+nl+block+nl
    text, binary = Path("ItemInfo.txt"), Path("ItemInfo.bin")
    before[text], before[binary] = (resource/text).read_bytes(), (resource/binary).read_bytes()
    client_before = client.read_bytes()
    after[text], after[binary], client_after = make_item_tables(before[text], before[binary], client_before, installed, retire_legacy=retire_legacy)
    after[forge.TEXT], after[forge.BINARY] = add_vendor(after[forge.TEXT], after[forge.BINARY])
    from native_gems import enable_script
    after[forge.SCRIPT] = enable_script(after[forge.SCRIPT])
    if forge.MARKER in after:
        receipt = json.loads(after[forge.MARKER])
        receipt["world_expansion"] = True
        vendor_rows,_=city.validate_npcs(after[forge.TEXT],after[forge.BINARY])
        receipt['world_supply_npc_id']=next(i for i,r in vendor_rows.items() if r[11]==VENDOR)
        receipt['healing_food_prices']={str(i):PRODUCTS['cooking'][i] for i in (1849,1078,1079,1080,1082,1083,3122,3123,3124,3125,3126,3127,3128,1084,1085,1087,1088,1089,1090,3099,3134,3135,3136,3137,3138,3139,3140)}
        for path, payload in after.items():
            if path != forge.MARKER and payload != before[path]:
                receipt["installed_sha256"][path.as_posix()] = hashlib.sha256(payload).hexdigest()
        after[forge.MARKER] = (json.dumps(receipt, ensure_ascii=False, indent=2)+"\n").encode()
    changes = {resource/p: payload for p, payload in after.items() if payload != before[p]}
    from trophy_drops import patch as patch_trophies
    character = resource/"CharacterInfo.txt"
    compiled = next((p for p in resource.iterdir() if p.name.casefold()=="characterinfo.bin"),None)
    original_characters = character.read_bytes()
    original_compiled = compiled.read_bytes() if compiled else None
    kinds = {int(fields[0]): int(fields[10])
             for line in before[text].splitlines() for fields in (line.split(b"\t"),)
             if len(fields)>10 and fields[0].strip().isdigit() and fields[10].strip().isdigit()}
    try:
        updated_characters, updated_compiled, managed, fallback = patch_trophies(
            original_characters, original_compiled, kinds, TROPHIES)
    except ValueError as error:
        if trophy_report is None:
            raise
        trophy_report["warning"] = str(error)
        updated_characters, updated_compiled = original_characters, original_compiled
    else:
        if trophy_report is not None:
            trophy_report.update(managed=managed, fallback=fallback)
    if updated_characters!=original_characters:
        changes[character]=updated_characters
    if compiled and updated_compiled!=original_compiled:
        changes[compiled]=updated_compiled
    if client_after != client_before:
        changes[client] = client_after
    if bot_assets and (bot_assets / "world-npcs.json").is_file():
        assets = bot_assets
        from installer import catalog, make_overlay
        overlay_path = assets / "owner-city-shops.json"
        overlay = (json.dumps(make_overlay(catalog(), receipt), ensure_ascii=False, indent=2)+"\n").encode()
        if not overlay_path.exists() or overlay_path.read_bytes() != overlay:
            changes[overlay_path] = overlay
    return changes


def restore_spawns(resource):
    from spawn_density import restore_plan
    changes, removed, skipped = restore_plan(resource)
    if removed:
        print(f"Убрано дополнительных мест мобов в исходных группах: {removed}.")
    elif not skipped:
        print("Отметок увеличения плотности Alpha90 не найдено.")
    for detail in skipped:
        print("Требуется сверка файла спавна: " + detail)
    return changes, skipped


def ensure_stopped(also_client):
    if sys.platform!="win32":
        return
    import subprocess
    try:
        listing = subprocess.check_output(["tasklist", "/FO", "CSV", "/NH"])
    except subprocess.CalledProcessError as error:
        raise ValueError("Не удалось проверить, остановлен ли GameServer.") from error
    if re.search(rb'(?i)"GameServer[0-9]*\.exe"', listing):
        raise ValueError("Сначала останови все процессы GameServer.")
    if also_client and re.search(rb'(?i)"Game\.exe"', listing):
        raise ValueError("Сначала закрой игровой клиент.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server")
    parser.add_argument("--client")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--retire-legacy-ids", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--restore-spawns-only", action="store_true")
    mode.add_argument("--enable-gem-drops", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / "native"))
    from installer import apply_files, locate_client
    try:
        if args.apply:
            ensure_stopped(also_client=not args.restore_spawns_only)
        resource = city.locate(args.server or input("Папка GameServer или resource: "))
        if args.restore_spawns_only:
            changes, skipped = restore_spawns(resource)
        elif args.enable_gem_drops:
            from native_gems import plan as enable_gems
            client = locate_client((args.client or input("Папка игрового клиента: ")).strip().strip('"'))
            changes = enable_gems(resource, client)
            skipped = []
            print("Проверены исходные ID гемов и клиентский StoneInfo. Включён дополнительный шанс 3% на штатный гем.")
        else:
            client = locate_client((args.client or input("Папка игрового клиента: ")).strip().strip('"'))
            trophy_report = {}
            changes = plan(resource, client, bot_assets=ROOT.parent / "assets",
                           retire_legacy=args.retire_legacy_ids, trophy_report=trophy_report)
            if "warning" in trophy_report:
                print("Таблицы трофеев оставлены без изменений: " + trophy_report["warning"])
            else:
                print(f"Трофей в штатной добыче: {trophy_report['managed']} видов мобов. "
                      f"Сохранён прежний способ выдачи: {trophy_report['fallback']}.")
            restored, skipped = restore_spawns(resource)
            changes.update(restored)
            if not args.retire_legacy_ids and set(LEGACY) & item_text(
                    (resource/"ItemInfo.txt").read_bytes(), LEGACY).keys():
                print("Старые ID сохранены для уже добытых предметов. См. инструкцию по переносу.")
        print(f"Файлов к обновлению: {len(changes)}.")
        if args.apply and changes:
            backup = resource.parent / ("world-expansion-backup-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
            apply_files(changes, backup)
            print(f"Обновление установлено. Резервная копия: {backup}")
        return int(bool(skipped))
    except (OSError, ValueError, RuntimeError, StopIteration) as error:
        print(f"Ошибка установки: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
