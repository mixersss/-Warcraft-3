"""Explicit role-based, bounded curves for the 500-level Classic arena."""
import json
from functools import lru_cache
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
@lru_cache(maxsize=1)
def config():return json.loads((ROOT/'map/balance-profiles.json').read_text())
def progress(rank,cap,shape=60):
    if cap<=1:return 0.
    x=(rank-1)/(cap-1)
    return x if not shape else ((rank-1)/(rank-1+shape))/((cap-1)/(cap-1+shape))
def curve(raw,field,rank,cap,default=None):
    spec=config()['curves'].get(raw,{}).get(field)
    if spec is None:return default
    t=progress(rank,cap,spec['shape'])
    return round(spec['start']+(spec['cap']-spec['start'])*t,6)
def hybrid(raw,rank,cap=200):
    start,end=config()['hybrid'][raw]
    return round(start+(end-start)*progress(rank,cap),5)
def illusion_damage(rank,count):
    start,end=config()['illusion_group_damage']
    return round((start+(end-start)*progress(rank,200))/max(1,count),6)
@lru_cache(maxsize=1)
def summon_families():
    seeds=json.loads((ROOT/'map/ability-seeds.json').read_text());result={}
    for raw,seed in seeds.items():
        originals=set()
        for f in seed['fields']:
            if f['id']in {'Hwe1','Osf1','Efnu','Esvu','Nbau','Ndou','Nef1','Nsy2','Nsyu','Rai3','Uin4','Ntou','Ulsu'}:
                for value in f['values']:originals.update(value.split(','))
        count=[f for f in seed['fields']if f['id']in {'Hwe2','Osf2','Efn1','Esv1','Nba2','Ndo2','Rai1'}]
        for original in originals:result.setdefault((original,seed['ultimate']),[]).extend(count)
    return result

@lru_cache(maxsize=None)
def summon_count(original,rank,ultimate):
    maximum=1
    for f in summon_families().get((original,ultimate),[]):
        value=f['values'][min(rank,len(f['values']))-1]+rank//10
        if f['id']=='Esv1':value*=3
        maximum=max(maximum,value)
    return maximum

def summon_stats(original,rank,ultimate,stock,balance):
    t=progress(rank,50 if ultimate else 200,0)
    cfg=config()['summons'];prefix='ultimate' if ultimate else 'normal'
    hp_factor=cfg[prefix+'_hp_factor'];damage_factor=cfg[prefix+'_damage_factor']
    if original in ('ndr1','ndr2','ndr3'):
        hp_factor=2.;damage_factor=3.
    budget=1+cfg['extra_unit_budget_weight']*max(0,summon_count(original,rank,ultimate)-summon_count(original,1,ultimate))
    hp=stock['hp']*(1+(hp_factor-1)*t)/budget
    damage=(stock['damage']*(1+(damage_factor-1)*t)+rank*(.2 if ultimate else .15))/budget
    armor=stock['armor']+cfg[prefix+'_armor_bonus']*t
    if ultimate:
        hp*=balance['ultimate_summon_hp_multiplier'];damage*=balance['ultimate_summon_damage_multiplier']
    boost=balance['hero_skill_balance']['panda_power_multiplier']if original in ('npn1','npn2','npn3')else balance['hero_skill_balance']['factory_power_multiplier']if original in ('ncgb','ncg1','ncg2','nfac','nfa1','nfa2')else 1
    hp*=boost;damage*=boost
    if original=='ninf':hp*=balance['infernal_power_multiplier'];damage*=balance['infernal_power_multiplier'];armor*=balance['infernal_power_multiplier']
    return max(1,round(hp*balance['summon_hp_multiplier'])),max(0,round(damage*balance['summon_damage_multiplier'])),round(armor)

def incinerate_ability():
    seed=json.loads((ROOT/'map/incinerate-seed.json').read_text())
    mods=[('anam',3,'Испепеление'),('aher',0,1),('aite',0,0),('alev',0,200),('arlv',0,1),('alsk',0,1),('ahky',3,'E'),('auhk',3,'E'),('arhk',3,'E'),('abpx',0,2),('abpy',0,2),('arpx',0,2),('arpy',0,0),('areq',3,''),('aart',3,'ReplaceableTextures\\PassiveButtons\\PASBTNIncinerate.blp'),('arar',3,'ReplaceableTextures\\CommandButtons\\BTNIncinerate.blp'),('aret',3,'Изучить Испепеление [уровень %d]')]
    for rank in range(1,201):
        t=progress(rank,200)
        values={'Nic1':2+18*t,'Nic2':50+750*t,'Nic3':100.,'Nic4':25+375*t,'Nic5':200.,'Nic6':.2}
        for f in seed['fields']:mods.append((f['id'],2,round(values[f['id']],6),rank,f['column']))
        mods += [('adur',2,2.,rank,0),('ahdu',2,2.,rank,0),('amcs',0,0,rank,0),('atar',3,'air,ground,enemy,neutral',rank,0),('atp1',3,'Испепеление ['+str(rank)+']',rank,0),('aub1',3,f"Удары накапливают по {values['Nic1']:.2f} дополнительного урона. Взрыв при смерти: {values['Nic2']:.1f} урона в радиусе 100, половина до 200. Пассивно; рост на каждом ранге.",rank,0)]
    return [('ANic','Finc',mods)]
