"""Isolated native troop traits. No edits to the existing hero spell tables."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def data():
    return json.loads((ROOT/'map/army-traits.json').read_text())
def abilities():
    return [(r['base'],r['id'],[tuple(m)for m in r['mods']])for r in data()['abilities']]
def unit_changes(raw,base):
    row=data()['troops'].get(raw)
    if row is None:return []
    result=[('uhpm',0,round(base['hp']*row['hp_multiplier'])),('ua1b',0,round(base['damage']*row['damage_multiplier'])),
            ('udef',0,base['armor']+row['armor_bonus']),('umvs',0,row['move_speed']),('ua1c',2,row['attack_cooldown']),
            ('ua1r',0,row['range']),('uabi',3,row['abilities']),('utub',3,row['description']),('utip',3,row['description'])]
    for key,value in row['fields'].items():
        kind=3 if isinstance(value,str)else 2 if isinstance(value,float)else 0
        result.append((key,kind,value))
    return result
