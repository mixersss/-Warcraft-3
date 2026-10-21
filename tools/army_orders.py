"""Instant barracks orders replace the four branch cards after commitment."""
from army_branches import ORDERS
CORNERS=('нижняя левая база','нижняя правая база','верхняя правая база','верхняя левая база')
CELLS=((1,1),(2,1),(0,2),(1,2))
def abilities():
    result=[]
    for corner in range(4):
        for center in (False,True):
            title='Держать центр' if center else 'Наступать: '+CORNERS[corner]
            description='Солдаты сражаются в центре и возвращаются туда после преследования.' if center else 'Все новые волны сначала идут в центр, затем наступают на '+CORNERS[corner]+'. Уже вышедшая армия меняет направление через центр. При уничтожении выбранной команды — держать центр.'
            result.append(('ANcl',('Fac' if center else 'Fao')+str(corner),[
                ('anam',3,title),('aher',0,0),('aite',0,0),('alev',0,1),('areq',3,''),
                ('aart',3,'ReplaceableTextures\\CommandButtons\\'+('BTNHoldPosition.blp' if center else 'BTNMove.blp')),
                ('abpx',0,CELLS[corner][0]),('abpy',0,CELLS[corner][1]),('ahky',3,'ZXCV'[corner]),
                ('atp1',3,title,1,0),('aub1',3,description+' Приказ действует только на вашу армию. Экстренная защита своей крепости имеет приоритет.',1,0),
                ('amcs',0,0,1,0),('acdn',2,0.,1,0),('acas',2,0.,1,0),('adur',2,0.,1,0),('ahdu',2,0.,1,0),
                ('Ncl1',2,0.,1,1),('Ncl2',0,0,1,2),('Ncl3',0,1,1,3),('Ncl4',2,0.,1,4),('Ncl5',0,0,1,5),('Ncl6',3,ORDERS[corner],1,6)]))
    return result
