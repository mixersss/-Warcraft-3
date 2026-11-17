"""Classic five-group forge frames and complete payment/inventory confirmation flows."""
import copy
import dataclasses
import struct
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from crafting import Crafting,request,unfix
from classic_wire import string
from inventory import BagItem
from mechanics import forge_parts
import test_mechanics as source
from equipment import ItemCatalog
GEAR=ItemCatalog(ROOT/'assets/items.json')

def item(identity,parameter=0,fusion=0,level=1):
 return BagItem(identity,1,10000,10000,0,level,0,True,(parameter,fusion),())

class Craft58Tests(unittest.TestCase):
 def make(self,parameter=0,fusion=0):
  w=source.actor();w.own.values.update({0:35,4:1,8:1000000});w.own.x=219600;w.own.y=270350
  target=item(5002 if fusion else 1397,parameter,fusion)
  w.own.equipment={9:target.identity};w.own.equipment_details={9:dict(identity=target.identity,count=1,valid=True,endurance=10000,max_endurance=10000,parameters=target.parameters)}
  w.entities[77]=dataclasses.replace(w.own,identity=77,control=2,x=219750,y=270350)
  life=copy.copy(source.LIFE);life.owner_shops={'catalog_revision':58,'npcs':[
   {'script_function':'OwnerForge','position':[219750,270350]},
   {'script_function':'OwnerClothes','position':[224750,277750],'offers':[5002]}]}
  life.prices=dict(life.prices);life.prices.update({i:5000 for i in (885,886,890,891,453,454,455,456)});life.prices[5002]=50000
  c=Crafting(w,GEAR,source.K,life,SimpleNamespace(phase=lambda *a:'craft'),Mock(),'Bot00000001')
  p=SimpleNamespace(sequence=1,emit=Mock(),position=lambda now:w.own.position,travel=None,nav=Mock(),move_to=Mock(return_value=True))
  p.nav.nearest.side_effect=lambda point,radius:point
  return w,c,p,target
 def test_safe_unfix_and_five_groups_match_native_writer(self):
  self.assertEqual(unfix(123,4,9,2),struct.pack('>IIBBh',123,4,10,9,2))
  self.assertEqual(request(3,(2,0,1)),b'\1\3'+struct.pack('>9h',1,2,1,1,0,1,1,1,1)+b'\0\0\0\0')
  with self.assertRaises(ValueError):unfix(1,1,9,-1)
  with self.assertRaises(ValueError):request(1,(0,0,1))
 def test_socket_cycle_requires_native_unequip_quote_payment_materials_and_result(self):
  w,c,p,target=self.make();w.bag={0:item(890),1:item(891)}
  self.assertTrue(c.tick(100,p));self.assertEqual(p.emit.call_args.args[0][8],10)
  self.assertEqual(w.own.equipment,{9:1397});self.assertEqual(c.confirmed,0)
  w.own.equipment={};w.bag[2]=target;c.tick(100.2,p);c.tick(100.4,p)
  menu=struct.pack('>IB',77,1)+string('Forge')+b'\1'+string('Create sockets')
  self.assertTrue(c.observe(802,menu,100.5));self.assertTrue(c.observe(837,b'',100.6))
  self.assertEqual(c.send.call_args.args,(525,request(3,(2,0,1))))
  c.observe(548,struct.pack('>BI',3,50000),100.7)
  self.assertEqual(c.send.call_args.args,(526,b'\1'));self.assertEqual(c.confirmed,0)
  c.observe(549,struct.pack('>IBB',w.own_id,3,1),100.8);c.tick(100.9,p)
  self.assertEqual(c.confirmed,0)
  w.bag={2:dataclasses.replace(target,parameters=(1000000000,0))};w.own.values[8]-=50000;c.tick(101,p)
  self.assertEqual(c.confirmed,1);self.assertEqual(c.pending['stage'],'reequip')
  c.tick(101.2,p);self.assertEqual(p.emit.call_args.args[0][8],11)
  self.assertEqual(w.own.equipment,{})
  w.own.equipment={9:1397};w.bag={};c.tick(101.4,p);self.assertFalse(c.busy)
 def test_no_unequip_far_from_npc_or_when_not_enough_money(self):
  w,c,p,target=self.make();w.bag={0:item(890),1:item(891)}
  w.own.x-=50000;c.tick(100,p);p.emit.assert_not_called();p.move_to.assert_called_once()
  w.own.values[8]=100;c.tick(101,p);p.emit.assert_not_called()
 def test_unexpected_quote_is_cancelled_without_fake_result(self):
  w,c,p,target=self.make();c.op=c.propose(target,2);w.bag={0:item(890),1:item(891)};c.op=c.propose(target,2)
  c.context={'npc':77,'stage':'quote','deadline':20}
  before=copy.deepcopy(w.bag)
  c.observe(548,struct.pack('>BI',3,999999),10)
  self.assertEqual(c.send.call_args.args,(526,b'\0'));self.assertEqual(w.bag,before);self.assertEqual(c.confirmed,0)
 def test_equally_levelled_owned_gems_are_combined_before_higher_embed(self):
  param=2000000000+12*10000000+1000000+13*10000+1000
  w,c,p,target=self.make(param,(1397<<16)|1)
  w.bag={0:item(886),1:item(863),2:item(863)}
  op=c.propose(target,9)
  self.assertEqual((op.mode,op.slots,op.fee),(2,(0,1,2),50000))
  w.bag={0:item(886),1:item(863,level=2),2:item(863,level=1),3:item(863,level=1)}
  # Desired rank3 may use lower-rank pairs recursively without buying fake rank3 gems.
  param=2000000000+12*10000000+2*1000000+13*10000+2*1000
  op=c.propose(dataclasses.replace(target,parameters=(param,(1397<<16)|2)),9)
  self.assertEqual((op.mode,op.slots),(2,(0,2,3)))
 def test_fused_equipment_scores_original_stats_and_real_embedded_gems(self):
  w,c,p,target=self.make()
  fused=item(5002,1000000000+12*10000000+1000000,1397<<16)
  self.assertEqual(GEAR.effective(5002,fused)['level'],35)
  self.assertTrue(GEAR.compatible(w.own,5002,fused))
  score=GEAR.loadout_score(w.own,{9:5002},{9:fused})
  self.assertGreater(score,GEAR.loadout_score(w.own,{9:1397}))
  self.assertIsNotNone(GEAR.upgrade(w.own,5002,10,fused))
 def test_same_model_with_better_forge_is_not_ignored(self):
  w,c,p,target=self.make()
  better=item(1397,1000000000+12*10000000+1000000)
  self.assertIsNotNone(GEAR.upgrade(w.own,1397,10,better))
 def test_refining_gems_are_combined_using_owned_pairs_and_scroll(self):
  param=2000000000+12*10000000+1000000+13*10000+1000
  w,c,p,target=self.make(param,(1397<<16)|1)
  w.bag={0:item(886),1:item(863,level=2),2:item(885),3:item(885)}
  op=c.propose(target,9)
  self.assertEqual((op.mode,op.slots,op.fee),(2,(0,2,3),50000))
  self.assertEqual(op.before.identity,885);self.assertEqual(c.confirmed,0)
 def test_real_apparel_vendor_binding_is_used(self):
  w,c,p,target=self.make()
  self.assertEqual(c.apparel(target),5002)

class Market58Tests(unittest.TestCase):
 def make(self):
  from test_market import MarketTests
  w,s,m,p=MarketTests().make();m.catalog.enable_forging_catalog(m.gear,m.life);m.forging_economy=True
  return w,m,p
 def test_higher_gem_prices_include_combination_costs(self):
  w,m,p=self.make();base=m.item_ask_price(item(863));level3=m.item_ask_price(item(863,level=3))
  self.assertEqual(level3,base*4+150000)
 def test_known_forged_spares_are_eligible_but_unknown_forge_data_is_protected(self):
  w,m,p=self.make();known=item(1397,1000000000+12*10000000+1000000)
  self.assertTrue(m.safe_forged(known))
  self.assertFalse(m.safe_forged(dataclasses.replace(known,parameters=(1000000000+99*10000000+1000000,0))))
  self.assertFalse(m.safe_forged(dataclasses.replace(known,endurance=0)))

if __name__=='__main__':unittest.main()
