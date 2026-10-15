"""Three fortress shops and item effects supported by the Classic API."""
import json
from pathlib import Path

# Field IDs, types and data columns from Classic AbilityMetaData.slk.
EFFECTS={
 'attack':('AItg','Iatt',0,1), 'armor':('AId2','Idef',0,1),
 'strength':('AIs1','Istr',0,3), 'agility':('AIa1','Iagi',0,1),
 'intelligence':('AIi1','Iint',0,2), 'health':('AIlf','Ilif',0,1),
 'mana':('AImm','Iman',0,1), 'health_regen':('Arel','Ihpr',0,1),
 'mana_regen':('AIrm','Imrp',2,1),
}


def item_effects(root):
    abilities=[]; item_abilities={}
    for row in json.loads((Path(root)/'map/equipment.json').read_text()):
        ids=[]
        for stat,value in row['stats'].items():
            base,field,kind,column=EFFECTS[stat]
            raw=f'Fg{len(abilities):02d}';ids.append(raw)
            abilities.append((base,raw,[('alev',0,1),('aher',0,0),('aite',0,1),
                                      (field,kind,value,1,column)]))
        item_abilities[row['id']]=','.join(ids)
    return abilities,item_abilities
