import ctypes,ctypes.util,json,struct,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import install
from render import render
CAT=json.loads((ROOT/'catalog.json').read_text())

def fixture(root):
 resource=root/'resource';(resource/'script/MisScript').mkdir(parents=True);(resource/'script/MisSdk').mkdir();(resource/'garner').mkdir()
 (resource/'script/MisScript/NpcScript01.lua').write_bytes(b'-- original file\nfunction Existing() end\n')
 (resource/'script/MisSdk/NpcSdk.lua').write_bytes(b'function Dispatch()\nif false then return\nelseif item.func == TradeGoods then return 1 end end\n')
 records=[];lines=[]
 for identity in (0,18):
  r=bytearray(428);struct.pack_into('<I',r,0,1);struct.pack_into('<I',r,4,identity);struct.pack_into('<I',r,100,identity)
  name=b'Original Merchant';r[108:236]=name.ljust(128,b'\0');r[8:48]=name.ljust(40,b'\0');r[394:410]=b'r_trade'.ljust(16,b'\0')
  struct.pack_into('<H',r,238,17);struct.pack_into('<iiii',r,244,223250,278750,223250,278750);records.append(bytes(r))
  lines.append(str(identity).encode()+b'\tOriginal Merchant\t1\t17\t12\t223250,278750\t223250,278750\t180\tArgent City\t1\t0\tr_trade\t0')
 (resource/'garner/garnernpc.txt').write_bytes(b'\n'.join(lines)+b'\n')
 (resource/'garner/garnerNPC.bin').write_bytes(struct.pack('<I',428)+b''.join(records))
 (resource/'ItemInfo.txt').write_bytes(b'\n'.join(str(i['id']).encode()+b'\t'+i['name'].encode('ascii')+b'\t0'*8+b'\t'+str(i['kind']).encode() for shop in CAT['shops'] for i in shop['items']))
 return resource

class PatchTests(unittest.TestCase):
 def test_server_folder_resolution_accepts_inner_script_path_and_file(self):
  with tempfile.TemporaryDirectory(prefix='owner server ') as d:
   root=fixture(Path(d))
   for selected in (root,root.parent,root/'script',root/'script/MisScript',root/'script/MisScript/NpcScript01.lua','"'+str(root/'script/MisScript')+'"'):
    self.assertEqual(install.locate(selected),root)
 def test_exact_five_owner_coordinates_written_to_both_npc_formats(self):
  with tempfile.TemporaryDirectory() as d:
   root=fixture(Path(d));_,output,report=install.plan(root,install.DEFAULT_CENTER)
   expected=[(2247,2777),(2247,2779),(2247,2781),(2247,2783),(2247,2784)]
   self.assertEqual(report['positions_m'],expected)
   records=install.binary_rows(output[Path('garner/garnerNPC.bin')])[-5:]
   for record,(x,y) in zip(records,expected):
    self.assertEqual(struct.unpack_from('<ii',record,244),(x*100+50,y*100+50))
   install.validate_npcs(output[Path('garner/garnernpc.txt')],output[Path('garner/garnerNPC.bin')])
 def test_catalog_has_five_npcs_and_exact_owner_prices(self):
  self.assertEqual(len(CAT['shops']),5);s={s['key']:s for s in CAT['shops']}
  self.assertTrue(all(i['price']==50000 for i in s['apparel']['items']))
  self.assertTrue(all(i['price']==5000 for key in ('forge','tickets') for i in s[key]['items']))
  self.assertTrue(all(i['price']==10000 for i in s['boosts']['items']))
  prices={i['id']:i['price'] for i in s['fairies']['items']}
  self.assertEqual(prices[680],20000);self.assertEqual(prices[681],20000);self.assertEqual(prices[232],2000)
  for i in range(276,281):self.assertEqual(prices[i],5000)
  for i in range(222,227):self.assertNotIn(i,prices)
  self.assertEqual(prices[227],1000);self.assertEqual(prices[3918],2000)
 def test_preview_changes_nothing_and_preserves_existing_binary_records(self):
  with tempfile.TemporaryDirectory() as d:
   root=fixture(Path(d));old=(root/'garner/garnerNPC.bin').read_bytes()
   original,output,report=install.plan(root,(2232,2787))
   self.assertTrue(output[Path('garner/garnerNPC.bin')].startswith(old));self.assertEqual(len(report['npc_ids']),5)
   self.assertEqual((root/'garner/garnerNPC.bin').read_bytes(),old)
   self.assertEqual(output[Path('script/MisSdk/NpcSdk.lua')].count(b'item.func == OwnerMarketBuy'),1)
 def test_install_idempotence_backups_and_unchanged_item_prices(self):
  with tempfile.TemporaryDirectory() as d:
   root=fixture(Path(d));before={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
   report=install.install(root,(2232,2787),True);again=install.install(root,(2232,2787),True)
   self.assertTrue(report['applied']);self.assertTrue(again['already_installed'])
   self.assertEqual(len(install.binary_rows((root/'garner/garnerNPC.bin').read_bytes())),7)
   for p in report['installed_sha256']:self.assertEqual((Path(report['backup'])/p).read_bytes(),before[p])
   self.assertEqual((root/'ItemInfo.txt').read_bytes(),before['ItemInfo.txt'])
   (root/'script/MisScript/NpcScript01.lua').write_bytes(b'user changed source')
   with self.assertRaises(ValueError):install.install(root,(2232,2787),True)
 def test_invalid_coordinates_or_binary_refuse_before_writes(self):
  with tempfile.TemporaryDirectory() as d:
   root=fixture(Path(d));path=root/'garner/garnerNPC.bin';before=path.read_bytes()
   with self.assertRaises(ValueError):install.install(root,(0,0),True)
   self.assertEqual(path.read_bytes(),before);path.write_bytes(b'invalid')
   with self.assertRaises(ValueError):install.install(root,(2232,2787),True)
 def test_partial_file_write_rolls_back_all_resources(self):
  with tempfile.TemporaryDirectory() as d:
   root=fixture(Path(d));before={p:p.read_bytes() for p in root.rglob('*') if p.is_file()};calls=[0];original_replace=install.os.replace
   def fail_once(a,b):
    calls[0]+=1
    if calls[0]==2:raise OSError('simulated interrupted write')
    return original_replace(a,b)
   with patch.object(install.os,'replace',fail_once):
    with self.assertRaises(OSError):install.install(root,(2232,2787),True)
   for p,data in before.items():self.assertEqual(p.read_bytes(),data)
   self.assertFalse((root/'owner-city-shops-v1.json').exists());self.assertEqual(list(root.rglob('*.tmp')),[])

MOCKS=b'''
LUA_TRUE=1;LUA_FALSE=0;ATTR_GD=8
function SystemNotice(c,s) c.notice=s end
function LG(...) end
function ChaIsBoat(c) return c.boat or 0 end
function GetChaFreeBagGridNum(c) return c.free end
function GetChaAttr(c,id) return c.gold end
function CheckBagItem(c,id) return c.bag[id] or 0 end
function TakeMoney(c,n,price)
 if c.fail_pay then c.gold=c.gold-17;return 0 end
 c.gold=c.gold-price;return 1
end
function AddMoney(c,n,price) c.gold=c.gold+price;return 1 end
function GiveItem(c,n,id,count,quality)
 assert(count==1 and quality==4)
 if c.fail_give then return 0 end
 c.bag[id]=(c.bag[id] or 0)+1
 if c.throw_after_delivery then error('late engine error') end
 return 1
end
function Fresh(gold) return {gold=gold,bag={},free=24} end
'''

class LuaTests(unittest.TestCase):
 def runlua(self,extra):
  name=ctypes.util.find_library('lua5.4')
  if not name:self.skipTest('liblua5.4 unavailable')
  lua=ctypes.CDLL(name);lua.luaL_newstate.restype=ctypes.c_void_p
  lua.luaL_openlibs.argtypes=[ctypes.c_void_p];lua.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
  lua.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
  lua.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.POINTER(ctypes.c_size_t)];lua.lua_tolstring.restype=ctypes.c_char_p;lua.lua_close.argtypes=[ctypes.c_void_p]
  state=lua.luaL_newstate()
  try:
   lua.luaL_openlibs(state);status=lua.luaL_loadstring(state,MOCKS+render(CAT)+extra.encode())
   if not status:status=lua.lua_pcallk(state,0,0,0,0,None)
   self.assertEqual(status,0,lua.lua_tolstring(state,-1,None) if status else None)
  finally:lua.lua_close(state)
 def test_all_catalog_pages_fit_twelve_options_and_byte_page_ids(self):
  self.runlua('''
function JumpPage() end;function CloseTalk() end
function Talk(p,s) assert(Page[p]);Page[p][1].talk=s end
function Text(p,s,func,a,b)
 Page[p].count=Page[p].count+1;assert(Page[p].count<=12 and Page[p].count<=255 and p<=255)
 assert(Page[p][Page[p].count]);Page[p][Page[p].count].func=func
end
for _,f in ipairs({OwnerClothes,OwnerFairies,OwnerForge,OwnerTickets,OwnerBoosts}) do
 Page={};for p=1,32 do Page[p]={count=0};for k=1,12 do Page[p][k]={} end end
 f()
end
''')
 def test_real_lua_payment_and_item_are_exact_for_all_products(self):
  self.runlua('''
for key,shop in pairs(OwnerMarketCatalog) do
 for id,offer in pairs(shop) do
  local c=Fresh(100000);assert(OwnerMarketBuy(c,0,key,id)==1)
  assert(c.gold==100000-offer.price and c.bag[id]==1)
 end
end
''')
 def test_failures_refund_only_actual_payment_and_never_duplicate_delivery(self):
  self.runlua('''
local c=Fresh(10000);c.fail_pay=true;assert(OwnerMarketBuy(c,0,'forge',885)==0);assert(c.gold==10000 and c.bag[885]==nil)
c=Fresh(10000);c.fail_give=true;assert(OwnerMarketBuy(c,0,'forge',885)==0);assert(c.gold==10000 and c.bag[885]==nil)
c=Fresh(10000);c.throw_after_delivery=true;assert(OwnerMarketBuy(c,0,'forge',885)==1);assert(c.gold==5000 and c.bag[885]==1)
''')
 def test_full_bag_insufficient_money_boat_and_forged_offer_are_rejected(self):
  self.runlua('''
for _,mode in ipairs({'bag','gold','boat','forged'}) do
 local c=Fresh(10000)
 if mode=='bag' then c.free=0 elseif mode=='gold' then c.gold=1 elseif mode=='boat' then c.boat=1 end
 local before=c.gold;local id=mode=='forged' and 999999 or 885
 assert(OwnerMarketBuy(c,0,'forge',id)==0);assert(c.gold==before and c.bag[885]==nil)
end
''')
 def test_npc_accepts_many_players_without_shared_stock_or_cooldown(self):
  self.runlua('''
for i=1,300 do local c=Fresh(5000);assert(OwnerMarketBuy(c,7,'forge',885)==1);assert(c.gold==0 and c.bag[885]==1) end
''')

if __name__=='__main__':unittest.main()
