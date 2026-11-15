"""650 input cases,100 multistep contexts, native channels, coordination and privacy."""
import dataclasses,hashlib,json,math,struct,sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from classic_wire import string,Reader
from dialogue_data import DialogueData
from dialogue_memory import DialogueManager
from chat_coordinator import BotCoordinator
from chat_adapter import ChatAdapter,fit
from public_chat import PublicChat,PublicBudget
from social import Social,ChatBudget
from test_development import scene
DATA=DialogueData(ROOT/'assets')

def incoming(channel,source,text,receiver=None,identity=2):
    if channel=='local':return 501,struct.pack('>I',identity)+string(text)
    if channel=='private':return 5403,string(source)+string(receiver)+string(text)
    return (5402 if channel=='world' else 5401),string(source)+string(text)

def fixture(name='Bot12345678',coordinator=None,budget=None,public_budget=None,identity=1):
    w=scene();own=w.entities.pop(1);own.identity=identity;own.name=name;w.entities[identity]=own;w.own_id=identity
    w.entities[2].name='Player';w.own.values.update({0:20,4:1,8:100000,2:100,32:100});w.bag_ready=True;w.bag_capacity=24
    p=SimpleNamespace(world=w,target=None,resting=False,market=None,offmesh_since=None,vendor=None,
                      move_goal=None,party=None,adventure=None,petcare=None,commerce=None,helper=None,direct_trade=None,mob_knowledge=None)
    send=Mock();s=Social(w,send,name,budget or ChatBudget(2),name);public=PublicChat(w,send,public_budget or PublicBudget(),name)
    c=coordinator or BotCoordinator(DATA.settings);a=ChatAdapter(w,p,s,public,None,DATA,c,send,name)
    a.profile.values=dict(a.profile.values,response_chance=1,max_bytes=120)
    a.register(0);return w,p,s,public,c,send,a

class RecognitionAndDataTests(unittest.TestCase):
    def test_at_least500_authored_distinct_incoming_cases(self):
        examples=[]
        for row in DATA.rows:
            for text in row['examples']:
                with self.subTest(intent=row['id'],message=text):self.assertEqual(DATA.recognizer.recognize(text).name,row['id'])
                examples.append(text)
        self.assertGreaterEqual(len(set(examples)),500)
    def test_nonexample_semantic_forms_negation_slang_and_translit(self):
        cases={'ПРИВЕТ!!!':'greeting','ghbdtn':'greeting','privet':'greeting','здраствуйте':'greeting',
               'пригласи меня пожалуйста в пати':'party_invite','кинь пожалуйста инвайт':'party_invite',
               'я не хочу покупать у тебя меч':'trade_decline','не приглашай пожалуйста меня':'party_decline',
               'не против пати на кач':'hunt_offer','не знаю где торговец':'merchant_location',
               'купи у меня ID684 за500':'sell','сколько стоит ID684':'price','мой коралл совсем разряжен':'coral',
               'вернулся после афк':'returned','как добавить слоты для камней':'sockets','ne priglashay v party':'party_decline',
               'а почему мы тут вообще стоим':'why','совсем постороннее предложение про квантовый объект':'unknown'}
        for text,wanted in cases.items():
            with self.subTest(text=text):self.assertEqual(DATA.recognizer.recognize(text).name,wanted)
    def test_unique_replies_count_factual_difference_not_style_permutations(self):
        self.assertGreaterEqual(DATA.unique_lines,5000);self.assertGreaterEqual(len(DATA.rows),100)
        self.assertEqual(len({p['id'] for p in DATA.profiles}),12)
        self.assertEqual(len({r['text'] for r in DATA.facts}),5424)
        self.assertNotEqual(DATA.item('ID684')['text'],DATA.item('ID1000')['text'])
    def test_real_item_name_and_client_only_facts_are_not_stock_claims(self):
        self.assertEqual(DATA.item('новый пергамент')['id'],684)
        example=next(row for row in DATA.facts if not row['in_server'])
        self.assertIn('не подтверждён',example['text']);self.assertNotIn('продаю',example['text'])
    def test_bad_catalog_keeps_validation_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)
            for name in ('dialogue-intents.json','dialogue-personalities.json','dialogue-settings.json','dialogue-facts.json'):
                (path/name).write_bytes((ROOT/'assets'/name).read_bytes())
            config=json.loads((path/'dialogue-settings.json').read_text());config['memory_turns']=100000
            (path/'dialogue-settings.json').write_text(json.dumps(config))
            with self.assertRaises(ValueError):DialogueData(path)

class MemoryAndDialoguesTests(unittest.TestCase):
    def test100_different_multistep_item_dialogues_preserve_context_and_topic_change(self):
        w,p,s,public,c,send,a=fixture()
        for ordinal,fact in enumerate(DATA.facts[:100],1):
            i=fact['id'];now=ordinal*1000;source='Player'+str(i)
            a.observe(*incoming('private',source,f'что за предмет ID{i}',a.name),now)
            ctx=a.memory.context('private',w.map,source,now)
            self.assertEqual(ctx['item'],i);self.assertEqual(ctx['topic'],'item')
            a.tick(now+5)
            r=Reader(send.call_args.args[1]);self.assertEqual(r.string(),source);reply=r.string();r.end()
            self.assertIn('ID'+str(i),reply)
            a.observe(*incoming('private',source,'повтори',a.name),now+6);a.tick(now+16)
            a.observe(*incoming('private',source,'давай о другом',a.name),now+20)
            self.assertIsNone(ctx['item']);self.assertIsNone(ctx['topic'])
            self.assertLessEqual(len(ctx['messages']),20)
        self.assertLessEqual(len(a.memory.contexts),32)
    def test_level_followup_is_contextual_not_assumed_without_a_question(self):
        w,p,s,public,c,send,a=fixture()
        a.observe(*incoming('private','Player','го кач',a.name),10)
        ctx=a.memory.context('private',w.map,'Player',10);self.assertEqual(ctx['awaiting'],'level')
        a.observe(*incoming('private','Player','21',a.name),11)
        self.assertEqual(ctx['level'],21)
        a.observe(*incoming('private','Other','21',a.name),12)
        other=a.memory.context('private',w.map,'Other',12);self.assertIsNone(other['level'])
    def test_private_details_do_not_flow_to_world_trade_or_local_context(self):
        m=DialogueManager(DATA.settings)
        private=m.context('private','garner','Player',0);private['item']=684;private['level']=37;private['last_reply']='СЕКРЕТНЫЕ УСЛОВИЯ'
        for channel in ('local','world','trade'):
            public=m.context(channel,'garner','Player',1)
            self.assertIsNone(public['item']);self.assertIsNone(public['level']);self.assertIsNone(public['last_reply'])
    def test_contexts_expire_and_reconnect_starts_without_transcripts(self):
        w,p,s,public,c,send,a=fixture();ctx=a.memory.context('private',w.map,'Player',0);ctx['item']=684
        self.assertIsNone(a.memory.context('private',w.map,'Player',901)['item'])
        another=ChatAdapter(w,p,s,public,None,DATA,c,send,a.name)
        self.assertEqual(len(another.memory.contexts),0);self.assertFalse(another.summary()['transcripts_saved'])
    def test_silence_cancels_queued_answers_but_does_not_change_gameplay(self):
        w,p,s,public,c,send,a=fixture();p.move_goal=(1,2);p.target=99
        a.observe(*incoming('private','Player','привет',a.name),10)
        a.observe(*incoming('private','Player','замолчи',a.name),11)
        self.assertEqual(len(a.queue),1);self.assertEqual(p.move_goal,(1,2));self.assertEqual(p.target,99)
        a.tick(20);count=send.call_count
        a.observe(*incoming('private','Player','как дела',a.name),30);a.tick(40)
        self.assertEqual(send.call_count,count)
    def test_no_action_for_negated_party_request(self):
        w,p,s,public,c,send,a=fixture();p.party=SimpleNamespace(request_name=Mock())
        a.observe(*incoming('private','Player','не приглашай в пати',a.name),10)
        p.party.request_name.assert_not_called()
    def test_unknown_requests_get_clarification_not_random_achievement(self):
        w,p,s,public,c,send,a=fixture()
        a.observe(*incoming('private','Player','несвязная абракадабра',a.name),10)
        self.assertEqual(a.intents['unknown'],1);a.tick(15)
        r=Reader(send.call_args.args[1]);r.string();text=r.string()
        self.assertTrue('Уточни' in text or 'уточни' in text)

class RoutingAndLimitTests(unittest.TestCase):
    def test_reply_uses_actual_local_world_trade_and_private_packet_ids(self):
        for channel,expected in [('local',1),('world',6402),('trade',6401),('private',6403)]:
            w,p,s,public,c,send,a=fixture()
            message=a.name+', '+('какая цена' if channel=='trade' else 'какой у тебя уровень')
            a.observe(*incoming(channel,'Player',message,a.name),10);a.tick(15)
            self.assertEqual(send.call_args.args[0],expected,channel)
    def test_local_distance_map_visibility_and_targeted_other_bot_filter(self):
        w,p,s,public,c,send,a=fixture();w.entities[2].x=w.own.x+10000
        a.observe(*incoming('local','Player',a.name+', привет'),10);a.tick(15)
        send.assert_not_called()
        w.entities[2].x=w.own.x+100
        c.register('Botabcdef00',dict(c.rows[a.name],identity=55))
        a.observe(*incoming('local','Player','Botabcdef00, привет'),20);a.tick(25)
        send.assert_not_called()
    def test_trade_channel_rejects_unrelated_chat(self):
        w,p,s,public,c,send,a=fixture()
        a.observe(*incoming('trade','Player',a.name+', какая погода'),10);a.tick(15)
        send.assert_not_called();self.assertTrue(any(r['reason'].startswith('off-topic') for r in a.decisions))
    def test_10_50_100_clients_never_reply_in_chorus(self):
        for count in (10,50,100):
            c=BotCoordinator(DATA.settings)
            for i in range(count):c.register(f'Bot{i:08x}',{'identity':i+10,'ready':True,'map':'garner','cash':100000,'until':100,'position':(0,0),'visible':set(range(10,110))})
            winners=[n for n in list(c.rows) if c.elect(n,'world','garner','Player','какой у тебя уровень',1)]
            self.assertEqual(len(winners),1)
            followup=[n for n in list(c.rows) if c.elect(n,'world','garner','Player','21',2)]
            self.assertEqual(followup,winners)
    def test_public_budget_is_shared_and_paid_message_needs_server_echo(self):
        budget=PublicBudget();a=fixture(public_budget=budget);b=fixture(name='Bot99999999',public_budget=budget)
        pa,pb=a[3],b[3]
        self.assertTrue(pa.reply('world','Привет',1));self.assertFalse(pb.reply('world','Привет',2))
        self.assertEqual(pa.confirmed_world,0)
        pa.observe(5402,string(a[0].own.name)+string('Привет'),3);self.assertEqual(pa.confirmed_world,1)
    def test_incoming_bot_echo_without_authorized_scene_cannot_start_a_loop(self):
        w,p,s,public,c,send,a=fixture()
        for i in range(100):a.observe(*incoming('world','Bot11111111','привет'),i)
        a.tick(105);self.assertEqual(len(a.queue),0);send.assert_not_called()
    def test_player_intervention_cancels_old_bot_scene(self):
        c=BotCoordinator(DATA.settings)
        base={'ready':True,'map':'garner','cash':100000,'until':100,'position':(0,0),'visible':{1,2,3}}
        for i in (1,2,3):c.register(f'Bot{i:08x}',dict(base,identity=i))
        c.next_scene=1;s=c.start('Bot00000001',2);self.assertIsNotNone(s)
        token=s['id'];c.sent(token,s['sender'],s['text'])
        for n in list(c.rows):c.elect(n,'local','garner',99,'я тоже хочу в группу',3,{1,2,3})
        self.assertFalse(c.valid_scene(token));self.assertEqual(c.interrupted,1)
    def test_scenes_require_exact_actual_echo_and_are_finite(self):
        c=BotCoordinator(DATA.settings)
        base={'ready':True,'map':'garner','cash':0,'until':100,'position':(0,0),'visible':{1,2,3,4}}
        for i in (1,2,3,4):c.register(f'Bot{i:08x}',dict(base,identity=i))
        c.next_scene=1;s=c.start('Bot00000001',2);self.assertTrue(2<=len(s['members'])<=4)
        self.assertIsNone(c.scene_for(s['receiver'],s['channel'],s['sender'],s['text'],3))
        for i in range(6):
            if not c.scene:break
            s=dict(c.scene);c.sent(s['id'],s['sender'],s['text'])
            result=c.scene_for(s['receiver'],s['channel'],s['sender'],s['text'],4+i)
            self.assertIsNotNone(result)
            if not result['finish']:c.prepare_scene_reply(s['id'],'Ответ '+str(i))
        self.assertIsNone(c.scene)
    def test_malformed_chat_is_isolated_and_does_not_change_bot_actions(self):
        w,p,s,public,c,send,a=fixture();p.move_goal=(500,600)
        for command in (501,5401,5402,5403):a.observe(command,b'bad',10)
        self.assertGreater(sum(a.errors.values()),0);self.assertEqual(p.move_goal,(500,600));send.assert_not_called()
    def test_queue_and_memory_are_bounded_under_message_storm(self):
        w,p,s,public,c,send,a=fixture()
        for i in range(1000):a.observe(*incoming('private','P'+str(i),'что за ID684',a.name),10+i*.01)
        self.assertLessEqual(len(a.queue),8);self.assertLessEqual(len(a.memory.contexts),32)
        self.assertLessEqual(len(a.decisions),16)
    def test_two_independent_clients_exchange_actual_local_frames_without_game_pause(self):
        c=BotCoordinator(DATA.settings);budget=ChatBudget(2)
        wa,pa,sa,puba,c,senda,a=fixture(coordinator=c,budget=budget)
        wb,pb,sb,pubb,c,sendb,b=fixture(name='Bot99999999',coordinator=c,budget=budget,identity=3)
        wa.entities[3]=dataclasses.replace(wb.own);wb.entities[1]=dataclasses.replace(wa.own)
        wa.own.values[8]=wb.own.values[8]=0
        a.register(2);b.register(2);c.next_scene=2
        pa.move_goal=(100,200);pb.move_goal=(300,400)
        a.tick(3);a.tick(10)
        self.assertEqual(senda.call_args.args[0],1)
        text=Reader(senda.call_args.args[1]).string()
        b.observe(501,struct.pack('>I',1)+string(text),11);b.tick(17)
        self.assertEqual(sendb.call_args.args[0],1)
        reply=Reader(sendb.call_args.args[1]).string()
        a.observe(501,struct.pack('>I',3)+string(reply),18)
        self.assertIsNone(c.scene)
        self.assertEqual(pa.move_goal,(100,200));self.assertEqual(pb.move_goal,(300,400))

    def test_wire_fitting_is_bounded_and_removes_controls(self):
        self.assertLessEqual(len(fit('слово '*200).encode('cp1251')),120)
        self.assertNotIn('\n',fit('привет\nпока'))

if __name__=='__main__':unittest.main()
