"""Five fortress shops and item effects supported by the Classic API."""
import json
from pathlib import Path

# Field IDs, types and data columns from Classic AbilityMetaData.slk.
EFFECTS={
 'attack':('AItg','Iatt',0,1), 'armor':('AId2','Idef',0,1),
 'strength':('AIs1','Istr',0,3), 'agility':('AIa1','Iagi',0,1),
 'intelligence':('AIi1','Iint',0,2), 'health':('AIlf','Ilif',0,1),
 'mana':('AImm','Iman',0,1), 'health_regen':('Arel','Ihpr',0,1),
 'mana_regen':('AIrm','Imrp',2,1),
 'move_speed':('AIms','Imvb',0,1), 'attack_speed':('AIsx','Isx1',2,1),
 'fire_dps':('AIcf','Icfd',0,1), 'lifesteal':('AIva','Ivam',2,1),
 'critical_chance':('AIcs','Ocr1',2,1),
}


def item_effects(root):
    abilities=[]; item_abilities={}
    for row in json.loads((Path(root)/'map/equipment.json').read_text()):
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
        item_abilities[row['id']]=','.join(ids)
    return abilities,item_abilities
