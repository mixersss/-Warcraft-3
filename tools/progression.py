"""Classic ability data expansion. Keep unit IDs, flags and timings well formed."""
import json
from pathlib import Path


def scaled_value(field, rank, ultimate):
    values = field['values']; last = values[-1]
    if rank <= len(values): return values[rank-1]
    if field['kind'] == 3:
        if field['id'] in ('Neg3','Neg4','Neg5','Neg6'):
            # No further ability replacement after the third engineering form.
            return ''
        return last
    label = field['label'].lower(); raw = field['id']
    if raw == 'acdn':
        return max(1.0, last*max(0.5, 1-0.08*(rank-1))) if ultimate and last > 1 else last
    if raw in ('acas','adur','ahdu','aare','aran','amcs'):
        return last
    if any(word in label for word in ('flag','type','allow','can ','boolean','interval','duration','delay','distance','range','factor','permanent','invulnerable')):
        return last
    meaningful = any(word in label for word in ('damage','heal','bonus','regenerat','chance','evasion','life','hit point','strength','agility','intelligence','corpses','creep level'))
    if not meaningful: return last
    delta = last-values[-2] if len(values)>1 else 0
    value = last+max(0,delta)*(rank-len(values))
    if ultimate and len(values)==1 and last>0: value = last*(1+0.2*(rank-1))
    if any(word in label for word in ('chance','evasion','life stolen','damage reduction','damage reflected')):
        value = min(value,0.75 if max(values)<=1 else 75)
    if 'speed bonus' in label: value = min(value,1.0 if max(values)<=1 else 100)
    if 'multiplier' in label: value = min(value,10)
    if 'corpses' in label: value = min(value,12)
    return int(round(value)) if field['kind']==0 else round(value,5)


def hero_abilities(root):
    seeds = json.loads((Path(root)/'map/ability-seeds.json').read_text())
    entries = []
    for rawcode, seed in seeds.items():
        ultimate = seed['cap']==7
        req, skip = (6,12) if ultimate else (1,2)
        changes = [('alev',0,seed['cap']),('arlv',0,req),('alsk',0,skip)]
        changes += [('aret',3,f'Изучить {seed["name"]} [уровень %d]'),('arut',3,f'{seed["name"]}. Максимальный ранг: {seed["cap"]}. Требования: уровень героя {req}, затем каждые {skip} уровней.')]
        for rank in range(1,seed['cap']+1):
            for field in seed['fields']:
                changes.append((field['id'],field['kind'],scaled_value(field,rank,ultimate),rank,field['column']))
            details = []
            for field in seed['fields']:
                if field['kind']!=3 and field['column']>0 and any(w in field['label'].lower() for w in ('damage','heal','bonus','evasion','chance')):
                    details.append(f'{field["label"]}: {scaled_value(field,rank,ultimate):g}')
            text = f'Ранг {rank}/{seed["cap"]}. '+ '; '.join(details[:5])
            changes += [('atp1',3,f'{seed["name"]} [уровень {rank}]',rank,0),('aub1',3,text,rank,0)]
        entries.append((rawcode,'\0'*4,changes))
    return entries


def summon_bonus_abilities():
    entries = []
    for base, rawcode, field, kind, amount in [('AIlf','FsHP','Ilif',0,50),('AItg','FsDM','Iatt',0,3),('AId2','FsAR','Idef',2,0.5)]:
        changes = [('alev',0,18),('aher',0,0)]
        for rank in range(1,19): changes.append((field,kind,amount*(rank-1),rank,1))
        entries.append((base,rawcode,changes))
    return entries
