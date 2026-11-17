"""Success probability only; native eligibility/payment/ingredients still decide legality."""
import unittest
import sys
import tempfile
from pathlib import Path
from forge_success import patch
import test_native as base

# Owned tiny source fixture, never the private server forge.lua.
FORGE=b'''-- unrelated byte-for-byte content
function can_forge_item_main() return allowed end
function begin_forge_item()
 if not can_forge_item_main() then return 0 end
 paid=paid+100;materials=materials-2
 local Check_A = 0.01
 local CheckFaild = Percentage_Random ( Check_A )
 return CheckFaild
end
function Check_CG_HechengBS(level,kind,skill)
 local b=0;local a=0.01
 if kind==49 then
  b = Percentage_Random ( a )
 elseif kind==50 then
  b = Percentage_Random ( a )
 else return 0 end
 return b
end
function Check_CG_damo(item,skill)
 local a=0.01
 local b = Percentage_Random ( a )
 return b
end
function Check_CG_beuplv(level)
 local ran = math.random ( 1, 100 )
 if level<=20 then return ran<=10 and 1 or 0 end
 return 0
end
function unchanged_tail() return 987 end
'''

class Success58Tests(unittest.TestCase):
 runlua=base.NativeLuaTests.runlua
 def test_valid_native_operation_succeeds_and_pays_invalid_one_does_nothing(self):
  out,report=patch(FORGE)
  self.runlua('function Percentage_Random(n) return 0 end\nallowed=false;paid=0;materials=4\n'+out.decode()+'''
assert(begin_forge_item()==0 and paid==0 and materials==4)
allowed=true
assert(begin_forge_item()==1 and paid==100 and materials==2)
assert(Check_CG_HechengBS(9,49,1)==1 and Check_CG_HechengBS(9,50,1)==1)
assert(Check_CG_HechengBS(9,31,1)==0)
assert(Check_CG_damo({},1)==1 and Check_CG_beuplv(19)==1 and Check_CG_beuplv(21)==0)
assert(unchanged_tail()==987)
''')
  self.assertEqual(len(report),4)
 def test_repeat_crlf_and_unrelated_content_are_preserved(self):
  raw=FORGE.replace(b'\n',b'\r\n');out,_=patch(raw)
  self.assertEqual(patch(out)[0],out)
  self.assertEqual(out.count(b'\r\n'),raw.count(b'\r\n'))
  self.assertIn(b'function can_forge_item_main() return allowed end\r\n',out)
 def test_edited_marker_or_unknown_roll_is_refused(self):
  out,_=patch(FORGE)
  with self.assertRaises(ValueError):patch(out.replace(b'local CheckFaild = 1',b'local CheckFaild = 0'))
  with self.assertRaises(ValueError):patch(FORGE.replace(b'Check_A )',b'Other_Rate )'))

 def test_restoring_bot_knowledge_refuses_changed_native_forge(self):
  project=Path(__file__).resolve().parents[3]
  source=project/'piratia-bots/src'
  if not source.exists():source=project/'src'
  sys.path.insert(0,str(source))
  from restore_shop_knowledge import restore
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);server,client=base.fixture(root);assets=root/'assets';assets.mkdir();(assets/'world-npcs.json').write_text('{}')
   base.isolated_install(server,client,True,assets)
   self.assertEqual(restore(server,assets)['catalog_revision'],base.CAT['catalog_revision'])
   target=server/'script/calculate/forge.lua';target.write_bytes(target.read_bytes()+b'\n-- changed externally\n')
   before=(assets/'owner-city-shops.json').read_bytes()
   with self.assertRaisesRegex(ValueError,'ковка'):restore(server,assets)
   self.assertEqual((assets/'owner-city-shops.json').read_bytes(),before)

if __name__=='__main__':unittest.main()
