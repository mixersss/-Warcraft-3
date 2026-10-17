"""Independently authored chapter. Only the scenery/terrain comes from the source map."""
import json
from pathlib import Path
ROOT=Path(__file__).parent
# Coordinates are inside the four original first-chapter forest regions.
NODES=[(-14711,15611),(-12057,14824),(-10654,13930),(-8868,13112)]
OFFSETS=[(0,0),(8192,0),(0,-4864),(8192,-4864)]
ITEMS=[('rat6','Rc01','Кунай шиноби',150),('rst1','Rc02','Повязка выносливости',120),('rag1','Rc03','Повязка ловкости',120),('rin1','Rc04','Повязка чакры',120),('rde1','Rc05','Защитный жилет',160),('phea','Rc06','Лечебный настой',75),('pman','Rc07','Восстановление чакры',90)]
# Imported source art; keep independently configured effects and prices unchanged.
SHOP_ICONS={'rat6':'Icon_Kunai.BLP','rst1':'Icon_SoldierPills.blp','rag1':'Icon_Shuriken.BLP','rin1':'Icon_SoldierPills.blp','rde1':'Icon_GeninArmor.blp','phea':'Icon_Ramen.BLP','pman':'Icon_SoldierPills.blp'}
def item_entries():
 return [(base,raw,[('unam',3,name),('iico',3,SHOP_ICONS[base]),('utip',3,name),('utub',3,{'rat6':'+6 к урону.','rst1':'+3 к силе.','rag1':'+3 к ловкости.','rin1':'+3 к интеллекту.','rde1':'+2 к броне.','phea':'Восстанавливает 250 здоровья.','pman':'Восстанавливает 150 маны.'}[base]),('igol',0,cost),('ilum',0,0),('isto',0,1),('istr',0,10),('isst',0,0)]) for base,raw,name,cost in ITEMS]
def scroll_entries():
 return [('rat6',raw,[('unam',3,name),('utip',3,name),('utub',3,'Экзамен: принесите свитки Неба и Земли к башне в последние две минуты. Один комплект на отряд.'),('iico',3,icon),('ifil',3,'ScrollRed.mdl'),('iabi',3,''),('igol',0,0),('ilum',0,0),('idrp',0,1),('idro',0,1),('ipaw',0,0),('iper',0,1),('icla',3,'Campaign')]) for raw,name,icon in [('Eshe','Свиток Неба','Icon_ScrollHeaven.BLP'),('Esea','Свиток Земли','Icon_ScrollEarth.BLP')]]
def unit_entries():
 out=[]
 defs=[('re01','Разбойник Тумана','MistNin.mdl',650,26,128,1.05),('re02','Шиноби Дождя','RainGenin.mdl',850,32,450,1.),('re03','Хаку','haku.mdl',3800,48,550,.95),('re04','Момочи Забуза','Zabuza.mdl',8500,75,140,1.4),('re05','Водяной клон Забузы','Zabuza.mdl',1100,26,140,1.2),('re06','Генин Дождя','RainGenin.mdl',1400,45,550,1.),('re07','Генин Тумана','MistNin.mdl',1750,55,140,1.05),('rq01','Какаши — командир миссии','KakashiNew.mdl',5000,0,128,1.)]
 for raw,name,model,hp,damage,ran,scale in defs:
  mods=[('unam',3,name),('umdl',3,model),('uico',3,'ReplaceableTextures\\CommandButtons\\BTNBandit.blp'),('usca',1,scale),('uhpm',0,hp),('uhpr',2,0.),('ua1b',0,damage),('ua1d',0,1),('ua1s',0,1),('ua1c',2,1.6),('ua1r',0,ran),('umvs',0,290),('ucol',2,20.),('uabi',3,''),('upgr',3,''),('ureq',3,''),('ubba',0,0),('ubdi',0,0),('ubsi',0,0),('ulev',0,1)]
  if raw in ('re06','re07'):mods.extend([('uabi',3,'Aens'),('umpm',0,400),('umpi',0,400),('umpr',2,3.),('ulev',0,6)])
  if ran>200:mods.extend([('ua1w',3,'missile'),('ua1m',3,'Kunai.mdl'),('ua1z',0,1400)])
  if raw=='rq01':mods += [('uaen',0,0),('uabi',3,'Avul'),('umvs',0,0)]
  out.append(('hfoo',raw,mods))
 out.append(('ngme','rqsh',[('unam',3,'Снабжение отряда'),('usei',3,','.join(x[1] for x in ITEMS)),('uabi',3,'Aneu,Apit,Avul'),('ucol',2,32.),('upgr',3,''),('ureq',3,'')]))
 out.append(('hfoo','rean',[('unam',3,'Анко — экзаменатор'),('umdl',3,'Anko.mdl'),('uico',3,'ReplaceableTextures\\CommandButtons\\BTNFarSight.blp'),('uabi',3,'Avul'),('uaen',0,0),('umvs',0,0),('ucol',2,0.),('upgr',3,''),('ureq',3,'')]))
 # Sand crest: persistent visible Birth animation; no attack, collision or orders.
 out.append(('hfoo','rswv',[('unam',3,'Песчаное цунами'),('umdl',3,'GaaraSand2.mdl'),('uico',3,'ReplaceableTextures\\CommandButtons\\BTNFarSight.blp'),('uabi',3,'Aloc,Avul'),('uaen',0,0),('umvs',0,0),('ucol',2,0.),('ushr',0,0),('usca',1,1.5)]))
 # Four original mentors, paused in camp until their departure timer expires.
 mentors=json.loads((ROOT/'src/original-forest-spawns.json').read_text())['mentors']
 template=next(mods for _,raw,mods in out if raw=='rq01')
 for n,mentor in enumerate(mentors[1:],2):
  mods=[(k,t,mentor['name'] if k=='unam' else mentor['model'] if k=='umdl' else v) for k,t,v in template]
  out.append(('hfoo','rq0'+str(n),mods))
 for base,raw,mods in out:
  if raw.startswith('rq0'):
   mods.extend([('uaen',0,1),('ua1b',0,65),('umvs',0,340)])
  if raw in ('re01','re02'):mods.extend([('ulev',0,4)])
  if raw=='re03':mods.extend([('ulev',0,20)])
  if raw=='re04':mods.extend([('ulev',0,30)])
  if raw=='re04':mods.extend([('uabi',3,'Zbwp,Zbce,Zbbl'),('umpm',0,1000),('umpi',0,1000),('umpr',2,6.)])
 for _,_,mods in out:mods[:]=list({k:(k,t,v) for k,t,v in mods}.values())
 return out

def generated_data():
 lines=[]
 source=json.loads((ROOT/'src/original-forest-spawns.json').read_text())
 for t,(ox,oy) in enumerate(OFFSETS):
  for n,(x,y) in enumerate(NODES):
   lines += [f'    set StoryX[{t*4+n}]={float(x+ox)}',f'    set StoryY[{t*4+n}]={float(y+oy)}']
 for t,positions in enumerate(source['ninjas']):
  for n,(x,y) in enumerate(positions+ [source['haku'][t],source['zabuza'][t]]):
   lines += [f'    set EnemySpawnX[{t*18+n}]={x}',f'    set EnemySpawnY[{t*18+n}]={y}']
  lines += [f"    set StoryMentorType[{t}]='rq0{t+1}'",f'    set StoryMentorName[{t}]='+json.dumps(source['mentors'][t]['name'],ensure_ascii=False)]
 from loot import LOOT
 for n,row in enumerate(LOOT):lines.append(f"    set StoryLootType[{n}]='{row[2]}'")
 for n,(_,raw,_,cost) in enumerate(ITEMS):lines += [f"    set StoryItem[{n}]='{raw}'",f'    set StoryPrice[{n}]={cost}']
 exam=json.loads((ROOT/'src/exam-source.json').read_text())
 for t,(x,y) in enumerate(exam['navigation']['entrances']):lines += [f'    set ExamSpawnX[{t}]={float(x)}',f'    set ExamSpawnY[{t}]={float(y)}']
 for j,(x,y) in enumerate(exam['navigation']['enemies']):lines += [f'    set ExamEnemyX[{j}]={float(x)}',f'    set ExamEnemyY[{j}]={float(y)}']
 for j,row in enumerate(json.loads((ROOT/'src/exam-questions.json').read_text())):
  text=row['text']+' |n'+'   '.join(str(k+1)+') '+v for k,v in enumerate(row['options']))
  lines += [f'    set ExamQuestionText[{j}]='+json.dumps(text,ensure_ascii=False),f"    set ExamCorrect[{j}]={row['answer']}"]
 return '\n'+'\n'.join(lines)

def ability_entries():
 from loot import abilities
 out=abilities()
 # All heroes have a non-learnable smart-tree target. Runtime cancels native eating.
 out.append(('Aeat','Rjtr',[('anam',3,'Прыжок на дерево'),('aher',0,0),('aite',0,0),('alev',0,1),('areq',3,''),('aart',3,'UI\\Feedback\\Resources\\ResourceLumber.blp'),('atp1',3,'Прыжок на дерево [T]',1,0),('aub1',3,'ПКМ по живому дереву: прыжок в радиусе 1000. 50 чакры, перезарядка 3 сек. Дерево сохраняется.',1,0),('ahky',3,'T'),('abpx',0,2),('abpy',0,1),('amcs',0,0,1,0),('acdn',2,0.,1,0),('aran',2,1000.,1,0),('acas',2,10.,1,0),('atar',3,'tree',1,0),('adur',2,0.,1,0),('ahdu',2,0.,1,0),('Eat1',2,0.,1,1),('Eat2',2,.1,1,2),('Eat3',2,0.,1,3),('aani',3,'walk'),('aefs',3,''),('aefl',3,'')]))
 out.append(('AHtb','Zbwp',[('anam',3,'Суйтон: водяная тюрьма'),('aher',0,0),('aite',0,0),('alev',0,1),('areq',3,''),('Htb1',2,120.,1,1),('amcs',0,80,1,0),('acdn',2,12.,1,0),('aran',2,700.,1,0),('adur',2,2.,1,0),('ahdu',2,1.5,1,0),('atar',3,'ground,air,enemy,organic',1,0),('amat',3,'Abilities\\Weapons\\WaterElementalMissile\\WaterElementalMissile.mdl'),('amsp',0,1100,1,0),('aani',3,'spell'),('aefs',3,''),('aefl',3,'')]))
 out.append(('ACce','Zbce',[('anam',3,'Рассекающий удар'),('aher',0,0),('aite',0,0),('alev',0,1),('areq',3,''),('aare',2,225.,1,0),('aefs',3,''),('aefl',3,'')]))
 out.append(('AEbl','Zbbl',[('anam',3,'Рывок Скрытого Тумана'),('aher',0,0),('aite',0,0),('alev',0,1),('areq',3,''),('Ebl1',2,850.,1,1),('Ebl2',2,0.,1,2),('amcs',0,30,1,0),('acdn',2,10.,1,0),('aran',2,850.,1,0),('adur',2,.33,1,0),('aani',3,'spell'),('aefs',3,''),('aefl',3,'')]))
 return out
