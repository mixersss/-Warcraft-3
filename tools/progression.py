"""Explicit Classic skill ranks and per-skill summons, without runtime stat hacks."""
import json
from functools import lru_cache
from pathlib import Path

SUMMON_FIELDS = {'Hwe1','Osf1','Efnu','Esvu','Nbau','Ndou','Nef1','Nsy2','Nsyu','Rai3','Uin4','Ntou','Ulsu'}
COUNT_FIELDS = {'Hwe2','Osf2','Efn1','Esv1','Nba2','Ndo2','Rai1'}
# Active offensive spells only: preserve passive, toggle and support cooldowns.
OFFENSIVE_SKILLS = set(('AHtb AHtc AHbz AHfs AHbn AOcl AOws AOsh AOww AOeq AUdc AUfn AUcs AUim AUdd AUin AEer AEfk AEsh AEmb AEsf ANbf ANfl ANso ANvc ANht ANrf ANcs ANc1 ANc2 ANc3 ANst ANab ANsi ANdh ANdr AOhx AUsl ANch ANtm').split())

# Magnitudes only: never multiply flags, attack intervals or control durations.
ULTIMATE_MAGNITUDES = set('Eme5 Esf1 Etq1 Hav1 Hav2 Hav3 Ndo1 Nrg5 Nrg6 Nst3 Nvc5 Oeq2 Oww1 Uin1 Uls5'.split())
ULTIMATE_RECOVERY = {'AHmt':0.7,'AHre':0.65,'AUan':0.75,'ANch':0.7,'ANtm':0.7,'AOre':0.65,'AOvd':0.75}


def ultimate_value(ability, field, rank, value, power):
    raw=field['id']
    if raw in ULTIMATE_MAGNITUDES: value*=power
    if ability=='AUin' and raw=='Uin1': value=max(value,300+60*(rank-1))
    if ability=='AUdd' and raw=='Udd1': value=min(0.35,value*1.5)
    if ability=='AUls' and raw=='Uls4': value=min(6.0,value*1.5)
    if raw=='acdn' and ability in ULTIMATE_RECOVERY and value>1: value*=ULTIMATE_RECOVERY[ability]
    if ability=='AHmt' and raw=='Hmt1': value=max(value,min(96,24+2*rank))
    if ability=='AHmt' and raw=='Hmt2': value=max(1.0,2.5-0.03*(rank-1))
    if ability in ('ANch','ANtm') and raw in ('Nch1','Ntm3'): value=max(value,min(100,10+2*(rank-1)))
    if ability=='ANtm' and raw=='Ntm1': value=min(2.0,max(value,1.2+0.01*(rank-1)))
    if ability=='AOre' and raw=='Ore1': value=max(2.0,5.0-0.07*(rank-1))
    if ability=='AOvd' and raw in ('adur','ahdu'): value=min(40.0,35.0+0.1*(rank-1))
    if ability=='ANto' and raw in ('adur','ahdu'): value*=1.5
    if ability=='AOeq' and raw in ('aare','Oeq4'): value=400+4*(rank-1)
    return int(round(value)) if field['kind']==0 else round(value,5) if field['kind']!=3 else value



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
        return round(max(1.0,last*(1-0.6*extra/max(1,(50 if ultimate else 300)-len(values)))),4) if last>1 else last
    if raw == 'aare': return round(last*(1+min(extra*(0.01 if ultimate else 0.0012),0.35)),4)
    if raw in ('acas','adur','ahdu','aran','amcs'): return last
    if raw == 'Nms2': return last  # Mana Shield already absorbs 100%.
    if raw in ('Ocl3','Uts2'):
        # Less chain falloff / less damage received is the improvement.
        return round(max(last*0.4,last*(1-0.002*extra)),5)
    if 'movement speed increase' in label: return round(min(1.0,last+0.005*extra),5)
    if 'attack speed increase' in label: return round(min(3.0,last+0.01*extra),5)
    # These are engine mechanics and identifiers, not scalable magnitudes.
    progress=extra/max(1,(50 if ultimate else 300)-len(values))
    if 'chance' in label or 'evasion' in label:
        if max(values)<=0: return last
        limit=(0.75 if max(values)<=1 else 75.0) if ('evade' in label or 'evasion' in label) else (0.60 if max(values)<=1 else 60.0)
        return round(min(limit,last+(limit-last)*progress),6)
    if 'damage multiplier' in label and last>0:
        return round(last+(max(last,10.0)-last)*progress,5)
    if raw == 'nca1': return round(last+(2.0-last)*progress,5)
    if raw == 'Uts1': return round(last+(1.5-last)*progress,5)
    if raw == 'Ncs5' or raw == 'Nvc4' or raw == 'Nvc6': return last
    if 'life stolen' in label or 'damage increase (%)' in label or 'damage bonus (%)' in label:
        return round(last+(max(last,0.8)-last)*progress,5)
    if any(word in label for word in ('flag','type','allow','can ','boolean','interval','duration','delay','distance','range','permanent','invulnerable','split','generation')):
        if not any(word in label for word in ('damage per interval','damage interval amount','damage per second')):
            return last
    if raw == 'Omi1': return last+rank//10
    if raw == 'Omi2': return min(0.75,0.0025*extra)
    if raw == 'Omi3': return max(1.0,last-0.003*extra)
    if 'number of targets' in label or 'targets hit' in label:
        return min(32,last+rank//10)
    meaningful = any(word in label for word in ('damage','heal','bonus','regenerat','chance','evasion','life','hit point','strength','agility','intelligence','corpses','creep level','multiplier'))
    if not meaningful: return last
    delta = last-values[-2] if len(values)>1 else 0
    step = max(abs(delta),abs(last)*(0.12 if ultimate else 0.04))
    if 'corpses' in label:
        step=max(abs(delta),abs(last)*(0.15 if ultimate else 0.04))
    if 'defense bonus' in label or 'armor bonus' in label:
        step=abs(last)*(0.10 if ultimate else 0.04)
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
    balance=json.loads((root/'map/balance.json').read_text())
    units=[]; replacements={}; details={}; cache={}; support=[]
    def make_unit(original,rank,ultimate):
        key=(original,rank,ultimate)
        if key not in cache:
            raw=code(len(cache)); cache[key]=raw
            src=stock[original]; extra=rank-1
            factor=(1+extra*(0.60 if ultimate else 0.15))*(balance['ultimate_summon_hp_multiplier'] if ultimate else 1)
            damage_factor=1+extra*(0.45 if ultimate else 0.12)
            scale=src['scale']*balance['summon_model_scale']*(1+extra*(0.002 if ultimate else 0.0005))
            hp=round(src['hp']*factor)
            damage=round((src['damage']*damage_factor+extra*(2 if ultimate else 1))*(balance['ultimate_summon_damage_multiplier'] if ultimate else 1))
            armor=src['armor']+extra*(0.6 if ultimate else 0.2)
            if original=='ninf':
                hp=round(hp*balance['infernal_power_multiplier'])
                damage=round(damage*balance['infernal_power_multiplier'])
                armor*=balance['infernal_power_multiplier']
            units.append((original,raw,[('uhpm',0,hp),('ua1b',0,damage),('udef',0,round(armor)),
                ('usca',1,scale),('ucol',2,min(src['collision'],24.0)),
                ('upgr',3,''),('ufoo',0,0),('ugol',0,0),('ulum',0,0)]))
            details[raw]=(hp,damage,scale)
        return cache[key]
    for ability,seed in seeds.items():
        for rank in range(1,seed['cap']+1):
            for field in seed['fields']:
                if field['id'] not in SUMMON_FIELDS: continue
                originals=field['values'][min(rank,len(field['values']))-1].split(',')
                ids=[]
                for original in originals:
                    ids.append(make_unit(original,rank,seed['ultimate']))
                replacements[ability,rank,field['id']]=','.join(ids)
    # Append nested summons after the primary catalog, retaining existing rawcodes.
    def effect(base,raw,changes):
        support.append((base,raw,[('alev',0,1),('aher',0,0),('aite',0,0)]+changes))
        return raw
    def attach(original,rank,abilities,auto=None):
        raw=cache[original,rank,True]
        changes=next(row[2] for row in units if row[1]==raw)
        changes.append(('uabi',3,','.join(abilities)))
        if auto: changes.append(('udaa',3,auto))
    for rank in range(1,51):
        growth=1+0.18*(rank-1)
        fire=effect('ANpi',f'Fi{rank:02}',[('Eim1',2,balance['infernal_immolation_base']*growth,1,1),('aare',2,300.0,1,0),('atar',3,'ground,air,enemy,neutral',1,0)])
        attach('ninf',rank,['ACmi',fire,'ACrk'])
        fire=effect('Apig',f'Fk{rank:02}',[('Eim1',2,60.0*growth,1,1),('aare',2,280.0,1,0),('atar',3,'ground,air,enemy,neutral',1,0)])
        attach('npn1',rank,[fire,'ACrk'])
        spirit=make_unit('even',rank,True)
        vengeance=effect('Avng',f'Fv{rank:02}',[('Rai3',3,spirit,1,3)])
        attach('espv',rank,['ACmi','Asp1','ACrk',vengeance],vengeance)
        phoenix=cache['hphx',rank,True]; egg=make_unit('hpxe',rank,True)
        rebirth=effect('Aphx',f'Fh{rank:02}',[('Eme1',3,phoenix,1,1),('Emeu',3,egg,1,0)])
        fire=effect('Apxf',f'Fj{rank:02}',[('pxf1',2,120.0*growth,1,1),('pxf2',2,12.0*growth,1,2)])
        attach('hphx',rank,[rebirth,'ACmi','ACrk',fire])
        attach('hpxe',rank,[rebirth,'ACrk','ACmi'])
        tornado=effect('Atdg',f'Ft{rank:02}',[('Tdg1',2,21.0*growth,1,1),('Tdg3',2,150.0*growth,1,3)])
        attach('ntor',rank,[tornado,'Atsp','Atwa','Aasl'])
    return units,replacements,details,support


def summoned_units(root): return summon_catalog(str(root))[0]


def summon_support_abilities(root): return summon_catalog(str(root))[3]


def hero_abilities(root):
    seeds=json.loads((Path(root)/'map/ability-seeds.json').read_text())
    balance=json.loads((Path(root)/'map/balance.json').read_text())
    cooldown_multiplier=balance['offensive_cooldown_multiplier']
    _,replacements,summon_details,_=summon_catalog(str(root))
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
                if ultimate:
                    value=ultimate_value(rawcode,field,rank,value,balance['ultimate_power_multiplier'])
                aura=balance['aura_balance'].get(rawcode,{}).get(field['id'])
                if aura:
                    # Useful rank one, diminishing growth, exact finite rank-300 cap.
                    progress=((rank-1)/(rank-1+40))/((seed['cap']-1)/(seed['cap']-1+40))
                    value=round(min(aura['cap'],aura['start']+(aura['cap']-aura['start'])*progress),6)
                if rawcode in ('ANba','AEim') and field['id']=='atar':
                    # Do not exclude the undead/mechanical troop categories.
                    # Ground/air targets exclude the separate structure class.
                    value='air,ground,enemy,neutral'
                if rawcode=='ANba' and field['id']=='ahdu': value=2.0
                if field['id']=='acdn' and rawcode in ('AHds','AHtb','AEer','AOhx') and rank>seed['levels']:
                    # Prevent permanent shields or single-caster hard-control loops.
                    duration=max((f['values'][-1] for f in seed['fields'] if f['id']=='ahdu'),default=0)
                    floor=max(field['values'][-1]*0.4,duration+(8 if rawcode=='AHds' else 1))
                    floor=min(field['values'][-1],floor)
                    progress=(rank-seed['levels'])/max(1,seed['cap']-seed['levels'])
                    value=round(field['values'][-1]+(floor-field['values'][-1])*progress,4)
                if field['id']=='acdn' and rawcode in OFFENSIVE_SKILLS and value>0:
                    value=round(value*cooldown_multiplier,4)
                changes.append((field['id'],field['kind'],value,rank,field['column']))
                if aura:
                    multiplier=100 if aura['percent'] else 1
                    suffix='%' if aura['percent'] else ''
                    details.append(f'{aura["label"]}: +{value*multiplier:.2f}{suffix} (предел {aura["cap"]*multiplier:g}{suffix})')
                elif rawcode in balance['aura_balance'] and field['column']>0:
                    pass  # Hide technical aura flags from player tooltips.
                elif field['id'] in SUMMON_FIELDS:
                    hp,damage,scale=summon_details[value.split(',')[0]]
                    details.append(f'Призыв: {hp} HP; базовый урон {damage}; размер {scale:.2f}')
                elif field['id'] in COUNT_FIELDS:
                    details.append(f'Количество за вызов: {value}')
                elif field['kind']!=3 and field['column']>0 and any(w in field['label'].lower() for w in ('damage','heal','bonus','evasion','chance')):
                    details.append(f'{field["label"]}: {value:g}')
            text=f'Ранг {rank}/{seed["cap"]}. '+'; '.join(details[:3])
            if rawcode=='ANba': text+=' Цели: живые и Нежить. Убитые стрелой бойцы поднимаются скелетами.'
            changes += [('atp1',3,f'{seed["name"]} [{rank}]',rank,0),('aub1',3,text,rank,0)]
        entries.append((rawcode,'\0'*4,changes))
    return entries


def custom_hero_abilities(root):
    # Isolate mixed hero buttons: shared stock spells have conflicting positions.
    heroes=json.loads((Path(root)/'map/heroes.json').read_text())
    source={raw:changes for raw,_,changes in hero_abilities(root)}
    result=[]
    for hero in heroes:
        for slot,(raw,original) in enumerate(zip(hero['skills'],hero.get('skill_sources',[]))):
            changes=list(source[original])
            changes += [('aher',0,1),('abpx',0,slot),('abpy',0,2),('arpx',0,slot),('arpy',0,0)]
            result.append((original,raw,changes))
    return result


def attribute_ability():
    changes=[('anam',3,'Характеристики +'),('aher',0,1),('aite',0,0),('alev',0,500),
             ('arlv',0,1),('alsk',0,1),('arpx',0,3),('arpy',0,1),('abpx',0,3),('abpy',0,1),
             ('arar',3,'ReplaceableTextures\\CommandButtons\\BTNStatUp.blp'),
             ('aart',3,'ReplaceableTextures\\PassiveButtons\\PASBTNStatUp.blp'),
             ('aret',3,'Характеристики + [ранг %d]'),
             ('arut',3,'Одно очко навыка: +2 силы, +2 ловкости и +2 интеллекта за каждый ранг. До 500 рангов.')]
    for rank in range(1,501):
        changes += [('Iagi',0,2*rank,rank,1),('Iint',0,2*rank,rank,2),('Istr',0,2*rank,rank,3),
                    ('Ihid',0,0,rank,4),('atp1',3,f'Характеристики + [ранг {rank}]',rank,0),
                    ('aub1',3,f'+{rank*2} силы, ловкости и интеллекта. Каждый следующий ранг: ещё +2 ко всем.',rank,0)]
    return [('Aamk','Fatr',changes)]
