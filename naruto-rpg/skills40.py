"""Source-native helpers; source records stay checked in and are never mutated."""
import json
from pathlib import Path
ROOT=Path(__file__).parent
DATA=json.loads((ROOT/'src/skills40-source.json').read_text())
def helper(ver,old,new,ranks=1):
 obj=DATA[ver]['abilities'][old];mods=[]
 for m in obj['modifications']:
  if m['levelOrVariation']>ranks:continue
  if m['id'] in {'arhk','ahky','arlv','alsk','atp1','aub1','aret','arut','areq','abpx','abpy','arpx','arpy'}:continue
  mods.append((m['id'],m['variableType'],m['value'],m['levelOrVariation'],m['dataPointer']))
 mods += [('aher',0,0),('aite',0,0),('alev',0,ranks),('abpx',0,0),('abpy',0,-11),('aefs',3,''),('aefl',3,''),('acat',3,''),('aeat',3,''),('areq',3,'')]
 if old in {'A00V','A025','A02C'}:mods += [('amcs',0,0,1,0),('acdn',2,0.,1,0),('acas',2,0.,1,0)]
 # Source health/mana drain is channelled by an invisible helper.
 if old=='A024':
  mods += [('aart',3,'Icon_Kiba_SmokeBomb.BLP')]
  for n in range(1,5):mods += [('adur',2,.2,n,0),('ahdu',2,.1,n,0),('abuf',3,'BPSE',n,0),('amcs',0,0,n,0),('acdn',2,0.,n,0)]
 return obj['oldId'],new,mods
def abilities():
 out=[helper('35','A02C','R40d'),helper('42','A02P','R40p'),helper('42','A02Q','R40q'),helper('35','A025','R40w'),helper('35','A00V','R40t'),helper('35','A024','R40c',4)]
 agi=[('anam',3,'Ловкость четвероногой формы'),('aher',0,0),('alev',0,3),('abpy',0,-11),('aefs',3,''),('aefl',3,'')]
 for rank,value in enumerate([20,40,80],1):agi += [('Iagi',0,value,rank,1),('Iint',0,0,rank,2),('Istr',0,0,rank,3)]
 out.append(('Aamk','R40a',agi));return out
def units():
 caster=[('unam',3,'Вспомогательная техника'),('umdl',3,''),('uabi',3,'Aloc,Avul'),('uaen',0,0),('umvs',0,0),('umvt',3,'fly'),('ucol',2,0.),('ufoo',0,0),('usin',0,0),('usid',0,0),('umpr',2,0.),('umpm',0,10000),('umpi',0,10000),('ucpt',2,0.),('ucbs',2,0.)]
 out=[]
 for raw,abilities in [('r40d','R40d'),('r40w','R40w,R40t'),('r40c','R40c')]:out.append(('hfoo',raw,[(k,t,v+','+abilities if k=='uabi'else v)for k,t,v in caster]))
 out.append(('hfoo','r40s',[('unam',3,'Железный шар — управление правой кнопкой'),('umdl',3,'Iron Wrecking Ball.mdl'),('uico',3,'Icon_Tenten_Jindana.blp'),('uabi',3,'Avul'),('uaen',0,0),('umvs',0,0),('umvt',3,'fly'),('umvh',2,200.),('umvf',2,200.),('ucol',2,0.),('usca',1,12.),('ufoo',0,0),('usin',0,0),('usid',0,0),('umpr',2,0.),('umpm',0,0),('ureq',3,''),('upgr',3,'')]))
 bomb=DATA['42']['units']['n005'];mods=[(m['id'],m['variableType'],m['value'])for m in bomb['modifications']]
 mods += [('unam',3,'Бомба марионетки'),('uabi',3,'R40p,R40q,Aloc'),('uaen',0,0),('ufoo',0,0),('uhpm',0,100),('uhpr',2,0.),('ubba',0,0),('ubdi',0,0),('ubsi',0,0),('ureq',3,''),('upgr',3,'')]
 out.append((bomb['oldId'],'r40b',mods));return out
