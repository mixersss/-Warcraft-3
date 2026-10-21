"""Four native, zero-cost army branch buttons on the permanent barracks."""
from army_traits import data
ORDERS=('berserk','roar','taunt','howlofterror')
ICONS=('BTNHumanBarracks.blp','BTNOrcBarracks.blp','BTNCrypt.blp','BTNAncientOfWar.blp')
def abilities(races):
    result=[]
    traits=data()['troops']
    for race,row in enumerate(races):
        # Reserve native rally(3,1), busy cancel(3,2) and wave research(0,1).
        col,button_row=((1,1),(2,1),(0,2),(1,2))[race]
        title='Выбрать армию: '+row['name']
        description=' → '.join(row['tier_names'][1:])+'. '+ ' '.join(traits[f'fm{race}{tier}']['description'] for tier in range(1,5))+' До первого развития базы все получают одинаковых пехотинцев. Выбор ветки окончательный; развитие оплачивается отдельно.'
        result.append(('ANcl',f'Fbr{race}',[
            ('anam',3,title),('aher',0,0),('aite',0,0),('alev',0,1),
            ('aart',3,'ReplaceableTextures\\CommandButtons\\'+ICONS[race]),('abpx',0,col),('abpy',0,button_row),
            ('atp1',3,title,1,0),('aub1',3,description,1,0),('ahky',3,'ZXCV'[race]),
            ('amcs',0,0,1,0),('acdn',2,0.,1,0),('acas',2,0.,1,0),('adur',2,0.,1,0),('ahdu',2,0.,1,0),
            ('Ncl1',2,0.,1,1),('Ncl2',0,0,1,2),('Ncl3',0,1,1,3),('Ncl4',2,0.,1,4),('Ncl5',0,0,1,5),('Ncl6',3,ORDERS[race],1,6)]))
    return result
