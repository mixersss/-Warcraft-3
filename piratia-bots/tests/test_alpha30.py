"""Sell all safe junk, spread merchant admission and expose actual locations."""
import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from show_levels import render
from fleet import Fleet
import test_alpha18 as base

class SaleAndLocationTests(unittest.TestCase):
 def test_sale_visit_continues_past_five_stacks_until_all_safe_junk_is_sold(self):
  f=base.VendorTests();w,v,p=f.make();w.bag={i:f.item(1613,1) for i in range(6)}
  w.entities[77]=__import__('dataclasses').replace(w.own,identity=77,control=2)
  v.context=77,'ready',200
  for i in range(6):
   self.assertTrue(v.tick(100+i*2,p,True));self.assertEqual(v.pending[0],i)
   self.assertIn(i,w.bag)
   w.bag.pop(i);w.own.values[8]+=1
   v.tick(101+i*2,p,True)
  self.assertEqual(v.confirmed_sales,6);self.assertEqual(v.sales,6)
  self.assertFalse(v.tick(113,p,True));self.assertFalse(w.bag)
 def test_one_junk_item_can_start_sale_with_free_inventory_space(self):
  f=base.VendorTests();w,v,p=f.make();w.bag={0:f.item(1613,1)}
  p.allow_visit=lambda point,now:True
  self.assertTrue(v.tick(100,p,True));self.assertIsNotNone(v.sale_target)
 def test_one_piece_of_plain_junk_is_offered_without_any_reserve(self):
  f=base.VendorTests();w,v,p=f.make();w.bag={0:f.item(1613,1)}
  self.assertEqual(v.choices(p),[(0,1613,1)])
 def test_busy_nearest_merchant_does_not_block_all_other_city_shops(self):
  f=base.VendorTests();w,v,p=f.make();w.bag_capacity=1;w.bag={0:f.item(1613,1)}
  v.life.services={'shops':{'garner':[{'position':[w.own.x+100,w.own.y],'offers':[]},{'position':[w.own.x+500,w.own.y],'offers':[]}]}}
  p.allow_visit=lambda point,now:point[0]>w.own.x+100
  self.assertTrue(v.tick(100,p,True))
  self.assertEqual(v.sale_target['position'],[w.own.x+500,w.own.y])
 def test_all_merchants_busy_preserves_inventory_and_explains_retry(self):
  f=base.VendorTests();w,v,p=f.make();w.bag_capacity=1;w.bag={0:f.item(1613,1)}
  p.allow_visit=lambda point,now:False
  self.assertFalse(v.tick(100,p,True));self.assertEqual(w.bag[0].count,1)
  self.assertIn('заняты',v.reason);self.assertEqual(v.next_sale,115)
 def test_population_view_shows_map_coordinates_and_disconnected_status(self):
  with tempfile.TemporaryDirectory() as d:
   f=Fleet(200,Path(d)/'population-status.json')
   f.update(1,connected=True,map='garner',position=[222350,278550],level=13)
   f.update(2,connected=False,map='magicsea',position=[87614,357250],level=11)
   text=render(f.snapshot())
   self.assertIn('garner 2223,2785',text);self.assertIn('magicsea 876,3572 (не в сети)',text)
   self.assertIn('В сети: 1 / 200',text)

if __name__=='__main__':unittest.main()
