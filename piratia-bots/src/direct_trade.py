"""Classic player trade with exact quotes, native locks and authoritative settlement.

Based on public RoleCommon/PacketCmd_{CS,SC}; Windows owner-version validation
is still required. Unknown item layouts cancel the exchange rather than approve it.
"""
import math,struct
from classic_wire import Reader,ProtocolError
from inventory import BagItem
from bank import fingerprint,quantity

REQUEST,ACCEPT,REJECT,CANCEL,ITEM,LOCK,VALIDATE,MONEY=range(312,320)

def peer_request(identity):
    if not 0<identity<2**32:raise ValueError('Invalid trade peer')
    return struct.pack('>BI',0,identity)

def item_request(peer,slot,count):
    if not 0<=slot<256 or not 1<=count<=99:raise ValueError('Invalid quoted item')
    return peer_request(peer)+struct.pack('>BBBB',4,0,slot,count)

def money_request(peer,amount,modern=False):
    if not 0<amount<=2000000000:raise ValueError('Invalid trade gold')
    return peer_request(peer)+bytes([6])+(b'\0' if modern else b'')+struct.pack('>I',amount)

def read_item(payload):
    r=Reader(payload);actor,operation=r.long(),r.byte()
    if operation==3:
        bag_slot,grid,count=r.byte(),r.byte(),r.byte();r.end()
        if grid>=18:raise ProtocolError('Invalid trade grid')
        return actor,grid,None
    if operation!=4:raise ProtocolError('Unsupported trade item operation')
    identity,bag_slot,grid,count,kind=r.short(),r.byte(),r.byte(),r.byte(),r.short()
    if not identity or not 1<=count<=99 or grid>=18 or kind==43:raise ProtocolError('Unsupported trade item')
    endurance,maximum,energy,maxenergy=[r.short() for _ in range(4)]
    forge,valid=r.byte(),r.byte()
    if valid not in (0,1):raise ProtocolError('Invalid trade item validity')
    parameters=(r.long(),r.long());instance=r.byte()
    if instance not in (0,1):raise ProtocolError('Unsupported classic trade instance')
    attributes=tuple((r.short(),r.short()) for _ in range(5)) if instance else ()
    r.end()
    return actor,grid,BagItem(identity,count,endurance,maximum,energy,maxenergy,forge,bool(valid),parameters,attributes)

class DirectTrade:
    def __init__(self,world,send):
        self.world,self.send=world,send
        self.quotes={};self.peer=None;self.quote=None;self.state='idle';self.deadline=0
        self.offers={};self.money={};self.locks=set();self.sent_lock=False;self.sent_final=False
        self.baseline=None;self.success_notice=False;self.modern_money=False
        self.requests=self.confirmed=self.cancelled=self.unsupported=self.timeouts=0
        self.reason='';self.policy=None
        self.notify=None;self.notified={};self.clock=0

    def notify_peer(self,identity,text):
        peer=self.world.entities.get(identity)
        if not self.notify or not peer or self.notified.get(identity,0)>self.clock:return
        self.notified={k:v for k,v in self.notified.items() if v>self.clock}
        self.notified[identity]=self.clock+5;self.notify(peer.name,text,self.clock)

    @property
    def busy(self):return self.state!='idle'

    def quote_item(self,name,item,count,price,mode,now):
        if mode not in ('buy','sell') or not item.valid or not 1<=count<=99 or not 0<price<=2000000000:
            raise ValueError('Invalid trade quote')
        self.quotes={k:q for k,q in self.quotes.items() if q['until']>now}
        if len(self.quotes)>=64:self.quotes.pop(next(iter(self.quotes)))
        quote={'item':item,'count':count,'price':price,'mode':mode,'until':now+180}
        self.quotes[name.casefold()]=quote
        return quote

    def visible_peer(self,identity,now):
        w=self.world;peer=w.entities.get(identity)
        return peer if (peer and peer.control==1 and peer.identity!=w.own_id and peer.alive
                        and math.dist(w.position(now),w.position(now,identity))<=300) else None

    def reset(self):
        self.peer=None;self.quote=None;self.state='idle';self.offers={};self.money={}
        self.locks=set();self.sent_lock=self.sent_final=self.success_notice=False;self.baseline=None;self.reason=''

    def cancel(self,reason='сделка отменена'):
        if self.peer:
            self.send(CANCEL,peer_request(self.peer));self.notify_peer(self.peer,reason)
        self.cancelled+=1;self.reset();self.reason=reason

    def observe(self,command,payload,now,policy):
        self.clock=now
        self.policy=policy
        try:
            if command==811:
                r=Reader(payload);command=r.short();payload=r.take(len(r.data)-r.position)
                if command not in range(812,820):raise ProtocolError('Unknown trade subcommand')
            self._observe(command,payload,now,policy)
        except (ProtocolError,ValueError,KeyError):
            self.unsupported+=1
            if self.busy:self.cancel('неподдерживаемые данные торговли')

    def _observe(self,command,payload,now,policy):
        r=Reader(payload);w=self.world
        if command==812:
            kind,identity=r.byte(),r.long();r.end();peer=self.visible_peer(identity,now)
            quote=self.quotes.get(peer.name.casefold()) if peer else None
            blocked=any(getattr(feature,'context',None) or getattr(feature,'pending',None)
                        for feature in (getattr(policy,n,None) for n in
                            ('adventure','town','career','story','vendor','bank','equipment','skills','chests')) if feature)
            enemy=w.entities.get(getattr(policy,'target',None))
            in_combat=bool(enemy and enemy.alive and enemy.control==5)
            if (kind or self.busy or not quote or quote['until']<=now or blocked
                or (policy.market and policy.market.busy) or (policy.bank and policy.bank.busy)
                or not w.own.alive or in_combat or w.own.values.get(1,0)<w.own.values.get(31,1)*.55
                or not w.bag_ready or w.bag_disabled):
                self.notify_peer(identity,'Сейчас занят; согласуй товар и цену, затем повтори «Торговать».' if blocked or in_combat else
                                 'Сначала согласуем товар и цену в чате; затем открой «Торговать».')
                return # The classic client ignores an unaccepted invitation.
            self.peer=identity;self.quote=quote;self.state='opening';self.deadline=now+15
            policy.pending_action=None
            if getattr(policy,'action_open',False):policy.stop_action()
            self.send(ACCEPT,peer_request(identity));self.requests+=1;return
        if not self.busy:return
        if command==815:
            kind,acceptor,requester=r.byte(),r.long(),r.long();r.end()
            if kind or {acceptor,requester}!={self.peer,w.own_id}:raise ProtocolError('Trade page peer mismatch')
            if not self.visible_peer(self.peer,now):self.cancel();return
            self.state='open';self.deadline=now+90;self.reason='проверяет условия личной сделки'
            self.offers={w.own_id:{},self.peer:{}};self.money={w.own_id:0,self.peer:0}
            q=self.quote;item=q['item'];count=q['count'];key=fingerprint(item)
            self.baseline=(quantity(w.bag,key),w.own.values.get(8,0),key)
            if q['mode']=='sell':
                slot=next((s for s,i in w.bag.items() if fingerprint(i)==key and i.count>=count),None)
                if slot is None:self.cancel('оговорённой вещи уже нет в сумке');return
                # Recheck quest/upgrade protections at the time of accepting the real window.
                available=policy.market.offers(policy) if policy.market else []
                if not any(s==slot and n>=count for _,_,n,s in available):self.cancel('эта вещь нужна самому боту');return
                self.send(ITEM,item_request(self.peer,slot,count))
            return
        if command==813:
            actor=r.long();r.end()
            if actor in (self.peer,w.own_id):self.reset()
        elif command==814:
            actor,grid,item=read_item(payload)
            if actor not in self.offers:raise ProtocolError('Unexpected trade actor')
            if self.sent_lock:self.cancel('товар изменился после проверки');return
            if item is None:self.offers[actor].pop(grid,None)
            else:
                if self.quote['mode']=='buy' and actor==self.peer and (item.identity!=self.quote['item'].identity
                    or item.count!=self.quote['count'] or not item.valid or item.forge or any(item.parameters)
                    or any(a or b for a,b in item.instance_attributes)
                    or item.max_endurance and not item.endurance):
                    self.cancel('Эта вещь отличается от согласованной; такую покупку не подтверждаю.');return
                if (self.quote['mode']=='buy' and actor==self.peer and item.identity==self.quote['item'].identity
                    and item.count==self.quote['count'] and item.valid and not item.forge
                    and not any(item.parameters) and not any(a or b for a,b in item.instance_attributes)):
                    self.quote['item']=item
                    self.baseline=(quantity(w.bag,fingerprint(item)),self.baseline[1],fingerprint(item))
                self.offers[actor][grid]=item
            self.locks.clear()
        elif command==819:
            actor,amount=r.long(),r.long()
            if len(payload)==9:
                if r.byte()!=0:raise ProtocolError('Unsupported trade currency')
                self.modern_money=True
            elif len(payload)!=8:raise ProtocolError('Unsupported trade money layout')
            r.end()
            if actor not in self.money or amount>2000000000:raise ProtocolError('Invalid trade wallet')
            if self.sent_lock and self.money[actor]!=amount:self.cancel('цена изменилась после проверки');return
            self.money[actor]=amount;self.locks.clear()
            if self.state=='funding' and actor==w.own_id:self.state='open'
        elif command==816:
            actor=r.long();r.end()
            if actor not in (w.own_id,self.peer):raise ProtocolError('Invalid trade lock')
            self.locks.add(actor)
        elif command==817:
            actor=r.long();r.end()
            if actor not in (w.own_id,self.peer):raise ProtocolError('Invalid final actor')
        elif command==818:
            result=r.byte();r.end()
            if result!=7:self.reset();return
            if not self.sent_final:raise ProtocolError('Unsolicited trade success')
            self.success_notice=True;self.state='settling';self.deadline=now+15

    def exact_offer(self):
        if not self.quote or not self.baseline:return False
        w=self.world;q=self.quote
        seller=w.own_id if q['mode']=='sell' else self.peer
        buyer=self.peer if q['mode']=='sell' else w.own_id
        items=list(self.offers.get(seller,{}).values())
        return (len(items)==1 and fingerprint(items[0])==self.baseline[2] and items[0].count==q['count']
                and not self.offers.get(buyer) and self.money.get(seller,0)==0
                and self.money.get(buyer)==q['price'])

    def tick(self,now,policy):
        self.clock=now
        if not self.busy:return False
        w=self.world
        if not w.own.alive or not self.visible_peer(self.peer,now) or w.bag_disabled:
            self.cancel('участник сделки недоступен');return False
        if now>=self.deadline:
            self.timeouts+=1;self.cancel('время ожидания сделки истекло');return False
        if self.state=='settling':
            count,gold,key=self.baseline;q=self.quote;direction=1 if q['mode']=='sell' else -1
            if quantity(w.bag,key)==count-direction*q['count'] and w.own.values.get(8)==gold+direction*q['price']:
                if policy.market:policy.market.catalog.confirmed_price(q['item'].identity,q['price']//q['count'])
                self.notify_peer(self.peer,f"Сделка подтверждена: ID{q['item'].identity} за {q['price']}G. Спасибо.")
                self.confirmed+=1;self.reset()
            return True
        if self.state!='open':return True
        q=self.quote
        if q['mode']=='buy' and self.money.get(w.own_id,0)==0:
            items=list(self.offers.get(self.peer,{}).values())
            if len(items)==1 and fingerprint(items[0])==fingerprint(q['item']) and items[0].count==q['count']:
                if w.own.values.get(8,0)<q['price']+100 or (w.bag_capacity or 0)-len(w.bag)<2:
                    self.cancel('недостаточно денег или места');return False
                # Authoritative peer item reveals whether this connection is still classic.
                self.send(MONEY,money_request(self.peer,q['price'],self.modern_money));self.state='funding'
                return True
        if self.exact_offer():
            if not self.sent_lock:
                self.send(LOCK,peer_request(self.peer));self.sent_lock=True
            # Classic ValidateItemData notifies only the OTHER participant.
            # Our lock is a sent request; ValidateTrade enforces it on the server.
            elif self.peer in self.locks and not self.sent_final:
                self.send(VALIDATE,peer_request(self.peer));self.sent_final=True
        return True

    def summary(self):
        return {'state':self.state,'peer':self.peer,'requests':self.requests,'confirmed_trades':self.confirmed,
                'reason':self.reason,
                'cancelled':self.cancelled,'unsupported_packets':self.unsupported,'timeouts':self.timeouts,
                'own_lock_requested':self.sent_lock,'peer_lock_confirmed':self.peer in self.locks,
                'settlement_notice':self.success_notice}
