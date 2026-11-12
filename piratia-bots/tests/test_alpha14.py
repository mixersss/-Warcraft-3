"""100-worker policy, finite real-chat dialogues, hybrid phases and exact phrase growth."""
import json,sys,unittest
from collections import Counter
from pathlib import Path
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from coordination import tactic_for,TacticSchedule,Coordination
from conversations import Conversations
from social import Social,ChatBudget,say_request
from classic_wire import Reader
from world import Entity
from hunter import Hunter
from headless import Report
from navigation import Navigation
from test_development import scene
import test_coordination as base_tests

class CohortTests(unittest.TestCase):
    def test_exact_40_60_cohorts_for_hundred_and_two_hundred(self):
        for count in (100,200):
            roles=Counter(tactic_for(i) for i in range(1,count+1))
            self.assertEqual(roles,{'farm':count*4//10,'hybrid':count*6//10})
        self.assertEqual(tactic_for(1,'hunt'),'farm')
        self.assertEqual(tactic_for(1,'adventure'),'quests')
    def test_hybrid_cycles_only_when_not_busy_and_holds_for_profession(self):
        s=TacticSchedule('hybrid','test');first=s.tick(0)
        deadline=s.next_switch
        self.assertEqual(s.tick(deadline+1,busy=True),first)
        second=s.tick(deadline+2)
        self.assertNotEqual(first,second);self.assertEqual(s.switches,1)
        self.assertEqual(s.tick(deadline+3,mandatory=True),'quests')
        self.assertEqual(s.summary()['phase'],'quests')
        self.assertEqual(s.tick(deadline+1000,busy=True,mandatory=True),'quests')
        self.assertEqual(s.switches,1)
        self.assertEqual(s.tick(deadline+1001),second)
    def test_farm_cohort_never_enters_optional_quest_phase(self):
        s=TacticSchedule('farm','test')
        for now in (0,500,1000,10000):self.assertEqual(s.tick(now),'farm')
        self.assertEqual(s.switches,0)
    def test_two_hundred_policies_hold_two_hundred_unique_targets(self):
        # Reuse the same native-world based setup, not mocked claim decisions.
        setup=base_tests.CohortCombatTests();setup.nav=Navigation(ROOT/'assets/argent-navigation.json')
        coordinator=Coordination()
        policies=[setup.policy(i,coordinator,200)[1] for i in range(200)]
        for policy in policies:policy.tick(100)
        self.assertEqual(len({p.target for p in policies}),200)
        self.assertTrue(all(p.attacks==1 for p in policies))

class DialogueTests(unittest.TestCase):
    def pair(self):
        hub=Conversations(ROOT/'assets','test');budget=ChatBudget(8);pairs=[]
        for i in (1,2):
            w=scene();w.entities={}
            for actor in (1,2):
                w.entities[actor]=Entity(1,actor,100+actor,1,0,223200+actor*50,278700,40,
                                         {0:1,1:100,31:100},name=f'Bot{actor:08x}')
            w.own_id=i;w.map='garner';send=Mock()
            pairs.append((w,send,Social(w,send,w.own.name,budget,i,conversations=hub)))
        return hub,pairs
    def test_three_line_dialogue_advances_only_after_actual_peer_echo(self):
        hub,pairs=self.pair()
        for w,send,s in pairs:s.tick(0,False,True)
        hub.next_start=1
        delivered=[0,0]
        for now in range(1,40):
            for index,(w,send,s) in enumerate(pairs):
                s.tick(now,False,True)
                while delivered[index]<len(send.call_args_list):
                    call=send.call_args_list[delivered[index]];delivered[index]+=1
                    self.assertEqual(call.args[0],1)
                    text=Reader(call.args[1]).string()
                    other=pairs[1-index][2]
                    other.hear(w.own_id,text,now)
        self.assertEqual(sum(delivered),3)
        self.assertEqual(hub.summary()['dialogues_completed'],1)
        self.assertEqual(hub.summary()['active_dialogues'],0)
    def test_no_peer_echo_cannot_generate_a_reply_and_times_out(self):
        hub,pairs=self.pair()
        for w,send,s in pairs:s.tick(0,False,True)
        hub.next_start=1
        for now in range(1,50):
            for w,send,s in pairs:s.tick(now,False,True)
        self.assertEqual(sum(send.call_count for _,send,_ in pairs),1)
        self.assertEqual(hub.summary()['dialogues_completed'],0)
        self.assertGreater(hub.summary()['dialogues_expired'],0)
    def test_map_change_or_departure_cancels_dialogue(self):
        hub,pairs=self.pair()
        for w,send,s in pairs:s.tick(0,False,True)
        hub.next_start=1;pairs[0][2].tick(1,False,True)
        pairs[1][0].map='magicsea';pairs[1][2].tick(2,False,True)
        self.assertEqual(hub.summary()['active_dialogues'],0)
    def test_unknown_bot_speech_does_not_start_reply_loop(self):
        hub,pairs=self.pair()
        w,send,s=pairs[0]
        s.hear(2,w.own.name+' привет',0)
        self.assertIsNone(s.pending)
        s.tick(0,False,True);send.assert_not_called()
    def test_one_broadcast_human_greeting_gets_one_reply_for_hundred_bots(self):
        hub=Conversations(ROOT/'assets');budget=ChatBudget(8);bots=[]
        for i in range(100):
            w=scene();own=w.entities.pop(1);own.identity=1000+i;own.name=f'Bot{i:08x}'
            w.own_id=own.identity;w.entities[own.identity]=own
            send=Mock();s=Social(w,send,own.name,budget,i,conversations=hub)
            s.tick(0,False,True);s.hear(2,'Привет всем',1);bots.append((send,s))
        self.assertEqual(sum(s.pending is not None for _,s in bots),1)
        for now in range(2,15):
            for send,s in bots:s.tick(now,False,True)
        self.assertEqual(sum(send.call_count for send,_ in bots),1)
    def test_addressed_follow_up_can_change_intent_without_ambient_cooldown(self):
        hub=Conversations(ROOT/'assets');w=scene();send=Mock()
        s=Social(w,send,w.own.name,ChatBudget(8),'test',conversations=hub)
        s.tick(0,False,True);s.hear(2,w.own.name+' привет',1);s.tick(6,False,True)
        s.hear(2,w.own.name+' какой уровень',10);s.tick(20,False,True)
        self.assertEqual(send.call_count,2)
        self.assertIn('уровень',Reader(send.call_args.args[1]).string())
    def test_many_raw_chat_inputs_remain_nonpersistent_and_rate_limited(self):
        hub=Conversations(ROOT/'assets');w=scene();send=Mock()
        s=Social(w,send,w.own.name,ChatBudget(8),'test',conversations=hub)
        for i in range(1000):s.hear(2,'привет '+str(i),i*.001)
        self.assertEqual(len(hub.humans),1)
        self.assertNotIn('Traveller',str(s.summary()))

class PhraseTests(unittest.TestCase):
    def test_two_hundred_new_unique_lines_and_classic_packet_limit(self):
        bank=json.loads((ROOT/'assets/chat-phrases.json').read_text())
        rows=[line for lines in bank.values() for line in lines]
        self.assertEqual(len(rows),389)
        self.assertEqual(len(set(rows)),389)
        for line in rows:say_request(line)
        pairs=json.loads((ROOT/'assets/bot-dialogues.json').read_text())
        for p in pairs:
            for category,key in (('bot_open','open'),('bot_reply','reply'),('bot_close','close')):
                say_request('Bot12345678, '+bank[category][p[key]])


class PartyPopulationTests(unittest.TestCase):
    def test_simultaneous_leaders_choose_different_recipients(self):
        from party import Party,BotDirectory
        directory=BotDirectory();parties=[]
        for i in range(1,101):
            w=scene();name=f'Bot{i:08x}';w.own.name=name
            directory.update(name,i,w.map,w.position(0),1,0)
            parties.append((i,Mock(),w,name))
        names=[]
        for i,send,w,name in parties:
            Party(w,send,name,i,directory).tick(1,i)
            if send.called:names.append(Reader(send.call_args.args[1]).string())
        self.assertGreater(len(names),5)
        self.assertEqual(len(names),len(set(names)))
    def test_periodic_party_exit_waits_for_safe_time_and_server_confirmation(self):
        from party import Party,BotDirectory
        w=scene();send=Mock();d=BotDirectory();p=Party(w,send,w.own.name,2,d)
        p.members=(w.own.name,'Bot00000002');p.session_until=10
        p.tick(11,2,safe=False);send.assert_not_called()
        p.tick(12,2,safe=True);send.assert_called_once_with(6004,b'')
        self.assertEqual(len(p.members),2)
        p.tick(13,2,safe=True);self.assertEqual(send.call_count,1)
        p.observe(5002,b'\x00\x00',14)
        self.assertEqual(p.members,())
        self.assertIsNone(p.session_until)

class IntegratedScheduleTests(unittest.TestCase):
    def test_hunter_updates_optional_story_and_adventure_without_resetting_journal(self):
        from types import SimpleNamespace
        w=scene();w.own.values[4]=1
        h=Hunter(w,Navigation(ROOT/'assets/argent-navigation.json'),Mock(),Report(),lambda _:None,'test')
        h.tactic_schedule=TacticSchedule('hybrid','test')
        h.adventure=SimpleNamespace(tactic='quests',context=None,pending=None,journal=['keep'])
        h.update_tactic(0);first=h.quest_phase
        h.update_tactic(h.tactic_schedule.next_switch+1)
        self.assertNotEqual(first,h.quest_phase)
        self.assertEqual(h.optional_quests,h.quest_phase=='quests')
        self.assertEqual(h.adventure.tactic,h.quest_phase)
        self.assertEqual(h.adventure.journal,['keep'])

if __name__=='__main__':unittest.main()
