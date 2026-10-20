"""Channel is only a UI/order shell; every effect is implemented in creative-heroes.j."""
import json
from pathlib import Path

def abilities(root):
    result=[]
    for hero in json.loads((Path(root)/'map/heroes.json').read_text()):
        for slot,skill in enumerate(hero.get('creative',[])):
            cap=50 if slot==3 else 200
            changes=[('anam',3,skill['name']),('aher',0,1),('aite',0,0),('alev',0,cap),
                ('arlv',0,6 if slot==3 else 1),('alsk',0,10 if slot==3 else 1),('aani',3,'spell'),
                ('ahky',3,'QWER'[slot]),('auhk',3,'QWER'[slot]),('arhk',3,'QWER'[slot]),
                ('abpx',0,slot),('abpy',0,2),('arpx',0,slot),('arpy',0,0),
                ('aart',3,skill['icon']),('arar',3,skill['icon']),('aret',3,skill['name']+' [ранг %d]'),
                ('arut',3,skill['description']),('acat',3,''),('atat',3,''),('aeat',3,'')]
            for rank in range(1,cap+1):
                changes += [(field,kind,value,rank,ptr)for field,kind,value,ptr in [
                    ('amcs',0,skill['mana'],0),('acdn',2,float(skill['cooldown']),0),('acas',2,0.,0),
                    ('adur',2,0.,0),('ahdu',2,0.,0),('aran',2,700.,0),
                    ('Ncl1',2,0.,1),('Ncl2',0,skill['target'],2),('Ncl3',0,1,3),
                    ('Ncl4',2,0.,4),('Ncl5',0,0,5),('Ncl6',3,['berserk','roar','taunt','howlofterror'][slot],6),
                    ('atar',3,'air,ground,friend,self,hero' if hero['id']=='Fy01'and slot==1 else 'air,ground,enemy,neutral',0),
                    ('atp1',3,skill['name']+f' [{rank}]',0),('aub1',3,skill['description']+f' Ранг {rank}/{cap}. Мана {skill["mana"]}; откат {skill["cooldown"]} сек.',0)]]
            result.append(('ANcl',hero['skills'][slot],changes))
    return result
