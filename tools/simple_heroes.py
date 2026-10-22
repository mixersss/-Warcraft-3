"""Four straightforward kits: isolated native passives plus explicit summon/ultimate handlers."""
import json
from pathlib import Path
from balance_profiles import config as balance_profiles
from progression import hero_abilities

BUFFS=[('BOae','Bcbs'),('BOae','Bcas'),('BHad','Bcar'),('BOae','Bcsm'),('BOae','Bcua'),('BHad','Bcud'),('BOae','Bcrg')]
def buffs():return [(base,raw,[('fnam',3,'Усиление бойцов'),('fart',3,''),('fefl',3,'')])for base,raw in BUFFS]

def abilities(root):
    seeds={raw:mods for raw,_,mods in hero_abilities(root)};result=[]
    heroes=json.loads((Path(root)/'map/heroes.json').read_text())
    for hero in heroes:
        for slot,s in enumerate(hero.get('simple',[])):
            cap=50 if slot==3 else 200;raw=hero['skills'][slot];base=s['base']
            mods=list(seeds[base])if base!='ANcl'else[]
            mods += [('anam',3,s['name']),('aher',0,1),('aite',0,0),('alev',0,cap),('arlv',0,6 if slot==3 else 1),('alsk',0,10 if slot==3 else 1),('aani',3,'spell'),('aart',3,s['icon']),('arar',3,s['icon']),('aret',3,s['name']+' [ранг %d]'),('arut',3,s['description']),('ahky',3,'QWER'[slot]),('auhk',3,'QWER'[slot]),('arhk',3,'QWER'[slot]),('abpx',0,slot),('abpy',0,2),('arpx',0,slot),('arpy',0,0)]
            for rank in range(1,cap+1):
                t=(rank-1)/(cap-1);kind=s['kind'];
                if kind in ['army_speed','army_armor']:t=((rank-1)/(rank+19))/((cap-1)/(cap+19))
                v=[('atp1',3,s['name']+f' [{rank}]',0),('aub1',3,s['description']+f' Ранг {rank}/{cap}.',0),('amcs',0,s['mana'],0),('acdn',2,float(s['cooldown']),0)]
                if base=='ANcl':v += [('acas',2,0.,0),('adur',2,0.,0),('ahdu',2,0.,0),('aran',2,700.,0),('Ncl1',2,0.,1),('Ncl2',0,s['target'],2),('Ncl3',0,1,3),('Ncl4',2,0.,4),('Ncl5',0,0,5),('Ncl6',3,['berserk','roar','taunt','howlofterror'][slot],6)]
                if kind=='bowcrit':v += [('Ocr1',2,20.,1),('Ocr2',2,1.6+.7*t,2),('Ocr3',2,0.,3),('Ocr4',2,0.,4)]
                if kind in ['bowspeed','army_speed']:v += [('Oae1',2,0.,1),('Oae2',2,(.15+.5*t)if kind=='bowspeed'else(.12+.42*t),2),('aare',2,0. if kind=='bowspeed'else 900.,0),('atar',3,'self'if kind=='bowspeed'else'air,ground,friend,nonhero,vuln,invu',0),('abuf',3,'Bcbs'if kind=='bowspeed'else'Bcas',0)]
                if kind=='army_vamp':v += [('Uav1',2,0.,1),('aare',2,0.,0),('atar',3,'none',0),('abuf',3,'',0)]
                if kind=='army_armor':v += [('Had1',2,3.+19.*t,1),('Had2',0,0,2),('aare',2,900.,0),('atar',3,'air,ground,friend,nonhero,vuln,invu',0),('abuf',3,'Bcar',0)]
                if kind=='cleave':v += [('nca1',2,.35+.4*t,1),('aare',2,220.,0),('atar',3,'ground,enemy,neutral,nonstructure',0)]
                if kind=='evasion':v += [('Eev1',2,.15+.30*t,1)]
                if kind in ['escape','rogueescape']:v += [('adur',2,4.+(2. if kind=='escape'else 4.)*t,0),('ahdu',2,4.+(2. if kind=='escape'else 4.)*t,0),('Owk1',2,.1,1),('Owk2',2,.25 if kind=='escape'else.20,2),('Owk3',2,0. if kind=='escape'else 30.+3.*rank,3),('Owk4',0,0,4)]
                mods += [(field,typ,value,rank,ptr)for field,typ,value,ptr in v]
            mods=list({(m[0],m[3:]if len(m)==5 else(0,0)):m for m in mods}.values());result.append((base,raw,mods))
    # Hidden native item lifesteal works for actual ranged and melee attack damage.
    mods=[('anam',3,'Кровное братство'),('alev',0,480),('aher',0,0),('aite',0,1),('aart',3,'')]
    for rank in range(1,481):mods += [('Ivam',2,.001*rank,rank,1),('atar',3,'air,ground,enemy,neutral',rank,0)]
    result.append(('AIva','Clif',mods))
    for raw,base,buff,cap,values,radius in [('Csum','AOae','Bcsm',200,lambda t:(0.,.10+.15*t),700.),('Cuba','AOae','Bcua',50,lambda t:(0.,.20+.20*t),900.),('Cubd','AHad','Bcud',50,lambda t:(4.+8.*t,0),900.),('Crag','AOae','Bcrg',50,lambda t:(.15,.50+.40*t),0.)]:
        mods=[('anam',3,'Временное усиление'),('alev',0,cap),('aher',0,0),('aite',0,1),('aart',3,'')]
        for rank in range(1,cap+1):
            first,second=values((rank-1)/(cap-1));mods += [('abuf',3,buff,rank,0),('aare',2,radius,rank,0),('atar',3,'self'if raw=='Crag'else'air,ground,friend,nonhero,vuln,invu',rank,0)]
            mods += [('Oae1',2,first,rank,1),('Oae2',2,second,rank,2)]if base=='AOae'else[('Had1',2,first,rank,1),('Had2',0,0,rank,2)]
        result.append((base,raw,mods))
    result += [('AIva','Cvam',[('alev',0,1),('aher',0,0),('aite',0,1),('Ivam',2,.15,1,1)]),('AIsw','Cdet',[('alev',0,1),('aher',0,0),('aite',0,1),('amcs',0,0,1,0),('acdn',2,15.,1,0),('adur',2,180.,1,0),('ahdu',2,180.,1,0),('aran',2,500.,1,0)])]
    return result

def pet_stats(row,rank,balance):
    t=(rank-1)/(49 if row.get('ultimate') else 199)
    cfg=balance_profiles()['summons']
    budget=1+cfg['extra_unit_budget_weight']*(rank//10)
    hp=max(1,round(row['hp']*(1+(cfg['simple_hp_factor']-1)*t)*balance['summon_hp_multiplier']/budget))
    damage=round((row['damage']*(1+(cfg['simple_damage_factor']-1)*t)+rank*.15)*balance['summon_damage_multiplier']/budget)
    armor=round(row['armor']+8*t)
    scale=row['scale']*balance['summon_model_scale']*(1+.0005*(rank-1)*299/199)
    return hp,damage,armor,scale


def units(root):
    result=[]
    models=json.loads((Path(root)/'map/simple-pets.json').read_text())
    balance=json.loads((Path(root)/'map/balance.json').read_text())
    for family,row in enumerate(models):
        cap=50 if family==2 else 200
        for rank in range(1,cap+1):
            hp,damage,armor,scale=pet_stats(dict(row,ultimate=family==2),rank,balance)
            result.append((row['base'],f'k{family}{rank-1:02x}',[('unam',3,row['name']),('umdl',3,row['model']),('uico',3,row['icon']),('uhpm',0,hp),('ua1b',0,damage),('ua1d',0,1),('ua1s',0,2),('ua1c',2,row['attack_seconds']),('ua1r',0,row['range']),('uabi',3,'ACce'if family==2 else''),('umvt',3,'foot'),('umvs',0,300),('usca',1,scale),('ucol',2,16.),('udef',0,armor),('upgr',3,''),('ufoo',0,0),('ubba',0,0),('ubdi',0,0),('ubsi',0,0),('ureq',3,''),('uupt',3,''),('uclr',0,row['tint'][0]),('uclg',0,row['tint'][1]),('uclb',0,row['tint'][2])]))
    return result
