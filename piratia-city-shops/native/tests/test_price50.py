"""Global classic NPC buyback and safe48->50 migration, with existing five NPCs."""
import json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_native as base
native=base.native

class Price50Tests(unittest.TestCase):
    def test_patchouli_base3000_synchronizes_both_tables_for_classic1500_buyback(self):
        with tempfile.TemporaryDirectory() as d:
            server,client=base.fixture(Path(d));base.isolated_install(server,client,True)
            for table in (server/'ItemInfo.bin',client/'scripts/table/iteminfo.bin'):
                raw=table.read_bytes();price=next(struct.unpack_from('<i',raw,p+320)[0] for p in range(4,len(raw),868) if struct.unpack_from('<I',raw,p+4)[0]==1000)
                self.assertEqual(price,3000);self.assertEqual(price//2,1500)
            self.assertNotIn(1000,{i['id'] for s in native.catalog()['shops'] for i in s['items']})
            self.assertEqual(len(native.offers(native.catalog())),718)
    def test_upgrade48_keeps_old_npcs_and_outside_owner_changes(self):
        with tempfile.TemporaryDirectory() as d:
            server,client=base.fixture(Path(d))
            with patch.object(native,'CATALOG',native.ROOT/'catalog-alpha48.json'):
                base.isolated_install(server,client,True)
            before=(server/'garner/garnerNPC.bin').read_bytes()
            sdk=server/'script/MisSdk/NpcSdk.lua';sdk.write_bytes(sdk.read_bytes()+b'\n-- owner preserved50\n')
            report=base.isolated_install(server,client,True)
            self.assertEqual(report['upgraded_from'],'Alpha48');base.assert_actor_migration(self,before,(server/'garner/garnerNPC.bin').read_bytes())
            self.assertTrue(sdk.read_bytes().endswith(b'-- owner preserved50\n'))
            self.assertTrue(base.isolated_install(server,client,True)['already_installed'])

if __name__=='__main__':unittest.main()
