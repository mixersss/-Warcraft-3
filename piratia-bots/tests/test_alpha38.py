"""Native map format, underwater shore detours and checked world geometry."""
import base64
import importlib.util
import json
import struct
import sys
import unittest
import zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from navigation import Navigation
from regions import Regions
from build_world_navigation import MapFile,HEADER,TILE,project


def sample(overrides=None,missing=False):
    records=[]
    for y in range(8):
        for x in range(8):
            height,region,blocks=(overrides or {}).get((x,y),(6,1,(12,12,12,12)))
            records.append(TILE.pack(0,4,0,height,region,1,*blocks))
    raw=HEADER.pack(780627,8,8,8,8)+struct.pack('<I',0 if missing else 24)
    if not missing:raw+=b''.join(records)
    return raw,struct.pack('<II',16,16)+bytes(32)


class MapFormatTests(unittest.TestCase):
    def test_packed_native_fields_and_row_major_sections(self):
        raw,_=sample({(3,4):(-7,9,(1,2,128,64))})
        self.assertEqual(TILE.size,15)
        self.assertEqual(MapFile(raw).tile(3,4),{'height_cm':-70,'region':9,'blocks':(1,2,128,64)})
        self.assertEqual(MapFile(raw).tile(4,3)['height_cm'],60)

    def test_missing_sections_are_absent_not_default_walkable(self):
        raw,_=sample(missing=True);self.assertIsNone(MapFile(raw).tile(4,4))

    def test_unknown_version_and_corrupt_section_fail_closed(self):
        raw,_=sample()
        for broken in (b'',struct.pack('<I',780626)+raw[4:],raw[:-1],raw[:20]+struct.pack('<I',4)+raw[24:]):
            with self.assertRaises(ValueError):MapFile(broken)
        with self.assertRaises(ValueError):MapFile(raw).tile(8,0)


@unittest.skipUnless(importlib.util.find_spec('numpy'),'numpy required only for offline map building')
class ProjectionTests(unittest.TestCase):
    def test_underwater_vertex_excluded_with_shore_clearance(self):
        raw,blk=sample({(4,4):(-1,5,(12,12,12,12))});cells,audit=project(raw,blk)
        self.assertEqual(cells[1,1],1);self.assertEqual(cells[4,4],0)
        self.assertEqual(cells[3,3],0);self.assertEqual(cells[2,2],0)
        self.assertEqual(audit['underwater_vertices'],1);self.assertEqual(audit['water_excluded_tiles'],4)
        self.assertEqual(audit['client_server_block_differences_50cm'],0)

    def test_explicit_native_bridge_not_blocked_by_underwater_terrain(self):
        raw,blk=sample({(4,4):(-1,8,(12,12,12,12))})
        cells,audit=project(raw,blk)
        self.assertEqual(cells[4,4],1);self.assertEqual(audit['bridge_tiles'],1)
        raw,blk=sample({(4,4):(-1,8,(128,12,12,12))})
        cells,_=project(raw,blk);self.assertEqual(cells[4,4],0)

    def test_native_collision_bits_and_territory_are_both_required(self):
        raw,blk=sample({(4,4):(6,1,(128,12,12,12)),(1,1):(6,0,(12,12,12,12))})
        cells,audit=project(raw,blk)
        self.assertEqual(cells[4,4],0);self.assertEqual(cells[1,1],0)
        self.assertEqual(audit['client_server_block_differences_50cm'],1)
        raw,blk=sample({(4,4):(6,1,(64,64,64,64))})
        self.assertEqual(project(raw,blk)[0][4,4],1) # Sign of object height is not bit128 collision.

    def test_server_collision_union_retained_even_if_client_clear(self):
        raw,blk=sample();blk=bytearray(blk);index=8*16+8
        blk[8+index//8]|=1<<(7-index%8)
        cells,_=project(raw,bytes(blk));self.assertEqual(cells[4,4],0)
        for broken in (bytes(blk[:-1]),struct.pack('<II',8,8)+bytes(8)):
            with self.assertRaises(ValueError):project(raw,broken)

    def test_absent_sections_cannot_generate_ground(self):
        cells,audit=project(*sample(missing=True))
        self.assertEqual(audit['walkable_tiles'],0);self.assertFalse(cells.any())

    def test_server_territory_restriction_cannot_be_overridden_by_client(self):
        raw,blk=sample();attrs=bytearray(struct.pack('<II',8,8)+b'\x01\x00\x01'*64)
        attrs[8+3*(4*8+4)]=0
        cells,audit=project(raw,blk,bytes(attrs))
        self.assertEqual(cells[4,4],0);self.assertTrue(audit['server_attributes_checked'])
        self.assertEqual(audit['client_server_ground_eligibility_differences'],1)
        with self.assertRaises(ValueError):project(raw,blk,bytes(attrs[:-1]))


class PublishedGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=json.loads((ROOT/'assets/world-navigation.json').read_text())
        cls.garner=Navigation(ROOT/'assets/garner-navigation.json')

    def test_known_pond_floor_is_blocked_and_actual_route_goes_around(self):
        n=self.garner
        self.assertFalse(n.free(n.cell((202550,265950))))
        start=n.nearest((201850,266350),12);end=n.nearest((203650,266350),12)
        self.assertFalse(n.line_clear(start,end));path=n.path(start,end)
        self.assertTrue(path);self.assertEqual(path[-1],end)
        self.assertTrue(all(n.line_clear(a,b) for a,b in zip(path,path[1:])))
        self.assertTrue(any(p[1]!=start[1] for p in path))

    def test_argent_crop_exactly_matches_new_full_garner_grid(self):
        n=self.garner;c=Navigation(ROOT/'assets/argent-navigation.json')
        for y in range(c.height):
            start=(y+c.origin[1])*n.width+c.origin[0]
            self.assertEqual(c.cells[y*c.width:(y+1)*c.width],n.cells[start:start+c.width])

    def test_three_homes_and_all_saved_farm_goals_are_clear(self):
        from adventure import Adventure
        from test_adventure import role
        from test_development import scene
        from city_travel import TELEPORTERS
        regions=json.loads((ROOT/'assets/regions.json').read_text())
        for name,region in regions.items():
            n=Navigation(ROOT/'assets'/region['navigation'])
            self.assertTrue(n.waypoints,name)
            for p in region['spawns']:self.assertIsNotNone(n.nearest(p,12),name)
            for record in region['farms'].values():
                for p in record['points']:self.assertTrue(n.free(n.cell(p)),(name,p))
            home=n.nearest(region['spawns'][0],12)
            points=[TELEPORTERS[name]]
            for job in {'garner':(1,4),'magicsea':(5,),'darkblue':(2,)}[name]:
                w=scene();w.map=name;q=Adventure(w,lambda *a:None,role=role(job))
                keys=set(q.destinations.values())|set(q.letter_stops.values())
                points.extend(q.npcs[key] for key in keys)
            for point in points:
                goal=n.nearest(point,6)
                self.assertIsNotNone(goal,(name,point))
                self.assertLessEqual(__import__('math').dist(point,goal),220)
                path=n.path(home,goal);self.assertTrue(path,(name,point))
                self.assertTrue(all(n.line_clear(a,b) for a,b in zip(path,path[1:])))
        for model in ('237','240','43'):
            self.assertTrue(any(r['farms'].get(model,{}).get('points') for r in regions.values()),model)

    def test_twenty_nine_client_server_pairs_and_two_incomplete_maps(self):
        self.assertEqual(len(self.catalog['maps']),29)
        self.assertEqual(set(self.catalog['client_only_maps']),{'darkhouse','prisonisland'})
        for name,info in self.catalog['maps'].items():
            n=Navigation(ROOT/'assets'/info['navigation'])
            self.assertEqual((n.width,n.height),(info['width'],info['height']))
            self.assertEqual(sum(n.cells),info['walkable_tiles'])
        self.assertFalse(self.catalog['native_windows_verified'])

    def test_additional_maps_loaded_lazily_on_actual_entry_only(self):
        r=Regions(ROOT/'assets')
        self.assertEqual(set(r.navigation),{'garner','magicsea','darkblue'})
        n=r.nav('darkswamp');self.assertEqual(n.map,'darkswamp');self.assertTrue(n.incremental)
        self.assertIs(r.nav('darkswamp'),n);self.assertIsNone(r.get('darkswamp'))
        with self.assertRaises(ValueError):r.nav('darkhouse')

    def test_field_merchants_in_all_three_regions(self):
        shops=json.loads((ROOT/'assets/town-services.json').read_text())['shops']
        self.assertEqual(len(shops['garner']),19)
        self.assertEqual(len(shops['magicsea']),7)
        self.assertEqual(len(shops['darkblue']),11)
        self.assertTrue(all(s['offers'] for name in ('garner','magicsea','darkblue') for s in shops[name]))

    def test_quest_ingredient_farming_does_not_choose_unreachable_water_species(self):
        from test_alpha37 import ObjectiveReviewTests
        w,q=ObjectiveReviewTests().quest(64)
        q.region={'farms':{'1':{'level':1,'points':[],'drops':[1678]},
                           '2':{'level':2,'points':[[12350,23450]],'drops':[1678]}}}
        self.assertEqual(q.desired_models(),{2})
        self.assertEqual(q.farm_goals(),[[12350,23450]])


if __name__=='__main__':unittest.main()
