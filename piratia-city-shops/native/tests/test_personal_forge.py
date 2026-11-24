import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import test_native
import personal_forge as forge


class PersonalForgeInstallerTests(unittest.TestCase):
    def test_append_preserves_server_shop_hook_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            resource, _ = test_native.fixture(Path(directory))
            sdk = resource / forge.SDK
            sdk.write_bytes(sdk.read_bytes().replace(
                forge.city.ANCHOR, test_native.native.OPEN_HOOK + forge.city.ANCHOR))
            (resource / "script/calculate/forge.lua").write_text("\n".join(
                f"function {name}() end" for name in
                ("SetJinglian_Lv", "GetStone_TypeID", "Get_StoneLv", "TansferNum", "check_item_final_data")))
            (resource / "script/calculate/functions.lua").write_text(
                "function GetNum_Part1() end\nfunction SetNum_Part1() end")
            paths = (forge.SCRIPT, forge.SDK, forge.TEXT, forge.BINARY, Path("ItemInfo.txt"), Path("ItemInfo.bin"))
            hashes = {path.as_posix(): hashlib.sha256((resource / path).read_bytes()).hexdigest() for path in paths}
            (resource / forge.MARKER).write_text(json.dumps({"installed_sha256": hashes}))
            before, after, identity = forge.plan(resource)
            receipt = json.loads(after[forge.MARKER])["installed_sha256"]
            for path in paths[:4]:
                self.assertEqual(receipt[path.as_posix()], hashlib.sha256(after[path]).hexdigest())
            self.assertTrue(after[forge.BINARY].startswith(before[forge.BINARY]))
            self.assertIn(test_native.native.OPEN_HOOK + forge.city.ANCHOR, after[forge.SDK])
            self.assertNotIn(b"GetChaDefaultName", after[forge.SCRIPT])
            rows, _ = forge.city.validate_npcs(after[forge.TEXT], after[forge.BINARY])
            self.assertEqual(rows[identity][5], b"225750,277050")
            for path, content in after.items():
                (resource / path).write_bytes(content)
            original, repeated, repeated_id = forge.plan(resource)
            self.assertEqual(original, repeated)
            self.assertEqual(identity, repeated_id)

            # Simulate an older installed menu and a compiled table whose
            # bytes changed without changing the NPC definitions.
            script = after[forge.SCRIPT].replace(
                forge.END, b"-- Older menu\n" + forge.END)
            (resource / forge.SCRIPT).write_bytes(script)
            receipt[forge.SCRIPT.as_posix()] = hashlib.sha256(script).hexdigest()
            (resource / forge.MARKER).write_text(json.dumps({"installed_sha256": receipt}))
            binary = bytearray(after[forge.BINARY])
            binary[-1] ^= 1
            (resource / forge.BINARY).write_bytes(binary)
            original, updated, updated_id = forge.plan(resource)
            self.assertEqual(updated_id, identity)
            self.assertEqual({path for path in original if updated[path] != original[path]},
                             {forge.SCRIPT, forge.MARKER})
            self.assertEqual(updated[forge.BINARY], binary)
            self.assertEqual(json.loads(updated[forge.MARKER])["installed_sha256"],
                             json.loads(after[forge.MARKER])["installed_sha256"])
            # A real difference between the compiled and text coordinates
            # still fails structural validation.
            binary[-428 + 244] ^= 1
            (resource / forge.BINARY).write_bytes(binary)
            with self.assertRaisesRegex(ValueError, "Не совпадает структура НПС"):
                forge.plan(resource)


class PersonalForgeLuaTests(unittest.TestCase):
    def test_public_dialog_bulk_payment_rollback_rank_limit_and_three_sockets(self):
        private = (forge.ROOT / "personal_forge.lua").read_text(encoding="utf-8")
        test_native.NativeLuaTests().runlua(private + """
ITEMATTR_VAL_FUSIONID=1
ITEMATTR_VAL_LEVEL=2
ITEMATTR_MAXURE=3
ITEMATTR_URE=4
function IsPlayer(role) return 1 end
function GetCharID(role) return role.id end
function GetChaPos(role) return 225750,277050 end
function GetChaMapName(role) return "garner" end
function GetChaItem(role,bag,slot) return role.items[slot] end
function GetItemID(item) return item.id end
function GetItemType(item) return item.kind end
function GetItemName(id) return tostring(id) end
function GetItemAttr(item,key) return item.attrs[key] or 0 end
function Get_StoneLv(item) return item.rank end
function GetStone_TypeID(item) return item.stone or -1 end
function TansferNum(value) return value % 4294967296 end
local ids={10000000,10000,10}
local ranks={1000000,1000,1}
function GetNum_Part1(value) return math.floor(value/1000000000) end
function GetNum_Part2(value) return math.floor(value/ids[1])%100 end
function GetNum_Part4(value) return math.floor(value/ids[2])%100 end
function GetNum_Part6(value) return math.floor(value/ids[3])%100 end
function GetNum_Part3(value) return math.floor(value/ranks[1])%10 end
function GetNum_Part5(value) return math.floor(value/ranks[2])%10 end
function GetNum_Part7(value) return math.floor(value/ranks[3])%10 end
function SetJinglian_Lv(stone,rank,value)
    for i=1,3 do if math.floor(value/ids[i])%100==stone.stone then return value+ranks[i] end end
    for i=1,3 do if math.floor(value/ids[i])%100==0 then return value+stone.stone*ids[i]+ranks[i] end end
    return value
end
function check_item_final_data(item) item.refreshed=true end
function SetChaKitbagChange(role, flag) end
function CheckBagItem(role,id)
    local count=0
    for _,item in pairs(role.items) do if item.id==id then count=count+1 end end
    return count
end
function RemoveChaItem(role,id,count,bag,slot)
    if role.fail or role.items[slot].id~=id then return 0 end
    role.items[slot]=nil
    return 1
end
function DelBagItem(role,id,count)
    for slot=1,47 do
        if role.items[slot] and role.items[slot].id==id and count>0 then
            role.items[slot]=nil; count=count-1
        end
    end
    return count==0 and 1 or 0
end
function SendMissionPage(role,npc,page,message,options,count,missions,mission_count)
    assert(npc==44 and mission_count==0 and count==#options)
    role.dialog={page=page,message=message,options=options}
end
local pages = {}
function Talk(page, message) pages[page]={message=message} end
function Text(page, label, handler, parameter)
    table.insert(pages[page], {label=label,handler=handler,parameter=parameter})
end
function JumpPage() end
function CloseTalk() end
function CheckFusionItem(a,b) return 1 end
function FusionItem(a,b) a.attrs[7]=b.attrs[7]; return 1 end
local function stone(type_id,rank) return {id=680+type_id,kind=49,rank=rank,stone=type_id,forge=0,attrs={}} end
local app={id=5100,kind=1,forge=0,attrs={}}
local base={id=123,kind=1,forge=0,attrs={[7]=89}}
local c={id=1004,items={[0]=app,[1]=base}}
local stranger={id=1005,items={}}
local function action(role,_,command) return OwnerPersonalForgeAction(role,44,command) end
OwnForgePrivate()
assert(#pages[1]==5 and #pages[2]==2 and #pages[3]==1)
local function click(page,index)
    local option=pages[page][index]
    return option.handler(c,44,option.parameter)
end
c.items[1]=nil
assert(click(1,1)==0 and c.dialog.page==3)
assert(c.dialog.message:find("ячейки рюкзака",1,true))
c.items[1]=base
assert(click(1,1)==1 and app.attrs[2]==nil and c.dialog.page==2)
assert(c.dialog.options[1]==pages[2][1].label)
assert(action(stranger,nil,4)==0 and stranger.dialog.page==3)
assert(action(stranger,nil,5)==0 and stranger.dialog.message:find("128",1,true))
assert(click(2,1)==1 and app.attrs[2]==15 and app.attrs[1]==123 and app.attrs[7]==89)
assert(c.dialog.page==3 and c.dialog.message:find("Готово",1,true))
assert(c.items[1]==nil and action(c,nil,4)==0)
c.items[1]=stone(1,1)
assert(action(c,nil,2)==1)
c.fail=true
assert(action(c,nil,4)==0 and app.forge==0 and c.items[1])
c.fail=false
for rank=1,3 do
    c.items[1]=stone(1,1)
    if rank==3 then c.items[2]=stone(1,1) end
    assert(action(c,nil,2)==1 and action(c,nil,4)==1)
    assert(GetNum_Part3(TansferNum(app.forge))==rank and c.items[1]==nil)
end
assert(c.items[2]==nil)
for kind=2,3 do
    c.items[1]=stone(kind,1)
    assert(action(c,nil,2)==1 and action(c,nil,4)==1)
end
assert(GetNum_Part1(TansferNum(app.forge))==3)
assert(GetNum_Part3(TansferNum(app.forge))==3)
assert(GetNum_Part5(TansferNum(app.forge))==1)
assert(GetNum_Part7(TansferNum(app.forge))==1)
c.items[1]=stone(2,1)
assert(action(c,nil,2)==1 and c.dialog.message:find("Гнездо 2",1,true))
assert(action(c,nil,4)==1)
assert(GetNum_Part3(TansferNum(app.forge))==3)
assert(GetNum_Part5(TansferNum(app.forge))==2)
assert(GetNum_Part7(TansferNum(app.forge))==1)
c.items[1]=stone(4,1)
assert(action(c,nil,2)==0 and c.items[1])
c.items[1]=stone(1,3)
assert(action(c,nil,2)==1)
c.items[1]=stone(1,2)
assert(action(c,nil,4)==0 and c.items[1])
app.forge=GetNum_Part1(TansferNum(app.forge))*1000000000+18000000
c.items[1]=stone(1,8)
assert(action(c,nil,2)==1 and action(c,nil,4)==1)
assert(GetNum_Part3(TansferNum(app.forge))==9 and c.items[1]==nil)
c.items[1]=stone(1,9)
assert(action(c,nil,2)==0 and c.items[1])
GetChaPos=function() error("simulated native error") end
assert(click(1,2)==0 and c.dialog.page==3)
assert(c.dialog.message:find("журнал кузницы",1,true))

GetChaPos=function() return 225750,277050 end
GetKbCap=function() return 48 end
ForgeGroundStacks={[6400]=860}
StoneTpye_ID_Num=1
StoneTpye_ID={860}
local function put(value, divisor, digit, base)
    return value+(digit-math.floor(value/divisor)%base)*divisor
end
function SetNum_Part1(v,n) return put(v,1000000000,n,10) end
function SetNum_Part2(v,n) return put(v,10000000,n,100) end
function SetNum_Part3(v,n) return put(v,1000000,n,10) end
function CheckBagItem(role,id)
    local count=0
    for _,item in pairs(role.items) do
        if item.id==id then count=count+(item.count or 1) end
    end
    return count
end
function DelBagItem(role,id,count)
    for slot=2,3 do
        local item=role.items[slot]
        if item and item.id==id then
            local take=math.min(item.count,count)
            item.count=item.count-take;count=count-take
            if item.count==0 then role.items[slot]=nil end
        end
    end
    return count==0 and 1 or 0
end
app.forge=1018000000 -- one socket, type 1, rank 8
c.items[2]={id=6400,kind=31,forge=0,attrs={},count=99}
c.items[3]={id=6400,kind=31,forge=0,attrs={},count=40}
c.items[5]={id=6400,kind=31,forge=0,attrs={},count=1}
assert(action(c,nil,2)==0 and c.dialog.page==3)
c.items[5]=nil
assert(action(c,nil,2)==1 and c.dialog.message:find("128",1,true))
assert(action(c,nil,4)==1)
assert(c.items[2]==nil and c.items[3].count==11)
assert(GetNum_Part3(TansferNum(app.forge))==9)
""")
