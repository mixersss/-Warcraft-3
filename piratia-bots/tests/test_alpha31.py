"""Ordinary NPC merchants accept all players; no artificial admission quota."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from world import Entity
from adventure import talk_request
from vendor import sell_request
from unittest.mock import Mock
import test_alpha18 as base

class ConcurrentMerchantTests(unittest.TestCase):
 def test_two_hundred_bots_independently_talk_and_sell_to_same_npc(self):
  f=base.VendorTests();requests=0
  for index in range(200):
   w,v,p=f.make();w.bag={0:f.item(1613,1)}
   point=list(w.own.position)
   v.life.services={'shops':{'garner':[{'position':point,'offers':[]}]}}
   w.entities[77]=Entity(11,77,177,2,0,*point,40)
   p.allow_visit=Mock(side_effect=AssertionError('merchant admission must not be consulted'))
   self.assertTrue(v.tick(100,p,True));p.send.assert_called_with(301,talk_request(77))
   v.context=77,'ready',200;self.assertTrue(v.tick(101,p,True))
   p.send.assert_called_with(308,sell_request(77,0,1))
   self.assertEqual(w.bag[0].count,1);self.assertEqual(v.confirmed_sales,0)
   w.bag.clear();w.own.values[8]+=1;v.tick(102,p,True)
   self.assertEqual(v.confirmed_sales,1);p.allow_visit.assert_not_called();requests+=v.sales
  self.assertEqual(requests,200)

if __name__=='__main__':unittest.main()
