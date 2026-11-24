import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

import test_native
import personal_forge as forge
import spawn_density
import world_expansion as expansion
import trophy_drops


class ExpansionTests(unittest.TestCase):
    def test_full_install_preserves_original_gem_records_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            server, client = test_native.fixture(root)
            test_native.isolated_install(server, client, True)
            client = test_native.native.locate_client(client)
            text, binary = server/"ItemInfo.txt", server/"ItemInfo.bin"
            all_items = {**{i: 31 for i in expansion.SUPPLIES},
                         **{i: 1 for i in expansion.WEAPONS}, 1591: 41, 684: 31}
            known = expansion.item_text(text.read_bytes(), all_items)
            for identity, kind in all_items.items():
                if identity in known:
                    continue
                fields = [b"0"]*26
                fields[0:2] = str(identity).encode(), b"Fixture"
                fields[10], fields[20] = str(kind).encode(), b"99"
                with text.open("ab") as f:
                    f.write(b"\t".join(fields)+b"\n")
                row = bytearray(868)
                for offset in (4,108):
                    struct.pack_into("<I", row, offset, identity)
                struct.pack_into("<h", row, 308, kind)
                struct.pack_into("<i", row, 352, 99)
                for table in (binary, client):
                    with table.open("ab") as f:
                        f.write(row)
            duplicate_lines = b"".join(
                b"3037\t" + label + b"\t0"*24 + b"\r\n"
                for label in (b"Legacy entry", b"Alternate legacy entry")
            )
            with text.open("ab") as f:
                f.write(duplicate_lines)
            original = expansion.table_bin(binary.read_bytes())
            receipt_path = server/forge.MARKER
            receipt = json.loads(receipt_path.read_text())
            for path in (text, binary):
                receipt["installed_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            receipt_path.write_text(json.dumps(receipt))
            script = server/"script/calculate"
            with (script/"forge.lua").open("ab") as f:
                for name in ("SetJinglian_Lv","GetStone_TypeID","Get_StoneLv","Set_StoneLv","TansferNum","check_item_final_data"):
                    f.write(f"\nfunction {name}() end".encode())
            (script/"functions.lua").write_bytes(b"function GetNum_Part1() end\nfunction SetNum_Part1() end")
            changes = expansion.plan(server, client)
            self.assertIn(client, changes)
            self.assertIn(duplicate_lines, changes[text])
            for path, content in changes.items():
                path.write_bytes(content)
            self.assertEqual(expansion.plan(server, client), {})
            rows = expansion.table_bin(binary.read_bytes())
            for alias, identity in expansion.GEMS.items():
                self.assertEqual(rows[identity], original[identity])
                self.assertNotIn(alias, rows)
            self.assertEqual(struct.unpack_from("<i",rows[684],320)[0],200_000)
            for i, money in ((5622,5_000),(5623,6_000)):
                self.assertEqual(struct.unpack_from("<i",rows[i],320)[0],2*money)
            self.assertTrue(json.loads(receipt_path.read_text())["world_expansion"])

    def test_duplicate_used_as_a_template_is_rejected(self):
        row = b"860\tGem" + b"\t0"*24 + b"\n"
        with self.assertRaisesRegex(ValueError, r"ItemInfo.txt: 860"):
            expansion.make_item_tables(row * 2, b"", b"", False)

    def test_density_rounds_per_spawn_and_ignores_non_mobs(self):
        def row(index, count):
            return f"{index}\t0,0\t100,100\t-1\t2,3\t{count},1\t100,100\t10,10\n".encode()
        out, count = spawn_density.table(row(1,3)+row(2,1), {2})
        self.assertEqual(count,3)
        self.assertIn(b"\t2,3\t5,1\t",out)
        self.assertIn(b"\t2,3\t2,1\t",out)
        self.assertEqual(spawn_density.table(out,{2}),(out,0))
        raw = b"CreateCha(2,100,100,0,10)\nCreateCha(2,100,100,0,10)\n"
        self.assertEqual(spawn_density.startup(raw,{2})[1],2)

    def test_trophy_updates_only_ordinary_spawn_slots(self):
        fields=[b"0"]*62
        fields[0],fields[4],fields[46],fields[47],fields[51],fields[60]=(b"540",b"5",b"15,684",b"400,800",b"316",b"51")
        raw=b"\t".join(fields)+b"\r\n"
        row=bytearray(b"\xff"*968)
        struct.pack_into("<I",row,4,540)
        struct.pack_into("<4i",row,428,15,400,684,800)
        compiled=struct.pack("<I",968)+row
        updated,binary,count,fallback=trophy_drops.patch(raw,compiled,{15:1},expansion.TROPHIES)
        self.assertEqual((count,fallback),(1,0))
        self.assertEqual(updated.split(b"\t")[46:48],[b"15,684,5622",b"400,800,100"])
        self.assertEqual(updated.split(b"\t")[51],b"316")
        self.assertEqual(binary[:448],compiled[:448])
        self.assertEqual(struct.unpack_from("<ii",binary,448),(5622,100))
        self.assertEqual(binary[456:],compiled[456:])
        self.assertEqual(trophy_drops.patch(updated,binary,{15:1},expansion.TROPHIES)[:2],(updated,binary))

    def test_density_updates_bin_and_does_not_reapply_v1_increase(self):
        raw=(b"1\t0,0\t100,100\t-1\t2\t4\t100\t12\n"
             b"2\t0,0\t100,100\t-1\t2\t2\t100\t30\n"
             b"// WORLD_EXPANSION_DENSITY_V1\n")
        patched,count,records=spawn_density.table_plan(raw,{2})
        self.assertEqual(count,1)
        self.assertIn(b"\t2\t5\t100\t12",patched)
        self.assertIn(b"\t2\t2\t100\t30",patched)
        rows=[]
        for identity,base,delay in ((1,3,12),(2,1,30)):
            row=bytearray(b"\xff"*160)
            struct.pack_into("<I",row,4,identity)
            struct.pack_into("<4i",row,104,2,base,100,delay)
            rows.append(row)
        binary=struct.pack("<I",160)+b"".join(rows)
        output=spawn_density.update_binary(binary,records)
        self.assertEqual(struct.unpack_from("<i",output,112),(5,))
        self.assertEqual(struct.unpack_from("<i",output,272),(2,))
        self.assertEqual(spawn_density.table(patched,{2}),(patched,0))
        spawn=b"CreateCha(2,100,100,0,10)\n"
        old=spawn+spawn+spawn+b"-- WORLD_EXPANSION_DENSITY_V1\n"
        new,count=spawn_density.startup(old,{2})
        self.assertEqual(count,1)
        self.assertEqual(new.count(spawn),4)

    def test_spawn_recovery_only_restores_marked_tables_and_scripts(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            server,_=test_native.fixture(root)
            (server/"CharacterInfo.txt").write_bytes(b"2\tMob\t0\t0\t5\n")
            mapdir=server/"garner"
            density=mapdir/"garnerChaSpn.txt"
            base=b"1\t0,0\t100,100\t-1\t2\t3\t100\t12\r\n"
            expanded,count,_=spawn_density.table_plan(base,{2})
            self.assertEqual(count,2)
            density.write_bytes(expanded)
            record=bytearray(b"\xff"*160)
            struct.pack_into("<I",record,4,1)
            struct.pack_into("<4i",record,104,2,5,100,12)
            compiled=density.with_suffix(".bin")
            compiled.write_bytes(struct.pack("<I",160)+record)
            scripts=server/"script/monster"
            scripts.mkdir()
            spawn=b"CreateCha(2,100,100,0,10)\n"
            legacy=scripts/"unused.lua"
            legacy.write_bytes(spawn*3+b"-- WORLD_EXPANSION_DENSITY_V1\n")
            current=scripts/"spawn.lua"
            current.write_bytes(spawn_density.startup(spawn,{2})[0])
            untouched=scripts/"custom.lua"
            untouched.write_bytes(spawn*2)
            changed=scripts/"mixed.lua"
            changed.write_bytes(spawn+b"do_other_work()\n-- WORLD_EXPANSION_DENSITY_V2\n")
            changes,removed,skipped=spawn_density.restore_plan(server)
            self.assertEqual(removed,4)
            self.assertEqual(changes[density],base)
            self.assertEqual(struct.unpack_from("<i",changes[compiled],112),(3,))
            self.assertEqual(changes[legacy],spawn*2)
            self.assertEqual(changes[current],spawn)
            self.assertNotIn(untouched,changes)
            self.assertNotIn(changed,changes)
            self.assertIn(changed.name,skipped[0])
            for path,new in changes.items():
                path.write_bytes(new)
            self.assertEqual(spawn_density.restore_plan(server),({},0,skipped))

    def test_native_store_and_drop_hooks(self):
        lua = expansion.world_script().decode()
        test_native.NativeLuaTests().runlua("""
table.getn=function(t) return #t end
local native_shop=OwnerNativeShops['equipment']
local pages_before=#native_shop.pages
unpack=table.unpack
local expected
local actual
function SetItemFall(count,...)
    actual={...}
    assert(count==#actual)
end
function Owner56OriginalDropCheck()
    if not expected then assert(Owner56FallFilter==nil); return end
    assert(Owner56FallFilter[1] and Owner56FallFilter[3] and Owner56FallFilter[7])
    assert(not Owner56FallFilter[2] and not Owner56FallFilter[4] and not Owner56FallFilter[5])
    assert(not Owner56FallFilter[6] and not Owner56FallFilter[8] and not Owner56FallFilter[9])
    SetItemFall(2,4,10)
end
function GetResPath(name) return name end
local function row(id,fields,count)
    fields[1]=id
    for i=1,count do if not fields[i] then fields[i]=0 end end
    return table.concat(fields,string.char(9))
end
local fixture={
    ["ItemInfo.txt"]={
        row(1218,{[11]=41},11), row(15,{[11]=1},11), row(1573,{[11]=41},11),
        row(4915,{[11]=41},11), row(684,{[11]=31},11), row(868,{[11]=49},11),
        row(860,{[11]=49},11), row(5622,{[11]=41},11)
    },
    ["CharacterInfo.txt"]={row(42,{
        [5]=5,[47]="1218,0,15,1573,4915,684,868,860,555,9876,5622",
        [48]="101,0,102,103,104,105,106,107,108,109,100",[61]=50},61)}
}
io.open=function(path)
    return {lines=function()
        local i=0
        return function() i=i+1; return fixture[path][i] end
    end,close=function() end}
end
""" + lua + """
local more=OwnerNativeShops['forge-supply'].pages
assert(more[1][3].item[1]==4019 and more[3][3].item[1]==1067 and more[1][3].itemtype==2)
assert(more[1][3].count==36 and more[2][3].count==2 and more[5][3].count==23)
assert(OwnerNativeShops['equipment'].pages[pages_before+1][1].count==14)
local drops={}
ATTR_HP=1; ATTR_LV=2
function IsPlayer(e) return e.player end
function GetChaAttr(e, attr) if attr==ATTR_HP then return 0 else return e.level end end
function GetChaTypeID(e) return 42 end
function Owner57GroundDrop(e,id,stack) drops[id]=stack end
Owner56MonsterModels={[42]=true}
expected=true
Check_Baoliao({player=1},{player=0,level=50},101,102,103,104,105,106,107,108,109,100)
assert(#actual==2 and actual[1]==4 and actual[2]==10)
expected=false
Check_Baoliao({player=1},{player=0,level=50},101,102)
Check_Baoliao({player=1},{player=1,level=50},101,102,103,104,105,106,107,108,109)
assert(Owner56FallFilter==nil)
math.random=function(a,b) return 1 end
Owner56GroundGem({player=0,level=50},{player=1})
assert(drops[1000]==99 and drops[860]==1 and not drops[5609] and not drops[5622])
GetChaTypeID=function() return 43 end
Owner56MonsterModels[43]=true
Owner56GroundGem({player=0,level=60},{player=1})
assert(drops[5623]==99)
""")
