import ctypes,ctypes.util,hashlib,importlib.util,json,struct,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import installer as native
from render_native import render,pages,SERVICES
from price_tables import patch_binary,patch_text
legacy=native.legacy
CAT=native.catalog();ITEMS=native.offers(CAT)
spec=importlib.util.spec_from_file_location('legacy_shop_tests',ROOT.parent/'tests/test_shops.py');fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)

def isolated_install(server,client,apply=False,bot_assets=None):
 # Packaged tests must never write an overlay into the user's actual assets.
 assets=bot_assets if bot_assets is not None else Path(server).parent/'isolated-test-assets'
 return native.install(server,client,apply,assets)

def fixture(directory):
 server=fixtures.fixture(directory)
 sdk=server/'script/MisSdk/NpcSdk.lua';sdk.write_bytes(sdk.read_bytes()+b'\nfunction Buy( character, npc, trade, itemtype, index1, index2, count )\nreturn SafeBuy(character,trade[itemtype+1].item[index1+1],index2,count) end\n')
 allitems={i['id']:i for s in fixtures.CAT['shops'] for i in s['items']};allitems.update(ITEMS)
 texts=[];records=[]
 for identity,item in sorted(allitems.items()):
  row=[str(identity),item['name']]+['0']*93;row[10]=str(item['kind']);row[22]='1234';texts.append('\t'.join(row))
  r=bytearray(b'\xa5'*868);struct.pack_into('<I',r,4,identity);struct.pack_into('<I',r,108,identity)
  r[112:192]=item['name'].encode('ascii')[:79].ljust(80,b'\0');struct.pack_into('<h',r,308,item['kind']);struct.pack_into('<i',r,320,1234);records.append(r)
 (server/'ItemInfo.txt').write_text('\r\n'.join(texts)+'\r\n');raw=struct.pack('<I',868)+b''.join(records);(server/'ItemInfo.bin').write_bytes(raw)
 client=directory/'client/scripts/table';client.mkdir(parents=True);(client/'iteminfo.bin').write_bytes(raw)
 return server,directory/'client'

class PriceCodecTests(unittest.TestCase):
 def test_only_selected_price_bytes_change(self):
  with tempfile.TemporaryDirectory() as d:
   server,client=fixture(Path(d));raw=(server/'ItemInfo.bin').read_bytes();output=patch_binary(raw,ITEMS)
   self.assertEqual(len(raw),len(output))
   for p in range(4,len(raw),868):
    identity=struct.unpack_from('<I',raw,p+4)[0];self.assertEqual(raw[p:p+320],output[p:p+320]);self.assertEqual(raw[p+324:p+868],output[p+324:p+868])
    self.assertEqual(struct.unpack_from('<i',output,p+320)[0],ITEMS[identity]['price'] if identity in ITEMS else 1234)
   self.assertEqual(patch_binary(output,ITEMS),output)
 def test_text_keeps_fields_newlines_comments_and_unrelated_duplicates(self):
  item=next(iter(ITEMS.values()));identity=item['id'];row=[str(identity),item['name']]+['0']*22;row[10]=str(item['kind']);row[22]=' 17 '
  unrelated=b'2\tunused'+b'\t0'*23+b'\r\n';raw=b'// header\r\n'+unrelated+unrelated+'\t'.join(row).encode()+b'\r\n'
  out=patch_text(raw,{identity:item});self.assertEqual(out,raw.replace(b'\t 17 \t',b'\t '+str(item['price']).encode()+b' \t'))
 def test_mismatch_or_missing_item_refused(self):
  with self.assertRaises(ValueError):patch_binary(b'bad',ITEMS)
  with tempfile.TemporaryDirectory() as d:
   server,client=fixture(Path(d));raw=bytearray((server/'ItemInfo.bin').read_bytes());struct.pack_into('<h',raw,4+308,999)
   identity=struct.unpack_from('<I',raw,8)[0]
   with self.assertRaises(ValueError):patch_binary(bytes(raw),{identity:{'kind':1,'price':5000}})

class InstallationTests(unittest.TestCase):
 def test_bot_overlay_written_only_after_native_patch_and_can_be_repaired(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);server,client=fixture(p);assets=p/'bot-assets';assets.mkdir();(assets/'world-npcs.json').write_text('{}')
   isolated_install(server,client,False,assets);self.assertFalse((assets/'owner-city-shops.json').exists())
   isolated_install(server,client,True,assets);data=json.loads((assets/'owner-city-shops.json').read_text())
   self.assertEqual(len(data['npcs']),5);self.assertEqual(data['prices']['3844'],10000)
   self.assertTrue(isolated_install(server,client,True,assets)['already_installed'])
   (assets/'owner-city-shops.json').write_text('bad')
   isolated_install(server,client,True,assets);self.assertEqual(json.loads((assets/'owner-city-shops.json').read_text()),data)
 def test_fresh_install_native_stocks_and_synchronized_prices(self):
  with tempfile.TemporaryDirectory() as d:
   server,client=fixture(Path(d));original=(server/'garner/garnerNPC.bin').read_bytes();preview=isolated_install(server,client)
   self.assertFalse(preview['applied']);report=isolated_install(server,client,True)
   self.assertTrue(report['native_trade_windows']);self.assertEqual(report['positions_m'],[list(p) for p in legacy.DEFAULT_POINTS])
   self.assertTrue((server/'garner/garnerNPC.bin').read_bytes().startswith(original));self.assertEqual(len(legacy.binary_rows((server/'garner/garnerNPC.bin').read_bytes())),7)
   self.assertEqual((server/'ItemInfo.bin').read_bytes(),(client/'scripts/table/iteminfo.bin').read_bytes())
   script=(server/'script/MisScript/NpcScript01.lua').read_bytes();sdk=(server/'script/MisSdk/NpcSdk.lua').read_bytes()
   self.assertIn(b'OwnerNativeShops',script);self.assertNotIn(b'OwnerMarketBuy',script);self.assertIn(b'OwnerNativeBuy',sdk)
   self.assertTrue(isolated_install(server,client,True)['already_installed'])
 def test_upgrade_v1_keeps_existing_five_npcs_without_duplicates(self):
  with tempfile.TemporaryDirectory() as d:
   server,client=fixture(Path(d));legacy.install(server,legacy.DEFAULT_CENTER,True);before=(server/'garner/garnerNPC.bin').read_bytes()
   result=isolated_install(server,client,True)
   self.assertEqual((server/'garner/garnerNPC.bin').read_bytes(),before);self.assertEqual(result['npc_ids'],[19,20,21,22,23])
   sdk=(server/'script/MisSdk/NpcSdk.lua').read_bytes();self.assertEqual(sdk.count(b'item.func == OwnerOpenTrade'),1)
   self.assertNotIn(b'item.func == OwnerMarketBuy',sdk)
 def test_upgrade_preserves_edits_outside_owned_lua_block(self):
  with tempfile.TemporaryDirectory() as d:
   server,client=fixture(Path(d));legacy.install(server,legacy.DEFAULT_CENTER,True)
   script=server/'script/MisScript/NpcScript01.lua';sdk=server/'script/MisSdk/NpcSdk.lua'
   prefix=b'-- owner quest edit\nfunction OwnerQuestExtra() return 7 end\n'
   suffix=b'\n-- owner SDK edit\nfunction OwnerSdkExtra() return 9 end\n'
   script.write_bytes(prefix+script.read_bytes());sdk.write_bytes(sdk.read_bytes()+suffix)
   result=isolated_install(server/'script/MisScript',client,True)
   self.assertEqual(set(result['preserved_changed_files']),{'script/MisScript/NpcScript01.lua','script/MisSdk/NpcSdk.lua'})
   self.assertTrue(script.read_bytes().startswith(prefix));self.assertTrue(sdk.read_bytes().endswith(suffix))
   self.assertTrue(isolated_install(server,client,True)['already_installed'])
 def test_upgrade_refuses_modified_owned_shop_block_without_writes(self):
  with tempfile.TemporaryDirectory() as d:
   server,client=fixture(Path(d));legacy.install(server,legacy.DEFAULT_CENTER,True)
   script=server/'script/MisScript/NpcScript01.lua';script.write_bytes(script.read_bytes().replace(b'price=50000',b'price=1',1))
   before={p:p.read_bytes() for p in Path(d).rglob('*') if p.is_file()}
   with self.assertRaisesRegex(ValueError,'сам блок'):isolated_install(server,client,True)
   for p,raw in before.items():self.assertEqual(p.read_bytes(),raw)
 def test_upgrade_keeps_recompiled_npc_bytes_when_all_bindings_match(self):
  with tempfile.TemporaryDirectory() as d:
   server,client=fixture(Path(d));legacy.install(server,legacy.DEFAULT_CENTER,True)
   binary=server/'garner/garnerNPC.bin';text=server/'garner/garnernpc.txt'
   raw=bytearray(binary.read_bytes());raw[4+60]^=1;binary.write_bytes(raw)
   text.write_bytes(b'// owner table comment\n'+text.read_bytes());before=text.read_bytes()
   result=isolated_install(server,client,True)
   self.assertEqual(binary.read_bytes(),bytes(raw));self.assertEqual(text.read_bytes(),before)
   self.assertEqual(set(result['preserved_changed_files']),{'garner/garnernpc.txt','garner/garnerNPC.bin'})
 def test_wrong_client_is_refused_before_any_server_write(self):
  with tempfile.TemporaryDirectory() as d:
   server,client=fixture(Path(d));before={p:p.read_bytes() for p in server.rglob('*') if p.is_file()};(client/'scripts/table/iteminfo.bin').write_bytes(b'wrong format')
   with self.assertRaises(ValueError):isolated_install(server,client,True)
   for p,raw in before.items():self.assertEqual(p.read_bytes(),raw)
 def test_server_resource_cannot_be_used_as_client_folder(self):
  with tempfile.TemporaryDirectory() as d:
   server,client=fixture(Path(d));before={p:p.read_bytes() for p in server.rglob('*') if p.is_file()}
   with self.assertRaisesRegex(ValueError,'папка ИГРЫ'):isolated_install(server,server,True)
   for p,raw in before.items():self.assertEqual(p.read_bytes(),raw)
 def test_interrupted_server_client_update_rolls_back_all(self):
  with tempfile.TemporaryDirectory() as d:
   server,client=fixture(Path(d));before={p:p.read_bytes() for p in Path(d).rglob('*') if p.is_file()};actual=native.atomic;calls=[0]
   def fail_once(p,raw):
    calls[0]+=1
    if calls[0]==3:raise OSError('simulated write failure')
    return actual(p,raw)
   with patch.object(native,'atomic',fail_once):
    with self.assertRaises(OSError):isolated_install(server,client,True)
   for p,raw in before.items():self.assertEqual(p.read_bytes(),raw)
   self.assertFalse((server/native.MARKER).exists())
 def test_client_only_updates_prices_without_server(self):
  with tempfile.TemporaryDirectory() as d:
   server,client=fixture(Path(d));before=(server/'ItemInfo.bin').read_bytes();self.assertTrue(native.install_client(client,True)['applied'])
   self.assertEqual((server/'ItemInfo.bin').read_bytes(),before);self.assertTrue(native.install_client(client,True)['already_installed'])

MOCKS='''
LUA_TRUE=1;LUA_FALSE=0;TRADE_NOMAL=1;TRADE_BUY=1
function GetCharID(n) return n.id end
function SystemNotice(c,text) c.notice=text end
function SafeBuy(c,id,slot,count)
 local cost=Prices[id]*count
 if count>Stacks[id] or c.gold<cost or c.free<1 then return 0 end
 c.gold=c.gold-cost;c.bag[id]=(c.bag[id] or 0)+count;c.last=id
 if OwnerBasicGems and OwnerBasicGems[id] then
  for slot=0,239 do if not c.slots[slot] then c.slots[slot]={id=id,level=10};break end end
 end
 return 1
end
function TradePage(c,n,t,kind,p)
 assert(kind==1 and p==0)
 c.opened=t
 for i=1,3 do assert(t[i].count==#t[i].item and t[i].count<=60) end
end
function Talk(p,text) assert(Page[p]);Page[p][1].talk=text end
function Text(p,text,f,a,b)
 Page[p].count=Page[p].count+1;assert(Page[p].count<=12);assert(Page[p][Page[p].count]);Page[p][Page[p].count].func=f
end
function CloseTalk() end
function InitPage() Page={};for p=1,32 do Page[p]={count=0};for k=1,12 do Page[p][k]={} end end end
function GetChaItem(c,bag,slot) return c.slots[slot] end
function GetItemID(item) return item.id end
function Set_StoneLv(item,level) item.level=level end
function SynChaKitbag(c,reason) assert(reason==13);c.synced=(c.synced or 0)+1 end
function Fresh() return {gold=1000000,free=24,bag={},slots={}} end
'''

class NativeLuaTests(unittest.TestCase):
 def runlua(self,extra):
  dll=ctypes.util.find_library('lua5.4')
  if not dll:self.skipTest('liblua5.4 unavailable')
  l=ctypes.CDLL(dll);l.luaL_newstate.restype=ctypes.c_void_p;l.luaL_openlibs.argtypes=[ctypes.c_void_p];l.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
  l.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
  l.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];l.lua_tolstring.restype=ctypes.c_char_p;l.lua_close.argtypes=[ctypes.c_void_p]
  prices='Prices={'+','.join('[%d]=%d'%(i,item['price']) for i,item in ITEMS.items())+'};Stacks={'+','.join('[%d]=%d'%(i,item['stack']) for i,item in ITEMS.items())+'}\n'
  service='\n'.join('function '+f+'() end' for _,f in SERVICES)+'\n'
  code=(MOCKS+prices+service).encode()+render(CAT)+extra.encode();state=l.luaL_newstate()
  try:
   l.luaL_openlibs(state);status=l.luaL_loadstring(state,code)
   if not status:status=l.lua_pcallk(state,0,0,0,0,None)
   self.assertEqual(status,0,l.lua_tolstring(state,-1,None) if status else '')
  finally:l.lua_close(state)
 def test_all_products_are_real_native_trade_stock_and_purchase_resolves_exact_item(self):
  self.runlua('''
local total=0
for key,shop in pairs(OwnerNativeShops) do
 for page,stock in ipairs(shop.pages) do
  local c=Fresh();local npc={id=7};assert(OwnerOpenTrade(c,npc,key,page)==1);assert(c.opened==stock)
  for panel=1,3 do
   for index,id in ipairs(stock[panel].item) do
    c.gold=1000000;assert(OwnerNativeBuy(c,npc,shop.pages[1],panel-1,index-1,0,1)==1)
    assert(c.last==id and c.gold==1000000-Prices[id]);total=total+1
   end
  end
 end
end
assert(total==644)
''')
 def test_npc_initialization_exposes_trade_buttons_and_nonempty_catalog(self):
  self.runlua('''
for _,f in ipairs({OwnerClothes,OwnerFairies,OwnerForge,OwnerTickets,OwnerBoosts}) do
 InitPage();f();assert(Trade.owner_native_shop and Page[1].count<=12)
 assert(Trade[1].count+Trade[2].count+Trade[3].count>0);assert(Page[1][1].func==OwnerOpenTrade)
end
''')
 def test_two_players_select_different_pages_without_global_stock_changes(self):
  self.runlua('''
local a=Fresh();local b=Fresh();local npc={id=5};local shop=OwnerNativeShops.apparel
OwnerOpenTrade(a,npc,'apparel',1);OwnerOpenTrade(b,npc,'apparel',2)
assert(OwnerNativeBuy(a,npc,shop.pages[1],1,0,0,1)==1)
assert(OwnerNativeBuy(b,npc,shop.pages[1],1,0,0,1)==1)
assert(a.last~=b.last and a.last==shop.pages[1][2].item[1] and b.last==shop.pages[2][2].item[1])
''')
 def test_bad_indices_wrong_npc_no_active_window_and_insufficient_funds_fail(self):
  self.runlua('''
local c=Fresh();local n={id=2};local stock=OwnerNativeShops.forge.pages[1]
assert(OwnerNativeBuy(c,n,stock,2,0,0,1)==0);OwnerOpenTrade(c,n,'forge',1)
assert(OwnerNativeBuy(c,{id=3},stock,2,0,0,1)==0)
for _,i in ipairs({-1,1000,.5}) do assert(OwnerNativeBuy(c,n,stock,2,i,0,1)==0) end
assert(OwnerNativeBuy(c,n,stock,2,0,0,0)==0)
c.gold=0;assert(OwnerNativeBuy(c,n,stock,2,0,0,1)==0);assert(c.last==nil)
''')
 def test_forge_has_all_nine_native_services(self):
  self.runlua('''
InitPage();OwnerForge();local found={};for i=1,Page[1].count do found[Page[1][i].func]=true end
for _,f in ipairs({OpenForge,OpenUnite,OpenMilling,OpenGetStone,OpenFusion,OpenUpgrade,OpenItemTiChun,OpenItemEnergy,OpenRepair}) do assert(found[f]) end
''')
 def test_trade_mode_is_bound_when_npc_initializes_even_after_late_sdk_constants(self):
  self.runlua('''
for _,shop in pairs(OwnerNativeShops) do for _,page in pairs(shop.pages) do page.tp=nil end end
InitPage();OwnerForge();assert(Trade.tp==TRADE_NOMAL)
local c=Fresh();OwnerOpenTrade(c,{id=7},'apparel',2);assert(c.opened.tp==TRADE_NOMAL)
''')

 def test_only_new_paid_gem_is_initial_level_one_existing_gems_unchanged(self):
  self.runlua('''
local c=Fresh();c.slots[0]={id=885,level=9};c.bag[885]=1
local npc={id=7};local stock=OwnerNativeShops.forge.pages[1];local index=nil
for n,id in ipairs(stock[3].item) do if id==885 then index=n-1 end end
assert(index~=nil);OwnerOpenTrade(c,npc,'forge',1)
assert(OwnerNativeBuy(c,npc,stock,2,index,1,1)==1)
assert(c.slots[0].level==9 and c.slots[1].level==1 and c.gold==995000 and c.synced==1)
''')

if __name__=='__main__':unittest.main()
