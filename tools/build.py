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
import zlib
from progression import hybrid_power, hero_abilities, summoned_units, custom_hero_abilities, attribute_ability, summon_support_abilities, chemical_forms, army_passives, army_aura_buffs
from equipment import item_effects, potion_abilities, utility_abilities
from hero_picker import units as picker_units, controls as picker_controls, CARDS_PER_PAGE

ROOT = Path(__file__).resolve().parents[1]
SIZE = 96
HALF = SIZE * 64
BOUNDS = HALF - 256
MASK = 0xFFFFFFFF
WALL_RADIUS = 2300
WALL_HALF_THICKNESS = 96
GATE_HALF_WIDTH = 560
TUNNEL_LENGTH = 1600
TUNNEL_FLARE = 0.4
ENCLOSURES = [(-3904, -3904), (3904, -3904), (3904, 3904), (-3904, 3904)]


def catalog(name: str) -> list[dict]:
    return json.loads((ROOT / 'map' / f'{name}.json').read_text())


def wall_at(x: float, y: float) -> bool:
    # Four radial dividers seal all side routes; their only junction is center.
    if (abs(x)<=96 and abs(y)>=1350) or (abs(y)<=96 and abs(x)>=1350):
        return True
    for cx, cy in ENCLOSURES:
        dx, dy = x-cx, y-cy
        length = math.hypot(cx, cy)
        inward = (-cx*dx-cy*dy)/length
        sideways = (-cy*dx+cx*dy)/length
        half_width = GATE_HALF_WIDTH+max(0,inward-WALL_RADIUS)*TUNNEL_FLARE
        if WALL_RADIUS-160 <= inward <= WALL_RADIUS+TUNNEL_LENGTH and abs(abs(sideways)-half_width) <= WALL_HALF_THICKNESS:
            return True
        if abs(math.hypot(dx, dy)-WALL_RADIUS) <= WALL_HALF_THICKNESS:
            if inward <= 0 or abs(sideways) >= GATE_HALF_WIDTH:
                return True
    return False


def wall_segments() -> list[tuple[float, float, float]]:
    result = []
    for cx, cy in ENCLOSURES:
        for step in range(144):
            angle = step*2*math.pi/144
            x, y = cx+WALL_RADIUS*math.cos(angle), cy+WALL_RADIUS*math.sin(angle)
            if wall_at(x, y):
                result.append((x, y, math.degrees(angle)+90))
        length = math.hypot(cx, cy)
        for along in range(WALL_RADIUS-120, WALL_RADIUS+TUNNEL_LENGTH+1, 80):
            half_width = GATE_HALF_WIDTH+max(0,along-WALL_RADIUS)*TUNNEL_FLARE
            for side in (-half_width, half_width):
                result.append((cx-cx/length*along-cy/length*side,
                               cy-cy/length*along+cx/length*side,
                               math.degrees(math.atan2(-cy,-cx))+math.degrees(math.atan(TUNNEL_FLARE))*(1 if side>0 else -1)))
    for along in range(1350, HALF, 80):
        result += [(0,along,0),(0,-along,0),(along,0,90),(-along,0,90)]
    return result


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


def market_position(team: int, slot: int) -> tuple[int,int]:
    x,y=-5200+slot*288,-5488
    for _ in range(team):x,y=-y,x
    return x,y


def shop_positions() -> list[tuple[int,int]]:
    return [market_position(team,slot) for team in range(4) for slot in range(5)]


def supreme_positions() -> list[tuple[int,int]]:
    return [market_position(team,5) for team in range(4)]


def book_positions() -> list[tuple[int,int]]:
    return [market_position(team,6) for team in range(4) for _ in range(3)]


def bastion_positions() -> list[tuple[int,int]]:
    result=[]
    for team in range(4):
        for x,y in [(-5100,-3900),(-4600,-5100),(-3400,-4600)]:
            for _ in range(team): x,y=-y,x
            result.append((x,y))
    return result


def validate_balance(b: dict) -> None:
    assert 0 < b['spell_damage_multiplier'] <= 1
    assert 0 < b['summon_hp_multiplier'] <= 1
    assert 0 < b['summon_damage_multiplier'] <= 1
    assert 0 < b['water_elemental_growth']['early_fraction'] <= 1
    assert b['water_elemental_growth']['full_growth_rank'] == b['basic_skill_max']
    assert len(b['bot_tactics']) == 5
    for tactic in b['bot_tactics']:
        assert 10 <= tactic['tier_percent'] <= 60
        assert 10 <= tactic['gear_percent'] <= 75
        assert tactic['tier_percent'] + tactic['gear_percent'] <= 90
    assert len(b['tiers']) == 5
    assert 1 <= b['spawn_min_seconds'] <= b['spawn_seconds']
    assert 1 <= b['spawn_units'] <= b['army_cap'] <= 100
    assert b['upgrade_max'] <= 255
    assert 1 <= b['research_soft_cap'] < b['upgrade_max']
    assert b['advanced_research_cost_multiplier'] >= 2
    assert b['warmup_seconds'] >= 10
    for tier in b['tiers']:
        assert tier['hp'] > 0 and tier['damage'] > 0
        assert len(tier['melee_base']) == 4


def info(b: dict) -> bytes:
    name = f"{b['name']} {b['version']}"
    text = f'4 teams x 3. One troop type per army tier, 4 races, {len(catalog("heroes"))} heroes. Portrait selection and All Random (-ar before 15s). Barracks research: attack, armor, health (200 ranks each). Hero level 500, normal skills 200, ultimates 50. Powerful bastion towers. Waves every {b["spawn_seconds"]} seconds. Experience rate 50%. Hero-specific bot equipment. Classic TFT 1.26+.'
    data = i(25, 1, 6061) + s(name) + s('mixersss') + s(text) + s('1-12 (open slots stay empty)')
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
    if wall_at(x, y):
        return 3
    if min((x-hx)**2+(y-hy)**2 for hx, hy in positions()) < 520**2:
        return 3
    radius = math.hypot(x, y)
    if radius < 1500:
        return 3 if radius < 1400 else 2
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
        0x0E if x < 8 or y < 8 or x >= width-8 or y >= width-8
        else 0x0E if wall_at((x+0.5)*32-HALF, (y+0.5)*32-HALF) else 0x08
        for y in range(width) for x in range(width)
    )


def object_table(entries: list, extended: bool) -> bytes:
    data = bytearray(i(len(entries)))
    for original, custom, changes in entries:
        data += original.encode('ascii') + custom.encode('ascii') + i(len(changes))
        for change in changes:
            field, kind, value = change[:3]
            data += field.encode('ascii') + i(kind)
            if extended:
                data += i(*change[3:]) if len(change) == 5 else i(0, 0)
            data += s(value) if kind == 3 else f(value) if kind in (1, 2) else i(value)
            data += custom.encode('ascii')
    return bytes(data)


def objects(entries: list, extended: bool = False, original_entries: list | None = None) -> bytes:
    return i(2)+object_table(original_entries or [], extended)+object_table(entries, extended)


def units(b: dict) -> bytes:
    entries = []
    for race, faction in enumerate(catalog('races')):
        for tier, row in enumerate(b['tiers']):
            ranged = tier in faction['ranged_tiers']
            rawcode = 'fm' + f'{race}{tier}'
            changes = [
                ('unam', 3, faction['tier_names'][tier]),
                ('uhpm', 0, row['hp']),
                ('ua1b', 0, row['damage']),
                ('ua1d', 0, 1), ('ua1s', 0, 2), ('ua1c', 2, 1.5),
                ('ua1r', 0, 550 if ranged else 100),
                ('ua1t', 3, 'pierce' if ranged else 'normal'),
                ('uaen', 0, 1),
            ('udef', 0, row['armor']), ('udup', 0, b['armor_per_rank']),
            ('udu1', 0, b['attack_per_rank']), ('ua1g', 3, ('air,' if ranged else '')+'ground,structure,debris,item,ward'),
                ('umvs', 0, 300), ('umvr', 2, 0.6),
                ('usca', 1, b['army_model_scale']), ('ucol', 2, float(b['army_collision'])),
                ('uabi', 3, ''), ('upgr', 3, 'Rfat,Rfar,Rfhp,Rfa2,Rfr2,Rfh2'), ('ureq', 3, ''),
                ('ufoo', 0, 0), ('ubba', 0, 0), ('ubdi', 0, 0), ('ubsi', 0, 0),
                ('ugol', 0, b['transmute_troop_values'][tier]), ('ulum', 0, 0), ('uacq', 2, 650.0),
            ]
            entries.append((faction['units'][tier], rawcode, changes))
    entries += summoned_units(ROOT)
    entries += chemical_forms(ROOT)
    entries += picker_units(catalog('heroes'),b['basic_skill_max'])
    entries.append(('hbar', 'fbax', [
        ('unam', 3, 'Frenzy Barracks'), ('uhpm', 0, b['base_hp']),
        ('udef', 0, 5), ('ureq', 3, ''), ('utra', 3, ''), ('ures', 3, 'Rfat,Rfar,Rfhp,Rfti,Rfa2,Rfr2,Rfh2,Rfwn'),
        ('uupt', 3, ''), ('uabi', 3, ''), ('ubba', 0, 0), ('ubdi', 0, 0),
        ('ubsi', 0, 0), ('upgr', 3, 'Rfti'), ('uhpr', 2, 0.0),
        ('utip', 3, 'Frenzy Barracks'),
        ('utub', 3, f'Атака, броня, здоровье армии, развитие казармы и отдельная кнопка численности волн (+1 боец, от 2000 золота). Первые три исследования до 200 уровня. Новая ступень меняет тип бойца и даёт +{b["base_upgrade_hp"]} здоровья базе. Спавн раз в {b["spawn_seconds"]} секунд.'),
    ]))
    entries.append(('hgtw', 'ftow', [
        ('unam', 3, 'Frenzy Guard Tower'), ('uhpm', 0, b['tower_hp']),
        ('ua1b', 0, 24), ('ua1c', 2, 1.0), ('ua1r', 0, 700),
        ('ureq', 3, ''), ('uupt', 3, ''), ('ubba', 0, 0), ('ubdi', 0, 0),
        ('ubsi', 0, 0), ('upgr', 3, ''),
    ]))
    entries.append(('hgtw','fbst',[
        ('unam',3,'Бастионная башня'),('uhpm',0,b['bastion_hp']),('udef',0,b['bastion_armor']),
        ('uaen',0,1),('ua1b',0,b['bastion_damage']),('ua1d',0,1),('ua1s',0,2),
        ('ua1p',2,0.05),('ua1q',2,0.0),('ua1c',2,b['bastion_cooldown']),('ua1r',0,b['bastion_range']),('uacq',2,float(b['bastion_range'])),
        ('ua1g',3,'air,ground,structure,debris,item,ward'),('ureq',3,''),('uupt',3,''),
        ('uabi',3,''),('upgr',3,''),('ubba',0,0),('ubdi',0,0),('ubsi',0,0),('uhpr',2,0.0),
        ('utip',3,'Бастионная башня'),
        ('utub',3,f'Защищает казарму: включается при приближении противника к базе или при уроне базе/башне. {b["bastion_hp"]} HP, {b["bastion_armor"]} брони, {b["bastion_damage"]} базового урона, дальность {b["bastion_range"]}. Можно уничтожить; не возрождается.'),
    ]))
    entries.append(('ngme', 'fshp', [
        ('unam',3,'Магазин экипировки'),('usei',3,','.join(row['id'] for row in catalog('items'))),
        ('ucol',2,96.0),('ureq',3,''),('uhpm',0,b['shop_hp']),
        ('utub',3,'Общий магазин брони, оружия, сапог, колец и амулетов. Подведи героя к магазину и выбери предмет. Всего 6 мест в инвентаре.'),
    ]))
    for shop,name in enumerate(['Арсенал','Броня и сила','Лавка магии','Мастерская скорости','Лавка стихий']):
        entries.append(('ngme',f'fs{shop}p',[
            ('unam',3,name),('usei',3,','.join(row['id'] for row in catalog('equipment') if row['shop']==shop)),
            ('ucol',2,96.0),('ureq',3,''),('uhpm',0,b['shop_hp']),
            ('utub',3,'Сильная экипировка трёх ступеней. Для покупки подведи героя. Улучшенные предметы стоят дороже.'),
        ]))
    entries.append(('ngme','futl',[
        ('unam',3,'Походные припасы'),('usei',3,','.join([row['id'] for row in catalog('utility')]+['fpH0','fpM0'])),
        ('ucol',2,96.),('uhpm',0,b['shop_hp']),('ureq',3,''),
        ('utub',3,'Блинк-даггер, свитки усиления/лечения солдат и эликсиры героя. Подведите героя для покупки.'),
    ]))
    entries.append(('nfoh','ffnt',[
        ('unam',3,'Общий фонтан жизни и маны'),('uhpm',0,b['shop_hp']),('uabi',3,'Avul,FfHP,FfMP'),
        ('upat',3,''),('ucol',2,64.0),('ureq',3,''),
        ('utip',3,'Общий фонтан жизни и маны'),
        ('utub',3,f'Штатные ауры фонтана восстанавливают {b["fountain_hp_percent"]*100:g}% максимального HP и {b["fountain_mana_percent"]*100:g}% маны в секунду всем героям в радиусе {b["fountain_radius"]}, включая врагов и Нежить. Работает во время боя.'),
    ]))
    entries.append(('nfoh','fbfn',[
        ('unam',3,'Союзный фонтан жизни и маны'),('uhpm',0,b['shop_hp']),('uabi',3,'Avul,FbHP,FbMP'),
        ('upat',3,''),('ucol',2,48.0),('ureq',3,''),('utip',3,'Союзный фонтан'),
        ('utub',3,'Восстанавливает союзным героям рядом 0,5% максимального HP и маны в секунду. Радиус 1200.'),
    ]))
    entries.append(('ngme','fsup',[
        ('unam',3,'Сокровищница титанов'),('usei',3,','.join(row['id'] for row in catalog('supreme'))),
        ('ucol',2,96.0),('ureq',3,''),('uhpm',0,b['shop_hp']),
        ('utub',3,'Высшая экипировка: огромные бонусы за 44000–48000 золота. Подведи героя, шесть мест в инвентаре.'),
    ]))
    entries.append(('ngme','fpot',[
        ('unam',3,'Аптека арены'),('usei',3,','.join(row['id'] for row in catalog('potions'))),
        ('ucol',2,64.0),('ureq',3,''),('uhpm',0,b['shop_hp']),
        ('utub',3,'Одноразовые зелья здоровья, маны, скорости и невидимости.'),
    ]))
    entries.append(('ngme','fbks',[
        ('unam',3,'Лавка знаний'),('usei',3,','.join(row['id'] for row in catalog('books'))),
        ('ucol',2,48.0),('ureq',3,''),('uhpm',0,b['shop_hp']),
        ('utub',3,'Книги +2 силы, ловкости или интеллекта — по 280 золота; +1 уровень героя — 960. Применяются при покупке.'),
    ]))
    timings=json.loads((ROOT/'map/hero-attack-seeds.json').read_text())['units']
    speed=b['hero_attack_interval_multiplier']
    originals=[(hero['id'],'\0'*4,[('uhab',3,','.join(hero['skills']+['Fatr']))]) for hero in catalog('heroes') if 'base' not in hero]
    original_ids={row[0] for row in originals}
    for raw,values in timings.items():
        mods=[(field,2,round(value*speed,5)) for field,value in values.items()]
        normal={'Nalm':'Nalc','Nal2':'Nalc','Nal3':'Nalc','Edmm':'Edem','Nrob':'Ntin'}.get(raw)
        if normal: mods.append(('uhab',3,','.join(next(h['skills'] for h in catalog('heroes') if h['id']==normal)+['Fatr'])))
        if raw in original_ids: next(row[2] for row in originals if row[0]==raw).extend(mods)
        elif raw not in {h.get('base') for h in catalog('heroes') if 'base' in h}: originals.append((raw,'\0'*4,mods))
    for base,raw,mods in entries:
        if raw in {h['id'] for h in catalog('heroes') if 'base' in h}:
            mods.extend((field,2,round(value*speed,5)) for field,value in timings[base].items())
    return objects(entries,original_entries=originals)


def fountain_abilities(b: dict) -> list:
    entries=[]
    for base,raw,field,flag,rate,name in [
        ('ACnr','FfHP','Oar1','Oar2',b['fountain_hp_percent'],'Восстановление здоровья'),
        ('ANre','FfMP','Arm1','Arm2',b['fountain_mana_percent'],'Восстановление маны'),
    ]:
        entries.append((base,raw,[('alev',0,1),('aher',0,0),('aite',0,0),
            ('anam',3,name),('aare',2,float(b['fountain_radius']),1,0),
            ('atar',3,'ground,air,hero,vuln,invu',1,0),
            (field,2,rate,1,1),(flag,0,1,1,2),
            ('atp1',3,name,1,0),('aub1',3,f'{rate*100:g}% максимального запаса в секунду. Все герои, все команды, радиус {b["fountain_radius"]}.',1,0)]))
    for base,raw,field,flag,rate in [('ACnr','FbHP','Oar1','Oar2',b['base_fountain_hp_percent']),('ANre','FbMP','Arm1','Arm2',b['base_fountain_mana_percent'])]:
        entries.append((base,raw,[('alev',0,1),('aher',0,0),('aite',0,0),('aare',2,float(b['base_fountain_radius']),1,0),
            ('atar',3,'ground,air,hero,friend,self,vuln,invu',1,0),(field,2,rate,1,1),(flag,0,1,1,2)]))
    return entries


def expansion_abilities(b):
    tuning=b['hero_expansion']['warcry']
    changes=[('anam',3,'Зов стаи'),('aher',0,0),('aite',0,1),('alev',0,50),('aart',3,''),('areq',3,'')]
    for rank in range(1,51):
        changes += [('Oae1',2,0.0,rank,1),('Oae2',2,tuning['speed_base']+tuning['speed_step']*rank,rank,2),('aare',2,tuning['radius'],rank,0),('atar',3,'air,ground,friend,self,nonhero,vuln,invu',rank,0)]
    return [('AOae','Fxwr',changes)]


def menu_ability(b: dict) -> bytes:
    return objects(item_effects(ROOT)[0]+army_passives(ROOT)+fountain_abilities(b)+picker_controls()+custom_hero_abilities(ROOT)+expansion_abilities(b)+attribute_ability()+potion_abilities(ROOT)+utility_abilities(ROOT)+summon_support_abilities(ROOT), extended=True, original_entries=hero_abilities(ROOT))


def items() -> bytes:
    rows = catalog('items')+catalog('equipment')+catalog('supreme')+catalog('potions')+catalog('books')+catalog('utility')
    stock = set(json.loads((ROOT/'map/classic-object-ids.json').read_text())['tables']['items'])
    for row in rows:
        if row['base'] not in stock:
            raise ValueError(f"{row['id']}: unknown Classic item base {row['base']}")
    _,effects=item_effects(ROOT)
    return objects([(row['base'],row['id'],[
        ('unam',3,row['name']),('utip',3,row['name']),('utub',3,row['description']),
        ('igol',0,row['cost']),('ilum',0,0),('isto',0,12),('istr',0,2),('isst',0,0),
    ]+([('iabi',3,row['ability'])] if 'ability' in row else [('iabi',3,effects[row['id']])] if row['id'] in effects else [])) for row in rows])


def misc(b: dict) -> bytes:
    rate=b['experience_multiplier']
    factor=round(rate*100)
    hero_grants=','.join(str(round(v*rate)) for v in [100,120,160,220,300])
    return (f'[Misc]\nMaxHeroLevel={b["hero_max_level"]}\nHeroAbilityLevelSkip=1\n'
            f'HeroFactorXP={factor},{factor},{factor},{factor},{factor}\n'
            f'GrantHeroXP={hero_grants}\nGrantHeroXPFormulaA=1\nGrantHeroXPFormulaB=0\nGrantHeroXPFormulaC={factor}\n'
            'StrHitPointBonus=30\nIntManaBonus=18\n'
            'MaxUnitSpeed=480\n'
            'NeedHeroXP=200\nNeedHeroXPFormulaA=1.0\nNeedHeroXPFormulaB=100\nNeedHeroXPFormulaC=0\n').encode('ascii')


def walls() -> bytes:
    # Static WPM contains the collision. Removing the stock pathing texture
    # prevents rotated models from accidentally narrowing the only gate.
    return objects([('LTw0', 'fwll', [('bnam', 3, 'Fortress Wall'), ('bptx', 3, '')])])


def upgrades(b: dict) -> bytes:
    entries = []
    rows = [
        ('Rhme','Rfat','Атака армии','ratx',float(b['attack_per_rank']),b['attack_cost'],b['attack_cost_step'],'BTNSteelMelee.blp',f'+{b["attack_per_rank"]} к атаке всех существующих и новых бойцов.'),
        ('Rhar','Rfar','Броня армии','rarm',float(b['armor_per_rank']),b['armor_cost'],b['armor_cost_step'],'BTNHumanArmorUpOne.blp',f'+{b["armor_per_rank"]} к броне всех существующих и новых бойцов.'),
        ('Rhan','Rfhp','Здоровье армии','rhpo',b['health_percent'],b['health_cost'],b['health_cost_step'],'BTNPeriapt.blp',f'+{b["health_percent"]*100:g}% базового максимального здоровья всех существующих и новых бойцов.'),
        ('Rhac','Rfti','Развитие казармы','rhpx',float(b['base_upgrade_hp']),b['base_upgrade_cost'],b['base_upgrade_cost_step'],'BTNCastle.blp',f'Новый тип бойца следующих волн. Казарме +{b["base_upgrade_hp"]} здоровья.'),
    ]
    for column,(base,rawcode,name,effect,amount,cost,step,art,description) in enumerate(rows):
        stages=[(rawcode,4 if column==3 else b['research_soft_cap'],0,1)]
        if column<3:
            stages.append((['Rfa2','Rfr2','Rfh2'][column],b['upgrade_max']-b['research_soft_cap'],b['research_soft_cap'],1 if column==2 else b['advanced_research_cost_multiplier']))
        for raw,cap,offset,factor in stages:
            price=(cost+offset*step)*factor
            increment=step*factor
            changes = [('glvl',0,cap),('gbpx',0,column),('gbpy',0,0),
                ('gglb',0,price),('gglm',0,increment),('glmb',0,0),('glmm',0,0),('gtib',0,1),('gtim',0,0),
                ('gef1',3,effect),('gba1',2,amount),('gmo1',2,amount),
                ('gef2',3,''),('gef3',3,''),('gef4',3,'')]
            for rank in range(1,cap+1):
                total=rank+offset
                changes += [('gnam',3,name,rank,0),('gtp1',3,f'{name} [уровень {total}/{4 if column==3 else b["upgrade_max"]}]',rank,0),
                    ('gub1',3,description+f' Цена: {price+increment*(rank-1)} золота.'+(' Продвинутое исследование: цена ×4 после 10-го уровня.' if column<2 else ''),rank,0),
                    ('gar1',3,'ReplaceableTextures\\CommandButtons\\'+art,rank,0),
                    ('greq',3,rawcode if offset else '',rank,0),('grqc',3,str(offset) if offset else '',rank,0)]
            entries.append((base,raw,changes))
    changes=[('glvl',0,b['wave_upgrade_max']),('gbpx',0,0),('gbpy',0,1),
        ('gglb',0,b['wave_upgrade_cost']),('gglm',0,b['wave_upgrade_cost_step']),('glmb',0,0),('glmm',0,0),
        ('gtib',0,1),('gtim',0,0),('gef1',3,''),('gef2',3,''),('gef3',3,''),('gef4',3,'')]
    for rank in range(1,b['wave_upgrade_max']+1):
        changes += [('gnam',3,'Численность волн',rank,0),('gtp1',3,f'Ещё один воин [{rank}/{b["wave_upgrade_max"]}]',rank,0),
            ('gub1',3,f'Следующая волна: {b["spawn_units"]+rank} бойцов. Цена {b["wave_upgrade_cost"]+(rank-1)*b["wave_upgrade_cost_step"]} золота. Предел живой армии {b["army_cap"]} сохранён.',rank,0),
            ('gar1',3,'ReplaceableTextures\\CommandButtons\\BTNFootman.blp',rank,0),('greq',3,'',rank,0)]
    entries.append(('Rhac','Rfwn',changes))
    return objects(entries,extended=True)


def script(b: dict) -> str:
    heroes, races = catalog('heroes'), catalog('races')
    fields = ['starting_gold', 'income_per_second', 'spawn_seconds', 'spawn_min_seconds', 'spawn_units', 'army_cap', 'warmup_seconds', 'upgrade_max', 'attack_cost', 'attack_cost_step', 'armor_cost', 'armor_cost_step', 'health_cost', 'health_cost_step', 'hero_power_cost', 'hero_power_cost_step', 'base_hp', 'hero_max_level', 'basic_skill_max', 'ultimate_skill_max', 'tower_hp', 'fountain_radius', 'corpse_seconds', 'autosave_seconds', 'research_soft_cap', 'advanced_research_cost_multiplier', 'hero_respawn_seconds','wave_upgrade_cost','wave_upgrade_cost_step','wave_upgrade_max','transmute_gold_base','transmute_gold_step']
    generated = ['globals',f'    constant real SPELL_DAMAGE_MULTIPLIER = {b["spell_damage_multiplier"]}', '    real array HybridPower']
    for key,value in b['bot_combat'].items():
        generated.append(f'    constant integer BOT_{key.upper()} = {value}')
    for field in fields:
        generated.append(f'    constant integer {field.upper()} = {b[field]}')
    generated += [f'    constant real FOUNTAIN_HP_PERCENT = {b["fountain_hp_percent"]:.6f}', f'    constant real FOUNTAIN_MANA_PERCENT = {b["fountain_mana_percent"]:.6f}', f'    constant real EXPERIENCE_MULTIPLIER = {b["experience_multiplier"]:.6f}', f'    constant real KILL_GOLD_MULTIPLIER = {b["kill_gold_multiplier"]:.6f}']
    generated += [f'    constant integer HERO_COUNT = {len(heroes)}', f'    constant integer PICK_CARDS_PER_PAGE = {CARDS_PER_PAGE}', f'    constant integer PICK_PAGE_COUNT = {math.ceil(len(heroes)/CARDS_PER_PAGE)}',
        '    integer array BotTierBudget', '    integer array BotGearBudget', '    string array BotTacticName',
        '    integer array HeroBotRole', '    integer array BotRoleTactic', '    integer array HeroLearnOrder',
        '    real array BotRetreatHP', '    real array BotDangerRatio', '    string array BotRoleName',
        '    integer array BotSupplyId', '    integer array BotSupplyCost',
        '    integer array ArmyType', '    integer array TierCost',
        '    string array TierName', '    boolean array AutoArmy',
        '    string array RaceName', '    string array RaceAlias',
        '    integer array HeroType', '    string array HeroName', '    string array HeroAlias',
        '    integer array HeroGroup', '    integer array HeroSkill', '    integer array HeroPrimary', '    integer array PickToken',
        '    real array BookX', '    real array BookY', '    integer array SuperId', '    integer array SuperCost', '    integer array SuperBuild', '    real array SuperX', '    real array SuperY', '    integer array GearId', '    integer array GearCost', '    integer array GearShop', '    integer array HeroGear',
        '    integer array SpellAbility', '    string array SpellOrder', '    integer array SpellMode',
        '    integer array SpellHold', '    integer array AutoSkill', '    string array AutoOrder',
        '    integer array ArmyResearch', '    integer array AdvancedArmyResearch', 'endglobals']
    generated[-1:-1] = ['    trigger array ExpansionThinkTrigger','    constant integer EXPANSION_FIRST_HERO = 36','    integer array ExpansionSlot','    string array ExpansionEffect','    integer array ExpansionTicks','    integer array ExpansionZoneAt','    real array ExpansionX','    real array ExpansionY','    real array ExpansionDamage','    effect array ExpansionZoneArt','    effect array ExpansionCastArt','    integer array ExpansionCastUntil','    unit array ExpansionPrey','    effect array ExpansionPreyArt','    integer array ExpansionPreyUntil','    integer array ExpansionPreyRank','    integer array ExpansionCharges','    integer array ExpansionChargeUntil','    integer array ExpansionWarcryUntil','    group ExpansionGroup = null']
    for mechanic,values in b['hero_expansion'].items():
        for key,value in values.items():
            generated[-1:-1] = [f"    constant {'integer' if isinstance(value,int) else 'real'} XH_{mechanic.upper()}_{key.upper()} = {value}"]
    source = (ROOT/'map/war3map.j').read_text()
    source = source.replace('// EXPANSION_MODULE', (ROOT/'map/expansion-heroes.j').read_text())
    source = source.replace('// BOT_AI_MODULE', (ROOT/'map/bot-ai.j').read_text())
    dispatch=['function HybridSpellKind takes integer raw returns integer']
    for kind,base in enumerate(['AHhb','AUdc','AEmb']):
        ids=[base]+[skill for hero in heroes for skill,seed in zip(hero['skills'],hero.get('skill_sources',[])) if seed==base]
        dispatch += ['    if '+' or '.join("raw=='"+raw+"'" for raw in ids)+' then', f'        return {kind}', '    endif']
    dispatch += ['    return -1','endfunction']
    source = source.replace('// SPELL_BALANCE_MODULE', '\n'.join(dispatch)+'\n'+(ROOT/'map/spell-balance.j').read_text())

    # JASS allows only one globals block, before any function declarations.
    source = source.replace('globals\n', '\n'.join(generated[:-1])+'\n', 1)
    init = ['function InitBalance takes nothing returns nothing']
    profiles=json.loads((ROOT/'map/bot-profiles.json').read_text())
    consumables={row['id']:row for row in catalog('potions')+catalog('utility')}
    for idx,raw in enumerate(['fpH0','fpM0','fshl','fsar','fsdm']):
        init += [f"    set BotSupplyId[{idx}] = '{raw}'",f'    set BotSupplyCost[{idx}] = {consumables[raw]["cost"]}']
    for role in profiles['roles'].values():
        rid=role['id']
        init += [f'    set BotRetreatHP[{rid}] = {role["retreat_hp"]}',f'    set BotDangerRatio[{rid}] = {role["danger_ratio"]}',f'    set BotRoleName[{rid}] = "{role["name"]}"']
        for style,tactic in enumerate(role['tactics']): init.append(f'    set BotRoleTactic[{rid*3+style}] = {tactic}')
    for idx,hero in enumerate(heroes):
        profile=profiles['heroes'][hero['id']]
        init.append(f'    set HeroBotRole[{idx}] = {profiles["roles"][profile["role"]]["id"]}')
        assert sorted(profile['skill_priority'])==[0,1,2]
        for slot,priority in enumerate(profile['skill_priority']): init.append(f'    set HeroLearnOrder[{idx*3+slot}] = {priority}')
    for idx,tactic in enumerate(b['bot_tactics']):
        init += [f'    set BotTierBudget[{idx}] = {tactic["tier_percent"]}',
                 f'    set BotGearBudget[{idx}] = {tactic["gear_percent"]}',
                 f'    set BotTacticName[{idx}] = "{tactic["name"]}"']
    for idx,(x,y) in enumerate(bastion_positions()):
        init += [f'    set BastionX[{idx}] = {x}.0',f'    set BastionY[{idx}] = {y}.0']
    for team,(x,y) in enumerate(ENCLOSURES):
        init += [f'    set FortressX[{team}] = {x}.0',f'    set FortressY[{team}] = {y}.0']
    for idx,(x,y) in enumerate(shop_positions()):
        init += [f'    set ShopX[{idx}] = {x}.0',f'    set ShopY[{idx}] = {y}.0']
    for idx,(x,y) in enumerate(supreme_positions()):
        init += [f'    set SuperX[{idx}] = {x}.0',f'    set SuperY[{idx}] = {y}.0']
    for team in range(4):
        x,y=market_position(team,7)
        init += [f'    set UtilityX[{team}] = {x}.0',f'    set UtilityY[{team}] = {y}.0']
    for idx,(x,y) in enumerate(book_positions()):
        init += [f'    set BookX[{idx}] = {x}.0',f'    set BookY[{idx}] = {y}.0']
    for idx,row in enumerate(catalog('supreme')):
        init += [f"    set SuperId[{idx}] = '{row['id']}'",f'    set SuperCost[{idx}] = {row["cost"]}']
    for row in catalog('equipment'):
        idx=row['family']*3+row['rank']
        init += [f"    set GearId[{idx}] = '{row['id']}'",f'    set GearCost[{idx}] = {row["cost"]}',f'    set GearShop[{idx}] = {row["shop"]}']
    for kind, rawcode in enumerate(['Rfat','Rfar','Rfhp','Rfti']):
        init += [f"    set ArmyResearch[{kind}] = '{rawcode}'"]
    for kind, rawcode in enumerate(['Rfa2','Rfr2','Rfh2']):
        init += [f"    set AdvancedArmyResearch[{kind}] = '{rawcode}'"]
    for n, row in enumerate(b['tiers']):
        init += [f'    set TierCost[{n}] = {row["cost"]}']
    for race, faction in enumerate(races):
        init += [f'    set RaceName[{race}] = "{faction["name"]}"', f'    set RaceAlias[{race}] = "{faction["alias"]}"']
        for tier in range(5):
            idx = race*5+tier
            init += [f"    set ArmyType[{idx}] = 'fm{race}{tier}'", f'    set TierName[{idx}] = "{faction["tier_names"][tier]}"']
    for idx, hero in enumerate(heroes):
        init += [f"    set PickToken[{idx}] = 'fp{idx:02d}'"]
        super_build=[hero['primary'],6,3,4,5,2 if hero['primary']==0 else 0]
        assert len(set(super_build))==6
        for slot,choice in enumerate(super_build):
            init += [f'    set SuperBuild[{idx*6+slot}] = {choice}']
        assert len(set(hero['gear_families']))==6 and all(0<=k<12 for k in hero['gear_families'])
        for slot,family in enumerate(hero['gear_families']):
            init += [f'    set HeroGear[{idx*6+slot}] = {family}']
        init += [f"    set HeroType[{idx}] = '{hero['id']}'", f'    set HeroName[{idx}] = "{hero["name"]}"', f'    set HeroAlias[{idx}] = "{hero["alias"]}"', f'    set HeroGroup[{idx}] = {hero["group"]}', f'    set HeroPrimary[{idx}] = {hero["primary"]}']
        if hero.get('signature'):
            init += [f"    set ExpansionSlot[{idx-36}] = {hero['signature']['slot']}",f"    set ExpansionEffect[{idx-36}] = {json.dumps(hero['signature']['effect'])}"]
        for slot, skill in enumerate(hero['skills']):
            init += [f"    set HeroSkill[{idx*4+slot}] = '{skill}'"]
        for slot in range(4):
            if slot < len(hero['spells']):
                ability, order, mode, *hold = hero['spells'][slot]
                init += [f"    set SpellAbility[{idx*4+slot}] = '{ability}'", f'    set SpellOrder[{idx*4+slot}] = "{order}"', f'    set SpellMode[{idx*4+slot}] = {mode}', f'    set SpellHold[{idx*4+slot}] = {hold[0] if hold else 1}']
            else:
                init += [f'    set SpellAbility[{idx*4+slot}] = 0', f'    set SpellOrder[{idx*4+slot}] = ""']
        auto = hero.get('autocast')
        init += [f"    set AutoSkill[{idx}] = '{auto[0]}'" if auto else f'    set AutoSkill[{idx}] = 0', f'    set AutoOrder[{idx}] = "{auto[1] if auto else ""}"']
    for p, (x, y) in enumerate(positions()):
        init += [f'    set HomeX[{p}] = {x}.0', f'    set HomeY[{p}] = {y}.0']
    for t in range(4):
        homes = positions()[t*3:t*3+3]
        init += [f'    set TeamX[{t}] = {sum(x for x,y in homes)/3:.3f}', f'    set TeamY[{t}] = {sum(y for x,y in homes)/3:.3f}']
    for kind,base in enumerate(['AHhb','AUdc','AEmb']):
        for rank in range(1,b['basic_skill_max']+1):
            init += [f'    set HybridPower[{kind*200+rank-1}] = {float(hybrid_power(ROOT,base,rank))}']
    init += ['endfunction', '', 'function InitWalls takes nothing returns nothing']
    for x, y, angle in wall_segments():
        init += [f"    call SetDestructableInvulnerable(CreateDestructable('fwll', {x:.3f}, {y:.3f}, {angle:.3f}, 1.0, 0), true)"]
    init += ['endfunction', '']
    source = source.replace('function TeamOf ', '\n'.join(init)+'\nfunction TeamOf ', 1)
    config = ['function config takes nothing returns nothing', f'    call SetMapName("{b["name"]} {b["version"]}")', '    call SetMapDescription("Four teams of three. Endless waves, upgrades, heroes and bots. Type -help.")', '    call SetPlayers(12)', '    call SetTeams(4)', '    call SetGamePlacement(MAP_PLACEMENT_FIXED)', '    call SetGameTypeSupported(GAME_TYPE_USE_MAP_SETTINGS, true)', '    call SetMapFlag(MAP_LOCK_ALLIANCE_CHANGES, true)']
    for p, (x, y) in enumerate(positions()):
        # Keep all slots joinable for multiplayer. Runtime bots only occupy selected computer slots.
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
            if wall_at(x, y):
                color = (185, 180, 165)
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
MPQ_SECTOR_SHIFT = 3
MPQ_SECTOR_SIZE = 512 << MPQ_SECTOR_SHIFT


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


def sector_file(payload: bytes) -> bytes:
    if not payload:
        return b''
    count = (len(payload)+MPQ_SECTOR_SIZE-1)//MPQ_SECTOR_SIZE
    offsets = [(count+1)*4]
    chunks = []
    for start in range(0,len(payload),MPQ_SECTOR_SIZE):
        raw = payload[start:start+MPQ_SECTOR_SIZE]
        compressed = b'\x02'+zlib.compress(raw,9)
        stored = compressed if len(compressed)<len(raw) else raw
        chunks.append(stored)
        offsets.append(offsets[-1]+len(stored))
    return struct.pack('<'+'I'*len(offsets),*offsets)+b''.join(chunks)


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
        # Use ordinary sector files, as Classic World Editor does. The 0.4.0
        # compressed SINGLE_UNIT layout passed modern readers but the user's
        # 1.26 Storm reader failed in SFile.cpp. Keep each inflate bounded to
        # 4096 bytes and include an explicit sector-offset table.
        stored = sector_file(payload)
        flags = 0x80000200 if payload else 0x80000000
        blocks += struct.pack('<IIII', 32+len(content), len(stored), len(payload), flags)
        content += stored
    hash_pos = 32+len(content)
    block_pos = hash_pos+16*table_size
    hashes_bytes = encrypt_table(b''.join(hashes), mpq_hash('(hash table)', 3))
    blocks_bytes = encrypt_table(bytes(blocks), mpq_hash('(block table)', 3))
    length = block_pos+len(blocks_bytes)
    header = struct.pack('<4sIIHHIIII', b'MPQ\x1a', 32, length, 0, MPQ_SECTOR_SHIFT, hash_pos, block_pos, table_size, len(files))
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
        'war3map.w3a': menu_ability(b), 'war3map.w3b': walls(),
        'war3map.w3h': objects(army_aura_buffs(ROOT)), 'war3map.w3t': items(), 'war3mapMisc.txt': misc(b),
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
