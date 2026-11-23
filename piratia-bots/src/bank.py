"""Personal vault: live NPC menu, classic kitbag snapshots and two-sided transfer checks.

Public classic EActionType/BeginAction and CPlayer::SynBank document actions26/27.
No local inventory mutations or cached items are treated as server stock.
"""
import math,re,struct
from adventure import talk_request
from classic_wire import Reader,ProtocolError
from town import function_request

BANK,CLOSE_BANK=26,27

def transfer_request(source,slot,count,target,destination):
    if source not in (0,1) or target!=1-source or not 0<=slot<256 or not 0<=destination<256 or not 1<=count<=65535:
        raise ValueError('Invalid bank transfer')
    return struct.pack('>BHHBH',source,slot,count,target,destination)

def fingerprint(item):
    return (item.identity,item.endurance,item.max_endurance,item.energy,item.max_energy,
            item.forge,item.valid,item.parameters,item.instance_attributes)

def quantity(items,key):
    return sum(i.count for i in items.values() if fingerprint(i)==key)

class Bank:
    def __init__(self,world,send,npcs):
        self.world,self.send,self.npcs=world,send,npcs
        self.context=None;self.pending=None;self.deadline=0;self.next_visit=0
        self.state='idle';self.reason='';self.npc=None;self.snapshot_revision=0
        self.mode='deposit';self.patchouli_audit=False;self.patchouli_audited=False;self.deposits=self.withdrawals=self.requests=self.timeouts=0
        self.last_world_map=world.map
        self.trip_started=None;self.progress_at=0;self.last_position=None
        self.inventory_relief=False

    @property
    def busy(self):return self.state!='idle'

    def end(self,now,policy=None):
        if policy and self.state in ('opening','open','transfer'):
            from hunter import action_header
            policy.emit(action_header(self.world.own_id,policy.sequence,CLOSE_BANK))
        self.state='idle';self.context=None;self.pending=None;self.npc=None
        self.next_visit=now+1200;self.reason=''
        self.trip_started=None;self.last_position=None;self.inventory_relief=False

    def candidates(self,policy,items=None):
        market=policy.market
        if not market:return []
        source=self.world.bag if items is None else items
        protected=market.protected(policy);reserved={};result=[]
        stall_stock={slot:count for _,_,count,slot in market.offers(policy)} if items is None and not self.inventory_relief and getattr(market,'keep_stall_stock',False) is True and self.world.own.values.get(0,0)>=getattr(market,'minimum_level',30) else {}
        for slot,item in sorted(source.items()):
            if item.identity==1000:
                if items is not None and item.valid and item.identity not in protected and not item.forge and not any(item.parameters) and not any(a or b for a,b in item.instance_attributes):result.insert(0,(slot,item,item.count))
                continue # Patchouli is NPC cash, never a bank deposit or stall reserve.
            if (not item.valid or item.identity not in market.catalog.items or item.identity in protected
                or item.identity in self.world.own.equipment.values() or market.useful_gear(item.identity)):continue
            reserve=market.reserve_count(item.identity)
            if self.inventory_relief and market.catalog.items[item.identity].get('category')=='gem':
                reserve=max(1,min(2,reserve))
            keep=max(stall_stock.get(slot,0),max(0,reserve-reserved.get(item.identity,0))) if items is None else 0
            reserved[item.identity]=reserved.get(item.identity,0)+min(keep,item.count)
            if item.count>keep:result.append((slot,item,item.count-keep))
        return result

    def observe(self,command,payload,now):
        if command!=802 or not self.context:return False
        r=Reader(payload);npc,page=r.long(),r.byte();r.string_bytes();count=r.byte()
        if count>64:raise ProtocolError('Too many bank NPC functions')
        labels=[r.string() for _ in range(count)]
        if npc!=self.context:return False
        choice=None
        for index,label in enumerate(labels):
            text=label.casefold()
            # The supplied ordinary vaults charge200G; unknown paid services are not selected.
            if (('vault' in text or 'хранилищ' in text or 'банк' in text)
                and '200' in text and not any(int(x)>200 for x in re.findall(r'\d+',text))):
                choice=index;break
        if choice is None:self.end(now);return True
        self.send(301,function_request(npc,page,choice));self.context=None
        self.snapshot_revision=self.world.bank_revision;self.state='opening';self.deadline=now+12
        return True

    def tick(self,now,policy,safe,dialogue_busy=False):
        w=self.world
        if self.last_world_map!=w.map:
            self.end(now);self.last_world_map=w.map
        if self.busy and (not safe or not w.own.alive or w.bank_disabled):
            self.end(now,policy);return False
        if self.state=='talk':
            if now>=self.deadline:self.timeouts+=1;self.end(now)
            return self.busy
        if self.state=='opening':
            if w.bank_ready and w.bank_revision>self.snapshot_revision:
                self.state='open';self.patchouli_audited=True
                if any(i.identity==1000 for _,i,_ in self.candidates(policy,w.bank)):self.mode='withdraw_patchouli'
            elif now>=self.deadline:self.timeouts+=1;self.end(now,policy)
            return self.busy
        if self.pending:
            key,count,bag_before,bank_before,deadline=self.pending
            direction=1 if self.mode=='deposit' else -1
            if (quantity(w.bag,key)==bag_before-direction*count
                and quantity(w.bank,key)==bank_before+direction*count):
                if self.mode=='deposit':self.deposits+=1
                else:self.withdrawals+=1
                self.pending=None;self.state='open'
            elif now>=deadline:self.timeouts+=1;self.end(now,policy)
            return True
        if self.state=='open':
            source=w.bag if self.mode=='deposit' else w.bank
            destination=w.bank if self.mode=='deposit' else w.bag
            capacity=w.bank_capacity if self.mode=='deposit' else w.bag_capacity
            options=self.candidates(policy,None if self.mode=='deposit' else w.bank)
            if self.mode=='withdraw_patchouli':options=[r for r in options if r[1].identity==1000]
            empty=next((s for s in range(capacity or 0) if s not in destination),None)
            if (not options or empty is None or
                (self.mode=='deposit' and self.inventory_relief and (w.bag_capacity or 0)-len(w.bag)>=6) or
                (self.mode=='withdraw' and (w.bag_capacity or 0)-len(w.bag)<=6)):
                self.end(now,policy);return False
            slot,item,count=options[0]
            from hunter import action_header
            policy.emit(action_header(w.own_id,policy.sequence,BANK)+
                transfer_request(0 if self.mode=='deposit' else 1,slot,count,1 if self.mode=='deposit' else 0,empty))
            self.pending=(fingerprint(item),count,quantity(w.bag,fingerprint(item)),quantity(w.bank,fingerprint(item)),now+12)
            self.requests+=1;self.state='transfer';return True
        if (now<self.next_visit or not safe or dialogue_busy or not policy.market or policy.market.busy
            or not w.bag_ready or w.bag_disabled or w.bank_disabled or w.own.values.get(8,0)<300):return False
        free=(w.bag_capacity or 0)-len(w.bag)
        self.inventory_relief=bool(getattr(policy,'fast_progression',False) and free<=1)
        valuables=self.candidates(policy)
        deposit=bool(valuables) and (free<=8 or len(valuables)>=4)
        withdraw=(w.own.values.get(0,0)>=getattr(policy.market,'minimum_level',30) and w.skills.get(241,{}).get('level',0)
                  and policy.market.next_shift is not None and now>=policy.market.next_shift
                  and not policy.market.offers(policy) and free>6)
        recover_patchouli=bool(free>2 and (any(i.identity==1000 for _,i,_ in self.candidates(policy,w.bank))
                              or self.patchouli_audit and not self.patchouli_audited and now-policy.started>=900))
        if recover_patchouli:deposit=False;withdraw=True
        if not deposit and not withdraw:
            self.trip_started=None;self.last_position=None;return False
        banks=[n for n in self.npcs.by_service.get('bank',()) if n['map']==w.map]
        if not banks:return False
        position=policy.position(now)
        if self.trip_started is None:
            self.trip_started=now;self.progress_at=now;self.last_position=position
        if math.dist(position,self.last_position)>=100:self.progress_at=now;self.last_position=position
        if now-self.trip_started>=180 or now-self.progress_at>=35:
            self.trip_started=None;self.last_position=None;self.next_visit=now+120
            self.reason='путь к банку не продвигается; продолжает другие дела';return False
        self.mode='deposit' if deposit else ('withdraw_patchouli' if recover_patchouli else 'withdraw')
        npc=min(banks,key=lambda n:math.dist(policy.position(now),n['position']))
        entity=next((e for e in w.entities.values() if e.control in (2,3) and e.model==npc['model'] and
                     math.dist(e.position,npc['position'])<350),None)
        self.reason='относит ценности в банк' if deposit else 'забирает товар из банка'
        if entity and math.dist(policy.position(now),entity.position)<=220:
            self.send(301,talk_request(entity.identity));self.context=entity.identity
            self.state='talk';self.deadline=now+10;return True
        goal=policy.nav.nearest(npc['position'],6)
        if goal and policy.move_to(goal,now):return True
        self.next_visit=now+120;return False

    def summary(self):
        return {'state':self.state,'reason':self.reason,'mode':self.mode,'requests':self.requests,
                'confirmed_deposits':self.deposits,'confirmed_withdrawals':self.withdrawals,
                'timeouts':self.timeouts,'known_slots':len(self.world.bank),
                'patchouli_never_deposited':True,'patchouli_bank_audited':self.patchouli_audited,'snapshot_ready':self.world.bank_ready,'unsupported':self.world.bank_disabled}
