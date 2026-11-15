import json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_native as base
n=base.native

class Shops55Tests(unittest.TestCase):
 def test_alpha50_upgrade_preserves_every_old_actor_except_requested_forge_move(self):
  with tempfile.TemporaryDirectory() as d:
   server,client=base.fixture(Path(d))
   with patch.object(n,'CATALOG',n.ROOT/'catalog-alpha50.json'):base.isolated_install(server,client,True)
   before=(server/'garner/garnerNPC.bin').read_bytes()
   report=base.isolated_install(server,client,True)
   self.assertEqual(report['upgraded_from'],'Alpha50');base.assert_actor_migration(self,before,(server/'garner/garnerNPC.bin').read_bytes())
   self.assertEqual(report['positions_m'][2],[2197,2703]);self.assertEqual(report['positions_m'][-1],[2192,2710])
   self.assertTrue(base.isolated_install(server,client,True)['already_installed'])
 def test_wearable_tiers_black_dragon_and_books_have_real_source_records_and_prices(self):
  cat=n.catalog();db={r['id']:r for r in json.loads((n.ROOT/'item-database.json').read_text())}
  shop=next(s for s in cat['shops'] if s['key']=='equipment')
  self.assertEqual(len(shop['items']),61)
  tiers={35:50000,45:200000,55:450000,65:900000}
  for item in shop['items']:
   row=db[item['id']];self.assertTrue(row['in_server'] and row['in_client']);self.assertNotIn('Sealed',row['name_en'])
   if row['level'] in tiers:self.assertEqual(item['price'],tiers[row['level']])
   else:self.assertEqual(row['level'],75);self.assertGreater(item['price'],900000)
  books=next(s for s in cat['shops'] if s['key']=='fairies')['items'];ids={i['id'] for i in books}
  self.assertTrue({243,244,246,247,249,250,252,253,259,260}<=ids)
  self.assertFalse({245,248,251,254,261}&ids)
 def test_both_global_income_prices_are_identical_on_server_and_client(self):
  with tempfile.TemporaryDirectory() as d:
   server,client=base.fixture(Path(d));base.isolated_install(server,client,True)
   for file in (server/'ItemInfo.bin',client/'scripts/table/iteminfo.bin'):
    raw=file.read_bytes();prices={struct.unpack_from('<I',raw,p+4)[0]:struct.unpack_from('<i',raw,p+320)[0] for p in range(4,len(raw),868)}
    self.assertEqual(prices[1000]//2,1500);self.assertEqual(prices[4915]//2,2500)
 def test_section_pages_cover_exact_stock_without_duplicates(self):
  shop=next(s for s in n.catalog()['shops'] if s['key']=='equipment')
  pages=base.pages(shop);ids=[i for page in pages for panel in page for i in panel]
  self.assertEqual(len(pages),6);self.assertEqual(len(ids),len(set(ids)))
  self.assertEqual(set(ids),{i['id'] for i in shop['items']})

if __name__=='__main__':unittest.main()
