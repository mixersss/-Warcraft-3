"""Possession uses actual paid stamina and retains native end/state/XP formulas."""
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import test_native as base
from loot_protection import plan

SETUP='''
ITEMATTR_VAL_STR=1;ITEMATTR_VAL_CON=2;ITEMATTR_VAL_AGI=3;ITEMATTR_VAL_DEX=4;ITEMATTR_VAL_STA=5;ITEMATTR_URE=6
function NewFairy(ure,gen)
 return {kind=59,attrs={[1]=6,[2]=0,[3]=0,[4]=0,[5]=0,[6]=ure},generation=gen or 1}
end
function GetChaItem(c,kind,slot) assert(kind==2 and slot==1);return c.fairy or 0 end
function GetItemType(i) return i.kind end
function GetItemForgeParam(i,n) return i.generation*1000000000 end
function GetNum_Part1(n) return math.floor(n/1000000000) end
function GetItemAttr(i,n) return i.attrs[n] end
function SetItemAttr(i,n,v) i.attrs[n]=v end
function SkillUnable(c) c.rejected=true end
function SystemNotice(c,s) c.message=s end
'''

class PossessionTests(unittest.TestCase):
 runlua=base.NativeLuaTests.runlua
 def test_buba_level6_fairy_above_half_satiety_can_pay_each_real_rank(self):
  self.runlua(SETUP+'''
for rank=1,3 do
 local c={fairy=NewFairy(3000)}
 Skill_JLFT_BEGIN(c,rank)
 assert(not c.rejected and c.fairy.attrs[6]==3000-math.ceil(1800/rank))
end
''')
 def test_insufficient_cost_rejects_without_changing_fairy(self):
  self.runlua(SETUP+'''
local c={fairy=NewFairy(599)};Skill_JLFT_BEGIN(c,3)
assert(c.rejected and c.fairy.attrs[6]==599 and string.find(c.message,"12 stamina",1,true))
local exact={fairy=NewFairy(600)};Skill_JLFT_BEGIN(exact,3)
assert(not exact.rejected and exact.fairy.attrs[6]==0)
''')
 def test_empty_slot_and_first_generation_still_reject(self):
  self.runlua(SETUP+'''
local c={};Skill_JLFT_BEGIN(c,3);assert(c.rejected)
c={fairy=NewFairy(5000,0)};Skill_JLFT_BEGIN(c,3)
assert(c.rejected and c.fairy.attrs[6]==5000)
c={fairy=NewFairy(5000)};c.fairy.kind=31;Skill_JLFT_BEGIN(c,3)
assert(c.rejected and c.fairy.attrs[6]==5000)
''')

 def test_high_level_fairy_cannot_spend_into_negative_stamina(self):
  self.runlua(SETUP+'''
local c={fairy=NewFairy(5000)};c.fairy.attrs[1]=60
Skill_JLFT_BEGIN(c,3);assert(c.rejected and c.fairy.attrs[6]==5000)
''')

class Installation57Tests(unittest.TestCase):
 def test_upgrade56_preserves_every_actor_and_personal_sdk_hook(self):
  n=base.native
  with tempfile.TemporaryDirectory() as d:
   server,client=base.fixture(Path(d))
   with patch.object(n,'CATALOG',n.ROOT/'catalog-alpha56.json'):base.isolated_install(server,client,True)
   actors=(server/'garner/garnerNPC.bin').read_bytes()
   sdk=server/'script/MisSdk/NpcSdk.lua';sdk.write_bytes(sdk.read_bytes()+b'\n-- owner personal hook\n')
   result=base.isolated_install(server,client,True)
   self.assertEqual(result['upgraded_from'],'Alpha56')
   self.assertEqual((server/'garner/garnerNPC.bin').read_bytes(),actors)
   self.assertTrue(sdk.read_bytes().endswith(b'-- owner personal hook\n'))
   self.assertTrue(base.isolated_install(server,client,True)['already_installed'])
 def test_protection_uses_one_second_never_zero_and_preserves_other_config_bytes(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a=root/'GameServer.cfg';b=root/'GameServer01.cfg'
   a.write_bytes(b'[GAME]\r\nitem_prot_time = 30000 // seconds\r\nmap = garner\r\n')
   b.write_bytes(b'map = magicsea\n')
   changes,report=plan(root)
   self.assertEqual(changes[a],a.read_bytes().replace(b'30000',b'1'))
   self.assertIn(b'item_prot_time = 1\n',changes[b]);self.assertEqual(report['seconds'],1)
   for p,raw in changes.items():p.write_bytes(raw)
   self.assertEqual(plan(root)[0],{})

if __name__=='__main__':unittest.main()
