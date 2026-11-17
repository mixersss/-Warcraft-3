"""Native forge menus/quotes, owned inputs and inventory-confirmed results only."""
from dataclasses import dataclass
import hashlib
import math
import struct
import time
from adventure import talk_request
from classic_wire import Reader,ProtocolError
from inventory import BagItem
from mechanics import forge_parts
from owner_shops import npc_near
from town import function_request

LABELS={1:'Insert gems',2:'Combine gems',3:'Create sockets',4:'Fuse apparel',5:'Strengthen fusion'}
OPEN={1:835,2:836,3:837,4:833,5:834}
GEMS={860,861,862,863,864,865,866,1012}

def request(mode,slots):
    if mode not in LABELS or not 3<=len(slots)<=4 or len(set(slots))!=len(slots) or any(not 0<=s<256 for s in slots):
        raise ValueError('Invalid owned forge inputs')
    return bytes([1,mode])+b''.join(struct.pack('>hhh',1,s,1) for s in slots)+b'\0\0'*(5-len(slots))

def unfix(actor,sequence,link,empty_slot):
    if link not in (0,2,3,4,5,6,7,8,9) or not 0<=empty_slot<256:raise ValueError('Invalid safe bag destination')
    return struct.pack('>IIBBh',actor,sequence,10,link,empty_slot) # Never -1/-2: those can throw the item.

@dataclass
class Operation:
    mode:int
    slots:tuple
    fee:int
    target:int
    before:BagItem
    consumed:tuple
    gem_type:int=0
    source_parameters:tuple=()

class Crafting:
    def __init__(self,world,gear,knowledge,life,economy,send,name):
        self.world,self.gear,self.knowledge,self.life,self.economy,self.send=world,gear,knowledge,life,economy,send
        self.name=name;self.context=None;self.pending=None;self.target=None;self.op=None
        self.retry=0;self.visit_until=0;self.requests=0;self.confirmed=0;self.timeouts=0;self.rejected=0
        self.reason='';self.goals=[];self.demand={};self.required_levels={};self.gem_units_needed={};self.clock=0
        self.is_specialist=int.from_bytes(hashlib.sha256((name+':forge').encode()).digest()[:4],'big')%100<20
    @property
    def busy(self):return bool(self.context or self.pending or self.target)
    def count(self,identity):return sum(i.count for i in self.world.bag.values() if i.identity==identity)
    def slot(self,identity,level=None,exclude=()):
        return next((s for s,i in self.world.bag.items() if i.identity==identity and i.valid and s not in exclude and (level is None or i.max_energy==level)),None)
    def due(self,now):
        return (now>=self.retry and self.world.own.values.get(0,0)>=35
                and self.economy.phase(self.world,now)=='craft')
    def worn(self):
        result=[];w=self.world
        for link,identity in sorted(w.own.equipment.items()):
            details=w.own.equipment_details.get(link,{})
            g=self.gear.effective(identity,details)
            if (not g or details.get('identity')!=identity or details.get('valid') is not True or g['level']<35
                    or g['kind'] not in self.knowledge.data['forgeable_item_kinds']):continue
            item=BagItem(identity,1,details.get('endurance',0),details.get('max_endurance',0),details.get('energy',0),details.get('max_energy',0),details.get('forge',0),True,details.get('parameters',(0,0)),details.get('instance_attributes',()))
            result.append((link,item))
        return sorted(result,key=lambda row:(forge_parts(row[1].parameters[0])['total_level'],row[0]))
    def gem_choices(self,item):
        kind=self.gear.types.get(item.identity);job=self.world.own.values.get(4,0)
        if kind in (1,2,3,4,7,9):choices=(1012,) if job in (4,5,13,14,16) else (863,864)
        elif kind in (11,22,27):choices=(862,865)
        elif kind==23:choices=(861,866) if job in (1,2,8,9,12) else (866,)
        elif kind==24:choices=(860,866) if job in (1,2,9,12) else (866,860)
        else:choices=()
        return tuple(i for i in choices if i in self.knowledge.stone_items and kind in self.knowledge.stone_items[i]['compatible_item_kinds'])
    def apparel(self,item):
        kind=self.gear.types.get(item.identity);own=self.world.own
        stock=next((s for s in (self.life.owner_shops or {}).get('npcs',[]) if s['script_function']=='OwnerClothes'),None)
        candidates=[i for i in (stock or {}).get('offers',[]) if 5000<i<6000 and i in self.gear.gear
                    and self.gear.compatible(own,i) and self.gear.types[i]==kind]
        return min(candidates,key=lambda i:hashlib.sha256(f'{self.name}:{item.identity}:{i}'.encode()).digest(),default=None)
    def propose(self,item,slot):
        """Return a real operation or material goals. Never invent or edit a bag item."""
        self.goals=[];self.demand={};self.required_levels={};self.gem_units_needed={}
        state=forge_parts(item.parameters[0]);cash=self.world.own.values.get(8,0)
        choices=self.gem_choices(item)
        if not choices:return None
        def prepare_gem(identity,level):
            exact=self.slot(identity,level,(slot,))
            if exact is not None:return exact,None
            pieces=[(s,i) for s,i in self.world.bag.items() if i.identity==identity and i.valid and s!=slot and 1<=i.max_energy<level]
            scroll=self.slot(886)
            if level>1:
                for rank in range(level-1,0,-1):
                    pair=[s for s,i in pieces if i.max_energy==rank]
                    if len(pair)>=2:
                        if scroll is None:self.goals.append((886,1,'свиток объединения'));return None,None
                        if cash<52000:return None,None
                        a,b=pair[:2]
                        return None,Operation(2,(scroll,a,b),50000,a,self.world.bag[a],((scroll,886,self.world.bag[scroll].count),(b,identity,self.world.bag[b].count)))
            if identity in GEMS:
                units=max(0,2**(level-1)-sum(2**(i.max_energy-1) for _,i in pieces))
                self.gem_units_needed[identity]=units;self.demand[identity]=self.count(identity)+units;self.required_levels[identity]=level
            else:
                low=sum(1 for _,i in pieces if i.max_energy==1)
                self.goals.append((identity,max(1,(2 if level>1 else 1)-low),'камни улучшения для ковки/объединения'))
            return None,None
        def materials(ids,fee,mode,target=slot,gem_type=0):
            if cash<fee+2000:return None
            found=[]
            for identity,level in ids:
                s=self.slot(identity,level,tuple(found)+(slot,))
                if s is None:
                    if identity in GEMS:
                        units=2**max(0,(level or 1)-1)
                        self.demand[identity]=self.count(identity)+units;self.gem_units_needed[identity]=units;self.required_levels[identity]=level or 1
                    else:self.goals.append((identity,1,'материал для штатной ковки'))
                else:found.append(s)
            if len(found)!=len(ids):return None
            groups=(target,*found) if mode in (1,3) else tuple(found)
            consumed=tuple((s,self.world.bag[s].identity,self.world.bag[s].count) for s in groups if s!=target)
            return Operation(mode,groups,fee,target,item,consumed,gem_type)
        if state['sockets']<min(2,len(choices)):
            return materials(((890,None),(891,None)),(state['sockets']+1)*50000,3)
        # Socket/gem upgrade costs rise; native caps are9for normal gems,15for apparel.
        for identity in choices:
            stone=self.knowledge.stone_items[identity]['stone_type']
            embedded=next((s['level'] for s in state['slots'] if s['stone_type']==stone),0)
            if embedded>=9:continue
            if embedded>=1:continue
            needed=embedded+1
            gem=self.slot(identity,needed, (slot,));refining=self.slot(885,needed,(slot,))
            fee=(state['total_level']+1)*100000
            return materials(((identity,needed),(885,needed)),fee,1,gem_type=stone)
        base=(item.parameters[1]>>16)&65535;apparel_level=item.parameters[1]&65535
        if not base:
            look=self.apparel(item)
            if look and cash>=self.gear.effective(item.identity,item)['level']*1000+65000:
                look_slot=next((s for s,i in self.world.bag.items() if i.identity==look and i.valid and not i.forge and i.parameters==(0,0)),None)
                if look_slot is None:self.goals=[(look,1,'подходящая аппарель для своей экипировки')];return None
                fee=self.gear.effective(item.identity,item)['level']*1000
                scroll=self.slot(453);catalyst=self.slot(454)
                if scroll is None or catalyst is None:
                    self.goals=[(i,1,'материал слияния с сохранением ковки') for i,s in ((453,scroll),(454,catalyst)) if s is None];return None
                return Operation(4,(scroll,look_slot,slot,catalyst),fee,look_slot,self.world.bag[look_slot],((scroll,453,self.world.bag[scroll].count),(slot,item.identity,item.count),(catalyst,454,self.world.bag[catalyst].count)),source_parameters=item.parameters)
        elif apparel_level<min(15,15 if all(s['level']>=9 for s in state['slots'] if s['stone_type']) else max(1,(state['total_level']+1)//2)):
            fee=(apparel_level+1)**2*10000
            scroll=self.slot(455);crystal=self.slot(456)
            if cash<fee+12000:return None
            if scroll is None or crystal is None:self.goals=[(i,1,'усиление вплавленного снаряжения') for i,s in ((455,scroll),(456,crystal)) if s is None];return None
            return Operation(5,(scroll,slot,crystal),fee,slot,item,((scroll,455,self.world.bag[scroll].count),(crystal,456,self.world.bag[crystal].count)))
        # Later cycles increase existing gems, with the same native compatibility/cost checks.
        for identity in choices:
            stone=self.knowledge.stone_items[identity]['stone_type']
            level=next((s['level'] for s in state['slots'] if s['stone_type']==stone),0)
            if level<9:
                for desired in (identity,885):
                    piece,combination=prepare_gem(desired,level+1)
                    if combination:return combination
                    if piece is None:return None
                return materials(((identity,level+1),(885,level+1)),(state['total_level']+1)*100000,1,gem_type=stone)
        return None
    def purchase_goals(self):
        if self.busy or not self.due(time.monotonic()):return []
        candidates=self.worn()
        if candidates:self.propose(candidates[0][1],-1)
        return [(i,n,why) for i,n,why in self.goals if n>0]
    def stone_needs(self):
        if not self.world.own or self.world.own.values.get(0,0)<35:return {}
        candidates=self.worn()
        if candidates:self.propose(candidates[0][1],-1)
        return {i:max(0,n-self.count(i)) for i,n in self.demand.items() if self.count(i)<n}
    def finish(self,now,reason,failed=False):
        self.context=None;self.pending=None;self.op=None;self.reason=reason
        self.retry=now+(120 if failed else 20);self.visit_until=0
        # Keep a removed equipment item for an ordinary native re-equip step.
        if self.target:self.pending={'stage':'reequip','deadline':now+10}
    def observe(self,command,payload,now):
        if not self.context or not self.op:return False
        c=self.context;mode=self.op.mode
        if command==802 and c['stage']=='menu':
            r=Reader(payload);npc,page=r.long(),r.byte();r.string_bytes();n=r.byte()
            if n>64:raise ProtocolError('Unsupported crafting menu')
            labels=[r.string() for _ in range(n)]
            if npc!=c['npc']:return False
            if LABELS[mode] not in labels:self.rejected+=1;self.finish(now,'НПС не предлагает нужную операцию',True);return True
            self.send(301,function_request(npc,page,labels.index(LABELS[mode])))
            c.update(stage='ui',deadline=now+8);return True
        if command==OPEN[mode] and c['stage']=='ui':
            self.send(525,request(mode,self.op.slots));self.requests+=1
            c.update(stage='quote',deadline=now+10);return True
        if command==548 and c['stage']=='quote':
            r=Reader(payload);kind,fee=r.byte(),r.long();r.end()
            if kind!=mode or fee!=self.op.fee or self.world.own.values.get(8,0)<fee+2000:
                self.send(526,b'\0');self.rejected+=1;self.finish(now,'Отклонена неожиданная/недоступная цена ковки',True);return True
            self.send(526,b'\1');self.pending={'stage':'result','gold':self.world.own.values.get(8,0),'deadline':now+15,'ack':False}
            c.update(stage='result',deadline=now+15);return True
        if command==549:
            if len(payload)==2:
                self.rejected+=1;self.finish(now,'Сервер отклонил ковку; предметы проверяются заново',True);return True
            r=Reader(payload);actor,kind,result=r.long(),r.byte(),r.byte();r.end()
            if actor!=self.world.own_id or kind!=mode:return False
            if result==1 and self.pending:self.pending['ack']=True
            elif result==2:self.rejected+=1;self.finish(now,'Нативная операция не подтверждена успешной',True)
            return True
        return False
    def result_matches(self):
        op=self.op;w=self.world
        if not op or op.target not in w.bag:return False
        after=w.bag[op.target]
        if not after.valid:return False
        for s,identity,before in op.consumed:
            if (w.bag[s].count if s in w.bag and w.bag[s].identity==identity else 0)!=before-1:return False
        if op.mode==3:
            old=forge_parts(op.before.parameters[0]);new=forge_parts(after.parameters[0])
            return after.identity==op.before.identity and new['sockets']==old['sockets']+1 and new['slots']==old['slots'] and after.parameters[1]==op.before.parameters[1]
        if op.mode==2:return after.identity==op.before.identity and after.max_energy==op.before.max_energy+1
        if op.mode==1:
            old=forge_parts(op.before.parameters[0]);new=forge_parts(after.parameters[0])
            previous=next((s['level'] for s in old['slots'] if s['stone_type']==op.gem_type),0)
            return (after.identity==op.before.identity and new['sockets']==old['sockets'] and new['total_level']==old['total_level']+1
                    and any(s=={'stone_type':op.gem_type,'level':previous+1} for s in new['slots'])
                    and [s for s in new['slots'] if s['stone_type'] not in (0,op.gem_type)]==[s for s in old['slots'] if s['stone_type'] not in (0,op.gem_type)]
                    and after.parameters[1]==op.before.parameters[1])
        if op.mode==4:
            source=op.consumed[1][1]
            return after.identity==op.before.identity and (after.parameters[1]>>16)&65535==source and after.parameters[0]==op.source_parameters[0]
        if op.mode==5:return after.identity==op.before.identity and after.parameters[1]==op.before.parameters[1]+1
        return False
    def tick(self,now,policy,safe=True,dialogue_busy=False):
        self.clock=now;w=self.world
        if self.pending:
            p=self.pending
            if p['stage']=='unfix':
                link,identity=p['link'],p['id']
                candidate=w.bag.get(p['slot'])
                found=p['slot'] if candidate and candidate.identity==identity and candidate.parameters==p['parameters'] else None
                if w.own.equipment.get(link)!=identity and found is not None:self.target=(link,found);self.pending=None
            elif p['stage']=='reequip':
                link,slot=self.target
                item=w.bag.get(slot)
                if item and not p.get('sent'):
                    from hunter import action_header
                    policy.emit(action_header(w.own_id,policy.sequence,11)+struct.pack('>hh',slot,-1));p['sent']=True;p['id']=item.identity
                if p.get('sent') and p.get('id') in w.own.equipment.values() and slot not in w.bag:
                    self.pending=None;self.target=None;return False
            elif p['stage']=='result' and p.get('ack') and self.result_matches() and w.own.values.get(8,0)==p['gold']-self.op.fee:
                self.confirmed+=1
                if self.target:self.target=(self.target[0],self.op.target)
                self.finish(now,'Ковка подтверждена: результат, материалы и золото');return True
            if self.pending and now>=p['deadline']:
                self.timeouts+=1
                if p['stage']=='reequip':self.pending=None;self.target=None;self.context=None;self.op=None;self.retry=now+120
                else:self.finish(now,'Нет полного подтверждения ковки; повтор после сверки сумки',True)
            return self.busy
        if self.context:
            if now>=self.context['deadline']:
                if self.context['stage'] in ('quote','ui'):self.send(525,b'\0')
                self.timeouts+=1;self.finish(now,'Истекло ожидание меню/цены ковки',True)
            return self.busy
        if not w.bag_ready or w.bag_disabled or not safe or dialogue_busy:return False
        if not self.target and not self.due(now):return False
        if self.target:
            slot=self.target[1];item=w.bag.get(slot)
            if not item:self.target=None;self.retry=now+120;return False
        else:
            candidates=self.worn()
            if not candidates:return False
            link,item=candidates[0];slot=-1
        op=self.propose(item,slot)
        if not op:
            if self.target:self.finish(now,'Нужны материалы; возвращает экипировку',False);return True
            return False
        if w.own.values.get(8,0)<op.fee+2000:return False
        if w.map!='garner':
            self.reason='Идёт в Аргент для ковки'
            return bool(policy.travel and policy.travel.tick(now,policy,safe,dialogue_busy))
        shop=next((n for n in self.life.owner_shops['npcs'] if n['script_function']=='OwnerForge'),None)
        if not shop:return False
        npc=npc_near(w,shop['position']);point=npc.position if npc else shop['position']
        self.reason='Штатная ковка: '+LABELS[op.mode]
        if not npc or math.dist(policy.position(now),point)>220:
            if not self.visit_until:self.visit_until=now+120
            if now>=self.visit_until:self.finish(now,'Не успел дойти до ковщика; возвращается к охоте',True);return False
            goal=policy.nav.nearest((point[0]-150,point[1]),2)
            if goal and policy.move_to(goal,now):return True
            self.finish(now,'Не найден безопасный подход к ковщику',True);return False
        if not self.target and op.mode not in (2,):
            empty=next((s for s in range(w.bag_capacity or 0) if s not in w.bag),None)
            if empty is None or (w.bag_capacity or 0)-len(w.bag)<5:return False
            policy.emit(unfix(w.own_id,policy.sequence,link,empty))
            self.pending={'stage':'unfix','link':link,'slot':empty,'id':item.identity,'parameters':item.parameters,'deadline':now+10};return True
        # Bag-only combination does not need to remove worn equipment.
        self.op=op
        self.send(301,talk_request(npc.identity));self.context={'npc':npc.identity,'stage':'menu','deadline':now+8};return True
    def summary(self):
        return {'state':self.reason,'requests':self.requests,'confirmed':self.confirmed,'rejected':self.rejected,'timeouts':self.timeouts,
                'stage':self.pending or self.context,'native_operation':self.op.mode if self.op else None,'material_goals':self.goals,
                'gem_needs':self.demand,'native_gold_and_inventory_required':True,'specialist':self.is_specialist}
