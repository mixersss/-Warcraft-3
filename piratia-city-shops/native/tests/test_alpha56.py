"""Public profession services, real ground-overflow adapter and exact gem rolls."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import test_native as base

n=base.native
GROUND=(n.ROOT/'ground_gems.lua').read_text()

ROLE_MOCKS='''
unpack=table.unpack
ATTR_HP=1;ATTR_JOB=4;ATTR_LV=0;MONSTER_BAOLIAO=1
function IsPlayer(c) return c.player and 1 or 0 end
function GetChaTypeID(c) return c.body or 1 end
function GetChaAttr(c,a) return c.attrs[a] or 0 end
function GetSkillLv(c,id) return c.skills[id] or 0 end
function AddChaSkill(c,id,lv,set,points,skip)
 assert(set==1 and points==0);c.skills[id]=lv;c.learns=(c.learns or 0)+1
end
function SetProfession(c,job) c.attrs[ATTR_JOB]=job end
function GetKbCap(c) return c.capacity end
function CheckBagItem(c,id)
 local count=0;for _,item in pairs(c.slots) do if item.id==id then count=count+item.count end end;return count
end
function GetChaItem(c,kind,slot) return c.slots[slot] end
function LG(...) end
function NewRole(body,job,level)
 return {player=true,body=body,attrs={[0]=level,[4]=job,[1]=100,[7]=0},skills={},slots={},capacity=24,gold=12345}
end
'''

DROP_MOCKS=ROLE_MOCKS+'''
Ground={};ExpCalls=0
function GetExp_New(dead,attacker) ExpCalls=ExpCalls+1 end
function Creat_Item(item,kind,level,event) return 1,30,10,0,0,0,0,0,0,0,0,0,0,0,0 end
ITEMATTR_MAXENERGY=30
function Set_StoneLv(item,level) item.level=level end
function TakeItem(c,npc,id,count)
 for slot=0,c.capacity-1 do if count>0 and c.slots[slot] and c.slots[slot].id==id then c.slots[slot]=nil;count=count-1 end end
 return count==0 and 1 or 0
end
-- Faithful to native GiveItem/KbPushItem: split unstackable copies into free
-- slots; overflow becomes ItemSpawn at the receiver, not at the player.
function GiveItem(c,npc,id,count,event)
 assert(not c.player and c.attrs[ATTR_HP]==0 and event==1)
 local item={id=id,count=1};Creat_Item(item,49,0,event)
 for slot=0,c.capacity-1 do
  if count>0 and c.slots[slot]==nil then c.slots[slot]={id=id,count=1,level=item.level};count=count-1 end
 end
 if count>0 then table.insert(Ground,{id=id,count=count,source=c,level=item.level}) end
 return 1
end
function SetItemFall(count,...)
 Falls={count=count,values={...}}
end
function Check_Baoliao(attacker,dead,...) SetItemFall(3,1,2,3) end
'''


class ProgressionLuaTests(unittest.TestCase):
    runlua=base.NativeLuaTests.runlua

    def test_professions_enforce_level_body_and_current_job_without_stat_reset(self):
        self.runlua(ROLE_MOCKS+'''
local c=NewRole(2,0,8)
assert(OwnerProgressAction(c,{},"owner-profession",1)==0 and c.attrs[4]==0)
c.attrs[0]=9
assert(OwnerProgressAction(c,{},"owner-profession",1)==1 and c.attrs[4]==1)
assert(OwnerProgressAction(c,{},"owner-profession",9)==0)
c.attrs[0]=40
assert(OwnerProgressAction(c,{},"owner-profession",8)==1 and c.attrs[4]==8)
assert(c.gold==12345 and c.attrs[7]==0)
assert(OwnerProgressAction(c,{},"owner-profession",1)==0)
''')

    def test_stall_and_basic_spell_are_idempotent_and_preserve_earned_skills(self):
        self.runlua(ROLE_MOCKS+'''
local c=NewRole(4,5,20);c.skills[97]=3
assert(OwnerProgressAction(c,{},"owner-stall",0)==1)
assert(c.skills[241]==3 and c.attrs[7]==0)
OwnerProgressAction(c,{},"owner-stall",0);assert(c.learns==1)
OwnerProgressAction(c,{},"owner-combat",0);assert(c.skills[99]==1 and c.skills[97]==3)
OwnerProgressAction(c,{},"owner-combat",0);assert(c.learns==2)
''')

    def test_all_six_bag_expanders_are_given_once_without_gold_charge(self):
        self.runlua(ROLE_MOCKS+'''
function GiveItem(c,npc,id,count,event)
 for slot=0,c.capacity-1 do if c.slots[slot]==nil then c.slots[slot]={id=id,count=count};return 1 end end
 return 0
end
local c=NewRole(1,1,10)
OwnerProgressAction(c,{},"owner-bags",0)
for id=3088,3093 do assert(CheckBagItem(c,id)==1) end
OwnerProgressAction(c,{},"owner-bags",0)
for id=3088,3093 do assert(CheckBagItem(c,id)==1) end
assert(c.gold==12345)
''')

    def test_all_eight_npc_menus_fit_classic_button_limit(self):
        self.runlua('''
for _,f in ipairs({OwnerClothes,OwnerFairies,OwnerForge,OwnerTickets,OwnerBoosts,OwnerEquipment,OwnerJewellery,OwnerProgress}) do
 InitPage();f();assert(Page[1].count<=12)
 if Page[2] then assert(Page[2].count<=12) end
end
''')


class GroundLuaTests(unittest.TestCase):
    runlua=base.NativeLuaTests.runlua

    def test_exact_three_percent_ignores_x10_and_spawns_only_one_allowed_ground_gem(self):
        self.runlua(DROP_MOCKS+GROUND+'''
local rolls=0;local choices=0
math.random=function(a,b)
 if b==100 then rolls=rolls+1;return (rolls-1)%100+1 end
 assert(b==8);choices=choices+1;return (choices-1)%8+1
end
MF_RAID=10
local attacker=NewRole(1,1,35);local dead={player=false,attrs={[1]=0},slots={},skills={},capacity=24}
local old={id=123,count=1};dead.slots[4]=old
for i=1,800 do GetExp_New(dead,attacker) end
assert(#Ground==24 and ExpCalls==800 and Owner56GemStats.rolls==24)
assert(dead.slots[4]==old and attacker.gold==12345 and next(attacker.slots)==nil)
local counts={}
for _,item in ipairs(Ground) do assert(item.count==1 and item.source==dead and item.level==1);counts[item.id]=(counts[item.id] or 0)+1 end
for _,id in ipairs(Owner56GemIDs) do assert(counts[id]==3 and CheckBagItem(dead,id)==0) end
MF_RAID=100
for i=1,800 do GetExp_New(dead,attacker) end
assert(#Ground==48 and ExpCalls==1600)
''')

    def test_zero_capacity_monster_still_gets_ground_drop_not_player_inventory(self):
        self.runlua(DROP_MOCKS+GROUND+'''
math.random=function(a,b) return 1 end
local a=NewRole(1,1,35);local d={player=false,attrs={[1]=0},slots={},capacity=0}
GetExp_New(d,a)
assert(#Ground==1 and Ground[1].source==d and Ground[1].count==1)
assert(next(a.slots)==nil and next(d.slots)==nil)
''')

    def test_no_gems_for_pvp_alive_targets_or_monster_killers(self):
        self.runlua(DROP_MOCKS+GROUND+'''
math.random=function(a,b) return 1 end
local a=NewRole(1,1,35);local d={player=false,attrs={[1]=10},slots={},capacity=0}
GetExp_New(d,a);GetExp_New(a,a);d.attrs[1]=0;GetExp_New(d,d)
assert(#Ground==0 and ExpCalls==3)
''')

    def test_normal_gem_slots_are_filtered_but_quest_pass_and_other_loot_survive(self):
        self.runlua(DROP_MOCKS+GROUND+'''
math.random=function(a,b) return b end
Owner56GemSlots[789]={[2]=true}
local a=NewRole(1,1,35);local d={player=false,body=789,attrs={[1]=0},slots={},capacity=0}
GetExp_New(d,a)
Check_Baoliao(a,d,100,200,300)
assert(Falls.count==2 and Falls.values[1]==1 and Falls.values[2]==3)
Check_Baoliao(a,d,100,200,300)
assert(Falls.count==3 and Falls.values[2]==2)
assert(#Ground==0)
''')


class Migration56Tests(unittest.TestCase):
    def test_upgrade55_adds_two_npcs_preserving_buba_hook_and_all_old_actors(self):
        with tempfile.TemporaryDirectory() as directory:
            server,client=base.fixture(Path(directory))
            with patch.object(n,'CATALOG',n.ROOT/'catalog-alpha55.json'):
                base.isolated_install(server,client,True)
            old=(server/'garner/garnerNPC.bin').read_bytes()
            sdk=server/'script/MisSdk/NpcSdk.lua';sdk.write_bytes(sdk.read_bytes()+b'\n-- preserve external buba hook\n')
            result=base.isolated_install(server,client,True)
            self.assertEqual(result['upgraded_from'],'Alpha55')
            self.assertEqual(len(base.legacy.binary_rows((server/'garner/garnerNPC.bin').read_bytes())),len(base.legacy.binary_rows(old))+2)
            self.assertTrue((server/'garner/garnerNPC.bin').read_bytes().startswith(old))
            self.assertTrue(sdk.read_bytes().endswith(b'-- preserve external buba hook\n'))
            self.assertEqual(result['positions_m'][-2:],[[2214,2713],[2211,2713]])
            self.assertTrue(base.isolated_install(server,client,True)['already_installed'])

    def test_only_allowed_corals_cost_one_and_chaos_parts_are_unsealed_stock(self):
        cat=n.catalog();goods=n.offers(cat)
        self.assertEqual({i for i,row in goods.items() if row['price']==1},{817,867,635})
        self.assertEqual({i:goods[i]['price'] for i in (1125,1126)},{1125:450000,1126:450000})
        self.assertEqual(cat['owner_progression']['gem_ids'],[860,861,862,863,864,865,866,1012])


if __name__=='__main__':unittest.main()
