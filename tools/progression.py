"""Explicit Classic skill ranks and per-skill summons, without runtime stat hacks."""
import json
from balance_profiles import curve as balance_curve, hybrid as balanced_hybrid, illusion_damage, summon_stats, config as balance_profiles
from functools import lru_cache
from pathlib import Path

SUMMON_FIELDS = {'Hwe1','Osf1','Efnu','Esvu','Nbau','Ndou','Nef1','Nsy2','Nsyu','Rai3','Uin4','Ntou','Ulsu'}
COUNT_FIELDS = {'Hwe2','Osf2','Efn1','Esv1','Nba2','Ndo2','Rai1'}
# Active offensive spells only: preserve passive, toggle and support cooldowns.
OFFENSIVE_SKILLS = set(('AHtb AHtc AHbz AHfs AHbn AOcl AOws AOsh AOww AOeq AUdc AUfn AUcs AUim AUdd AUin AEer AEfk AEsh AEmb AEsf ANbf ANfl ANso ANvc ANht ANrf ANcs ANc1 ANc2 ANc3 ANst ANab ANsi ANdh ANdr AOhx AUsl ANch ANtm').split())

# Magnitudes only: never multiply flags, attack intervals or control durations.
ULTIMATE_MAGNITUDES = set('Eme5 Esf1 Etq1 Hav1 Hav2 Hav3 Ndo1 Nrg5 Nrg6 Nst3 Nvc5 Oeq2 Oww1 Uin1 Uls5'.split())
ULTIMATE_RECOVERY = {'AHmt':0.7,'AHre':0.65,'AUan':0.75,'ANch':0.7,'ANtm':0.7,'AOre':0.65,'AOvd':0.75}


def ultimate_value(ability, field, rank, value, power, tuning):
    raw=field['id']
    if raw in ULTIMATE_MAGNITUDES: value*=power
    if ability=='AUin' and raw=='Uin1': value=max(value,300+60*(rank-1))
    if ability=='AUdd' and raw=='Udd1': value=min(0.35,value*1.5)
    if ability=='AUls' and raw=='Uls4': value=min(6.0,value*1.5)
    if raw=='acdn' and ability in ULTIMATE_RECOVERY and value>1: value*=ULTIMATE_RECOVERY[ability]
    if ability=='AHmt' and raw=='Hmt1': value=max(value,min(96,24+2*rank))
    if ability=='AHmt' and raw=='Hmt2': value=max(1.0,2.5-0.03*(rank-1))
    if ability in ('ANch','ANtm') and raw in ('Nch1','Ntm3'): value=max(value,min(100,10+2*(rank-1)))
    # Fixed scripted reward replaces both native value conversion and bounty.
    if ability=='ANtm' and raw in ('Ntm1','Ntm4'): value=0
    if ability in ('AHre','AUan') and raw in ('Hre1','Uan1'):
        value=tuning['resurrection_start']+tuning['resurrection_step']*(rank-1)
    if ability=='AEme' and raw=='Eme5': value*=tuning['metamorph_hp_multiplier']
    if ability in ('ANrg','ANg1','ANg2','ANg3') and raw in ('Nrg5','Nrg6'):
        value=max(round(value*tuning['robo_power_multiplier']),round(field['values'][0]*power*tuning['robo_power_multiplier'])+(tuning['robo_strength_step']*(rank-1) if raw=='Nrg5' else (rank-1)//2))
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
        return round(max(1.0,last*(1-0.6*extra/max(1,(50 if ultimate else 200)-len(values)))),4) if last>1 else last
    if raw == 'aare': return round(last*(1+min(extra*(0.01 if ultimate else 0.0012),0.35)),4)
    if raw in ('acas','adur','ahdu','aran','amcs'): return last
    if raw == 'Nms2': return last  # Mana Shield already absorbs 100%.
    if raw in ('Ocl3','Uts2'):
        # Less chain falloff / less damage received is the improvement.
        return round(max(last*0.4,last*(1-0.002*extra)),5)
    if 'movement speed increase' in label: return round(min(1.0,last+0.005*extra),5)
    if 'attack speed increase' in label: return round(min(3.0,last+0.01*extra),5)
    # These are engine mechanics and identifiers, not scalable magnitudes.
    progress=extra/max(1,(50 if ultimate else 200)-len(values))
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
    if not ultimate: step *= (300-len(values))/max(1,200-len(values))
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
            src=stock[original]; extra=(rank-1)*(299/199 if not ultimate else 1)
            factor=(1+extra*(0.60 if ultimate else 0.15))*(balance['ultimate_summon_hp_multiplier'] if ultimate else 1)
            damage_factor=1+extra*(0.45 if ultimate else 0.12)
            scale=src['scale']*balance['summon_model_scale']*(1+extra*(0.002 if ultimate else 0.0005))
            damage_extra=extra
            if original in ('hwat','hwt2','hwt3') and not ultimate:
                # Keep the former maximum, but defer most growth until later ranks.
                tuning=balance['water_elemental_growth']
                progress=min(1.,(rank-1)/(tuning['full_growth_rank']-1))
                growth_extra=extra*(tuning['early_fraction']+(1.-tuning['early_fraction'])*progress)
                factor=1.+growth_extra*.15
                damage_factor=1.+growth_extra*.12
                damage_extra=growth_extra
            hp=round(src['hp']*factor)
            damage=round((src['damage']*damage_factor+damage_extra*(2 if ultimate else 1))*(balance['ultimate_summon_damage_multiplier'] if ultimate else 1))
            armor=src['armor']+extra*(0.6 if ultimate else 0.2)
            tuning=balance['hero_skill_balance']
            boost=tuning['panda_power_multiplier'] if original in ('npn1','npn2','npn3') else tuning['factory_power_multiplier'] if original in ('ncgb','ncg1','ncg2','nfac','nfa1','nfa2') else 1
            hp=round(hp*boost);damage=round(damage*boost)
            if original=='ninf':
                hp=round(hp*balance['infernal_power_multiplier'])
                damage=round(damage*balance['infernal_power_multiplier'])
                armor*=balance['infernal_power_multiplier']
            # Modest global reduction after all rank/type-specific tuning, including nested summons.
            hp=max(1,round(hp*balance['summon_hp_multiplier']))
            damage=round(damage*balance['summon_damage_multiplier'])
            units.append((original,raw,[('uhpm',0,hp),('ua1b',0,damage),('udef',0,round(armor)),
                ('usca',1,scale),('ucol',2,min(src['collision'],24.0)),
                ('upgr',3,''),('ufoo',0,0),('ugol',0,0),('ulum',0,0)]))
            hp,damage,armor=summon_stats(original,rank,ultimate,src,balance)
            units[-1][2][:3]=[('uhpm',0,hp),('ua1b',0,damage),('udef',0,armor)]
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
        growth=1+(balance_profiles()['summons']['secondary_effect_factor']-1)*(rank-1)/49.
        fire=effect('ANpi',f'Fi{rank:02}',[('Eim1',2,balance['infernal_immolation_base']*growth,1,1),('aare',2,300.0,1,0),('atar',3,'ground,air,enemy,neutral',1,0)])
        attach('ninf',rank,['ACmi',fire,'ACrk'])
        fire=effect('Apig',f'Fk{rank:02}',[('Eim1',2,60.0*growth*balance['hero_skill_balance']['panda_power_multiplier'],1,1),('aare',2,280.0,1,0),('atar',3,'ground,air,enemy,neutral',1,0)])
        attach('npn1',rank,[fire,'ACrk'])
        spirit=make_unit('even',rank,True)
        vengeance=effect('Avng',f'Fv{rank:02}',[('Rai3',3,spirit,1,3)])
        attach('espv',rank,['ACmi','Asp1','ACrk',vengeance],vengeance)
        phoenix=cache['hphx',rank,True]; egg=make_unit('hpxe',rank,True)
        rebirth=effect('Aphx',f'Fh{rank:02}',[('Eme1',3,phoenix,1,1),('Emeu',3,egg,1,0)])
        fire=effect('Apxf',f'Fj{rank:02}',[('pxf1',2,120.0*growth,1,1),('pxf2',2,12.0*growth,1,2)])
        attach('hphx',rank,[rebirth,'ACmi','ACrk',fire])
        attach('hpxe',rank,[rebirth,'ACrk','ACmi'])
        tornado_boost=balance['hero_skill_balance']['tornado_damage_multiplier']
        tornado=effect('Atdg',f'Ft{rank:02}',[('Tdg1',2,21.0*growth*tornado_boost*balance['spell_damage_multiplier'],1,1),('Tdg3',2,150.0*growth*tornado_boost*balance['spell_damage_multiplier'],1,3)])
        attach('ntor',rank,[tornado,'Atsp','Atwa','Aasl'])
    return units,replacements,details,support


def chemical_forms(root):
    balance=json.loads((Path(root)/'map/balance.json').read_text())
    timing=json.loads((Path(root)/'map/hero-attack-seeds.json').read_text())['units']['Nalc']
    result=[]
    for rank in range(1,balance['basic_skill_max']+1):
        bonus=balance_curve('ANcr','Ncr6',rank,balance['basic_skill_max'])
        mods=[(field,2,round(value*balance['hero_attack_interval_multiplier']/(1+bonus),6)) for field,value in timing.items()]
        mods.append(('uhab',3,'ANab,ANcr,ANhs,ANtm,Fatr'))
        result.append((['Nalm','Nal2','Nal3'][min(rank,3)-1],f'Zc{rank:02x}',mods))
    return result


def summoned_units(root): return summon_catalog(str(root))[0]


def summon_support_abilities(root): return summon_catalog(str(root))[3]


def hybrid_power(root,rawcode,rank):
    seeds=json.loads((Path(root)/'map/ability-seeds.json').read_text())
    raw={'AHhb':'Hhb1','AUdc':'Udc1','AEmb':'Emb1'}[rawcode]
    return balanced_hybrid(rawcode,rank)


def hero_abilities(root):
    seeds=json.loads((Path(root)/'map/ability-seeds.json').read_text())
    balance=json.loads((Path(root)/'map/balance.json').read_text())
    names=json.loads((Path(root)/'map/skill-names-ru.json').read_text())
    cooldown_multiplier=balance['offensive_cooldown_multiplier']
    _,replacements,summon_details,_=summon_catalog(str(root))
    entries=[]
    for rawcode,seed in seeds.items():
        seed=dict(seed,name=names.get(rawcode,seed['name']))
        ultimate=seed['ultimate']
        req,skip=(6,10) if ultimate else (1,1)
        changes=[('alev',0,seed['cap']),('arlv',0,req),('alsk',0,skip)]
        slots={skill:slot for hero in json.loads((Path(root)/'map/heroes.json').read_text()) if 'base' not in hero for slot,skill in enumerate(hero['skills'])}
        slot=slots.get(rawcode,2 if rawcode=='AEfn' else None)
        if rawcode[:3] in ('ANs','ANc','ANg') and rawcode[-1:].isdigit(): slot={'ANs':0,'ANc':1,'ANg':3}[rawcode[:3]]
        if slot is not None:
            key='QWER'[slot]
            changes += [('ahky',3,key),('auhk',3,key),('arhk',3,key),('abpx',0,slot),('abpy',0,2),('arpx',0,slot),('arpy',0,0)]
        changes += [('aret',3,f'Изучить {seed["name"]} [уровень %d]'),('arut',3,f'{seed["name"]}. Максимальный ранг: {seed["cap"]}. Требования: уровень героя {req}, затем каждые {skip} уровней.')]
        for rank in range(1,seed['cap']+1):
            details=[]
            for field in seed['fields']:
                value=replacements.get((rawcode,rank,field['id']),scaled_value(field,rank,ultimate))
                if ultimate:
                    value=ultimate_value(rawcode,field,rank,value,balance['ultimate_power_multiplier'],balance['hero_skill_balance'])
                if rawcode=='AOmi' and field['id'] in ('Omi2','Omi3'):
                    t=balance['hero_skill_balance'];prefix='mirror_damage' if field['id']=='Omi2' else 'mirror_taken'
                    value=round(t[prefix+'_start']+(t[prefix+'_cap']-t[prefix+'_start'])*(rank-1)/(seed['cap']-1),6)
                if rawcode=='ANab':
                    if field['id']=='Nab4': value=20.+12.*(rank-1)
                    elif field['id']=='Nab5': value=12.+8.*(rank-1)
                    elif field['id']=='Nab3': value=min(60,6+(rank-1)//4)
                if rawcode=='ANcr':
                    if field['id']=='Emeu': value=f'Zc{rank:02x}'
                    elif field['id']=='Ncr6': value=round(min(3.,.25+(rank-1)*2.75/(seed['cap']-1)),6)
                aura=balance['aura_balance'].get(rawcode,{}).get(field['id'])
                if aura:
                    # Useful rank one, diminishing growth, exact finite final-rank cap.
                    shape=balance['aura_curve_shape']
                    progress=((rank-1)/(rank-1+shape))/((seed['cap']-1)/(seed['cap']-1+shape))
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
                if field['id'] in balance['spell_damage_fields'].get(rawcode,[]):
                    value=round(value*balance.get('spell_damage_overrides',{}).get(rawcode,balance['spell_damage_multiplier']),5)
                if (rawcode,field['id']) in (('AHhb','Hhb1'),('AUdc','Udc1'),('AEmb','Emb1')):
                    # The shared native amount would also weaken healing/mana removal.
                    # A bounded spell-effect handler separates the damage component.
                    value=0.
                value=balance_curve(rawcode,field['id'],rank,seed['cap'],value)
                if rawcode=='AOmi' and field['id']=='Omi2':
                    count=scaled_value(next(f for f in seed['fields']if f['id']=='Omi1'),rank,False)
                    value=illusion_damage(rank,count)
                if rawcode in ('AHhb','AUdc','AEmb') and field['id']in ('Hhb1','Udc1','Emb1'):value=0.
                if field['kind']==0:value=round(value)
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
            if rawcode in ('AHre','AUan'): text+=f' Поднимает до {balance["hero_skill_balance"]["resurrection_start"]+rank-1} павших бойцов (+1 за ранг).'
            if rawcode=='ANtm': text+=f' За успешное превращение: ровно {balance["transmute_gold_base"]+balance["transmute_gold_step"]*(rank-1)} золота; +30 за ранг. Не зависит от цены цели.'
            if rawcode=='ANcr': text+=f' Настоящая ускоренная форма: +{balance_curve("ANcr","Ncr6",rank,seed["cap"])*100:.1f}% к частоте атак через уменьшение базового интервала.'
            if rawcode in ('AHhb','AUdc'):
                power=hybrid_power(root,rawcode,rank)
                text=f'Ранг {rank}/{seed["cap"]}. Лечение: {power:g}; урон вражеской цели: {power*.5*balance["spell_damage_multiplier"]:g}.'
            elif rawcode=='AEmb':
                power=hybrid_power(root,rawcode,rank)
                text=f'Ранг {rank}/{seed["cap"]}. Сжигает до {power:g} маны и наносит {balance["spell_damage_multiplier"]*100:g}% от сожжённой маны уроном.'
            if rawcode=='AOmi':
                count=scaled_value(next(f for f in seed['fields']if f['id']=='Omi1'),rank,False)
                text+=f' Суммарный урон всех {count} копий: {count*illusion_damage(rank,count)*100:.1f}% урона героя.'
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
        if hero.get('creative') or hero.get('simple'): continue
        for slot,(raw,original) in enumerate(zip(hero['skills'],hero.get('skill_sources',[]))):
            changes=list(source[original])
            if hero.get('ability_names'):
                name=hero['ability_names'][slot]
                changes += [('anam',3,name),('aret',3,name+' [ранг %d]')]
                for rank in range(1,(50 if slot==3 else 200)+1):
                    changes += [('atp1',3,name+f' [{rank}]',rank,0)]
            if hero.get('cast_animation'):
                changes += [('aani',3,hero['cast_animation'])]
            signature=hero.get('signature')
            if signature and (signature['slot']==slot or (signature['slot']==-1 and slot==0)):
                changes += [('anam',3,signature['name']),('aret',3,signature['name']+' [ранг %d]')]
                for rank in range(1, (50 if slot==3 else 200)+1):
                    tip=next(c[2] for c in changes if c[0]=='aub1' and len(c)==5 and c[3]==rank)
                    changes += [('atp1',3,signature['name']+f' [{rank}]',rank,0),('aub1',3,tip+' '+signature['name']+': '+signature['description'],rank,0)]
            changes += [('ahky',3,'QWER'[slot]),('auhk',3,'QWER'[slot]),('arhk',3,'QWER'[slot]),('aher',0,1),('abpx',0,slot),('abpy',0,2),('arpx',0,slot),('arpy',0,0)]
            changes=list({(c[0],c[3:] if len(c)==5 else (0,0)):c for c in changes}.values())
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


def army_passives(root):
    result=[]
    balance=json.loads((Path(root)/'map/balance.json').read_text());cap=balance['basic_skill_max'];shape=balance['aura_curve_shape']
    for spec in json.loads((Path(root)/'map/hero-passives.json').read_text()):
        slot=spec['slot'];icon=spec['icon']
        mods=[('anam',3,spec['name']),('aher',0,1),('aite',0,0),('alev',0,cap),('arlv',0,1),('alsk',0,1),
              ('ahky',3,'QWER'[slot]),('auhk',3,'QWER'[slot]),('arhk',3,'QWER'[slot]),
              ('abpx',0,slot),('abpy',0,2),('arpx',0,slot),('arpy',0,0),
              ('aart',3,f'ReplaceableTextures\\PassiveButtons\\PASBTN{icon}.blp'),
              ('arar',3,f'ReplaceableTextures\\CommandButtons\\BTN{icon}.blp'),
              ('aret',3,f'Изучить {spec["name"]} [ранг %d]'),('arut',3,'Пассивная аура для армии. Каждый ранг усиливает эффект; радиус 900.')]
        for rank in range(1,cap+1):
            progress=((rank-1)/(rank-1+shape))/((cap-1)/(cap-1+shape))
            amount=round(spec['start']+(spec['cap']-spec['start'])*progress,6)
            mult=100 if spec['percent'] else 1;suffix='%' if spec['percent'] else ''
            mods += [(spec['field'],spec['kind'],amount,rank,spec['column']),
                     (spec['zero_field'],0 if spec['zero_field']=='Oar2' else 2,0,rank,spec['zero_column']),
                     ('aare',2,float(spec['radius']),rank,0),('atar',3,spec['targets'],rank,0),('abuf',3,spec['buff'],rank,0),
                     ('atp1',3,f'{spec["name"]} [{rank}]',rank,0),
                     ('aub1',3,f'{spec["description"]}: +{amount*mult:.2f}{suffix}. Предел +{spec["cap"]*mult:g}{suffix}; радиус {spec["radius"]}. Действует на союзников, включая Нежить и механических бойцов.',rank,0)]
        result.append((spec['base'],spec['id'],mods))
    return result


def army_aura_buffs(root):
    # Unique buff IDs let these auras coexist with the stock hero/fountain auras.
    return [(s['buff_base'],s['buff'],[('fnam',3,s['name']),('ftip',3,s['name']),('fube',3,s['description']),('fefs',3,''),('fefl',3,'')])
            for s in json.loads((Path(root)/'map/hero-passives.json').read_text())]


def keeper_treants(root):
    """Native instant summon: identical ranked treants, no destructable targets."""
    original=next(changes for raw,_,changes in hero_abilities(root) if raw=='AEfn')
    changes=[]
    for change in original:
        field,kind,value,*position=change
        if field in ('atar','Efnu','Efn1'):
            if field=='atar':continue
            field='Hwe1' if field=='Efnu' else 'Hwe2'
        if field in ('aret','arut'):continue
        if field=='atp1':value=f'Сила природы [{position[0]}]'
        elif field=='aub1':value+=' Призывает энтов рядом с героем без деревьев; не требует выбора цели.'
        changes.append((field,kind,value,*position))
    changes += [('anam',3,'Сила природы'),('aher',0,1),('aite',0,0),('areq',3,''),
                ('aart',3,'ReplaceableTextures\\CommandButtons\\BTNEnt.blp'),
                ('arar',3,'ReplaceableTextures\\CommandButtons\\BTNEnt.blp'),
                ('asat',3,''),('acat',3,''),('atat',3,''),
                ('aret',3,'Изучить Силу природы [уровень %d]'),
                ('arut',3,'Призывает энтов рядом с героем без деревьев. Рост характеристик и числа энтов сохранён. До 200 рангов.')]
    # The inherited AHwe order is immediate and needs neither a tree nor a point.
    return [('AHwe','Fent',list({(c[0],c[3:] if len(c)==5 else (0,0)):c for c in changes}.values()))]
