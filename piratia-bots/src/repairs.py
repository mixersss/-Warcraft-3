"""Paid native repair: live NPC menu, server quote, unchanged item and real deltas.

Classic CS_ItemRepairAsk/Answer:23(II BB),24(B); SC:544(string,I),546().
Source protocol audit is not a live Windows validation.
"""
import math,struct
from classic_wire import Reader
from adventure import talk_request
from town import function_request
from owner_shops import npc_near

def fingerprint(item):
    if isinstance(item,dict):return tuple(item.get(k) for k in ('identity','parameters','instance_attributes','forge','max_endurance'))
    return item.identity,tuple(item.parameters),tuple(item.instance_attributes),item.forge,item.max_endurance

class Repairs:
    def __init__(self,world,npcs,gear,send):
        self.world,self.npcs,self.gear,self.send=world,npcs,gear,send
        self.context=None;self.pending=None;self.target=None;self.candidate=None;self.failed={};self.next_try=0
        self.reason='';self.requests=self.confirmed=self.refused=self.timeouts=0;self.last_quote=None
    @property
    def busy(self):return self.context is not None or self.pending is not None
    def item(self,key):
        kind,slot=key
        return self.world.own.equipment_details.get(slot) if kind==1 else self.world.bag.get(slot)
    def candidates(self):
        w=self.world;result=[];job=w.own.values.get(4)
        essential={3,4} if job in (2,12) else {9} if job in (5,13,14) else {1,7} if job in (4,16) else {1,2}
        if not w.bag_ready or w.bag_disabled:return []
        for kind,rows in ((1,w.own.equipment_details),(2,w.bag)):
            for slot,item in rows.items():
                get=item.get if isinstance(item,dict) else lambda k,d=None:getattr(item,k,d)
                identity=get('identity');meta=self.gear.gear.get(identity)
                maximum=get('max_endurance',0);endurance=get('endurance',maximum)
                if not meta or meta['kind'] not in (1,2,3,4,7,11,20,22,23,24,27,9) or maximum<=2500 or endurance>=maximum or not self.gear.compatible(w.own,identity):continue
                if get('valid',True) and endurance>max(50,maximum//5):continue
                if kind==2 and meta['kind'] not in essential and not self.gear.upgrade(w.own,identity):continue
                result.append(((meta['kind'] not in essential,get('valid',True),kind,endurance/max(1,maximum),slot),(kind,slot)))
        return [key for _,key in sorted(result)]
    def finish(self,now,reason='',failed=False):
        if failed and self.target:self.failed[self.target['key']]=now+60
        self.context=self.pending=self.target=self.candidate=None;self.next_try=now+(15 if failed else 0);self.reason=reason
    def observe(self,command,payload,now):
        if not self.context:return False
        npc,stage,deadline=self.context
        if command==802 and stage=='talk':
            r=Reader(payload);source,page=r.long(),r.byte();r.string_bytes();count=r.byte()
            if source!=npc:return False
            if count>64:self.finish(now,'неподдерживаемое меню ремонта',True);return True
            labels=[r.string() for _ in range(count)]
            index=next((i for i,s in enumerate(labels) if s.strip().casefold() in ('repair','ремонт','починить','ремонт снаряжения')),None)
            if index is None:self.finish(now,'у НПС нет доступной функции ремонта',True);return True
            self.send(301,function_request(npc,page,index));self.context=npc,'open',now+8;return True
        if command==546 and stage=='open':
            r=Reader(payload);r.end();self.context=npc,'ready',now+8;return True
        if command==544 and stage=='quote':
            r=Reader(payload);r.string_bytes();price=r.long();r.end();self.last_quote=price
            item=self.item(self.candidate['key']);cash=self.world.own.values.get(8,0)
            accept=bool(item and fingerprint(item)==self.candidate['fingerprint'] and 0<price<=max(0,cash-100))
            self.send(24,bytes([int(accept)]))
            if not accept:self.refused+=1;self.finish(now,'ремонт отложен: изменилась вещь или не хватает заработанных денег',True)
            else:self.pending=dict(self.candidate,cash=cash,price=price,deadline=now+12);self.context=npc,'confirm',now+12
            return True
        return False
    def tick(self,now,policy,safe=True):
        w=self.world
        if self.pending:
            p=self.pending;item=self.item(p['key']);get=item.get if isinstance(item,dict) else lambda k,d=None:getattr(item,k,d)
            if (item and fingerprint(item)==p['fingerprint'] and get('valid',False) and get('endurance',0)>p['endurance']
                    and w.own.values.get(8,p['cash'])==p['cash']-p['price']):
                self.confirmed+=1;self.finish(now,'ремонт подтверждён: прочность восстановлена, золото списано')
            elif now>=p['deadline']:self.timeouts+=1;self.finish(now,'сервер не подтвердил ремонт; вещи сохранены',True)
            return self.busy
        if self.context:
            npc,stage,deadline=self.context
            if now>=deadline:
                if stage=='quote':self.send(24,b'\x00')
                self.timeouts+=1;self.finish(now,'истекло ожидание ремонта',True);return False
            if stage=='ready':
                item=self.item(self.candidate['key']);actor=w.entities.get(npc)
                if not item or fingerprint(item)!=self.candidate['fingerprint'] or not actor or math.dist(actor.position,w.position(now))>250:
                    self.finish(now,'предмет или мастер изменился',True);return False
                self.send(23,struct.pack('>IIBB',actor.identity,actor.handle,*self.candidate['key']))
                self.requests+=1;self.context=npc,'quote',now+8
            return True
        if not safe or now<self.next_try or not self.npcs:return False
        choices=self.candidates()
        if not choices:return False
        if w.own.values.get(8,0)<=101:self.reason='ремонту нужны заработанные деньги';return False
        if not self.target:
            shops=[n for n in self.npcs.by_service.get('repair',()) if n['map']==w.map and self.failed.get(n['key'],0)<=now]
            if not shops:self.reason='на текущей карте нет подтверждённого мастера ремонта';return False
            self.target=min(shops,key=lambda n:math.dist(policy.position(now),n['position']))
        point=self.target['position'];actor=npc_near(w,point);self.reason='идёт чинить классовое оружие и изношенную экипировку'
        if actor and math.dist(actor.position,policy.position(now))<=220:
            key=choices[0];item=self.item(key);get=item.get if isinstance(item,dict) else lambda k,d=None:getattr(item,k,d)
            self.candidate={'key':key,'fingerprint':fingerprint(item),'endurance':get('endurance',0)}
            self.send(301,talk_request(actor.identity));self.context=actor.identity,'talk',now+8;return True
        for dx,dy in ((-150,0),(0,-150),(150,0),(0,150)):
            goal=policy.nav.nearest((point[0]+dx,point[1]+dy),2)
            if goal and math.dist(goal,point)<=220 and policy.move_to(goal,now):return True
        self.finish(now,'ищет другого доступного мастера ремонта',True);return False
    def summary(self):return {'state':self.reason,'repair_requests':self.requests,'confirmed_repairs':self.confirmed,'refused_quotes':self.refused,'timeouts':self.timeouts,'last_native_quote':self.last_quote,'pending':self.busy,'damaged_slots':[list(k) for k in self.candidates()]}
