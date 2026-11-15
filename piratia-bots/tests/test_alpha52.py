"""Slow-AI network servicing, contextual LFG, finite social scenes and useful trade."""
import copy,dataclasses,json,socket,struct,sys,tempfile,threading,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from classic_wire import Wire,Reader,string
from headless import Client,Report
from network_pump import NetworkPump
from fleet import Fleet
from diagnostic_io import write_snapshot
from connection_watchdog import ConnectionWatchdog
from chat_adapter import message_parts
from social_scenes import SocialBotCoordinator
import test_dialogue50 as dialogue
import test_market as markets
import test_pet_economy as pets
import test_alpha44 as scheduling
from inventory import BagItem

class Network52Tests(unittest.TestCase):
    def pair(self,**limits):
        a,b=socket.socketpair();self.addCleanup(a.close);self.addCleanup(b.close)
        client=Client(a,Report());client.wire.header_size=2
        server=Wire(b);server.header_size=2
        pump=NetworkPump(client,**limits).start();self.addCleanup(pump.close)
        return client,server,pump
    def test_ping_answers_do_not_wait_for_ai_consumption(self):
        client,server,pump=self.pair()
        server.send(501,b'pending world update');server.send(537)
        self.assertEqual(server.receive(time.monotonic()+1),(17,b''))
        self.assertEqual(pump.queue.qsize(),1)
        # Game ping uses exactly its native five uint32 values.
        payload=struct.pack('>5I',1,2,3,4,5);server.send(515,payload)
        self.assertEqual(server.receive(time.monotonic()+1),(15,payload))
        self.assertEqual(pump.receive(time.monotonic()+1),(501,b'pending world update'))
        deadline=time.monotonic()+1
        while pump.pings<2 and time.monotonic()<deadline:time.sleep(.001)
        self.assertEqual(pump.pings,2)
    def test_world_packets_preserve_order_without_background_world_mutations(self):
        client,server,pump=self.pair();handler=Mock();client.world_handler=handler
        for i in range(30):server.send(508,struct.pack('>I',i))
        messages=[pump.receive(time.monotonic()+1) for _ in range(30)]
        self.assertEqual(messages,[(508,struct.pack('>I',i)) for i in range(30)]);handler.assert_not_called()
        for command,payload in messages:client.service(command,payload)
        self.assertEqual(handler.call_count,30)
    def test_overflow_reconnects_instead_of_dropping_inventory_events(self):
        client,server,pump=self.pair(max_packets=1,max_bytes=16)
        server.send(508,b'one');server.send(508,b'two')
        deadline=time.monotonic()+1
        while pump.error is None and time.monotonic()<deadline:time.sleep(.005)
        with self.assertRaises(ConnectionError):pump.receive(time.monotonic()+1)
        self.assertEqual(pump.queue.qsize(),1)
    def test_concurrent_ping_and_actions_keep_encryption_serial(self):
        client,server,pump=self.pair()
        class Encryption:
            def __init__(self):self.counter=0
            def encrypt(self,body):
                value=self.counter;time.sleep(.0002);self.counter+=1;return struct.pack('>H',value)+body
        class Decryption:
            def __init__(self):self.counter=0
            def decrypt(self,body):
                value=struct.unpack('>H',body[:2])[0]
                if value!=self.counter:raise AssertionError('Cipher order broken')
                self.counter+=1;return body[2:]
        client.wire.out_cipher=Encryption();server.in_cipher=Decryption()
        thread=threading.Thread(target=lambda:[client.wire.send(6,bytes([i])) for i in range(40)])
        thread.start();server.send(537)
        messages=[server.receive(time.monotonic()+2) for _ in range(41)];thread.join(1)
        self.assertEqual(sum(c==17 for c,p in messages),1);self.assertEqual(sum(c==6 for c,p in messages),40)
    def test_diagnostic_file_lock_cannot_disconnect_bots_or_corrupt_old_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'report.json';path.write_text('{"old":true}')
            report=Report();fleet=Fleet(400,Path(d)/'population-status.json');fleet.update(1,connected=True)
            with patch('diagnostic_io.os.replace',side_effect=PermissionError('locked')):
                self.assertFalse(report.write(path));self.assertEqual(fleet.write()['connected'],1)
            self.assertEqual(json.loads(path.read_text()),{'old':True});self.assertEqual(report.result['diagnostic_write_failures'],1)
            self.assertTrue(report.write(path));self.assertEqual(json.loads(path.read_text())['diagnostic_write_failures'],1)
            self.assertEqual(fleet.snapshot()['connected'],1)
    def test_silence_watchdog_requires_own_actions_and_no_pending_bytes(self):
        watch=ConnectionWatchdog();wire=SimpleNamespace(last_receive_at=10,buffer=bytearray())
        self.assertFalse(watch.expired(11,wire,0));self.assertFalse(watch.expired(200,wire,0))
        wire.buffer.extend(b'x');self.assertFalse(watch.expired(200,wire,5));wire.buffer.clear()
        self.assertTrue(watch.expired(200,wire,5));wire.last_receive_at=201;self.assertFalse(watch.expired(202,wire,6))
    def test_protocol_retry_budget_resets_only_after_long_successful_session(self):
        from auto_bots import run_bot
        stop=Mock();stop.is_set.return_value=False;stop.wait.return_value=False
        failure=lambda seconds:(False,{'entered_world':True,'exit_reason':'protocol_or_state_error','error_type':'ProtocolError','session_elapsed_seconds':seconds})
        with tempfile.TemporaryDirectory() as d,patch('auto_bots._run_bot_once',side_effect=[failure(1)]*3+[failure(600), (True,{})]) as once:
            self.assertTrue(run_bot(1,{'preserve_existing':True},1973,0,stop,Path(d)));self.assertEqual(once.call_count,5)

class Context52Tests(unittest.TestCase):
    def make(self):
        w,p,s,public,c,send,a=dialogue.fixture()
        p.party=SimpleNamespace(members=(),invites=0,pending=None,humans=set())
        def invite(name,now):p.party.invites+=1;return 'Приглашение в пати отправлено. Подтверди его в игре.'
        p.party.request_name=invite
        return w,p,c,send,a
    def echo_offer(self,a,now=10):
        a.observe(*dialogue.incoming('world',a.name,'Ищу пати на кач, 20 ур. Кто рядом — пишите в ЛС!'),now)
    def test_nearby_reply_binds_actual_offer_then_acceptance_invites_natively(self):
        w,p,c,send,a=self.make();w.entities[2].values={0:21};self.echo_offer(a)
        a.observe(*dialogue.incoming('private','Player','я рядом',a.name),11)
        ctx=a.memory.context('private',w.map,'Player',11);self.assertEqual(ctx['party_dialogue']['stage'],'ready')
        self.assertIn('Пригласить',a.queue[0]['text']);self.assertEqual(p.party.invites,0)
        a.observe(*dialogue.incoming('private','Player','да',a.name),12);self.assertEqual(p.party.invites,1)
        a.observe(*dialogue.incoming('private','Player','да',a.name),13);self.assertEqual(p.party.invites,1)
        self.assertEqual(ctx['promises'][0]['state'],'requested')
    def test_unseen_reply_asks_level_then_map_without_faking_visibility(self):
        w,p,c,send,a=self.make();w.entities.pop(2);self.echo_offer(a)
        a.observe(*dialogue.incoming('private','Player','я рядом',a.name),11)
        ctx=a.memory.context('private',w.map,'Player',11);self.assertEqual(ctx['party_dialogue']['stage'],'level')
        a.observe(*dialogue.incoming('private','Player','21',a.name),12);self.assertEqual(ctx['party_dialogue']['stage'],'location')
        w.map='darkblue';a.observe(*dialogue.incoming('private','Player','ледынь',a.name),13);self.assertEqual(ctx['party_dialogue']['stage'],'ready')
        self.assertEqual(p.party.invites,0)
    def test_public_lfg_response_selects_origin_and_replies_privately_even_when_poor(self):
        c=dialogue.BotCoordinator(dialogue.DATA.settings);one=dialogue.fixture(coordinator=c);two=dialogue.fixture(name='Bot99999999',coordinator=c,identity=3)
        a,b=one[-1],two[-1];a.world.own.values[8]=1000;a.register(10);b.register(10);self.echo_offer(a)
        for adapter in (a,b):adapter.observe(*dialogue.incoming('world','Player','я рядом'),11)
        self.assertEqual(len(b.queue),0);self.assertEqual(a.queue[0]['channel'],'private');self.assertNotIn('Не понял',a.queue[0]['text'])
    def test_recent_offer_does_not_hijack_price_question_or_negated_invitation(self):
        w,p,c,send,a=self.make();self.echo_offer(a)
        a.observe(*dialogue.incoming('private','Player','какая цена',a.name),11)
        ctx=a.memory.context('private',w.map,'Player',11);self.assertNotIn('party_dialogue',ctx)
        a.observe(*dialogue.incoming('private','Player','не приглашай в пати',a.name),12);self.assertEqual(p.party.invites,0)
    def test_expired_offer_is_not_reused_by_an_unrelated_player(self):
        w,p,c,send,a=self.make();self.echo_offer(a);self.assertIsNone(c.recent_offer(a.name,'private',w.map,'я рядом',200))
    def test_answer_to_own_public_level_question_has_context(self):
        w,p,c,send,a=self.make();a.observe(*dialogue.incoming('world',a.name,'Кто какого уровня сейчас?'),10)
        a.observe(*dialogue.incoming('world','Player','21'),11)
        ctx=a.memory.context('private',w.map,'Player',11);self.assertEqual(ctx['level'],21)
        self.assertIn('У тебя 21',a.queue[0]['text'])
    def test_humour_accepts_laughter_negative_feedback_and_a_player_joke(self):
        w,p,c,send,a=self.make()
        for now,text in enumerate(('пошути','ахаха','не смешно','хочешь шутку','Последняя ячейка сумки снова победила'),10):
            a.observe(*dialogue.incoming('private','Player',text,a.name),now)
        self.assertEqual(a.intents['joke_negative'],1)
        self.assertTrue(any(word in a.queue[-1]['text'].casefold() for word in ('ах','хах','шут','смеш','улыб','понял','зацеп','ха','попыт','заход','такое','натян','любител','концов','раз','стран','неожидан')))
    def test_reply_parts_keep_native120byte_limit_and_context(self):
        text='Первое предложение объясняет текущую задачу и её условия. '+'Второе предложение добавляет полезные подробности. '*3
        parts=message_parts(text,230);self.assertEqual(len(parts),2);self.assertTrue(all(len(p.encode('cp1251'))<=120 for p in parts))
        w,p,c,send,a=self.make();a.profile.values['max_bytes']=230;ctx=a.memory.context('private',w.map,'Player',0)
        a.enqueue('private','Player',text,1,context=ctx);a.tick(5);a.tick(9)
        self.assertEqual(send.call_count,2);self.assertEqual(ctx['last_reply'],' '.join(parts))
    def test_authored_reply_variation_does_not_repeat_one_longest_answer(self):
        w,p,c,send,a=self.make();a.profile.values['id']='helper'
        variants={a.selector.select('greeting',a.state()) for _ in range(30)}
        self.assertGreaterEqual(len(variants),5);self.assertGreaterEqual(dialogue.DATA.summary()['authored_conversation_lines'],800)

class Scenes52Tests(unittest.TestCase):
    def setup_scene(self,count=4):
        c=SocialBotCoordinator(dialogue.DATA.settings,dialogue.DATA.scenes)
        for i in range(count):c.register(f'Bot{i:08x}',{'identity':i+10,'map':'garner','position':(0,0),'visible':set(range(10,20)),'ready':True,'cash':0,'until':500})
        c.area_delays[('garner',0,0)]=0;return c
    def test_two_round_scene_advances_only_on_exact_native_echo_and_finishes(self):
        c=self.setup_scene();s=c.start('Bot00000000',2);self.assertIsNotNone(s)
        self.assertIsNone(c.scene_for(s['receiver'],s['channel'],s['sender'],s['text'],3))
        count=0
        while c.scenes:
            count+=1;self.assertLessEqual(count,8);s=dict(next(iter(c.scenes.values())))
            c.sent(s['id'],s['sender'],s['text']);result=c.scene_for(s['receiver'],s['channel'],s['sender'],s['text'],4+count)
            if not result['finish']:c.prepare_scene_reply(s['id'],'Новый ответ '+str(count))
        self.assertGreaterEqual(count,4)
    def test_three_distant_scenes_do_not_reuse_speakers_and_human_interrupt_is_local(self):
        c=SocialBotCoordinator(dialogue.DATA.settings,dialogue.DATA.scenes)
        for area in range(4):
            for i in range(2):
                identity=area*2+i+10;c.register(f'Bot{identity:08x}',{'identity':identity,'map':'garner','position':(area*10000,0),'visible':{area*2+10,area*2+11},'ready':True,'cash':0,'until':500})
            c.area_delays[('garner',area*10000//3000,0)]=0
        for area in range(4):c.start(f'Bot{area*2+10:08x}',10+area*6)
        self.assertEqual(len(c.scenes),3);members=[n for s in c.scenes.values() for n in s['members']];self.assertEqual(len(members),len(set(members)))
        winner=next(n for n in c.rows if c.elect(n,'local','garner','Player','привет',40,{10,11}))
        self.assertTrue(winner);self.assertEqual(len(c.scenes),2)
    def test_quiet_mode_does_not_start_background_conversations(self):
        c=self.setup_scene();c.settings=dict(c.settings,intensity='quiet');self.assertIsNone(c.start('Bot00000000',10))

class TradeAndPet52Tests(unittest.TestCase):
    def market(self):
        w,send,m,p=markets.MarketTests().make();m.broad_goods=m.focused_goods=True;m.catalog.enable_broad_catalog();return w,send,m,p
    def test_audited_development_material_and_rune_are_saleable_but_patchouli_is_not(self):
        w,send,m,p=self.market();w.bag={0:pets.item(1640,10),1:pets.item(3388,10),2:pets.item(3425,20),3:pets.item(1000,28)}
        offered={w.bag[slot].identity for _,_,_,slot in m.offers(p)}
        self.assertIn(1640,offered);self.assertIn(3388,offered);self.assertIn(3425,offered);self.assertNotIn(1000,offered)
    def test_same_id_spare_gear_can_sell_without_selling_equipped_instance(self):
        w,send,m,p=self.market();identity=next(i for i,g in m.gear.gear.items() if g['kind']==22 and i in m.catalog.items and 1 in g['bodies'])
        w.own.equipment={2:identity};m.useful_gear=Mock(return_value=False);w.bag={0:pets.item(identity)}
        self.assertTrue(m.offers(p));self.assertEqual(w.own.equipment[2],identity)
        w.bag[0]=dataclasses.replace(w.bag[0],forge=1);self.assertEqual(m.offers(p),[])
    def test_native_shop_reference_prevents_basic_gem_at_ten_times_shop_price(self):
        w,send,m,p=self.market();m.catalog.npc_purchase_prices[885]=5000;m.catalog.owner_price_floor[885]=3750
        self.assertGreaterEqual(m.catalog.price(885),3750);self.assertLessEqual(m.catalog.price(885),4750)
    def test_market_directory_can_offer120_spaced_argent_leases(self):
        from market import MarketDirectory
        directory=MarketDirectory(live_count=lambda now:400,argent_target=120)
        self.assertEqual(len({directory.reserve(str(i),'garner',1) for i in range(120)}),120)
        self.assertIsNone(directory.reserve('extra','garner',1))
    def test_fairy_purchase_reserves_money_for_food_and_all_builds_have_goal(self):
        from builds import PROFILES
        for key,record in PROFILES.items():
            w,c,p=pets.FairyTests().make();w.own.build_id=key;c=pets.PetCare(w,c.life,c.mechanics,key,{'target_job':record['job']})
            self.assertTrue(c.summary()['goal_applies_to_every_bot'])
        w,c,p=pets.FairyTests().make();c.life=copy.copy(c.life);c.life.owner_shops={'catalog_revision':50,'fresh_fairies':True}
        w.bag={1:pets.item(232,endurance=49)}
        self.assertTrue(c.urgent_hunger());self.assertTrue(c.needs_food_visit())
        self.assertIn((2312,6,'пополняет запас автокорма феи'),c.purchase_goals())
        from town import Town
        from equipment import ItemCatalog
        import random
        town=Town(w,c.life,ItemCatalog(ROOT/'assets/items.json'),None,random.Random(1),(0,0));town.petcare=c
        self.assertEqual(town.critical_items()[0],2312);self.assertEqual(town.choose_want()[0],2312)
        w.bag={};fairy_price=c.life.prices[c.preferred];food_price=c.life.prices[2312]
        w.own.values[8]=fairy_price+2*food_price+99
        self.assertLess(town.spend_limit(c.preferred),fairy_price)
        w.bag[2]=pets.item(2312,2);self.assertGreaterEqual(town.spend_limit(c.preferred),fairy_price)
    def test_existing_mixed_fairy_is_fed_but_not_given_wrong_stat_fruit(self):
        w,c,p=pets.FairyTests().make();w.bag={1:pets.item(232,endurance=49,instance_attributes=((26,2),(28,2))),2:pets.item(2312,3),4:pets.item(276)}
        self.assertTrue(c.tick(1,p));self.assertEqual(p.emit.call_args.args[0][-4:],struct.pack('>hh',2,1))
        self.assertEqual(c.fruit_requests,0)
        w.bag[1]=dataclasses.replace(w.bag[1],endurance=2549);w.bag[2]=dataclasses.replace(w.bag[2],count=2)
        self.assertFalse(c.tick(2,p));self.assertEqual(c.confirmed,1);self.assertIsNone(c.pending)
    def test_stable_equipment_reuses_scan_but_inventory_change_invalidates_it(self):
        from equipment import Equipment,ItemCatalog
        w=pets.scene();w.own.values.update({0:20,4:1});w.bag_ready=True;w.bag_capacity=24;w.bag={}
        e=Equipment(w,ItemCatalog(ROOT/'assets/items.json'),Mock());policy=Mock(sequence=1)
        e.tick(1,policy);e.tick(2,policy);self.assertEqual(e.plan_scans,1);self.assertEqual(e.cached_scans,1)
        w.bag[0]=pets.item(1847);e.tick(3,policy);self.assertEqual(e.plan_scans,2)

if __name__=='__main__':unittest.main()
