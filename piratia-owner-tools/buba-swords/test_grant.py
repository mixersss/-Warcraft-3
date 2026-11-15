import ctypes,ctypes.util,importlib.util,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent

MOCK='''
ITEMATTR_VAL_FUSIONID=184;ITEMATTR_VAL_LEVEL=183;ITEMATTR_URE=51;ITEMATTR_MAXURE=52
role={name='buba',bag={[10]={id=1397,old=true,attrs={}},[20]={id=9,old=true,attrs={}}}}
made=0;removed=0;writes=0;fusion=0;ledger=nil;free=46
function GetPlayerByName(name) return role end
function GetChaDefaultName(r) return r.name end
function GetChaFreeBagGridNum(r) return free end
function GetChaItem(r,kind,slot) return r.bag[slot] end
function GetItemID(i) return i.id end
function GetResPath(path) return path end
function SystemNotice(r,text) last_notice=text end
function MakeItem(r,id,count,kind)
 local slot=0;while r.bag[slot] do slot=slot+1 end
 r.bag[slot]={id=id,attrs={},params=0};made=made+1;return 1,slot
end
function SetItemAttr(i,k,v) assert(not i.old);i.attrs[k]=v;return 1 end
function GetItemAttr(i,k) return i.attrs[k] or 0 end
function FusionItem(a,b) assert(not a.old and not b.old);fusion=fusion+1;return 1 end
function SetItemForgeParam(i,k,v) assert(not i.old);i.params=v;return 1 end
function GetItemForgeParam(i,k) return i.params end
function TansferNum(n) return n<0 and n+4294967296 or n end
function GetItem_JinglianLv(i)
 local n=TansferNum(i.params);return math.floor(n/1000000)%10+math.floor(n/1000)%10+n%10
end
function check_item_final_data(i) assert(not i.old);i.calculated=true end
function RemoveChaItem(r,id,n,kind,slot,a,b,c)
 local i=r.bag[slot];assert(i and not i.old and i.id==1397 and n==1)
 r.bag[slot]=nil;removed=removed+1;return 1
end
function SetChaKitbagChange(r,k) end
function SynChaKitbag(r,k) synchronized=true end
io={open=function(path,mode)
 if mode=='r' and not ledger then return nil end
 return {read=function() return ledger end,write=function(self,s) ledger=s;writes=writes+1;return true end,close=function() return true end}
end}
'''


class GrantTests(unittest.TestCase):
 def run_lua(self,before='',after='',filename='BubaSwords.lua'):
  library=ctypes.util.find_library('lua5.4')
  if not library:self.skipTest('Lua5.4 not installed; actual server Lua still required')
  lua=ctypes.CDLL(library);pointer=ctypes.c_void_p
  lua.luaL_newstate.restype=pointer;lua.luaL_openlibs.argtypes=[pointer]
  lua.luaL_loadstring.argtypes=[pointer,ctypes.c_char_p];lua.lua_pcallk.argtypes=[pointer,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,pointer]
  lua.lua_tolstring.argtypes=[pointer,ctypes.c_int,pointer];lua.lua_tolstring.restype=ctypes.c_char_p;lua.lua_close.argtypes=[pointer]
  script=ROOT.joinpath(filename).read_text()
  code=MOCK+'\n'+before+'\nfunction grant()\n'+script+'\nend\n'+after
  state=lua.luaL_newstate()
  try:
   lua.luaL_openlibs(state);status=lua.luaL_loadstring(state,code.encode())
   if not status:status=lua.lua_pcallk(state,0,0,0,0,None)
   self.assertEqual(status,0,lua.lua_tolstring(state,-1,None) if status else '')
  finally:lua.lua_close(state)
 def test_two_native_fusions_and_only_temporary_bases_removed(self):
  self.run_lua(after='''grant();assert(made==4 and removed==2 and fusion==2 and synchronized)
assert(role.bag[10].old and role.bag[20].old)
local count=0
for slot,item in pairs(role.bag) do if not item.old then
 count=count+1;assert(item.id==5002 and item.attrs[184]==1397 and item.attrs[183]==15)
 assert(item.params==3129139019 and GetItem_JinglianLv(item)==27 and item.calculated)
end end
assert(count==2 and string.find(ledger,'done buba'))
local ok=pcall(grant);assert(not ok and made==4 and removed==2)
''')
 def test_wrong_character_and_full_bag_do_not_create_items_or_ledger(self):
  for before in ["role.name='other'",'free=3']:
   self.run_lua(before, 'assert(not pcall(grant));assert(made==0 and ledger==nil)')
 def test_missing_api_refuses_before_any_change(self):
  self.run_lua('GetPlayerByName=nil','assert(not pcall(grant));assert(made==0 and ledger==nil)')
 def test_classic_empty_slots_may_be_zero_and_bag_capacity24(self):
  self.run_lua('''function GetChaItem(r,kind,slot)
 if slot>=24 then error('outside bag') end
 return r.bag[slot] or 0
end
''','grant();assert(made==4 and removed==2 and string.find(ledger,"done"))')
 def test_partial_failure_blocks_repetition_and_preserves_old_items(self):
  self.run_lua('function FusionItem(a,b) return 0 end','''assert(not pcall(grant));assert(made==2 and removed==0)
assert(string.find(ledger,'pending'));assert(not pcall(grant));assert(made==2)
assert(role.bag[10].old and role.bag[20].old)''')
 def test_never_edits_unexpected_occupied_slot(self):
  self.run_lua('function MakeItem(r,id,n,k) made=made+1;return 1,10 end',
   'assert(not pcall(grant));assert(role.bag[10].old and made==1 and removed==0)')
 def test_level35_uses_native_exp_delta_and_repeated_call_never_adds_again(self):
  self.run_lua('''
ATTR_LV=0;ATTR_CEXP=15;ATTR_JOB=4;GetExp={[35]=1435074};role.lv=12;role.xp=4000
function GetChaAttr(r,k) if k==0 then return r.lv elseif k==4 then return 1 else return r.xp end end
function AddExp(r,npc,a,b) assert(npc==nil and a==1431074 and a==b);r.xp=r.xp+a;r.lv=35;exp_calls=(exp_calls or 0)+1 end
''','grant();assert(role.lv==35 and exp_calls==1);grant();assert(exp_calls==1)',filename='BubaLevel35.lua')
 def test_level35_keeps_higher_level_and_rejects_unpromoted_character(self):
  for lv,job,success in [(40,1,True),(1,0,False)]:
   self.run_lua(f'''
ATTR_LV=0;ATTR_CEXP=15;ATTR_JOB=4;GetExp={{[35]=1435074}}
function GetChaAttr(r,k) if k==0 then return {lv} elseif k==4 then return {job} else return 0 end end
function AddExp(...) error('must not add experience') end
''',f"assert(pcall(grant)=={str(success).lower()})",filename='BubaLevel35.lua')
 def test_classic_npc_context_works_without_getplayerbyname_and_preserves_dispatch(self):
  sword=ROOT.joinpath('BubaSwords.lua').read_text()
  self.run_lua('''GetPlayerByName=nil
old_calls=0
function MsgProc(...) old_calls=old_calls+1;return 123 end
function Notice(s) ready=s end
function dofile(path)
assert(path=='script/BubaSwords.lua')
'''+sword+'''\nend
''','''grant();assert(string.find(ready,'READY'));assert(made==0)
assert(MsgProc({name='other'},{},'packet','page','trade','missions','exchange')==123)
assert(made==0 and old_calls==1)
assert(MsgProc(role,{},'packet','page','trade','missions','exchange')==123)
assert(made==4 and removed==2 and old_calls==2)
MsgProc(role,{},'packet','page','trade','missions','exchange');assert(made==4)
''',filename='BubaNPC.lua')
 def test_npc_error_is_visible_and_does_not_disable_other_players_dialogues(self):
  sword=ROOT.joinpath('BubaSwords.lua').read_text()
  self.run_lua('''GetPlayerByName=nil;MakeItem=nil
old_calls=0
function MsgProc(...) old_calls=old_calls+1 end
function Notice(s) ready=s end
function dofile(path)
'''+sword+'''\nend
''','''grant();MsgProc(role,{},'packet');assert(string.find(last_notice,'ERROR'))
assert(made==0 and ledger==nil)
MsgProc({name='other'},{},'packet');assert(old_calls==2)
''',filename='BubaNPC.lua')


class InstallTests(unittest.TestCase):
 def test_only_new_script_copied_idempotently_and_existing_edits_preserved(self):
  spec=importlib.util.spec_from_file_location('gift_installer',ROOT/'install.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);npc=root/'resource/script/MisScript/NpcScript01.lua';npc.parent.mkdir(parents=True);npc.write_bytes(b'original NPC')
   target=module.install(root);self.assertEqual(npc.read_bytes(),b'original NPC')
   self.assertEqual(module.install(root),target);target.write_bytes(b'owner edit')
   with self.assertRaises(ValueError):module.install(root)
   self.assertEqual(target.read_bytes(),b'owner edit')


if __name__=='__main__':unittest.main()
