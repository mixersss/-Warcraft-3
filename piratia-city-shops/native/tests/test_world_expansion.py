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


class ExpansionTests(unittest.TestCase):
    def test_full_install_preserves_original_gem_records_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            server, client = test_native.fixture(root)
            test_native.isolated_install(server, client, True)
            client = test_native.native.locate_client(client)
            text, binary = server/"ItemInfo.txt", server/"ItemInfo.bin"
            known = expansion.item_text(text.read_bytes())
            all_items = {**{i: 31 for i in expansion.SUPPLIES},
                         **{i: 1 for i in expansion.WEAPONS}, 1591: 41, 684: 31}
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
            original = expansion.table_bin(binary.read_bytes())
            receipt_path = server/forge.MARKER
            receipt = json.loads(receipt_path.read_text())
            for path in (text, binary):
                receipt["installed_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            receipt_path.write_text(json.dumps(receipt))
            script = server/"script/calculate"
            with (script/"forge.lua").open("ab") as f:
                for name in ("SetJinglian_Lv","GetStone_TypeID","Get_StoneLv","TansferNum","check_item_final_data"):
                    f.write(f"\nfunction {name}() end".encode())
            (script/"functions.lua").write_bytes(b"function GetNum_Part1() end\nfunction SetNum_Part1() end")
            changes = expansion.plan(server, client)
            self.assertIn(client, changes)
            for path, content in changes.items():
                path.write_bytes(content)
            self.assertEqual(expansion.plan(server, client), {})
            rows = expansion.table_bin(binary.read_bytes())
            for alias, identity in expansion.GEMS.items():
                self.assertEqual(rows[identity], original[identity])
                self.assertEqual(struct.unpack_from("<h",rows[alias],308)[0],31)
                self.assertEqual(struct.unpack_from("<i",rows[alias],352)[0],99)
            self.assertEqual(struct.unpack_from("<i",rows[684],320)[0],200_000)
            for i, money in ((6414,5_000),(6415,6_000)):
                self.assertEqual(struct.unpack_from("<i",rows[i],320)[0],2*money)
            self.assertTrue(json.loads(receipt_path.read_text())["world_expansion"])

    def test_density_rounds_per_model_and_ignores_non_mobs(self):
        def row(index, count):
            return f"{index}\t0,0\t100,100\t-1\t2,3\t{count},1\t100,100\t10,10\n".encode()
        out, count = spawn_density.table(row(1,3)+row(2,1), {2})
        self.assertEqual(count,2)
        self.assertIn(b"\t2,3\t4,1\t",out)
        self.assertIn(b"\t2,3\t2,1\t",out)
        self.assertEqual(spawn_density.table(out,{2}),(out,0))
        raw = b"CreateCha(2,100,100,0,10)\nCreateCha(2,100,100,0,10)\n"
        self.assertEqual(spawn_density.startup(raw,{2})[1],1)

    def test_native_store_and_drop_hooks(self):
        lua = (expansion.ROOT/"world_expansion.lua").read_text()
        test_native.NativeLuaTests().runlua("""
table.getn=function(t) return #t end
local native_shop=OwnerNativeShops['equipment']
local pages_before=#native_shop.pages
""" + lua + """
local more=OwnerNativeShops['forge-supply'].pages
assert(more[1][3].item[1]==1847 and more[2][3].item[1]==4602)
assert(OwnerNativeShops['equipment'].pages[pages_before+1][1].count==14)
local drops={}
ATTR_HP=1; ATTR_LV=2
function IsPlayer(e) return e.player end
function GetChaAttr(e, attr) if attr==ATTR_HP then return 0 else return e.level end end
function GetChaTypeID(e) return 42 end
function Owner57GroundDrop(e,id,stack) drops[id]=stack end
Owner56MonsterModels={[42]=true}
math.random=function(a,b) return 1 end
Owner56GroundGem({player=0,level=50},{player=1})
assert(drops[1000]==99 and drops[6400]==99 and drops[6414]==99)
Owner56GroundGem({player=0,level=60},{player=1})
assert(drops[6415]==99)
""")
