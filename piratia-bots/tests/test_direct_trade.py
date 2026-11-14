"""Synthetic classic source-layout exchanges; not a live Windows capture."""
import dataclasses,struct,sys,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from direct_trade import DirectTrade,item_request,money_request,read_item
from commerce import Commerce
from bank import fingerprint
from classic_wire import ProtocolError
import test_market as prior

class DirectTradeTests(unittest.TestCase):
    def make(self,mode='sell'):
        w,s,m,p=prior.MarketTests().make();p.market=m;p.bank=None;p.town=None;p.vendor=None;p.world=w
        item=prior.MarketTests().item(684,3);w.bag={0:item} if mode=='sell' else {}
        human=dataclasses.replace(w.own,identity=77,handle=177,name='Human',x=w.own.x+50)
        w.entities[77]=human;t=DirectTrade(w,s)
        t.quote_item('Human',item,1,5000,mode,10)
        t.observe(812,struct.pack('>BI',0,77),11,p)
        self.assertEqual(t.state,'opening');self.assertEqual(s.call_args.args[0],313)
        t.observe(815,struct.pack('>BII',0,w.own_id,77),12,p)
        return w,s,m,p,t,item

    def item_packet(self,actor,item,count=1):
        return (struct.pack('>IBHBBBH',actor,4,item.identity,0,0,count,41)
                +struct.pack('>4HBB2IB',item.endurance,item.max_endurance,item.energy,item.max_energy,
                             item.forge,int(item.valid),*item.parameters,bool(item.instance_attributes))
                +b''.join(struct.pack('>HH',*a) for a in item.instance_attributes))

    def offered(self,w,p,t,item):
        t.observe(814,self.item_packet(w.own_id,item),13,p)
        t.observe(819,struct.pack('>II',77,5000),14,p)

    def test_seller_adds_only_quoted_owned_item(self):
        w,s,m,p,t,item=self.make()
        self.assertEqual(s.call_args.args,(316,item_request(77,0,1)))
        self.assertEqual(w.bag[0].count,3);self.assertEqual(t.confirmed,0)

    def test_own_lock_request_and_native_peer_lock_allow_server_enforced_final(self):
        w,s,m,p,t,item=self.make();self.offered(w,p,t,item);t.tick(15,p)
        self.assertEqual(s.call_args.args[0],317);self.assertFalse(t.sent_final)
        t.observe(816,struct.pack('>I',77),16,p);t.tick(17,p)
        self.assertEqual(s.call_args.args[0],318);self.assertTrue(t.sent_final)

    def test_server_811_envelope_dispatches_embedded_trade_command(self):
        w,s,m,p,t,item=self.make()
        t.observe(811,struct.pack('>HI',816,77),13,p)
        self.assertIn(77,t.locks)

    def test_success_notice_without_gold_or_bag_change_does_not_count(self):
        w,s,m,p,t,item=self.make();self.offered(w,p,t,item);t.tick(15,p)
        for actor in (w.own_id,77):t.observe(816,struct.pack('>I',actor),16,p)
        t.tick(17,p);t.observe(818,bytes([7]),18,p);t.tick(19,p)
        self.assertEqual(t.confirmed,0)
        w.bag[0]=dataclasses.replace(item,count=2);t.tick(20,p);self.assertEqual(t.confirmed,0)
        w.own.values[8]+=5000;t.tick(21,p);self.assertEqual(t.confirmed,1);self.assertFalse(t.busy)

    def test_item_or_money_swap_after_lock_cancels(self):
        for command in (814,819):
            with self.subTest(command=command):
                w,s,m,p,t,item=self.make();self.offered(w,p,t,item);t.tick(15,p)
                payload=self.item_packet(w.own_id,dataclasses.replace(item,identity=1092)) if command==814 else struct.pack('>II',77,1)
                t.observe(command,payload,16,p)
                self.assertFalse(t.busy);self.assertEqual(s.call_args.args[0],315);self.assertEqual(t.confirmed,0)

    def test_different_item_forge_or_quantity_never_locks(self):
        for changed,count in (({'identity':1092},1),({'forge':1},1),({},2)):
            with self.subTest(changed=changed,count=count):
                w,s,m,p,t,item=self.make();s.reset_mock()
                t.observe(814,self.item_packet(w.own_id,dataclasses.replace(item,**changed),count),13,p)
                t.observe(819,struct.pack('>II',77,5000),14,p);t.tick(15,p)
                s.assert_not_called();self.assertFalse(t.sent_lock)

    def test_underpayment_or_extra_barter_does_not_lock(self):
        for extra in (False,True):
            w,s,m,p,t,item=self.make();self.offered(w,p,t,item)
            if extra:t.observe(814,self.item_packet(77,item),14,p)
            else:t.observe(819,struct.pack('>II',77,4999),14,p)
            s.reset_mock();t.tick(15,p);s.assert_not_called()

    def test_buyer_funds_only_after_verified_item_and_confirms_gold_echo(self):
        w,s,m,p,t,item=self.make('buy')
        t.observe(814,self.item_packet(77,item),13,p);t.tick(14,p)
        self.assertEqual(s.call_args.args,(319,money_request(77,5000)))
        self.assertFalse(t.sent_lock);t.observe(819,struct.pack('>II',w.own_id,5000),15,p);t.tick(16,p)
        self.assertTrue(t.sent_lock)

    def test_insufficient_gold_or_space_cancels_without_spending(self):
        for low_gold in (True,False):
            w,s,m,p,t,item=self.make('buy')
            if low_gold:w.own.values[8]=5000
            else:w.bag_capacity=1
            before=dict(w.own.values);t.observe(814,self.item_packet(77,item),13,p);t.tick(14,p)
            self.assertFalse(t.busy);self.assertEqual(w.own.values,before);self.assertEqual(t.confirmed,0)

    def test_timeout_or_peer_departure_releases_ai(self):
        for timeout in (True,False):
            w,s,m,p,t,item=self.make()
            if not timeout:w.entities.pop(77)
            t.tick(200 if timeout else 14,p);self.assertFalse(t.busy);self.assertEqual(w.bag[0],item)

    def test_malformed_item_and_unsolicited_success_cancel(self):
        for command,payload in ((814,b'\0'),(818,bytes([7]))):
            w,s,m,p,t,item=self.make();t.observe(command,payload,13,p)
            self.assertFalse(t.busy);self.assertEqual(t.unsupported,1);self.assertEqual(t.confirmed,0)

    def test_unknown_or_expired_quote_is_not_accepted(self):
        w,s,m,p,t,item=self.make();t.reset();s.reset_mock()
        t.observe(812,struct.pack('>BI',0,77),1000,p)
        s.assert_not_called();self.assertFalse(t.busy)

    def test_real_fight_is_not_interrupted_by_incoming_trade(self):
        w,s,m,p,t,item=self.make();t.reset();s.reset_mock()
        w.entities[88]=dataclasses.replace(w.own,identity=88,control=5,values={1:100,31:100})
        p.target=88;t.observe(812,struct.pack('>BI',0,77),15,p)
        s.assert_not_called();self.assertFalse(t.busy);self.assertEqual(p.target,88)

    def test_server_failure_and_cancel_do_not_mutate_inventory(self):
        for command,payload in ((818,bytes([8])),(813,struct.pack('>I',77))):
            w,s,m,p,t,item=self.make();before=dict(w.bag);t.observe(command,payload,13,p)
            self.assertFalse(t.busy);self.assertEqual(w.bag,before);self.assertEqual(t.confirmed,0)

    def test_classic_and_explicit_modern_money_encodings_are_separate(self):
        self.assertEqual(money_request(77,5000),struct.pack('>BIBI',0,77,6,5000))
        self.assertEqual(money_request(77,5000,True),struct.pack('>BIBBI',0,77,6,0,5000))


class CommerceTests(unittest.TestCase):
    def make(self):
        w,s,m,p,t,item=DirectTradeTests().make();t.reset();t.quotes.clear()
        return w,m,p,t,Commerce(p,t,m.life,'test')

    def test_quote_has_real_stock_price_and_current_meeting_position(self):
        w,m,p,t,c=self.make();answer=c.answer('Human','продашь новый пергамент?',100)
        self.assertIn('ID684',answer);self.assertIn(str(m.catalog.price(684)),answer)
        q=t.quotes['human'];self.assertEqual(q['item'],w.bag[0]);self.assertEqual(q['count'],1)
        answer=c.answer('Human','как встретимся?',104);self.assertIn('Аргент',answer)

    def test_no_inventory_does_not_create_a_quote(self):
        w,m,p,t,c=self.make();w.bag={}
        self.assertIn('нет',c.answer('Human','продай 684',100));self.assertFalse(t.quotes)

    def test_advertisement_requires_actual_open_stall_and_stock(self):
        w,m,p,t,c=self.make();self.assertIsNone(c.advertisement(100))
        m.state='selling';m.active_confirmed=True;m.stock=[(0,5000,1,0)]
        self.assertIn('ID684',c.advertisement(101));w.bag={};self.assertIsNone(c.advertisement(102))

    def test_general_npc_question_does_not_become_sales_pitch(self):
        w,m,p,t,c=self.make();self.assertIsNone(c.answer('Human','где купить лук?',100))

    def test_trade_chat_closes_stall_only_on_purchase_request(self):
        w,m,p,t,c=self.make();m.state='selling';m.active_confirmed=True
        c.answer('Human','цена 684',100);self.assertEqual(m.state,'selling')
        c.answer('Human','куплю 684',104);self.assertEqual(m.state,'closing')


if __name__=='__main__':unittest.main()
