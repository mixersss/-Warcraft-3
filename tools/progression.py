"""Explicit Classic skill ranks and per-skill summons, without runtime stat hacks."""
import json
from functools import lru_cache
from pathlib import Path

SUMMON_FIELDS = {'Hwe1','Osf1','Efnu','Esvu','Nbau','Ndou','Nef1','Nsy2','Nsyu','Rai3','Uin4','Ntou','Ulsu'}
COUNT_FIELDS = {'Hwe2','Osf2','Efn1','Esv1','Nba2','Ndo2','Rai1'}


def scaled_value(field, rank, ultimate):
    values = field['values']; last = values[-1]
    raw = field['id']; label = field['label'].lower()
    if raw in COUNT_FIELDS:
        return values[min(rank,len(values))-1] + rank//10
    if raw == 'Ucb5': return last + rank//10
    if rank <= len(values): return values[rank-1]
    extra = rank-len(values)
    if field['kind'] == 3:
        return '' if raw in ('Neg3','Neg4','Neg5','Neg6') else last
    if raw == 'acdn':
        return round(max(1.0,last*max(0.4,1-extra*(0.025 if ultimate else 0.003))),4) if last>1 else last
    if raw == 'aare': return round(last*(1+min(extra*(0.025 if ultimate else 0.002),0.75)),4)
    if raw in ('acas','adur','ahdu','aran','amcs'): return last
    if raw == 'Nms2': return last  # Mana Shield already absorbs 100%.
    if raw in ('Ocl3','Uts2'):
        # Less chain falloff / less damage received is the improvement.
        return round(max(last*0.4,last*(1-0.002*extra)),5)
    if 'movement speed increase' in label: return round(min(1.0,last+0.005*extra),5)
    if 'attack speed increase' in label: return round(min(3.0,last+0.01*extra),5)
    # These are engine mechanics and identifiers, not scalable magnitudes.
    if any(word in label for word in ('flag','type','allow','can ','boolean','interval','duration','delay','distance','range','permanent','invulnerable','split','generation')):
        return last
    if raw == 'Omi1': return last+rank//10
    if raw == 'Omi2': return min(0.75,0.0025*extra)
    if raw == 'Omi3': return max(1.0,last-0.003*extra)
    if 'number of targets' in label or 'targets hit' in label:
        return min(32,last+rank//10)
    meaningful = any(word in label for word in ('damage','heal','bonus','regenerat','chance','evasion','life','hit point','strength','agility','intelligence','corpses','creep level','multiplier'))
    if not meaningful: return last
    delta = last-values[-2] if len(values)>1 else 0
    step = max(abs(delta),abs(last)*(0.15 if ultimate else 0.04))
    value = last + (step*extra if last>=0 else -step*extra)
    if any(word in label for word in ('chance','evasion','life stolen','damage reduction','damage reflected','damage increase (%)','speed reduction')):
        value = min(value,0.80 if max(values)<=1 else 80)
    if 'speed bonus' in label: value = min(value,1.0 if max(values)<=1 else 100)
    if 'multiplier' in label: value = min(value,30)
    if 'damage stolen' in label or 'returned damage factor' in label: value = min(value,3.0)
    if 'corpses' in label: value = min(value,32)
    return int(round(value)) if field['kind']==0 else round(value,5)


def code(index):
    digits='0123456789abcdefghijklmnopqrstuvwxyz'
    return 's'+digits[index//1296]+digits[index//36%36]+digits[index%36]


@lru_cache(maxsize=1)
def summon_catalog(root):
    root=Path(root)
    seeds=json.loads((root/'map/ability-seeds.json').read_text())
    stock=json.loads((root/'map/summon-seeds.json').read_text())
    units=[]; replacements={}; details={}; cache={}
    for ability,seed in seeds.items():
        for rank in range(1,seed['cap']+1):
            for field in seed['fields']:
                if field['id'] not in SUMMON_FIELDS: continue
                originals=field['values'][min(rank,len(field['values']))-1].split(',')
                ids=[]
                for original in originals:
                    key=(original,rank,seed['ultimate'])
                    if key not in cache:
                        raw=code(len(cache)); cache[key]=raw
                        src=stock[original]
                        # Size and collision are separate so large models fit the gates.
                        extra=rank-1
                        factor=1+extra*(0.60 if seed['ultimate'] else 0.15)
                        damage_factor=1+extra*(0.45 if seed['ultimate'] else 0.12)
                        scale=src['scale']*(1+(rank-1)*(0.02 if seed['ultimate'] else 0.005))
                        hp=round(src['hp']*factor)
                        damage=round(src['damage']*damage_factor+extra*(2 if seed['ultimate'] else 1))
                        armor=src['armor']+extra*(0.6 if seed['ultimate'] else 0.2)
                        units.append((original,raw,[('uhpm',0,hp),('ua1b',0,damage),('udef',0,round(armor)),
                            ('usca',1,scale),('ucol',2,min(src['collision'],40.0)),
                            ('upgr',3,''),('ufoo',0,0),('ugol',0,0),('ulum',0,0)]))
                        details[raw]=(hp,damage,scale)
                    ids.append(cache[key])
                replacements[ability,rank,field['id']]=','.join(ids)
    return units,replacements,details


def summoned_units(root): return summon_catalog(str(root))[0]


def hero_abilities(root):
    seeds=json.loads((Path(root)/'map/ability-seeds.json').read_text())
    _,replacements,summon_details=summon_catalog(str(root))
    entries=[]
    for rawcode,seed in seeds.items():
        ultimate=seed['ultimate']
        req,skip=(6,10) if ultimate else (1,1)
        changes=[('alev',0,seed['cap']),('arlv',0,req),('alsk',0,skip)]
        changes += [('aret',3,f'Изучить {seed["name"]} [уровень %d]'),('arut',3,f'{seed["name"]}. Максимальный ранг: {seed["cap"]}. Требования: уровень героя {req}, затем каждые {skip} уровней.')]
        for rank in range(1,seed['cap']+1):
            details=[]
            for field in seed['fields']:
                value=replacements.get((rawcode,rank,field['id']),scaled_value(field,rank,ultimate))
                changes.append((field['id'],field['kind'],value,rank,field['column']))
                if field['id'] in SUMMON_FIELDS:
                    hp,damage,scale=summon_details[value.split(',')[0]]
                    details.append(f'Призыв: {hp} HP; базовый урон {damage}; размер {scale:.2f}')
                elif field['id'] in COUNT_FIELDS:
                    details.append(f'Количество за вызов: {value}')
                elif field['kind']!=3 and field['column']>0 and any(w in field['label'].lower() for w in ('damage','heal','bonus','evasion','chance')):
                    details.append(f'{field["label"]}: {value:g}')
            text=f'Ранг {rank}/{seed["cap"]}. '+'; '.join(details[:7])
            changes += [('atp1',3,f'{seed["name"]} [уровень {rank}]',rank,0),('aub1',3,text,rank,0)]
        entries.append((rawcode,'\0'*4,changes))
    return entries
