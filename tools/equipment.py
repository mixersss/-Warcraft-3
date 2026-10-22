"""Fortress and supreme shops and item effects supported by the Classic API."""
import json
from pathlib import Path

# Field IDs, types and data columns from Classic AbilityMetaData.slk.
EFFECTS={
 'attack':('AItg','Iatt',0,1), 'armor':('AId2','Idef',0,1),
 'strength':('AIs1','Istr',0,3), 'agility':('AIa1','Iagi',0,1),
 'intelligence':('AIi1','Iint',0,2), 'health':('AIlf','Ilif',0,1),
 'mana':('AImb','Iman',0,1), 'health_regen':('Arel','Ihpr',0,1),
 'mana_regen':('AIrm','Imrp',2,1),
 'move_speed':('AIms','Imvb',0,1), 'attack_speed':('AIsx','Isx1',2,1),
 'fire_dps':('AIcf','Icfd',0,1), 'lifesteal':('AIva','Ivam',2,1),
 'critical_chance':('AIcs','Ocr1',2,1),
}


def item_effects(root):
    abilities=[]; item_abilities={}
    for row in json.loads((Path(root)/'map/equipment.json').read_text())+json.loads((Path(root)/'map/supreme.json').read_text())+[r for r in json.loads((Path(root)/'map/arena-items.json').read_text())if 'stats'in r]:
        ids=[]
        for stat,value in row['stats'].items():
            if stat=='critical_multiplier': continue
            base,field,kind,column=EFFECTS[stat]
            raw=f'Fg{len(abilities):02d}';ids.append(raw)
            changes=[('alev',0,1),('aher',0,0),('aite',0,1),(field,kind,value,1,column)]
            if stat=='critical_chance': changes.append(('Ocr2',2,row['stats']['critical_multiplier'],1,2))
            if stat=='fire_dps':
                changes += [('aare',2,300.0,1,0),('atar',3,'ground,enemy',1,0)]
            abilities.append((base,raw,changes))
        item_abilities[row['id']]=','.join(ids+([row['extra_ability']]if 'extra_ability'in row else[]))
    return abilities,item_abilities


def potion_abilities(root):
    result=[]
    for row in json.loads((Path(root)/'map/potions.json').read_text()):
        if 'base_ability' not in row: continue
        result.append((row['base_ability'],row['ability'],[
            ('alev',0,1),('aher',0,0),('aite',0,1),(row['field'],0,row['amount'],1,1),('acdn',2,30.0,1,0),
            ('atp1',3,row['name'],1,0),('aub1',3,row['description'],1,0)]))
    return result


def utility_abilities(root):
    common=[('alev',0,1),('aher',0,0),('aite',0,1)]
    return [
      ('AIbk','Fdag',common+[('Ebl1',2,900.,1,1),('Ebl2',2,0.,1,2),('aran',2,900.,1,0),('amcs',0,0,1,0),('acdn',2,12.,1,0)]),
      ('AIrr','Fsdm',common+[('Roa1',2,.35,1,1),('aare',2,700.,1,0),('adur',2,45.,1,0),('ahdu',2,45.,1,0),('atar',3,'ground,air,friend,nonhero',1,0)]),
      ('AIda','Fsar',common+[('Idef',0,8,1,1),('aare',2,700.,1,0),('adur',2,45.,1,0),('ahdu',2,45.,1,0),('atar',3,'ground,air,friend,nonhero',1,0)]),
      ('AIha','Fshl',common+[('Ihpg',0,2500,1,1),('aare',2,700.,1,0),('atar',3,'ground,air,friend,nonhero,vuln,invu',1,0)])]
