"""Classic picker: seven cards, four controls, and the native rally command."""
import math

CARDS_PER_PAGE = 7


def controls():
    rows=[('Fprv','Предыдущая страница','BTNScrollOfTownPortal.blp','berserk'),
          ('Fnxt','Следующая страница','BTNScrollOfProtection.blp','taunt'),
          ('Frnd','Случайный герой','BTNSelectHeroOn.blp','roar'),
          ('Fmod','Режим игры','BTNBookOfTheDead.blp','howlofterror')]
    result=[]
    for col,(raw,name,icon,order) in enumerate(rows):
        result.append(('ANcl',raw,[('anam',3,name),('aher',0,0),('aite',0,0),('alev',0,1),
            ('aart',3,'ReplaceableTextures\\CommandButtons\\'+icon),('abpx',0,col),('abpy',0,2),
            ('atp1',3,name,1,0),('aub1',3,name+'. Выбор открыт до начала боя.',1,0),
            ('amcs',0,0,1,0),('acdn',2,0.0,1,0),('acas',2,0.0,1,0),
            ('adur',2,0.0,1,0),('ahdu',2,0.0,1,0),('Ncl1',2,0.0,1,1),
            ('Ncl2',0,0,1,2),('Ncl3',0,1,1,3),('Ncl4',2,0.0,1,4),
            ('Ncl5',0,0,1,5),('Ncl6',3,order,1,6),('acat',3,''),('atat',3,''),('aeat',3,'')]))
    return result


def units(heroes, basic_skill_max=200):
    result=[]
    for idx,hero in enumerate(heroes):
        result.append(('hpea',f'fp{idx:02d}',[
            ('unam',3,hero['name']),('uico',3,hero['icon']),
            ('utip',3,'Выбрать: '+hero['name']),
            ('utub',3,hero.get('description','Стандартный герой Warcraft III.')+f' Выбор бесплатный. Навыки до {basic_skill_max}, ульта до 50.'),
            ('ubpx',0,idx%CARDS_PER_PAGE%4),('ubpy',0,idx%CARDS_PER_PAGE//4),('ubld',0,1),
            ('ugol',0,0),('ulum',0,0),('ufoo',0,0),('ureq',3,''),('uabi',3,''),('upgr',3,''),
        ]))
    for page in range(math.ceil(len(heroes)/CARDS_PER_PAGE)):
        result.append(('hbar',f'fpk{page}',[
            ('unam',3,f'|cffffcc00ГАЛЕРЕЯ ГЕРОЕВ|r — {page+1}/{math.ceil(len(heroes)/CARDS_PER_PAGE)}'),
            ('utra',3,','.join(f'fp{idx:02d}' for idx in range(page*CARDS_PER_PAGE,min(len(heroes),(page+1)*CARDS_PER_PAGE)))),
            ('uabi',3,'Fprv,Fnxt,Frnd,Fmod'),('ures',3,''),('ureq',3,''),('uupt',3,''),
            ('upat',3,''),('ucol',2,0.0),('uico',3,'ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp'),
            ('umdl',3,'Buildings\\Other\\Tavern\\Tavern.mdl'),('usca',1,0.65),
            ('utip',3,'Выбор героя по портрету'),('utub',3,'Нажми портрет героя. Внизу: страницы, случайный герой и режим игры.'),
        ]))
    for hero in heroes:
        if 'base' not in hero: continue
        r,g,b=hero['tint']
        result.append((hero['base'],hero['id'],[
            ('unam',3,hero['name']),('upro',3,hero['proper_name']),('uico',3,hero['icon']),
            ('uhab',3,','.join(hero['skills']+['Fatr'])),('uabi',3,'AInv'),('ureq',3,''),('upgr',3,''),
            ('utip',3,hero['name']),('utub',3,hero['description']),
            ('uclr',0,r),('uclg',0,g),('uclb',0,b),
            ('umdl',3,hero['model']),('umvt',3,'foot'),('usca',1,hero.get('scale',0.8)),
            ('ustr',0,hero['stats']['strength']),('uagi',0,hero['stats']['agility']),('uint',0,hero['stats']['intelligence']),
            ('ustp',2,hero['stats']['strength_growth']),('uagp',2,hero['stats']['agility_growth']),('uinp',2,hero['stats']['intelligence_growth']),
            ('uhpm',0,hero['stats']['hp']),('umpm',0,hero['stats']['mana']),('ua1b',0,hero['stats']['damage']),('udef',0,hero['stats']['armor']),
        ]))
        if hero.get('signature') or hero.get('creative') or hero.get('simple'):
            result[-1][2].extend([('upra',3,['STR','AGI','INT'][hero['primary']]),('usnd',3,hero['soundset'])])
        if hero.get('attack_visual'):
            visual=hero['attack_visual']
            result[-1][2].extend([('ua1w',3,'missile'),('ua1r',0,visual['range']),('ua1m',3,visual['projectile']),('ua1z',0,visual['speed'])])
    return result
