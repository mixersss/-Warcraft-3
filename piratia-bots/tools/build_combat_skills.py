"""Project verified basic targeted skills; no original Lua or formulas packaged."""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# Explicitly inspected damage/heal effects. Target-entity casts; area shapes remain native server effects.
OFFENSIVE={81,82,85,86,90,91,96,99,213,214,216,224}
HEAL={97}

def build(resource):
    skills={}
    for line in (resource/'skillinfo.txt').read_bytes().decode('gb18030',errors='replace').splitlines():
        a=line.split('\t')
        if not a[0].isdigit() or int(a[0]) not in OFFENSIVE|HEAL:continue
        identity=int(a[0])
        # field15 is habitat (1land/2sea/3both), NOT an entity/point selector.
        # Illusion Slash and Dual Shot accept both habitats; field17 still selects an enemy entity.
        if (a[9]!='1' or a[14]!='1' or a[15] not in ('1','3') or
            a[17] not in ('4','5') or a[18] not in ('1','2')):raise ValueError('Unsupported cast shape')
        def requirement(field):return [list(map(int,p.split(','))) for p in field.split(';')]
        skills[identity]={'name':a[1],'jobs':[int(p.split(',')[0]) for p in a[3].split(';')],
                         'range_cm':int(a[16]),'role':'heal' if identity in HEAL else 'control' if identity==213 else 'damage',
                         'left':requirement(a[4]),'right':requirement(a[5]),'body':requirement(a[6]),
                         'coral':[] if a[7]=='-1' else list(map(int,a[7].split(',')))}
    (ROOT/'assets/combat-skills.json').write_text(json.dumps({'version':1,'skills':skills},ensure_ascii=False,separators=(',',':'))+'\n')
    print('Verified targeted skills',len(skills))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('resource',type=Path);build(p.parse_args().resource)
