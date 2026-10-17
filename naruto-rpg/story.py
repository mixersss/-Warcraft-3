"""Independently authored chapter. Only the scenery/terrain comes from the source map."""
import json
from pathlib import Path
ROOT=Path(__file__).parent
# Coordinates are inside the four original first-chapter forest regions.
NODES=[(-14711,15611),(-12057,14824),(-10654,13930),(-8868,13112)]
OFFSETS=[(0,0),(8192,0),(0,-4864),(8192,-4864)]
ITEMS=[('rat6','Rc01','Кунай шиноби',150),('rst1','Rc02','Повязка выносливости',120),('rag1','Rc03','Повязка ловкости',120),('rin1','Rc04','Повязка чакры',120),('rde1','Rc05','Защитный жилет',160),('phea','Rc06','Лечебный настой',75),('pman','Rc07','Восстановление чакры',90)]
def item_entries():
 return [(base,raw,[('unam',3,name),('utip',3,name),('utub',3,{'rat6':'+6 к урону.','rst1':'+3 к силе.','rag1':'+3 к ловкости.','rin1':'+3 к интеллекту.','rde1':'+2 к броне.','phea':'Восстанавливает 250 здоровья.','pman':'Восстанавливает 150 маны.'}[base]),('igol',0,cost),('ilum',0,0),('isto',0,1),('istr',0,10),('isst',0,0)]) for base,raw,name,cost in ITEMS]
def unit_entries():
 out=[]
 defs=[('re01','Разбойник Тумана','MistNin.mdl',650,26,128,1.05),('re02','Шиноби Дождя','RainGenin.mdl',850,32,450,1.),('re03','Хаку','haku.mdl',3800,48,550,.95),('re04','Момочи Забуза','Zabuza.mdl',8500,75,140,1.4),('re05','Водяной клон Забузы','Zabuza.mdl',1100,26,140,1.2),('rq01','Какаши — командир миссии','KakashiNew.mdl',5000,0,128,1.)]
 for raw,name,model,hp,damage,ran,scale in defs:
  mods=[('unam',3,name),('umdl',3,model),('uico',3,'ReplaceableTextures\\CommandButtons\\BTNBandit.blp'),('usca',1,scale),('uhpm',0,hp),('uhpr',2,0.),('ua1b',0,damage),('ua1d',0,1),('ua1s',0,1),('ua1c',2,1.6),('ua1r',0,ran),('umvs',0,290),('ucol',2,20.),('uabi',3,''),('upgr',3,''),('ureq',3,''),('ubba',0,0),('ubdi',0,0),('ubsi',0,0),('ulev',0,1)]
  if ran>200:mods.extend([('ua1w',3,'missile'),('ua1m',3,'Kunai.mdl'),('ua1z',0,1400)])
  if raw=='rq01':mods += [('uaen',0,0),('uabi',3,'Avul'),('umvs',0,0)]
  out.append(('hfoo',raw,mods))
 out.append(('ngme','rqsh',[('unam',3,'Снабжение отряда'),('usei',3,','.join(x[1] for x in ITEMS)),('uabi',3,'Aneu,Apit,Avul'),('ucol',2,32.),('upgr',3,''),('ureq',3,'')]))
 # Sand crest: persistent visible Birth animation; no attack, collision or orders.
 out.append(('hfoo','rswv',[('unam',3,'Песчаное цунами'),('umdl',3,'GaaraSand2.mdl'),('uico',3,'ReplaceableTextures\\CommandButtons\\BTNFarSight.blp'),('uabi',3,'Aloc,Avul'),('uaen',0,0),('umvs',0,0),('ucol',2,0.),('ushr',0,0),('usca',1,1.5)]))
 return out

def generated_data():
 lines=[]
 for t,(ox,oy) in enumerate(OFFSETS):
  for n,(x,y) in enumerate(NODES):
   lines += [f'    set StoryX[{t*4+n}]={float(x+ox)}',f'    set StoryY[{t*4+n}]={float(y+oy)}']
 for n,(_,raw,_,cost) in enumerate(ITEMS):lines += [f"    set StoryItem[{n}]='{raw}'",f'    set StoryPrice[{n}]={cost}']
 return '\n'+'\n'.join(lines)
