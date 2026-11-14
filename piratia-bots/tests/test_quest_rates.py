"""Encoding-preserving, idempotent quest-rate edits with recoverable atomic writes."""
import ctypes,ctypes.util,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch as mock_patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from configure_quest_rewards import patch,apply,discover,PatchError

SAMPLE=b'''-- private unrelated bytes: \xff\x80
function ActionProc(character, npc, actions)
 for i=1,2 do
  if actions[i].func == Other then
   return LUA_FALSE
  elseif actions[i].func == AddExp then
   local retExpState = GetExpState(character)
   actions[i].p1 = actions[i].p1 * GetExpState(character) / 100
   actions[i].p2 = actions[i].p2 * GetExpState(character) / 100
   local ret = AddExp(character, npc, actions[i].p1, actions[i].p2)
   if ret ~= LUA_TRUE then
    return LUA_FALSE
   end
  elseif actions[i].func == AddExpAndType then
   local ret = AddExpAndType(character, npc, actions[i].p1, actions[i].p2, actions[i].p3)
  elseif actions[i].func == AddMoney then
   local ret = AddMoney(character, npc, actions[i].p1)
   if ret ~= LUA_TRUE then
    return LUA_FALSE
   end
  elseif actions[i].func == TakeMoney then
   TakeMoney(character,npc,actions[i].p1)
  end
 end
end
-- untouched footer
'''

class QuestRatesTests(unittest.TestCase):
    def test_preserves_encoding_newlines_and_unrelated_life_rewards_or_costs(self):
        for newline in (b'\n',b'\r\n'):
            original=SAMPLE.replace(b'\n',newline);updated=patch(original)
            self.assertTrue(updated.startswith(b'-- private unrelated bytes: \xff\x80'+newline))
            self.assertTrue(updated.endswith(b'-- untouched footer'+newline))
            self.assertIn(b'AddExpAndType(character, npc, actions[i].p1, actions[i].p2, actions[i].p3)',updated)
            self.assertIn(b'TakeMoney(character,npc,actions[i].p1)',updated)
            self.assertNotIn(b'\r\r\n',updated)
            self.assertNotIn(b'actions[i].p1 =',updated)

    def test_second_run_is_byte_identical_and_changing_rates_replaces_them(self):
        updated=patch(SAMPLE,9,5);self.assertEqual(patch(updated,9,5),updated)
        changed=patch(updated,3,2);self.assertIn(b'AddExp x3',changed);self.assertIn(b'AddMoney x2',changed)
        self.assertNotIn(b'AddExp x9',changed);self.assertNotIn(b'AddMoney x5',changed)

    def test_backup_contains_exact_original_and_noop_does_not_create_another(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'MissionSdk.lua';file.write_bytes(SAMPLE)
            backup=apply(file);self.assertEqual(backup.read_bytes(),SAMPLE)
            self.assertEqual(file.read_bytes(),patch(SAMPLE));self.assertIsNone(apply(file))
            self.assertEqual(len(list(Path(d).glob('*.bak'))),1)

    def test_failed_replace_preserves_original_and_verified_backup(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'MissionSdk.lua';file.write_bytes(SAMPLE)
            with mock_patch('configure_quest_rewards.os.replace',side_effect=OSError('locked')):
                with self.assertRaises(OSError):apply(file)
            self.assertEqual(file.read_bytes(),SAMPLE)
            self.assertEqual(next(Path(d).glob('*.bak')).read_bytes(),SAMPLE)
            self.assertFalse(list(Path(d).glob('*.tmp')))

    def test_discovery_finds_content_regardless_of_lua_filename(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'resource'/'script'/'RenamedSdk.LUA';file.parent.mkdir(parents=True);file.write_bytes(SAMPLE)
            self.assertEqual(discover(d),file)

    def test_ambiguous_or_missing_dispatchers_are_not_modified(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(PatchError):discover(d)
            for name in ('a.lua','b.lua'):(Path(d)/name).write_bytes(SAMPLE)
            with self.assertRaises(PatchError):discover(d)
            self.assertEqual((Path(d)/'a.lua').read_bytes(),SAMPLE)

    def test_backup_and_data_folders_are_not_scanned(self):
        with tempfile.TemporaryDirectory() as d:
            for folder in ('data','backups','live'):
                directory=Path(d)/folder;directory.mkdir();(directory/'test.lua').write_bytes(SAMPLE)
            self.assertEqual(discover(d),Path(d)/'live'/'test.lua')

    def test_unknown_custom_side_effect_is_refused_before_backup_or_write(self):
        original=SAMPLE.replace(b'local retExpState =',b'UnknownCustomAction(character)\n   local retExpState =')
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'MissionSdk.lua';file.write_bytes(original)
            with self.assertRaises(PatchError):apply(file)
            self.assertEqual(file.read_bytes(),original);self.assertEqual(list(Path(d).glob('*.bak')),[])

    def test_duplicate_or_missing_handler_is_refused(self):
        for original in (SAMPLE+SAMPLE,SAMPLE.replace(b'func == AddMoney then',b'func == Different then')):
            with self.assertRaises(PatchError):patch(original)

    def test_invalid_multiplier_is_refused(self):
        for value in (0,-1,101,1.5,True):
            with self.assertRaises(PatchError):patch(SAMPLE,value,5)

    def test_real_lua_repeated_quest_completions_do_not_compound_rewards(self):
        name=ctypes.util.find_library('lua5.4')
        if not name:self.skipTest('Optional local liblua5.4 unavailable')
        lua=ctypes.CDLL(name);lua.luaL_newstate.restype=ctypes.c_void_p
        lua.luaL_openlibs.argtypes=[ctypes.c_void_p];lua.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
        lua.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
        lua.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.POINTER(ctypes.c_size_t)];lua.lua_tolstring.restype=ctypes.c_char_p
        lua.lua_close.argtypes=[ctypes.c_void_p]
        code=b'''LUA_TRUE=1;LUA_FALSE=0
function GetExpState(c) return c.bonus end
function AddExp(c,n,a,b) c.xp=a; c.upper=b; return 1 end
function AddMoney(c,n,a) c.gold=a; return 1 end
'''+patch(SAMPLE)+b'''
local actions={{func=AddExp,p1=250,p2=300},{func=AddMoney,p1=1100}}
for k=1,10 do
 local c={bonus=100}; ActionProc(c,0,actions)
 assert(c.xp==2250 and c.upper==2700 and c.gold==5500)
 assert(actions[1].p1==250 and actions[1].p2==300 and actions[2].p1==1100)
end
local buffed={bonus=150}; ActionProc(buffed,0,actions)
assert(buffed.xp==3375 and buffed.gold==5500)
'''
        state=lua.luaL_newstate()
        try:
            lua.luaL_openlibs(state);status=lua.luaL_loadstring(state,code)
            if not status:status=lua.lua_pcallk(state,0,0,0,0,None)
            self.assertEqual(status,0,lua.lua_tolstring(state,-1,None) if status else None)
        finally:lua.lua_close(state)

if __name__=='__main__':unittest.main()
