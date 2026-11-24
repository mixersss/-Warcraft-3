"""Install stackable first-rank gems and an additional Argent shop."""
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
GEMS = dict(zip(range(6400, 6408), (860, 861, 862, 863, 864, 865, 866, 1012)))
TROPHIES = {6410+level-1: (1591, level*1000) for level in range(1, 31)}
SUPPLIES = {1847: 10, 1848: 55, 1849: 180, 3094: 10_000,
            **dict.fromkeys((*range(893, 898), *range(1854, 1860)), 180),
            **dict.fromkeys(range(4602, 4605), 500)}
WEAPONS = {i: 1_800_000 for i in range(2331, 2345)}
START = b"-- WORLD_EXPANSION_BEGIN"
END = b"-- WORLD_EXPANSION_END"
VENDOR = b"ForgeSupply"
LOCATION = (2260, 2770)


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


def make_item_tables(text, server, client, installed):
    aliases = {i: (source, 31, 0, b" (Lv1)") for i, source in GEMS.items()}
    aliases.update({i: (source, 41, 2*price, f" Trophy {price//100}".encode())
                    for i, (source, price) in TROPHIES.items()})
    required = {source for source, _, _, _ in aliases.values()} | SUPPLIES.keys() | WEAPONS.keys() | {684}
    rows = item_text(text, required | aliases.keys())
    binaries = [table_bin(server), table_bin(client)]
    for table in (rows, *binaries):
        if missing := required - table.keys():
            raise ValueError("В таблице отсутствуют предметы обновления: " + ", ".join(map(str, sorted(missing))))
    existing = [set(aliases) & table.keys() for table in (rows, *binaries)]
    expected = set(aliases) if installed else set()
    valid_client = existing[2] in (set(), expected)
    if existing[:2] != [expected, expected] or not valid_client:
        raise ValueError("Выбранные ID стопок заняты или таблицы обновлены частично.")
    for identity, (_, kind, _, _) in aliases.items():
        if installed:
            if int(rows[identity][10]) != kind or int(rows[identity][20]) != 99:
                raise ValueError(f"Неверная текстовая запись стопки {identity}.")
            if any(struct.unpack_from("<h", t[identity], 308)[0] != kind
                   or struct.unpack_from("<i", t[identity], 352)[0] != 99
                   for t in binaries if identity in t):
                raise ValueError(f"Неверная двоичная запись стопки {identity}.")
    if not installed:
        nl = b"\r\n" if b"\r\n" in text else b"\n"
        added = []
        for identity, (original, kind, price, suffix) in aliases.items():
            row = rows[original].copy()
            if identity in GEMS and (int(row[10]) != 49 or int(row[20]) != 1):
                raise ValueError(f"Неверный исходный гем {original}.")
            row[0], row[1], row[10], row[20], row[22] = (
                str(identity).encode(), row[1]+suffix, str(kind).encode(), b"99", str(price).encode())
            for i, field in enumerate(row):
                if field == b"ItemUse_hexin":
                    row[i] = b"0"
            added.append(b"\t".join(row))
        separator = b"" if text.endswith((b"\r", b"\n")) else nl
        text += separator + nl.join(added) + nl

    results = []
    for raw, table in zip((server, client), binaries):
        out = bytearray(raw)
        for identity, (original, kind, price, suffix) in aliases.items():
            if identity in table:
                continue
            record = bytearray(table[original])
            if identity in GEMS and (struct.unpack_from("<h", record, 308)[0] != 49
                                    or struct.unpack_from("<i", record, 352)[0] != 1):
                raise ValueError(f"Неверная двоичная запись исходного гема {original}.")
            for offset in (4, 108):
                struct.pack_into("<I", record, offset, identity)
            name = record[112:192].split(b"\0", 1)[0]
            if len(name)+len(suffix) >= 80:
                raise ValueError(f"Слишком длинное имя исходного гема {original}.")
            record[112:192] = (name+suffix).ljust(80, b"\0")
            struct.pack_into("<h", record, 308, kind)
            struct.pack_into("<i", record, 320, price)
            struct.pack_into("<i", record, 352, 99)
            hook = b"ItemUse_hexin"
            offset = record.find(hook)
            if offset >= 0:
                record[offset:offset+len(hook)] = b"0".ljust(len(hook), b"\0")
            out.extend(record)
        results.append(bytes(out))
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


def plan(resource, client, encoding="cp1251", bot_assets=None):
    sys.path.insert(0, str(ROOT / "native"))
    before, after, _ = forge.plan(resource, encoding)
    script = after[forge.SCRIPT]
    if forge.MARKER not in after:
        raise ValueError("Не найден журнал действующей серверной ревизии 60.")
    if not all(token in before[forge.SCRIPT] for token in
               (b"function Owner57GroundDrop", b"function OwnerEquipment", b"OwnerNativeShops")):
        raise ValueError("Нужна установленная серверная ревизия 60 с торговцами и наземными гемами.")
    installed = START in script
    block = (ROOT / "world_expansion.lua").read_bytes()
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
    after[text], after[binary], client_after = make_item_tables(before[text], before[binary], client_before, installed)
    after[forge.TEXT], after[forge.BINARY] = add_vendor(after[forge.TEXT], after[forge.BINARY])
    if forge.MARKER in after:
        receipt = json.loads(after[forge.MARKER])
        receipt["world_expansion"] = True
        for path, payload in after.items():
            if path != forge.MARKER and payload != before[path]:
                receipt["installed_sha256"][path.as_posix()] = hashlib.sha256(payload).hexdigest()
        after[forge.MARKER] = (json.dumps(receipt, ensure_ascii=False, indent=2)+"\n").encode()
    changes = {resource/p: payload for p, payload in after.items() if payload != before[p]}
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server")
    parser.add_argument("--client")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / "native"))
    from installer import apply_files, locate_client
    try:
        resource = city.locate(args.server or input("Папка GameServer или resource: "))
        client = locate_client((args.client or input("Папка игрового клиента: ")).strip().strip('"'))
        changes = plan(resource, client, bot_assets=ROOT.parent / "assets")
        from spawn_density import plan as plan_density
        spawn_changes, added, skipped = plan_density(resource)
        changes.update(spawn_changes)
        print(f"Файлов к обновлению: {len(changes)}. Дополнительных мобов в проверенных группах: {added}.")
        if skipped:
            print("Группы с отдельным двоичным спавном: " + ", ".join(skipped))
        if args.apply and changes:
            backup = resource.parent / ("world-expansion-backup-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
            apply_files(changes, backup)
            print(f"Обновление установлено. Резервная копия: {backup}")
        return 0
    except (OSError, ValueError, RuntimeError, StopIteration) as error:
        print(f"Ошибка установки: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
