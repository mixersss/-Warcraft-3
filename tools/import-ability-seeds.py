#!/usr/bin/env python3
"""Extract only numeric/configuration seeds for our hero roster from classic data.

Usage: python3 tools/import-ability-seeds.py PATH_TO_W3X2LNI_DATA_ROOT
The source root must contain mpq/Units/abilitydata.slk and metadata.
Normal map builds use the checked-in seeds and need no external game files.
"""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def slk(path):
    rows = {}; x = y = 0
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if not line.startswith('C;'): continue
        for part in re.split(r';(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', line)[1:]:
            if part.startswith('X'): x = int(part[1:])
            elif part.startswith('Y'): y = int(part[1:])
            elif part.startswith('K'):
                value = part[1:]
                rows.setdefault(y, {})[x] = value[1:-1].replace('""', '"') if value.startswith('"') else value
    header = rows.pop(1)
    return [{header[k]: v for k,v in row.items() if k in header} for row in rows.values()]


def extract(source):
    units = source/'mpq/Units'
    abilities = {r['alias']: r for r in slk(units/'abilitydata.slk') if 'alias' in r}
    metadata = slk(units/'AbilityMetaData.slk')
    labels = {}
    for line in (source/'mpq/UI/WorldEditStrings.txt').read_text(encoding='cp1252').splitlines():
        if '=' in line:
            k,v = line.split('=',1); labels[k] = v.strip('"')
    names = {}; section = ''
    for file in units.glob('*abilitystrings.txt'):
        for line in file.read_text(encoding='utf-8-sig').splitlines():
            if line.startswith('['): section = line.strip('[]')
            elif line.startswith('Name='): names[section] = line[5:].strip('"')
    roster = json.loads((ROOT/'map/heroes.json').read_text())
    caps = {skill: 50 if slot == 3 else 300 for hero in roster for slot, skill in enumerate(hero['skills'])}
    for prefix, cap in [('ANs',300),('ANc',300),('ANg',50)]:
        for n in range(1,4): caps[prefix+str(n)] = cap
    output = {}
    for rawcode, cap in sorted(caps.items()):
        row = abilities[rawcode]; fields = []
        levels = int(row['levels'])
        for meta in metadata:
            if meta.get('slk') != 'AbilityData' or int(meta.get('repeat','0')) == 0: continue
            specific = meta.get('useSpecific','').split(',')
            if specific != [''] and rawcode not in specific and row['code'] not in specific: continue
            field = meta['field']; column = int(meta.get('data','0'))
            if field == 'Data':
                if specific == [''] or column < 1: continue
                field = 'Data'+chr(64+column)
            values = [row.get(field+str(n), '-').strip() for n in range(1, levels+1)]
            if all(v in ('-','_','') for v in values): continue
            dtype = meta['type']
            string_type = any(t in dtype.lower() for t in ('code','list','string')) or dtype == 'char'
            kind = 1 if dtype == 'real' else 2 if dtype == 'unreal' else 3 if string_type else 0
            if kind == 0 and any(not re.fullmatch(r'-?\d+(\.\d+)?',v) for v in values if v not in ('-','_','')):
                kind = 3
            normalized = []; last = '' if kind == 3 else 0
            for value in values:
                if value not in ('-','_',''):
                    last = value if kind == 3 else int(float(value)) if kind == 0 else float(value)
                normalized.append(last)
            label = labels.get(meta.get('displayName',''), meta['ID'])
            fields.append({'id':meta['ID'], 'kind':kind, 'column':column, 'values':normalized, 'label':label})
        output[rawcode] = {'name':names.get(rawcode,names.get(row['code'],rawcode)), 'levels':levels, 'cap':cap, 'ultimate':cap==50, 'fields':fields}
    return output


def extract_summons(source, abilities):
    from progression import SUMMON_FIELDS
    units=source/'mpq/Units'
    tables={name:{next(iter(row.values())):row for row in slk(units/f'{name}.slk')}
            for name in ('unitbalance','unitweapons','unitui')}
    ids={raw for seed in abilities.values() for field in seed['fields']
         if field['id'] in SUMMON_FIELDS for value in field['values'] for raw in value.split(',')}
    def number(row,key,default):
        try: return float(row[key])
        except (KeyError,ValueError): return default
    result={}
    for raw in sorted(ids):
        balance=tables['unitbalance'][raw]; weapon=tables['unitweapons'][raw]; ui=tables['unitui'][raw]
        result[raw]={'hp':number(balance,'HP',1),'damage':number(weapon,'dmgplus1',0),
                     'armor':number(balance,'def',0),'scale':number(ui,'modelScale',1),
                     'collision':number(balance,'collision',16)}
    return result


if __name__ == '__main__':
    source = Path(sys.argv[1])
    output = extract(source)
    target = ROOT/'map/ability-seeds.json'
    target.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    summons=extract_summons(source,output)
    (ROOT/'map/summon-seeds.json').write_text(json.dumps(summons,ensure_ascii=False,indent=2)+'\n')
    print(f'Extracted {len(output)} hero/engineering-variant ability seeds to {target}')
