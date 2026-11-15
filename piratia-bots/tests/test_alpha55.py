"""Earned transactions, possession state, compatibility and config preservation."""
import copy
import dataclasses
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import Mock
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import test_pet_economy as pets
import test_alpha44 as banking
import test_market as markets
from configure_dungeon_maps import configure, REQUIRED
from show_levels_gold import collect
from economy import Economy


class Reports55Tests(unittest.TestCase):
 def test_gold_fallback_is_aged_and_never_reads_private_accounts(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   (root/'population-status.json').write_text(json.dumps({'requested':3,'updated_unix':990,'bots':{'1':{'level':30,'gold':1000,'connected':True},'2':{'level':20,'connected':False}}}))
   (root/'bot-report-02.json').write_text(json.dumps({'time_utc':'1970-01-01T00:15:00+00:00','hunt':{'world':{'level':19}},'petcare':{'cash':240}}))
   (root/'bot-local.json').write_text('must never parse this')
   rows=collect(root,1000)
   self.assertEqual((rows[0]['gold'],rows[0]['snapshot_age_seconds']),(1000,10))
   self.assertEqual((rows[1]['level'],rows[1]['gold'],rows[1]['snapshot_age_seconds']),(19,240,100))
   self.assertIsNone(rows[2]['gold']);self.assertIsNone(rows[2]['level'])
 def test_missing_gold_is_unknown_instead_of_zero(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'population-status.json').write_text('{"requested":1,"bots":{}}')
   self.assertIsNone(collect(p,1000)[0]['gold'])


class Maps55Tests(unittest.TestCase):
 def fixture(self,root):
  (root/'GameServer.cfg').write_bytes(b'[ID]\r\nname = PrivateName\r\n[DB]\r\npassword = PRIVATE\r\n[MAP]\r\nmap = garner\r\n')
  (root/'GameServer2.cfg').write_bytes(b'map = magicsea\r\n')
  for name in REQUIRED:
   folder=root/'resource'/name;folder.mkdir(parents=True)
   for file in (name+'.blk',name+'.atr','ctrl.lua','entry.lua'):(folder/file).write_bytes(b'unchanged')
 def test_preview_apply_repeat_preserves_id_credentials_and_other_instances(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);old=(root/'GameServer.cfg').read_bytes()
   self.assertEqual(configure(root)['added_maps'],list(REQUIRED));self.assertEqual((root/'GameServer.cfg').read_bytes(),old)
   report=configure(root,True);self.assertTrue(report['applied']);new=(root/'GameServer.cfg').read_bytes()
   self.assertTrue(new.startswith(old.rstrip(b'\r\n')));self.assertEqual((root/'GameServer2.cfg').read_bytes(),b'map = magicsea\r\n')
   self.assertEqual(next(root.glob('*.backup')).read_bytes(),old)
   self.assertFalse(configure(root,True)['applied']);self.assertEqual((root/'GameServer.cfg').read_bytes(),new)
 def test_missing_map_resources_refuse_without_writing(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);(root/'resource/hell5/hell5.atr').unlink();old=(root/'GameServer.cfg').read_bytes()
   with self.assertRaises(ValueError):configure(root,True)
   self.assertEqual((root/'GameServer.cfg').read_bytes(),old);self.assertFalse(list(root.glob('*.backup')))
 def test_does_not_duplicate_maps_already_assigned_to_other_processes(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);(root/'GameServer2.cfg').write_bytes(b'map = magicsea\nmap = hell\n')
   self.assertNotIn('hell',configure(root)['added_maps'])


class Fairy55Tests(unittest.TestCase):
 def make(self):
  w,c,p=pets.FairyTests().make();w.own.values[2]=100
  w.skills[280]={'level':3,'state':1,'sp':20,'interval_ms':180000}
  w.bag={1:pets.item(681,energy=0,parameters=(1000000000,0),instance_attributes=((26,10),(27,0),(28,0),(29,0),(30,0)))}
  p.position=lambda now:w.own.position
  return w,c,p
 def test_junior_cast_requires_real_server_state_not_only_sent_request(self):
  w,c,p=self.make();before=dict(w.bag)
  self.assertTrue(c.possession_usable(1));self.assertTrue(c.tick(1,p));self.assertEqual(p.emit.call_args.args[0][8],2)
  c.possession_sent(1);self.assertEqual(c.possession_confirmed,0);self.assertEqual(w.bag,before)
  w.observe(511,struct.pack('>IBBB',w.own_id,1,174,3));c.tick(2,p)
  self.assertEqual(c.possession_confirmed,1);self.assertFalse(c.possession_usable(190))
  w.observe(511,struct.pack('>IB',w.own_id,0));self.assertTrue(c.possession_usable(190))
 def test_wrong_slot_generation_low_food_and_mana_never_fake_cast(self):
  for kind in ('slot','generation','food','mana','level'):
   w,c,p=self.make()
   if kind=='slot':w.bag={4:w.bag[1]}
   if kind=='generation':w.bag[1]=dataclasses.replace(w.bag[1],parameters=(0,0))
   if kind=='food':w.bag[1]=dataclasses.replace(w.bag[1],endurance=4999)
   if kind=='mana':w.own.values[2]=19
   if kind=='level':w.bag[1]=dataclasses.replace(w.bag[1],instance_attributes=((26,0),(27,0),(28,0),(29,0),(30,0)))
   self.assertFalse(c.possession_usable(1),kind)
 def test_skill_books_work_for_owned_book_not_only_when_buying_it(self):
  w,c,p=self.make();w.skills={};w.bag[4]=pets.item(246)
  self.assertIn(246,[i for i,_,_ in c.pet_skill_goals(1)])
  self.assertTrue(c.tick(1,p));self.assertEqual(p.emit.call_args.args[0][-4:],struct.pack('>hh',4,1))
  del w.bag[4];c.tick(2,p);self.assertEqual(c.confirmed,0)
  w.bag[1]=dataclasses.replace(w.bag[1],parameters=(1021000000,0));c.tick(3,p)
  self.assertEqual(c.confirmed,1)


class Economy55Tests(unittest.TestCase):
 def test_recovered_patchouli_requires_both_native_bag_and_bank_changes(self):
  w,s,m,p,b=banking.BankTests().make();item=pets.item(1000,24)
  w.bag={};w.bag_capacity=48;w.bank={3:item};w.bank_ready=True;w.bank_capacity=48
  b.state='open';b.mode='withdraw_patchouli';b.tick(10,p,True)
  self.assertEqual(p.emit.call_args.args[0][9:],struct.pack('>BHHBH',1,3,24,0,0))
  self.assertEqual(w.bank[3],item);self.assertEqual(w.bag,{})
  w.bank={};b.tick(11,p,True);self.assertEqual(b.withdrawals,0)
  w.bag={0:item};b.tick(12,p,True);self.assertEqual(b.withdrawals,1)
 def test_patchouli_cannot_be_deposited_and_can_be_retrieved_even_outside_catalog(self):
  w,s,m,p,b=banking.BankTests().make();w.bag={0:pets.item(1000,24)}
  self.assertEqual(b.candidates(p),[])
  w.bank={3:pets.item(1000,24)};m.catalog.items.pop(1000,None)
  self.assertEqual([(slot,i.identity,n) for slot,i,n in b.candidates(p,w.bank)],[(3,1000,24)])
 def test_common_materials_need_stack_but_actual_gear_can_sell_single(self):
  w,s,m,p=markets.MarketTests().make();m.broad_goods=m.focused_goods=True;m.catalog.enable_broad_catalog()
  w.bag={0:pets.item(1640,1),1:pets.item(3388,10)}
  offered={w.bag[slot].identity for _,_,_,slot in m.offers(p)}
  self.assertNotIn(1640,offered);self.assertIn(3388,offered)
 def test_randomized_activity_preserves_at_least_two_thirds_for_progression(self):
  w,_,_=pets.FairyTests().make()
  for name in ('one','two','three','four'):
   e=Economy(name,ROOT/'assets');e.phase(w,100)
   self.assertGreaterEqual(dict(e.stages)['progression'],1200)
   self.assertEqual(sum(n for _,n in e.stages),1800)


if __name__=='__main__':unittest.main()
