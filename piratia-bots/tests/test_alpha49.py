"""Native LFG handshake, bounded movement and gun-slot regressions."""
import math
import struct
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from classic_wire import string,Reader
from party import BotDirectory,Party
from hunt_party import HuntParty
from navigation import Navigation
from test_development import scene
from test_life import GEAR,LIFE,item
from town import Town
import random


def chat(sender,text,receiver=None):
    return string(sender)+(string(receiver) if receiver else b'')+string(text)


class RecruitmentTests(unittest.TestCase):
    def setUp(self):
        self.directory=BotDirectory();self.clients=[]
        for index in (3,6,9): # Old modulo cohort must not forbid these volunteers.
            w=scene();w.own.name=f'Bot{index:08d}';w.own.values.update({0:25,4:2})
            send=Mock();party=Party(w,send,w.own.name,index,self.directory)
            policy=SimpleNamespace(target=None,mandatory_work=lambda:False,transaction_busy=lambda:False,
                resting=False,town=None,vendor=None,career=None,story=None,travel=None,adventure=None,
                inventory_blocked=False,economy=None,nav=SimpleNamespace(nearest=lambda p,r:tuple(p)),
                move_to=Mock(return_value=True),change=Mock())
            hunt=HuntParty(w,policy,party,send);self.directory.update(party.name,index,w.map,w.position(0),25,0)
            hunt.tick(0);self.clients.append((w,party,hunt,send,policy))
        self.a,self.b,self.c=self.clients

    def handshake(self):
        aw,ap,a,sa,pa=self.a;bw,bp,b,sb,pb=self.b
        text=a.advertisement(1)
        self.assertFalse(a.leader);self.assertFalse(ap.members)
        a.observe(5402,chat(ap.name,text),1)
        b.observe(5402,chat(ap.name,text),1)
        self.assertEqual(sb.call_args.args[0],6403)
        r=Reader(sb.call_args.args[1]);receiver,reply=r.string(),r.string();r.end()
        a.observe(5403,chat(bp.name,reply,receiver),2)
        r=Reader(sa.call_args.args[1]);receiver,ack=r.string(),r.string();r.end()
        b.observe(5403,chat(ap.name,ack,receiver),2)
        return a,b

    def test_no_recruitment_without_actual_world_echo(self):
        w,p,h,s,policy=self.a
        self.assertIsNotNone(h.advertisement(1));h.work(1,policy,True)
        self.assertIsNone(h.leader);s.assert_not_called()

    def test_real_world_pm_invite_and_team_snapshot_required(self):
        a,b=self.handshake();aw,ap,_,sa,pa=self.a;bw,bp,_,sb,pb=self.b
        self.assertTrue(b.accepted);self.assertFalse(a.active());self.assertFalse(b.active())
        a.work(3,pa,True);self.assertEqual(sa.call_args.args[0],6001)
        bp.observe(5001,string(ap.name)+struct.pack('>IH',88,0),3)
        self.assertEqual(sb.call_args.args[0],6002);self.assertEqual(bp.members,())
        payload=b'\x01\x02'+b''.join(struct.pack('>I',i)+string(n)+string('')+struct.pack('>H',0)
            for i,n in ((1,ap.name),(2,bp.name)))
        for party in (ap,bp):party.observe(5002,payload,4)
        self.assertTrue(a.active());self.assertTrue(b.active())
        a.work(5,pa,True);self.assertEqual(ap.invites,1) # No duplicate invite to an existing member.

    def test_other_level_or_map_or_busy_bot_does_not_reply(self):
        aw,ap,a,sa,pa=self.a;bw,bp,b,sb,pb=self.b
        text=a.advertisement(1);a.observe(5402,chat(ap.name,text),1)
        for fields in ({'level':29},{'level':25,'map':'darkblue'},{'map':'garner','wants_xp':False}):
            self.directory.annotate(ap.name,**fields);b.observe(5402,chat(ap.name,text),2)
        sb.assert_not_called()

    def test_offmesh_bot_does_not_recruit_and_human_team_is_not_driven(self):
        w,p,h,send,policy=self.a
        policy.nav.needs_recovery=lambda point:True
        self.assertIsNone(h.advertisement(1))
        policy.nav.needs_recovery=lambda point:False
        h.leader=p.name;h.until=90;p.members=(p.name,'Human');p.humans.add('Human')
        h.tick(2);self.assertIsNone(h.leader)
        self.assertEqual(p.members,(p.name,'Human'));self.assertIsNone(p.session_until)
        send.assert_not_called()

    def test_unregistered_human_lfg_does_not_take_over_bot(self):
        w,p,h,s,policy=self.a
        h.observe(5402,chat('Human','Ищу пати на кач, 25 ур. Кто рядом — пишите в ЛС!'),1)
        self.assertIsNone(h.leader);s.assert_not_called()

    def test_unsolicited_bot_invite_is_rejected(self):
        aw,ap,a,sa,pa=self.a;bw,bp,b,sb,pb=self.b
        bp.observe(5001,string(ap.name)+struct.pack('>IH',88,0),1)
        self.assertEqual(sb.call_args.args[0],6003)

    def test_no_meeting_movement_before_private_ack(self):
        aw,ap,a,sa,pa=self.a;bw,bp,b,sb,pb=self.b
        text=a.advertisement(1);a.observe(5402,chat(ap.name,text),1);b.observe(5402,chat(ap.name,text),1)
        self.directory.annotate(ap.name,position=(220000,278700))
        self.assertFalse(b.work(2,pb,True));pb.move_to.assert_not_called()

    def test_unanswered_meeting_expires_without_waiting_forever(self):
        a,b=self.handshake();w,p,_,s,policy=self.b
        b.tick(100);self.assertIsNone(b.leader);self.assertEqual(b.timeouts,1)
        self.assertFalse(b.work(100,policy,True));self.assertIsNone(b.advertisement(100))

    def test_failed_path_releases_meeting(self):
        a,b=self.handshake();w,p,_,s,policy=self.b
        self.directory.annotate(a.name,position=(220000,278700));policy.move_to.return_value=False
        self.assertFalse(b.work(3,policy,True));self.assertIsNone(b.leader)

    def test_four_follower_capacity_is_atomic_and_bounded(self):
        a,b=self.handshake()
        results=[self.directory.claim_recruit(a.name,str(i),3) for i in range(8)]
        self.assertEqual(sum(results),3) # One existing follower plus three more.

    def test_inventory_and_profession_take_priority(self):
        a,b=self.handshake();w,p,_,s,policy=self.b
        policy.inventory_blocked=True
        self.assertFalse(b.work(3,policy,True));self.assertIsNone(b.leader)


    def test_unproductive_confirmed_team_requests_safe_native_leave(self):
        a,b=self.handshake();aw,ap,_,sa,pa=self.a;bw,bp,_,sb,pb=self.b
        payload=b'\x01\x02'+b''.join(struct.pack('>I',i)+string(n)+string('')+struct.pack('>H',0)
            for i,n in ((1,ap.name),(2,bp.name)))
        for party in (ap,bp):party.observe(5002,payload,3)
        b.tick(4)
        self.directory.update(ap.name,3,aw.map,aw.position(125),25,125)
        b.tick(125)
        self.assertFalse(b.active());self.assertEqual(b.unproductive_sessions,1)
        self.assertEqual(len(bp.members),2) # Never fake a roster update.
        bp.tick(125,bp.index,True)
        self.assertEqual(sb.call_args.args[0],6004)

    def test_recruitment_uses_earned_2000_cash_and_requires_echo(self):
        from public_chat import PublicChat,PublicBudget
        w,p,h,send,policy=self.a
        public=PublicChat(w,send,PublicBudget(),'low-cash');public.recruitment_provider=h.advertisement
        public.next_world=public.next_trade=0;w.own.values[8]=1999
        public.tick(1,True);send.assert_not_called()
        w.own.values[8]=2000;public.tick(2,True)
        self.assertEqual(send.call_args.args[0],6402)
        self.assertIsNone(h.leader);self.assertEqual(public.confirmed_world,0)
        public.tick(40,True);self.assertEqual(public.expired_echoes,1)
        self.assertEqual(public.confirmed_world,0)

    def test_lower_lfg_cash_gate_does_not_enable_ordinary_chatter(self):
        from public_chat import PublicChat,PublicBudget
        w,p,h,send,policy=self.a;w.own.values[8]=5000
        public=PublicChat(w,send,PublicBudget(),'ordinary');public.next_world=public.next_trade=0
        public.context_provider=lambda c:'Охочусь.'
        public.tick(1,True);send.assert_not_called()

    def test_confirmed_hunt_temporarily_overrides_random_errand_phase(self):
        from economy import Economy
        w,p,h,send,policy=self.a;e=Economy(p.name,ROOT/'assets')
        original=e.phase(w,3);e.group_hunting=True
        self.assertEqual(e.phase(w,3),'progression')
        e.group_hunting=False;self.assertEqual(e.phase(w,3),original)


class MovementAndGunTests(unittest.TestCase):
    def test_long_direct_route_is_short_checked_prefix(self):
        nav=object.__new__(Navigation);nav.origin=(0,0);nav.width=100;nav.height=10;nav.cells=bytes([1])*1000
        points=nav.movement_segment((50,50),(9050,50))
        self.assertLessEqual(sum(math.dist(a,b) for a,b in zip(points,points[1:])),2401)
        self.assertNotEqual(points[-1],(9050,50));self.assertTrue(nav.line_clear(*points))

    def test_short_prefix_never_cuts_through_wall(self):
        nav=object.__new__(Navigation);nav.origin=(0,0);nav.width=80;nav.height=15
        cells=bytearray([1])*1200
        for y in range(12):cells[y*80+12]=0
        nav.cells=bytes(cells)
        route=nav.movement_segment((50,50),(6050,50))
        self.assertGreaterEqual(len(route),2)
        self.assertLessEqual(sum(math.dist(a,b) for a,b in zip(route,route[1:])),2401)
        self.assertTrue(all(nav.line_clear(a,b) for a,b in zip(route,route[1:])))

    def test_occupied_physical_shore_origin_may_exit_only_into_dry_cells(self):
        nav=object.__new__(Navigation);nav.origin=(0,0);nav.width=2;nav.height=2
        nav.cells=bytes([0,1,0,1]);nav.connected_bits=None
        nav.recovery_cells=None;nav.recovery_bits=bytes([255,255])
        nav.safe_recovery_bits=bytes([0b00110011,0b00110011])
        route=nav.recovery_path((75,75))
        self.assertGreater(len(route),1);self.assertEqual(route[0],(75,75))
        for point in route[1:]:
            x,y=nav.recovery_cell(point);i=y*4+x
            self.assertTrue(nav.safe_recovery_bits[i//8]&(1<<(7-i%8)))

    def test_occupied_shore_does_not_allow_crossing_nondry_water(self):
        nav=object.__new__(Navigation);nav.origin=(0,0);nav.width=3;nav.height=2
        nav.cells=bytes([0,0,1,0,0,1]);nav.connected_bits=None
        nav.recovery_cells=None;nav.recovery_bits=bytes([255,255,255])
        nav.safe_recovery_bits=bytes([0b00001100,0b00110000,0b11000011])
        self.assertEqual(nav.recovery_path((25,25)),[])

    def test_owned_pistol_is_compatible_and_improves_empty_shooter(self):
        w=scene();w.own.model=1;w.own.values.update({0:25,4:2});w.own.equipment={}
        change=GEAR.upgrade(w.own,37,5)
        self.assertIsNotNone(change)
        self.assertEqual(change[1],[9])

    def test_equipped_pistol_in_right_hand_satisfies_critical_weapon(self):
        w=scene();w.own.model=1;w.own.values.update({0:25,4:2});w.own.equipment={9:37,6:9999}
        t=Town(w,LIFE,GEAR,None,random.Random(1),w.own.position)
        critical=t.critical_items()
        self.assertFalse(any(GEAR.types.get(i) in (3,4) for i in critical))

if __name__=='__main__':unittest.main()
