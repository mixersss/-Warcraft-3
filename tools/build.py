#!/usr/bin/env python3
"""Reproducible TFT 1.26 map build; Python standard library only.

Classic formats: W3I 25, W3E 11 (7-byte vertices), objects 2, MPQ 0.
Do not save in a modern World Editor if retaining 1.26 compatibility.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
SIZE = 96
HALF = SIZE * 64
BOUNDS = HALF - 256
MASK = 0xFFFFFFFF


def i(*values: int) -> bytes:
    return struct.pack('<' + 'i' * len(values), *values)


def f(*values: float) -> bytes:
    return struct.pack('<' + 'f' * len(values), *values)


def s(value: str) -> bytes:
    return value.encode('utf-8') + b'\0'


def positions() -> list[tuple[int, int]]:
    first = [(-4700, -3600), (-4200, -4700), (-3100, -4200)]
    result = []
    for team in range(4):
        for x, y in first:
            for _ in range(team):
                x, y = -y, x
            result.append((x, y))
    return result


def validate_balance(b: dict) -> None:
    assert len(b['tiers']) == 5
    assert 1 <= b['spawn_min_seconds'] <= b['spawn_seconds']
    assert 1 <= b['spawn_units'] <= b['army_cap'] <= 100
    assert b['upgrade_max'] <= 20
    assert b['warmup_seconds'] >= 10
    for tier in b['tiers']:
        assert tier['hp'] > 0 and tier['damage'] > 0
        assert len(tier['melee_base']) == 4


def info(b: dict) -> bytes:
    name = f"{b['name']} {b['version']}"
    text = '4 teams x 3 players. Endless army waves, five tiers, heroes and scripted bots. Destroy enemy barracks. Type -shop or -help. Classic TFT 1.26+; alpha, in-game validation pending.'
    data = i(25, 1, 6061) + s(name) + s('mixersss') + s(text) + s('1-12 (bots fill empty slots)')
    data += f(-BOUNDS, -BOUNDS, BOUNDS, BOUNDS, -BOUNDS, BOUNDS, BOUNDS, -BOUNDS)
    data += i(2, 2, 2, 2, SIZE-4, SIZE-4, 0x60) + b'L'
    data += i(-1) + s('') + s(text) + s(b['name']) + s('Four teams. One survivor.')
    data += i(2) + s('') + s('') + s('') + s('')
    data += i(0) + f(3000, 5000, 0.5) + bytes([0, 0, 0, 255])
    data += i(0) + s('Default') + b'L' + bytes([255, 255, 255, 255])
    data += i(12)
    for p, (x, y) in enumerate(positions()):
        allies = 7 << (p//3*3)
        data += i(p, 1, 1, 1) + s(f'Player {p+1}') + f(x, y) + i(0, allies)
    data += i(4)
    for t in range(4):
        data += i(0x0B, 7 << (t*3)) + s(f'Team {t+1}')
    return data + i(0, 0, 0, 0)


def texture(x: float, y: float) -> int:
    if min((x-hx)**2+(y-hy)**2 for hx, hy in positions()) < 520**2:
        return 3
    radius = math.hypot(x, y)
    if radius < 950:
        return 3 if radius < 780 else 2
    if abs(abs(x)-abs(y)) < 330 or 3550 < max(abs(x), abs(y)) < 4250:
        return 2
    if int(x//640 + y//640) % 7 == 0:
        return 1
    return 0


def terrain() -> bytes:
    data = b'W3E!' + i(11) + b'L' + i(1, 4) + b'LgrsLgrdLdrtLrok'
    data += i(2) + b'CLdiCLgr' + i(SIZE+1, SIZE+1) + f(-HALF, -HALF)
    for y in range(SIZE+1):
        for x in range(SIZE+1):
            edge = x < 2 or y < 2 or x > SIZE-2 or y > SIZE-2
            # Base height 2 corresponds to flat z=0 with ground=8192.
            data += struct.pack('<HHBBB', 8192, 8192, texture(x*128-HALF, y*128-HALF) | (0x80 if edge else 0), (x*7+y*3)%4, 2)
    return data


def pathing() -> bytes:
    width = SIZE*4
    return b'MP3W' + i(0, width, width) + bytes(
        0x0E if x < 8 or y < 8 or x >= width-8 or y >= width-8 else 0x08
        for y in range(width) for x in range(width)
    )


def objects(entries: list, extended: bool = False) -> bytes:
    data = i(2, 0, len(entries))
    for original, custom, changes in entries:
        data += original.encode('ascii') + custom.encode('ascii') + i(len(changes))
        for field, kind, value in changes:
            data += field.encode('ascii') + i(kind)
            if extended:
                data += i(0, 0)
            data += s(value) if kind == 3 else f(value) if kind in (1, 2) else i(value)
            data += custom.encode('ascii')
    return data


def units(b: dict) -> bytes:
    entries = []
    for tier, row in enumerate(b['tiers']):
        for ranged in (False, True):
            rawcode = ('fr' if ranged else 'fm') + f'{tier:02d}'
            changes = [
                ('unam', 3, row['name'] + (' Rifleman' if ranged else ' Soldier')),
                ('uhpm', 0, round(row['hp'] * (0.65 if ranged else 1))),
                ('ua1b', 0, round(row['damage'] * (0.8 if ranged else 1))),
                ('ua1d', 0, 1), ('ua1s', 0, 2), ('ua1c', 2, 1.5),
                ('ua1r', 0, 550 if ranged else 100),
                ('ua1t', 3, 'pierce' if ranged else 'normal'),
                ('udef', 2, float(row['armor'])), ('udup', 2, 1.0),
                ('udu1', 0, 3), ('ua1g', 3, 'ground,structure,debris,item,ward'),
                ('umvs', 0, 300), ('umvr', 2, 0.6),
                ('uabi', 3, ''), ('upgr', 3, 'Rfat,Rfar'), ('ureq', 3, ''),
                ('ufoo', 0, 0), ('ubba', 0, 0), ('ubdi', 0, 0), ('ubsi', 0, 0),
                ('ugol', 0, 0), ('ulum', 0, 0), ('uacq', 2, 650.0),
            ]
            entries.append(('hrif' if ranged else row['melee_base'], rawcode, changes))
    entries.append(('hbar', 'fbax', [
        ('unam', 3, 'Frenzy Barracks'), ('uhpm', 0, b['base_hp']),
        ('udef', 2, 5.0), ('ureq', 3, ''), ('utra', 3, ''), ('ures', 3, ''),
        ('uupt', 3, ''), ('uabi', 3, ''), ('ubba', 0, 0), ('ubdi', 0, 0),
        ('ubsi', 0, 0), ('upgr', 3, ''), ('uhpr', 2, 0.0),
        ('utip', 3, 'Frenzy Barracks'),
        ('utub', 3, 'Produces army waves automatically. Type -shop to buy upgrades. Keep this building alive to produce troops and revive your hero.'),
    ]))
    entries.append(('hgtw', 'ftow', [
        ('unam', 3, 'Frenzy Guard Tower'), ('uhpm', 0, 1200),
        ('ua1b', 0, 24), ('ua1c', 2, 1.0), ('ua1r', 0, 700),
        ('ureq', 3, ''), ('uupt', 3, ''), ('ubba', 0, 0), ('ubdi', 0, 0),
        ('ubsi', 0, 0), ('upgr', 3, ''),
    ]))
    return objects(entries)


def upgrades(b: dict) -> bytes:
    return objects([
        ('Rhme', 'Rfat', [('gnam', 3, 'Frenzy Weapons'), ('glvl', 0, b['upgrade_max']), ('gef1', 3, 'ratd'), ('gba1', 2, 1.0), ('gmo1', 2, 0.0), ('gef2', 3, ''), ('gef3', 3, ''), ('gef4', 3, ''), ('greq', 3, '')]),
        ('Rhar', 'Rfar', [('gnam', 3, 'Frenzy Armor'), ('glvl', 0, b['upgrade_max']), ('gef1', 3, 'rarm'), ('gba1', 2, 1.0), ('gmo1', 2, 0.0), ('gef2', 3, ''), ('gef3', 3, ''), ('gef4', 3, ''), ('greq', 3, '')]),
    ], extended=True)


def script(b: dict) -> str:
    fields = ['starting_gold', 'income_per_second', 'spawn_seconds', 'spawn_min_seconds', 'spawn_units', 'army_cap', 'warmup_seconds', 'upgrade_max', 'attack_cost', 'attack_cost_step', 'armor_cost', 'armor_cost_step', 'spawn_cost', 'spawn_cost_step', 'hero_power_cost', 'hero_power_cost_step', 'base_hp']
    generated = ['globals']
    for field in fields:
        generated.append(f'    constant integer {field.upper()} = {b[field]}')
    generated += ['    integer array MeleeType', '    integer array RangedType', '    integer array TierCost', '    string array TierName', '    boolean array AutoArmy', 'endglobals']
    source = (ROOT/'map/war3map.j').read_text()
    # JASS allows only one globals block, before any function declarations.
    source = source.replace('globals\n', '\n'.join(generated[:-1])+'\n', 1)
    init = ['function InitBalance takes nothing returns nothing']
    for n, row in enumerate(b['tiers']):
        init += [f"    set MeleeType[{n}] = 'fm{n:02d}'", f"    set RangedType[{n}] = 'fr{n:02d}'", f'    set TierCost[{n}] = {row["cost"]}', f'    set TierName[{n}] = "{row["name"]}"']
    for p, (x, y) in enumerate(positions()):
        init += [f'    set HomeX[{p}] = {x}.0', f'    set HomeY[{p}] = {y}.0']
    for t in range(4):
        homes = positions()[t*3:t*3+3]
        init += [f'    set TeamX[{t}] = {sum(x for x,y in homes)/3:.3f}', f'    set TeamY[{t}] = {sum(y for x,y in homes)/3:.3f}']
    init += ['endfunction', '']
    source = source.replace('function TeamOf ', '\n'.join(init)+'\nfunction TeamOf ', 1)
    config = ['function config takes nothing returns nothing', f'    call SetMapName("{b["name"]} {b["version"]}")', '    call SetMapDescription("Four teams of three. Endless waves, upgrades, heroes and bots. Type -help.")', '    call SetPlayers(12)', '    call SetTeams(4)', '    call SetGamePlacement(MAP_PLACEMENT_FIXED)', '    call SetGameTypeSupported(GAME_TYPE_USE_MAP_SETTINGS, true)', '    call SetMapFlag(MAP_LOCK_ALLIANCE_CHANGES, true)']
    for p, (x, y) in enumerate(positions()):
        # Keep all slots joinable for multiplayer. Runtime bots fill empty slots.
        control = 'MAP_CONTROL_USER'
        config += [f'    call DefineStartLocation({p}, {x}.0, {y}.0)', f'    call SetPlayerStartLocation(Player({p}), {p})', f'    call ForcePlayerStartLocation(Player({p}), {p})', f'    call SetPlayerColor(Player({p}), ConvertPlayerColor({p}))', f'    call SetPlayerRacePreference(Player({p}), RACE_PREF_HUMAN)', f'    call SetPlayerRaceSelectable(Player({p}), false)', f'    call SetPlayerController(Player({p}), {control})', f'    call SetPlayerTeam(Player({p}), {p//3})']
    for p in range(12):
        for q in range(12):
            if p != q and p//3 == q//3:
                config += [f'    call SetPlayerAlliance(Player({p}), Player({q}), ALLIANCE_PASSIVE, true)', f'    call SetPlayerAlliance(Player({p}), Player({q}), ALLIANCE_SHARED_VISION, true)']
    config += ['endfunction', '']
    return source+'\n'+'\n'.join(config)


def minimap() -> bytes:
    # An uncompressed 24-bit TGA also works as a classic map preview.
    width = 256
    header = struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, width, width, 24, 0)
    palette = [(58, 91, 48), (64, 77, 39), (92, 88, 67), (117, 119, 117)]
    teams = [(220, 65, 55), (65, 135, 230), (175, 85, 220), (235, 190, 50)]
    pixels = bytearray()
    for py in range(width):
        for px in range(width):
            x, y = (px/width*2-1)*HALF, (py/width*2-1)*HALF
            color = palette[texture(x, y)]
            for p, (hx, hy) in enumerate(positions()):
                if (hx-x)**2+(hy-y)**2 < 240**2:
                    color = teams[p//3]
            pixels += bytes(reversed(color))
    return header+pixels


# MPQ tables follow Blizzard's original Storm hash/encryption algorithm.
def crypt_table() -> list[int]:
    table = [0]*0x500
    seed = 0x100001
    for low in range(256):
        for high in range(5):
            seed = (seed*125+3) % 0x2AAAAB
            upper = (seed & 0xFFFF) << 16
            seed = (seed*125+3) % 0x2AAAAB
            table[high*256+low] = upper | (seed & 0xFFFF)
    return table


CRYPT = crypt_table()


def mpq_hash(name: str, kind: int) -> int:
    a, b = 0x7FED7FED, 0xEEEEEEEE
    for char in name.replace('/', '\\').upper().encode('ascii'):
        a = (CRYPT[kind*256+char] ^ (a+b)) & MASK
        b = (char+a+b+(b << 5)+3) & MASK
    return a


def encrypt_table(data: bytes, key: int) -> bytes:
    seed = 0xEEEEEEEE
    out = bytearray()
    for (value,) in struct.iter_unpack('<I', data):
        seed = (seed+CRYPT[0x400+(key & 255)]) & MASK
        out += struct.pack('<I', value ^ ((key+seed) & MASK))
        key = ((((~key & MASK) << 21)+0x11111111) | (key >> 11)) & MASK
        seed = (value+seed+(seed << 5)+3) & MASK
    return bytes(out)


def archive(files: dict[str, bytes], name: str) -> bytes:
    files = dict(files)
    files['(listfile)'] = ('\r\n'.join(sorted(files))+'\r\n(listfile)\r\n').encode('ascii')
    # The Warcraft header is outside the MPQ, padded to a 512-byte boundary.
    wrapper = b'HM3W'+i(0)+s(name)+i(0x60, 12)
    assert len(wrapper) < 512
    wrapper = wrapper.ljust(512, b'\0')
    table_size = 64
    hashes = [b'\xff'*16 for _ in range(table_size)]
    blocks, content = bytearray(), bytearray()
    for block, (filename, payload) in enumerate(sorted(files.items())):
        slot = mpq_hash(filename, 0) % table_size
        while hashes[slot] != b'\xff'*16:
            slot = (slot+1) % table_size
        hashes[slot] = struct.pack('<IIHHI', mpq_hash(filename, 1), mpq_hash(filename, 2), 0, 0, block)
        # Stored uncompressed, single-unit file, MPQ_FILE_EXISTS.
        blocks += struct.pack('<IIII', 32+len(content), len(payload), len(payload), 0x81000000)
        content += payload
    hash_pos = 32+len(content)
    block_pos = hash_pos+16*table_size
    hashes_bytes = encrypt_table(b''.join(hashes), mpq_hash('(hash table)', 3))
    blocks_bytes = encrypt_table(bytes(blocks), mpq_hash('(block table)', 3))
    length = block_pos+len(blocks_bytes)
    header = struct.pack('<4sIIHHIIII', b'MPQ\x1a', 32, length, 0, 3, hash_pos, block_pos, table_size, len(files))
    return wrapper+header+content+hashes_bytes+blocks_bytes


def build() -> Path:
    b = json.loads((ROOT/'map/balance.json').read_text())
    validate_balance(b)
    out = ROOT/'build'
    unpacked = out/'map'
    unpacked.mkdir(parents=True, exist_ok=True)
    files = {
        'war3map.w3i': info(b), 'war3map.w3e': terrain(), 'war3map.wpm': pathing(),
        'war3map.w3u': units(b), 'war3map.w3q': upgrades(b),
        'war3map.j': script(b).encode('utf-8'),
        'war3map.doo': b'W3do'+i(8, 11, 0, 0, 0),
        'war3mapUnits.doo': b'W3do'+i(8, 11, 0),
        'war3map.w3r': i(5, 0), 'war3map.w3c': i(0, 0),
        'war3map.w3s': i(1, 0), 'war3map.imp': i(1, 0),
        'war3map.shd': bytes(SIZE*4*SIZE*4),
        'war3mapMap.tga': minimap(), 'war3mapPreview.tga': minimap(),
    }
    for filename, payload in files.items():
        (unpacked/filename).write_bytes(payload)
    target = out/f'FourFrontsFrenzy-{b["version"]}.w3x'
    target.write_bytes(archive(files, f'{b["name"]} {b["version"]}'))
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (out/'SHA256SUMS').write_text(f'{digest}  {target.name}\n')
    print(f'Built {target}: {target.stat().st_size:,} bytes\nSHA256 {digest}')
    return target


if __name__ == '__main__':
    build()
