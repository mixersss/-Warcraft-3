import hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
import install_npc_hook as fix
import test_grant as model

ROOT=Path(__file__).resolve().parent
SAMPLE=b'-- owner SDK\r\nfunction MsgProc( character, npc, rpk, page, trade, missionlist, exchangeData )\r\n return OriginalDialogue(character,npc,rpk,page,trade,missionlist,exchangeData)\r\nend\r\n'

class HookTests(unittest.TestCase):
 def test_hook_is_inside_native_entry_and_original_bytes_can_be_recovered(self):
  out=fix.patch_sdk(SAMPLE)
  self.assertEqual(fix.patch_sdk(out),out)
  self.assertEqual(out.replace(fix.HOOK.replace(b'\n',b'\r\n'),b'').replace(b'\r\n'+fix.BOOT.replace(b'\n',b'\r\n'),b''),SAMPLE)
  self.assertLess(out.index(fix.BEGIN),out.index(b'return OriginalDialogue'))
 def test_install_backs_up_sdk_and_updates_only_known_shop_checksum(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);sdk=r/fix.SDK;sdk.parent.mkdir(parents=True);sdk.write_bytes(SAMPLE)
   npc=r/'script/MisScript/NpcScript01.lua';npc.parent.mkdir();npc.write_bytes(b'unchanged original NPCs')
   ledger=r/'owner-buba-swords-01.state';ledger.write_bytes(b'do not delete')
   marker=r/'owner-city-shops-v2.json';marker.write_text(json.dumps({'installed_sha256':{fix.SDK.as_posix():fix.digest(SAMPLE),'other':'keep'},'other_field':'keep'}))
   report=fix.install(r);self.assertEqual(ledger.read_bytes(),b'do not delete');self.assertEqual(npc.read_bytes(),b'unchanged original NPCs')
   data=json.loads(marker.read_text());self.assertEqual(data['installed_sha256'][fix.SDK.as_posix()],fix.digest(sdk.read_bytes()));self.assertEqual(data['installed_sha256']['other'],'keep')
   self.assertEqual(next(Path(report['backup']).glob('*NpcSdk.lua')).read_bytes(),SAMPLE)
   self.assertTrue(fix.install(r)['already_installed'])
 def test_edited_helper_or_sdk_refuse_before_writes(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);sdk=r/fix.SDK;sdk.parent.mkdir(parents=True);sdk.write_bytes(SAMPLE)
   npc=r/'script/MisScript/NpcScript01.lua';npc.parent.mkdir();npc.write_bytes(b'NPC')
   (r/'script/BubaSwords.lua').write_bytes(b'unknown owner changes')
   with self.assertRaises(ValueError):fix.install(r)
   self.assertEqual(sdk.read_bytes(),SAMPLE);self.assertFalse((r/'owner-buba-backups').exists())
 def test_compiled_entry_invokes_grant_without_global_replacement_or_name_lookup(self):
  sword=(ROOT/'BubaSwords.lua').read_text()
  before='''GetPlayerByName=nil
function Notice(s) end
old_calls=0
function OriginalDialogue(c,n,r,p,t,m,e) assert(r=='packet' and e=='exchange');old_calls=old_calls+1;return 123 end
function dofile(path)
'''+sword+'\nend\n'+fix.patch_sdk(SAMPLE).decode()
  model.GrantTests().run_lua(before,'''assert(MsgProc(role,{},'packet','page','trade','mission','exchange')==123)
assert(made==4 and removed==2 and old_calls==1)
assert(MsgProc({name='other'},{},'packet','page','trade','mission','exchange')==123)
assert(made==4 and old_calls==2)
''')

if __name__=='__main__':unittest.main()
