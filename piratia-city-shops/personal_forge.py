"""Install a private Argent forge alongside the current server patch."""
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

ROOT = Path(__file__).resolve().parent
SCRIPT = Path("script/MisScript/NpcScript01.lua")
SDK = Path("script/MisSdk/NpcSdk.lua")
TEXT = Path("garner/garnernpc.txt")
BINARY = Path("garner/garnerNPC.bin")
POINT = (2257, 2770)
LABEL = b"Personal Forge"
ACTOR = b"OwnForgePrivate"
START = b"-- OWNER_PERSONAL_FORGE_BEGIN"
END = b"-- OWNER_PERSONAL_FORGE_END"
MARKER = Path("owner-city-shops-v2.json")
DISPATCH = (b"elseif item.func == OwnerPersonalForgeAction then\n"
            b"\t\t\treturn OwnerPersonalForgeAction(character,npc,item.p1)\n\t\t")


def refresh_shop_receipt(resource, original, result, *, menu_update=False):
    path = resource / MARKER
    if not path.is_file():
        return
    raw = path.read_bytes()
    receipt = json.loads(raw)
    hashes = receipt.get("installed_sha256", {})
    expected = {p.as_posix() for p in (*original, Path("ItemInfo.txt"), Path("ItemInfo.bin"))}
    if set(hashes) != expected:
        raise ValueError("Журнал ревизии серверных магазинов неполный.")
    for name, expected_hash in hashes.items():
        file = Path(name)
        before = original[file] if file in original else (resource / file).read_bytes()
        if hashlib.sha256(before).hexdigest() != expected_hash:
            # A menu update can leave a structurally valid compiled table in place.
            # Keep its recorded hash so this installer never certifies unrelated edits.
            if menu_update and file == BINARY and result[BINARY] == original[BINARY]:
                continue
            raise ValueError("Сначала нужно сверить серверные магазины. Отличается " + name)
    for file, after in result.items():
        if after != original[file]:
            hashes[file.as_posix()] = hashlib.sha256(after).hexdigest()
    original[MARKER] = raw
    result[MARKER] = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def plan(resource, encoding="cp1251"):
    original = {p: (resource / p).read_bytes() for p in (SCRIPT, SDK, TEXT, BINARY)}
    result = dict(original)
    rows, records = city.validate_npcs(original[TEXT], original[BINARY])
    matches = [i for i, row in rows.items() if row[11].strip() == ACTOR]
    script = original[SCRIPT]
    sdk = original[SDK]
    block = re.compile(re.escape(START) + rb"[\s\S]*?" + re.escape(END))
    if (len(matches) > 1 or script.count(START) != len(matches)
            or script.count(END) != len(matches)
            or sdk.count(b"elseif item.func == OwnerPersonalForgeAction then") != len(matches)):
        raise ValueError("Неполная установка личной кузницы. Проверь предыдущую резервную копию.")
    for filename, names in (
        ("forge.lua", ("SetJinglian_Lv", "GetStone_TypeID", "Get_StoneLv", "TansferNum", "check_item_final_data")),
        ("functions.lua", ("GetNum_Part1", "SetNum_Part1")),
    ):
        raw = (resource / "script/calculate" / filename).read_bytes()
        if any(not re.search(rb"(?m)^\s*function\s+" + name.encode() + rb"\s*\(", raw) for name in names):
            raise ValueError("Серверные скрипты ковки отличаются от проверенной версии.")
    patch = (ROOT / "personal_forge.lua").read_text(encoding="utf-8").strip()
    patch = patch.encode(encoding)
    def newline(value):
        return b"\r\n" if b"\r\n" in value else b"\n"
    patch = patch.replace(b"\n", newline(script))
    if matches:
        row = rows[matches[0]]
        position = f"{POINT[0]*100+50},{POINT[1]*100+50}".encode()
        if row[1].strip() != LABEL or row[5] != position or row[6] != position:
            raise ValueError("Установленная кузница отличается от записи на карте Аргента.")
        result[SCRIPT] = block.sub(lambda _: patch, script)
        if len(block.findall(result[SCRIPT])) != 1:
            raise ValueError("Не найден цельный блок кузницы.")
        refresh_shop_receipt(resource, original, result, menu_update=True)
        return original, result, matches[0]
    anchor = city.ANCHOR
    previous = re.search(rb"elseif item\.func == OwnerOpenTrade then\s+return OwnerOpenTrade[^\r\n]*\s+" +
                         re.escape(anchor), sdk)
    if sdk.count(anchor) != 1:
        raise ValueError("Не найдена точка подключения меню НПС.")
    index = previous.start() if previous else sdk.index(anchor)
    result[SDK] = sdk[:index] + DISPATCH.replace(b"\n", newline(sdk)) + sdk[index:]
    result[SCRIPT] = script + newline(script) + patch + newline(script)

    safety = json.loads((ROOT / "city-safety.json").read_text(encoding="utf-8"))
    mask = zlib.decompress(base64.b64decode(safety["safe_zlib"]))
    x, y = (p - start for p, start in zip(POINT, safety["origin"]))
    if not (0 <= x < safety["width"] and 0 <= y < safety["height"] and mask[y*safety["width"]+x]):
        raise ValueError("Место кузницы не проходит проверку карты.")
    px, py = (value*100+50 for value in POINT)
    for row in rows.values():
        nx, ny = map(int, row[5].split(b","))
        if (nx-px)**2 + (ny-py)**2 < 100**2:
            raise ValueError("Точка 2257, 2770 занята другим НПС.")
    identity = max(rows) + 1
    record = bytearray(next(r for r in records if struct.unpack_from("<I", r, 4)[0] == 18))
    row = list(rows[18])
    struct.pack_into("<I", record, 4, identity)
    struct.pack_into("<I", record, 100, identity)
    record[8:48] = LABEL.ljust(40, b"\0")
    record[108:236] = LABEL.ljust(128, b"\0")
    record[394:410] = ACTOR.ljust(16, b"\0")
    record[410:426] = b"0".ljust(16, b"\0")
    struct.pack_into("<iiiiI", record, 244, px, py, px, py, 180)
    row[0], row[1] = str(identity).encode(), LABEL
    row[5] = row[6] = f"{px},{py}".encode()
    row[7], row[11], row[12] = b"180", ACTOR, b"0"
    nl = newline(original[TEXT])
    result[TEXT] += nl + b"\t".join(row) + nl
    result[BINARY] += record
    city.validate_npcs(result[TEXT], result[BINARY])
    refresh_shop_receipt(resource, original, result)
    return original, result, identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server")
    parser.add_argument("--encoding", default="cp1251", choices=("cp1251", "utf-8"))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        resource = city.locate(args.server or input("Папка GameServer или resource: "))
        before, after, identity = plan(resource, args.encoding)
        changes = {resource / path: raw for path, raw in after.items() if before[path] != raw}
        if args.apply and changes:
            sys.path.insert(0, str(ROOT / "native"))
            from native.installer import apply_files
            backup = resource.parent / ("personal-forge-backup-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
            apply_files(changes, backup)
            print(f"Личная кузница установлена. Резервная копия: {backup}")
        elif changes:
            print("Проверка прошла. Для записи файлов укажи --apply.")
        else:
            print("Личная кузница уже установлена.")
        print(f"Аргент 2257, 2770. ID НПС {identity}.")
        return 0
    except (OSError, ValueError, RuntimeError, StopIteration) as error:
        print(f"Ошибка установки: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
