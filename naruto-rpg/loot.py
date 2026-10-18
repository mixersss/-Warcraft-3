"""Original equipment names/art and independently configured Classic item effects."""
# source id, base, new id, name, icon, ground model, ability, charges, price, description
LOOT=[
('I00A','rde1','Nlga','Снаряжение генина','Icon_GeninArmor.blp','Bag_1.mdl','Lgar',0,200,'+10 к броне.'),
('I00K','rde1','Nlca','Снаряжение чунина','Icon_ChuninArmor3.blp','Bag_1.mdl','Lcar',0,450,'+25 к броне.'),
('I00G','crdt','Nlku','Кунай','Icon_Kunai.BLP','Kunai.mdl','Ljkn',1,35,'Бросок: 150 урона, короткое оглушение; дальность 700.'),
('I002','crdt','Nlsh','Сюрикены','Icon_Shuriken.BLP','Shurikens.mdl','Ljsh',2,60,'Два броска: по 150 урона с коротким оглушением; дальность 500.'),
('I007','pres','Nlra','Рамен','Icon_Ramen.BLP','Ramen.mdl','Lrmn',2,75,'Две порции: по 400 здоровья и 400 чакры за 20 секунд. Работает при полной чакре или полном здоровье; восстановление продолжается при получении урона.'),
('I006','pres','Nlpi','Солдатские пилюли','Icon_SoldierPills.blp','Bag_1.mdl','AIsa',4,30,'Четыре порции для восстановления выносливости.'),
('I008','crdt','Nlne','Сети','ReplaceableTextures\\CommandButtons\\BTNEnsnare.blp','Abilities\\Spells\\Orc\\Ensnare\\EnsnareMissile.mdl','Ljnt',2,30,'Две сети: временно удерживают противника.')]
def items():
 out=[]
 for source,base,raw,name,icon,model,ability,charges,price,desc in LOOT:
  out.append((base,raw,[('unam',3,name),('utip',3,name),('utub',3,desc),('ides',3,desc),('iico',3,icon),('ifil',3,model),('iabi',3,ability),('igol',0,price),('ilum',0,0),('isto',0,10),('istr',0,0),('isst',0,0),('iuse',0,charges),('iprn',0,int(charges>0)),('iper',0,1),('icla',3,'Charged' if charges else 'Permanent')]))
 return out

def abilities():
 out=[]
 def entry(base,raw,name,mods):
  out.append((base,raw,[('anam',3,name),('aher',0,0),('aite',0,1),('alev',0,1),('areq',3,''),('aefs',3,''),('aefl',3,'')]+mods))
 for raw,armor in [('Lgar',10),('Lcar',25)]:entry('AId1',raw,'Защита снаряжения',[('Idef',0,armor,1,1)])
 for raw,ran,model in [('Ljkn',700.,'Kunai.mdl'),('Ljsh',500.,'Shurikens.mdl')]:
  entry('AHtb',raw,'Бросок куная' if raw=='Ljkn' else 'Бросок сюрикена',[('Htb1',2,150.,1,1),('amcs',0,0,1,0),('acdn',2,2.5,1,0),('aran',2,ran,1,0),('adur',2,.5,1,0),('ahdu',2,.25,1,0),('atar',3,'ground,air,enemy,neutral,organic',1,0),('amat',3,model),('amsp',0,1200 if raw=='Ljkn' else 800,1,0)])
 entry('ANcl','Lrmn','Рамен',[('Ncl1',2,0.,1,1),('Ncl2',0,0,1,2),('Ncl3',0,1,1,3),('Ncl4',2,0.,1,4),('Ncl5',0,0,1,5),('Ncl6',3,'rejuvenation',1,6),('amcs',0,0,1,0),('acdn',2,1.,1,0),('adur',2,0.,1,0),('ahdu',2,0.,1,0),('atar',3,'',1,0)])
 entry('ANcl','Lexp','Установить взрывную печать',[('aart',3,'Icon_ExplodingNote.BLP'),('Ncl1',2,0.,1,1),('Ncl2',0,2,1,2),('Ncl3',0,17,1,3),('Ncl4',2,0.,1,4),('Ncl5',0,0,1,5),('Ncl6',3,'stasistrap',1,6),('amcs',0,0,1,0),('acdn',2,2.,1,0),('aran',2,300.,1,0),('atar',3,'',1,0)])
 entry('Aens','Ljnt','Сеть',[('amcs',0,0,1,0),('acdn',2,6.,1,0),('aran',2,600.,1,0),('adur',2,6.,1,0),('ahdu',2,3.,1,0)])
 return out

def note_units():
 return [('nglm','rnnt',[('unam',3,'Взрывная печать'),('umdl',3,'Note.mdl'),('uico',3,'Icon_ExplodingNote.BLP'),('usca',1,1.5),('uhpm',0,100),('uhpr',2,0.),('uabi',3,''),('uaen',0,0),('umvs',0,0),('ucol',2,0.),('usin',0,0),('usid',0,0),('ufoo',0,0),('ureq',3,''),('upgr',3,'')])]
