"""Report-derived regressions: 510 sword switch, deferred EndAction, and earned AP increments."""
import json,struct,sys,unittest
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from classic_wire import Reader,sequence
from headless import Client,Report,ServerError
from hunter import movement,normal_attack
from navigation import Navigation
from progression import Progression,attribute_request
from auto_bots import connect_bot
from test_development import scene
import test_coordination as base

class RuntimeFixTests(unittest.TestCase):
 def policy(self):
  fixture=base.CohortCombatTests();fixture.nav=Navigation(ROOT/'assets/argent-navigation.json')
  return fixture.policy()
 def test_native_9byte_sword_update_reaches_world_from_real_client(self):
  w,p=self.policy();self.assertEqual(w.default_skill,25);known=dict(w.skills)
  packet=bytes.fromhex(json.loads((ROOT/'tests/fixtures/native_skill_update.json').read_text())['packet510'])
  client=Client(Mock(),Report());client.world_handler=w.observe;client.service(510,packet)
  self.assertEqual(w.default_skill,28);self.assertEqual(w.skills,known)
  p.tick(100);self.assertEqual(struct.unpack('>III',p.send.call_args.args[1][-12:])[0],28)
 def test_other_actors_skill_change_does_not_replace_own_attack(self):
  w,p=self.policy();w.observe(510,struct.pack('>IHBH',999,30,1,0));self.assertEqual(w.default_skill,25)
 def test_separate_default_skill_packet_is_also_routed(self):
  w,p=self.policy();c=Client(Mock(),Report());c.world_handler=w.observe
  c.service(531,struct.pack('>IH',w.own_id,30));self.assertEqual(w.default_skill,30)
 def test_move_replacement_waits_for_matching_deferred_stop(self):
  w,p=self.policy();goal=(223800,278700)
  p.move_to(goal,100);self.assertEqual(p.send.call_args.args[0],6)
  p.move_to((224000,278700),101);p.send.assert_called_with(7,b'')
  self.assertTrue(p.pending_action);self.assertEqual(len([c for c in p.send.call_args_list if c.args[0]==6]),1)
  self.assertTrue(p.flush_action(101.1));self.assertEqual(p.flushed_actions,0)
  # This is an old stop for a different packet: do not treat it as the new acknowledgement.
  w.stop_revision+=1;w.stop_packet_number=999;p.flush_action(101.2);self.assertEqual(p.flushed_actions,0)
  w.stop_revision+=1;w.stop_packet_number=p.last_sent_sequence;p.flush_action(101.3)
  self.assertEqual(p.flushed_actions,1);self.assertIsNone(p.pending_action);self.assertEqual(p.send.call_args.args[0],6)
 def test_finished_action_does_not_create_unnecessary_stop_pause(self):
  w,p=self.policy();p.move_to((223800,278700),100)
  w.stop_revision+=1;w.stop_packet_number=p.last_sent_sequence
  p.move_to((224000,278700),101);self.assertIsNone(p.pending_action);self.assertEqual(p.end_action_requests,0)
 def test_queue_timeout_is_bounded_when_server_has_no_active_action_to_stop(self):
  w,p=self.policy();p.move_to((223800,278700),100);p.move_to((224000,278700),101)
  p.flush_action(102.1);self.assertIsNone(p.pending_action);self.assertEqual(p.flushed_actions,1)
 def test_queued_attack_is_never_sent_to_dead_target(self):
  w,p=self.policy();p.move_to((223800,278700),100);p.clock=101
  p.emit(normal_attack(w.own_id,p.sequence,1,25,1000,2000,w.own.position))
  w.entities[1000].values[1]=0;p.flush_action(102.1)
  self.assertEqual(p.attacks,0);self.assertEqual(p.sent_action_counts.get('2',0),0)
 def test_movement_stop_and_skill_stop_keep_packet_identity(self):
  w,p=self.policy();packet=struct.pack('>IIBHH',w.own_id,41,1,1,0)+sequence(struct.pack('<iiii',223200,278700,223200,278700))
  w.observe(508,packet);self.assertEqual(w.stop_packet_number,41);self.assertEqual(w.stop_revision,1)
  # Native skill-source prefix: fight ID, angle, state, stop pose. Unneeded effect tail stays unparsed.
  packet=struct.pack('>IIBBHHH',w.own_id,42,3,7,0,1,0)+struct.pack('>IIBH',28,1000,0,0)+b'\0\0\0'
  w.observe(508,packet);self.assertEqual(w.stop_packet_number,42);self.assertEqual(w.stop_revision,2)
 def test_stat_request_is_increment_then_both_confirmations(self):
  w=scene();send=Mock();g=Progression(w,send);g.tick(0,True)
  send.assert_called_once_with(8,attribute_request(25,1));self.assertEqual(w.own.values[25],5)
  w.own.values[25]+=1;g.tick(1,True);self.assertEqual(g.confirmed,0)
  w.own.values[6]-=1;g.tick(2,True);self.assertEqual(g.confirmed,1)
 def test_busy_pin_creation_retries_same_secret_without_new_account(self):
  client=Mock();client.login.return_value=[];client.ensure_secondary_password.side_effect=[ServerError('create_secondary_password',532),None]
  report=Report();bot={'account':'saved-account','password':'saved-password','secondary_password':'saved-pin'}
  with patch('auto_bots.socket.create_connection',return_value=Mock()),patch('auto_bots.Client',return_value=client),patch('auto_bots.time.sleep'):
   connect_bot(bot,report,1973)
  self.assertEqual(client.login.call_count,1);self.assertEqual(client.ensure_secondary_password.call_count,2)
  self.assertTrue(all(c.args==('saved-pin',) for c in client.ensure_secondary_password.call_args_list))
 def test_nonbusy_pin_error_is_not_retried(self):
  client=Mock();client.login.return_value=[];client.ensure_secondary_password.side_effect=ServerError('create_secondary_password',533)
  with patch('auto_bots.socket.create_connection',return_value=Mock()),patch('auto_bots.Client',return_value=client),patch('auto_bots.time.sleep') as sleep:
   with self.assertRaises(ServerError):connect_bot({'account':'a','password':'p','secondary_password':'s'},Report(),1973)
   sleep.assert_not_called()

if __name__=='__main__':unittest.main()
