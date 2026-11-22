"""Owner regressions: NPC funding, shore recovery, role weapons and real treasure."""
import dataclasses,math,struct,sys,unittest,random
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from inventory import BagItem
from navigation import Navigation
from economy import Economy
from equipment import Equipment
from treasure_hunt import TreasureHunt
from progress_monitor import ProgressMonitor
from test_development import scene
from test_life import LIFE,GEAR,item
import test_market as market_fixtures
import test_alpha18 as vendor_fixtures
import test_alpha26 as scheduling_fixtures
from classic_wire import string

class ExtendedShoreRecoveryTests(unittest.TestCase):
    def test_snapshot_shore_needs_more_than_250cm_but_remains_bounded(self):
        import math
        from regions import Regions
        nav=Regions(ROOT/'assets').nav('garner')
        point=(212376,274878)
        self.assertFalse(nav.recovery_path(point))
        self.assertFalse(nav.shore_exit(point))
        self.assertFalse(nav.shore_exit(point,maximum_cm=500))
        route=nav.shore_exit(point,maximum_cm=550)
        self.assertGreater(len(route),1)
        self.assertEqual(route[0],point)
        self.assertFalse(nav.needs_recovery(route[-1]))
        self.assertLessEqual(sum(math.dist(a,b) for a,b in zip(route,route[1:])),550)

class FundingAndGearTests(unittest.TestCase):
    def test_report288_28_blueprints_are_sellable_but_np_and_gear_stay_safe(self):
        w,v,p=vendor_fixtures.VendorTests().make();v.sell_patchouli=True;w.bag={0:item(1000,28),1:item(684),2:item(289)}
        self.assertEqual(v.choices(p),[(0,1000,28)])
        w.bag[3]=dataclasses.replace(item(1000),parameters=(1,0))
        self.assertEqual(v.choices(p),[(0,1000,28)])
    def test_funding_selects_soft_patchouli_sources_even_for_level17_novice(self):
        import json
        w=scene();w.own.values.update({0:17,4:0,31:340,33:20,34:30})
        e=Economy(w.own.name,ROOT/'assets');region=json.loads((ROOT/'assets/regions.json').read_text())['garner']
        learned=SimpleNamespace(blocked=lambda *a:False,dangerous=lambda *a:False)
        selected=e.funding_models(w,region,learned,100)
        self.assertTrue(selected)
        self.assertTrue(all(region['farms'][str(m)]['level']<=12 for m in selected))
        self.assertTrue(all(str(m) in e.data['sources'] for m in selected))
    def test_class_weapon_replaces_higher_scoring_novice_sword(self):
        w=scene();w.own.model=1;w.own.values.update({0:25,4:2});w.own.equipment={9:9,6:9999}
        self.assertIsNotNone(GEAR.upgrade(w.own,37,5))
        w.own.values[4]=0
        self.assertIsNone(GEAR.upgrade(w.own,37,5))
    def test_instance_stats_affect_owned_upgrade_and_equipped_comparison(self):
        w=scene();w.own.model=1;w.own.values.update({0:25,4:2});w.own.equipment={9:37,6:9999}
        w.own.equipment_details={9:{'identity':37,'instance_attributes':((28,1),)}}
        better=dataclasses.replace(item(1406),instance_attributes=((28,20),))
        self.assertIsNotNone(GEAR.upgrade(w.own,1406,5,better))
        w.own.equipment_details[9]['instance_attributes']=((28,40),)
        self.assertIsNone(GEAR.upgrade(w.own,1406,5,better))
    def test_shore_from_owner_screenshot_has_short_physical_exit(self):
        n=Navigation(ROOT/'assets/garner-navigation.json');point=(207286,274389)
        self.assertEqual(n.recovery_path(point),[]);route=n.shore_exit(point)
        self.assertGreater(len(route),1);self.assertEqual(route[0],point)
        self.assertFalse(n.needs_recovery(route[-1]))
        self.assertLessEqual(sum(math.dist(a,b) for a,b in zip(route,route[1:])),250)
        for p in route:
            x,y=n.recovery_cell(p);i=y*n.width*2+x
            self.assertTrue(n.recovery_bits[i//8]&(1<<(7-i%8)))
    def test_disconnected_land_is_rejected_without_any_astar_expansion(self):
        n=Navigation(ROOT/'assets/garner-navigation.json');n.enable_incremental()
        first=n.land_labels.index(bytes([1]));second=n.land_labels.index(bytes([2]))
        a=n.position((first%n.width,first//n.width));b=n.position((second%n.width,second//n.width))
        n.begin_turn(expansions=0)
        try:self.assertEqual(n.path(a,b),[])
        finally:n.end_turn()
        self.assertEqual(n.planning_stats()['expanded_nodes'],0)
        self.assertEqual(n.planning_stats()['impossible_land_routes_rejected_without_search'],1)

    def test_shore_does_not_make_pond_crossing_normal_path_or_change_masks(self):
        n=Navigation(ROOT/'assets/garner-navigation.json');before=(n.cells,n.recovery_bits,n.safe_recovery_bits)
        n.shore_exit((207286,274389));self.assertEqual(before,(n.cells,n.recovery_bits,n.safe_recovery_bits))
        self.assertEqual(n.shore_exit((0,0)),[])
    def test_blueprints_no_longer_offered_or_wanted_in_focused_stalls(self):
        w,_,m,p=market_fixtures.MarketTests().make();m.focused_goods=True;w.bag={0:item(1000,28)}
        self.assertEqual(m.offers(p),[]);self.assertNotIn(1000,m.needed())
    def test_focused_stall_sells_real_drop_armour_with_stats_but_protects_forged(self):
        w,_,m,p=market_fixtures.MarketTests().make();m.focused_goods=True
        identity=next(i for i,g in GEAR.gear.items() if g['kind']==22 and g['jobs']!=[-1] and 1 not in g['jobs'] and i in m.catalog.items)
        ordinary=dataclasses.replace(item(identity),instance_attributes=((36,15),(37,150),(29,3),(0,0),(0,0)))
        w.bag={0:ordinary};self.assertEqual(len(m.offers(p)),1)
        w.bag[0]=dataclasses.replace(ordinary,parameters=(1,0));self.assertEqual(m.offers(p),[])
        w.bag[0]=dataclasses.replace(ordinary,forge=1);self.assertEqual(m.offers(p),[])

    def test_progress_monitor_uses_native_change_not_console_labels(self):
        w,p,_=scheduling_fixtures.ProfessionSchedulingTests().policy();w.own.values.update({0:17,4:1});p.target=None
        p.progress_monitor.tick(100,p);p.change('random label');p.progress_monitor.tick(146,p)
        self.assertGreaterEqual(p.progress_monitor.recoveries,1)
    def test_real_stall_or_exchange_is_not_aborted_by_progress_monitor(self):
        w,p,_=scheduling_fixtures.ProfessionSchedulingTests().policy();p.transaction_busy=Mock(return_value=True)
        p.progress_monitor.tick(100,p);p.progress_monitor.tick(200,p)
        self.assertEqual(p.progress_monitor.recoveries,0)

class MagicAndConnectionTests(unittest.TestCase):
    def test_magic_is_not_delayed_by_slow_physical_attack_interval(self):
        import test_alpha42 as magic_fixtures
        w,p=magic_fixtures.MagicTests().make();p.attack_interval=60
        p.tick(100)
        self.assertEqual(magic_fixtures.MagicTests().last_skill(p),99)
        self.assertLess(p.next_action,101)
    def test_caster_missing_staff_does_not_fall_back_to_hands(self):
        import test_alpha42 as magic_fixtures
        w,p=magic_fixtures.MagicTests().make();w.own.equipment={9:1}
        p.tick(100);p.tick(105)
        self.assertIsNone(magic_fixtures.MagicTests().last_skill(p))
        self.assertEqual(p.combat_skills.requests,0)
    def test_native_look_energy_updates_equipped_coral_without_inventing_charge(self):
        w=scene();w.own.equipment={7:867};w.own.equipment_details={7:{'identity':867,'energy':0,'valid':True}}
        energies=[0]*10;energies[7]=123
        w.observe(508,struct.pack('>IIB10H',w.own_id,77,23,*energies))
        self.assertEqual(w.own.equipment_details[7]['energy'],123)
        self.assertTrue(w.own.equipment_details[7]['valid'])
        self.assertEqual(w.own.equipment,{7:867})
        before=dict(w.own.equipment_details[7])
        w.observe(508,struct.pack('>IIBH',w.own_id,78,23,999))
        self.assertEqual(w.own.equipment_details[7],before)
        self.assertEqual(w.decode_info['look_energy'],'unsupported_slot_count')

    def test_protocol_reconnect_is_bounded_and_preserves_account_dictionary(self):
        from auto_bots import run_bot
        from unittest.mock import patch
        import tempfile,copy
        stop=Mock();stop.is_set.return_value=False;stop.wait.return_value=False
        bot={'preserve_existing':True};before=copy.deepcopy(bot)
        failure=(False,{'entered_world':True,'exit_reason':'protocol_or_state_error','error_type':'ProtocolError'})
        with tempfile.TemporaryDirectory() as d,patch('auto_bots._run_bot_once',return_value=failure) as once:
            self.assertFalse(run_bot(1,bot,1973,0,stop,Path(d)))
            self.assertEqual(once.call_count,4)
        self.assertEqual(bot,before)
    def test_recent_network_diagnostics_contain_only_bounded_packet_metadata(self):
        from headless import Report
        import tempfile,json
        report=Report()
        for i in range(100):report.event('receive',500+i,10)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'report.json';report.write(p);data=json.loads(p.read_text())
        self.assertEqual(len(data['recent_events']),40)
        self.assertTrue(all(set(e)=={'direction','command','bytes'} for e in data['recent_events']))

class TreasureTests(unittest.TestCase):
    def make(self):
        w=scene();w.own.values.update({0:20,4:5,1:100,31:100,2:100,32:100,8:20000})
        w.bag_ready=True;w.bag_capacity=24
        t=TreasureHunt(w,SimpleNamespace(phase=lambda *a:'income'))
        p=SimpleNamespace(world=w,sequence=2,emit=Mock(),transaction_busy=lambda:False,
            stuck_return=SimpleNamespace(pending=None,tick=Mock(return_value=True)),nav=SimpleNamespace(nearest=lambda p,r:p),move_to=Mock(return_value=True))
        return w,t,p
    def test_np_use_waits_for_both_consumption_and_real_map(self):
        w,t,p=self.make();w.bag={0:item(684)}
        self.assertTrue(t.tick(100,p,True));self.assertEqual(p.emit.call_args.args[0][8],11)
        self.assertEqual(t.maps_created,0);self.assertIn(0,w.bag)
        w.bag={1:item(682)};t.tick(101,p,False)
        self.assertEqual(t.maps_created,1)
    def test_no_free_map_or_ticket_or_reward(self):
        w,t,p=self.make();w.bag={}
        self.assertFalse(t.tick(100,p,True));p.emit.assert_not_called();self.assertEqual(t.completed,0)
        w.own.values[0]=14;w.bag={0:item(684)}
        self.assertFalse(t.tick(101,p,True));p.emit.assert_not_called()
    def test_treasure_coordinates_require_item_attributes_or_server_notice(self):
        w,t,p=self.make();w.bag={0:item(682)}
        t.tick(100,p,True);self.assertEqual(t.pending[0],'locate');self.assertIsNone(t.point)
        t.observe(501,struct.pack('>I',99)+string('Treasure is hidden at Treasure GulfRegion470,1000 nearby'))
        self.assertIsNone(t.point)
        t.observe(517,string('Treasure is hidden at Treasure GulfRegion470,1000 nearby'))
        self.assertEqual(t.point,(47000,100000))
    def test_no_trip_without_outward_and_home_tickets(self):
        w,t,p=self.make();w.bag={0:item(682),1:item(2445)};t.point=(47000,100000)
        self.assertFalse(t.tick(100,p,True));p.stuck_return.tick.assert_not_called()
        w.bag[2]=item(4602);self.assertTrue(t.tick(101,p,True))
        p.stuck_return.tick.assert_called_once_with(101,p,'jialebi')
    def test_dig_requires_nearby_real_coordinate_and_map_consumption(self):
        w,t,p=self.make();w.map='jialebi';w.own.x,w.own.y=47000,100000;t.point=w.own.position;w.bag={0:item(682)}
        self.assertTrue(t.tick(100,p,True));self.assertEqual(t.completed,0)
        w.bag={};t.tick(101,p,False);self.assertEqual(t.completed,1)
    def test_failed_dig_is_bounded_retry_not_fake_success(self):
        w,t,p=self.make();w.map='jialebi';w.own.x,w.own.y=47000,100000;t.point=w.own.position;w.bag={0:item(682)}
        t.tick(100,p,True);t.tick(113,p,True)
        self.assertEqual(t.completed,0);self.assertEqual(t.timeouts,1);self.assertFalse(t.tick(114,p,True))

if __name__=='__main__':unittest.main()
