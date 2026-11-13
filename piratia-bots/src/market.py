"""Classic real-inventory stalls: finite shifts, authoritative confirmations and earned budgets."""
import json,math,random,struct,threading
from pathlib import Path
from classic_wire import Reader,ProtocolError,string
from inventory import BagItem

START,VIEW,BUY,CLOSE=330,331,332,333
INFO,DELGOODS,CLOSED,STARTED,NAME=854,856,857,858,859

def start_request(title,goods):
    if not 1<=len(goods)<=6 or len(title.encode('cp1251'))>20:raise ValueError('Invalid stall title or size')
    rows=[];slots=set()
    for grid,price,count,slot in goods:
        if not 0<=grid<6 or grid in slots or not 0<=slot<256 or not 1<=count<=99 or not 1<=price<=2000000000:raise ValueError('Invalid stall offer')
        slots.add(grid);rows.append(struct.pack('>BIBB',grid,price,count,slot))
    return string(title)+bytes([len(goods)])+b''.join(rows)

def buy_request(owner,grid,count=1):
    if not owner or not 0<=grid<18 or not 1<=count<=99:raise ValueError('Invalid stall purchase')
    return struct.pack('>IBB',owner,grid,count) # Classic client has NO modern destination grid.

def read_offers(payload):
    r=Reader(payload);owner,n=r.long(),r.byte();r.string_bytes()
    if not owner or n>18:raise ProtocolError('Unsupported stall owner/count')
    offers=[];seen=set()
    for _ in range(n):
        grid,identity,count,price,kind=r.byte(),r.short(),r.byte(),r.long(),r.short()
        if grid>=18 or grid in seen or not identity or not count or price>2000000000:raise ProtocolError('Invalid stall offer')
        seen.add(grid)
        if kind==43:
            present=r.byte()
            if present not in (0,1):raise ProtocolError('Invalid stall boat')
            if present:r.string_bytes();r.take(2+2+10*4+2+4)
            continue # Boat ownership purchases are not implemented.
        endurance,maximum,energy,maxenergy=[r.short() for _ in range(4)]
        forge,valid=r.byte(),r.byte()
        params=(r.long(),r.long());instance=r.byte()
        if valid not in (0,1) or instance not in (0,1):raise ProtocolError('Unsupported classic stall details')
        attributes=tuple((r.short(),r.short()) for _ in range(5)) if instance else ()
        offers.append((grid,price,BagItem(identity,count,endurance,maximum,energy,maxenergy,forge,bool(valid),params,attributes)))
    r.end();return owner,offers

class MarketCatalog:
    def __init__(self,assets):
        self.data=json.loads((Path(assets)/'market-items.json').read_text())
        self.items={int(k):v for k,v in self.data['items'].items()}
    def price(self,identity):return self.items.get(identity,{}).get('reference_price',0)

class MarketDirectory:
    """One live lease per character and one spaced city pitch, bounded by 200 workers."""
    def __init__(self,limit=10,city_limits=None,live_count=None):self.lock=threading.Lock();self.rows={};self.limit=limit;self.city_limits=city_limits;self.live_count=live_count
    def reserve(self,name,city,now):
        with self.lock:
            self.rows={k:v for k,v in self.rows.items() if v['until']>now}
            limits=self.city_limits
            if self.live_count:
                total=self.live_count(now)//10;argent=round(total*.75);rest=total-argent
                limits={'garner':argent,'magicsea':(rest+1)//2,'darkblue':rest//2}
            limit=limits.get(city,0) if limits is not None else self.limit
            if name in self.rows:
                if self.rows[name]['slot']>=limit:self.rows.pop(name,None);return None
                self.rows[name]['until']=now+30;return self.rows[name]['slot']
            taken={v['slot'] for v in self.rows.values() if v['city']==city}
            for slot in range(limit):
                if slot not in taken:
                    self.rows[name]={'city':city,'slot':slot,'until':now+30};return slot
            return None
    def release(self,name):
        with self.lock:self.rows.pop(name,None)

class Market:
    def __init__(self,world,send,name,index,catalog,gear,life,directory):
        self.world,self.send,self.name,self.index=world,send,name,index
        self.catalog,self.gear,self.life,self.directory=catalog,gear,life,directory
        self.rng=random.Random(name+':market');self.next_shift=None;self.state='idle';self.deadline=0
        self.pending=None;self.context=None;self.stock=[];self.pitch=None;self.trade_until=0;self.next_scan=0
        self.scanned={};self.reason='';self.learn_pending=None;self.next_learn=0
        self.open_requests=self.confirmed_opens=self.close_requests=self.buy_requests=self.confirmed_buys=0
        self.timeouts=self.sold_units=self.confirmed_learns=0;self.disabled=False;self.active_confirmed=False
    def count(self,identity):return sum(i.count for i in self.world.bag.values() if i.identity==identity)
    @property
    def busy(self):return self.state!='idle' or self.pending is not None or self.context is not None or self.learn_pending is not None
    def protected(self,policy):
        result={3296,1847,3141}
        for feature in (policy.career,policy.story):
            if feature:result.update(feature.needed_items())
        if policy.chests:result.update(policy.chests.catalog.chests)
        if policy.adventure:
            task=policy.adventure.farm()
            if task and task[1]:result.add(task[1])
        result.update(self.life.books)
        return result
    def useful_gear(self,identity):
        w=self.world;g=self.gear.gear.get(identity)
        if not g or w.own.model not in g['bodies'] or g['level']>w.own.values.get(0,0)+5:return False
        if g['jobs']!=[-1] and w.own.values.get(4) not in g['jobs']:return False
        return any(g['score']>self.gear.gear.get(w.own.equipment.get(link),{}).get('score',0) for link in g['links'])
    def gem_goals(self):
        # A conservative build policy using actual owner-table gem IDs, not forging automation.
        if self.world.own.values.get(0,0)<30:return {}
        job=self.world.own.values.get(4,0)
        ids=(863,862) if job in (1,8,9) else (861,860) if job in (2,12) else (1012,862) if job in (4,5,13,14,16) else ()
        return {i:1 for i in ids if i in self.catalog.items}
    def reserve_count(self,identity):
        lv=self.world.own.values.get(0,0)
        for goal in self.catalog.data['goals'].values():
            if identity==goal['identity'] and lv>=goal['min_level']:return goal['keep']
        rune=self.rune_goal()
        return max(rune.get(identity,0),self.gem_goals().get(identity,0))
    def rune_goal(self):
        level=self.world.own.values.get(0,0)
        tiers=[g for g in self.catalog.data.get('rune_exchange_goals',[]) if g['level']<=level+5]
        return {int(k):v for k,v in max(tiers,key=lambda g:g['level'])['items'].items()} if tiers else {}
    def needs_life_study(self):
        w=self.world
        return not w.skills.get(241,{}).get('level',0) and w.own.values.get(13,0)<1
    def offers(self,policy):
        w=self.world;protected=self.protected(policy);result=[];reserved={}
        if not w.bag_ready or w.bag_disabled:return []
        priority={'kal':0,'refining':0,'gem':0,'rune':0,'sealed':1,'gear':2}
        for slot,item in sorted(w.bag.items(),key=lambda pair:(priority.get(self.catalog.items.get(pair[1].identity,{}).get('category'),9),pair[0])):
            meta=self.catalog.items.get(item.identity)
            if not meta or not item.valid or item.identity in protected or self.useful_gear(item.identity):continue
            # Never sell enhanced, instanced, equipped or potentially valuable personalized items cheaply.
            if item.forge or any(item.parameters) or any(a or b for a,b in item.instance_attributes):continue
            if item.identity in w.own.equipment.values():continue
            keep=max(0,self.reserve_count(item.identity)-reserved.get(item.identity,0))
            reserved[item.identity]=reserved.get(item.identity,0)+min(item.count,keep)
            count=min(99,item.count-keep)
            if count<=0:continue
            result.append((len(result),self.catalog.price(item.identity),count,slot))
            if len(result)==6:break
        return result
    def needed(self):
        w=self.world;wanted={}
        if not w.skills.get(241,{}).get('level',0) and not self.count(3296) and w.own.values.get(13,0)>0:wanted[3296]=1
        if self.count(1847)<5:wanted[1847]=5-self.count(1847)
        for goal in self.catalog.data['goals'].values():
            missing=goal['keep']-self.count(goal['identity'])
            if w.own.values.get(0,0)>=goal['min_level'] and missing>0:wanted[goal['identity']]=missing
        for identity,count in {**self.rune_goal(),**self.gem_goals()}.items():
            identity=int(identity)
            if self.count(identity)<count:wanted[identity]=count-self.count(identity)
        for identity,book in self.life.books.items():
            if (self.life.can_learn(w,book) and w.own.values.get(7,0)>=book['cost']
                    and not w.skills.get(book['skill'],{}).get('level',0) and not self.count(identity)):
                wanted[identity]=1
        return wanted
    def fair_cap(self,identity):
        # Explicit ceilings prevent players setting a huge price from draining bots.
        return self.catalog.price(identity) or self.life.prices.get(identity,0)
    def observe(self,command,payload,now):
        r=Reader(payload)
        if command==NAME:
            identity,title=r.long(),r.string();r.end()
            if identity in self.world.entities:self.world.entities[identity].stall=title
            if identity==self.world.own_id:
                if title and self.state=='opening':self.opened(now)
                elif not title and self.state=='closing':self.finish(now)
        elif command==STARTED:
            identity=r.long();r.end()
            if identity==self.world.own_id and self.state=='opening':self.opened(now)
        elif command==CLOSED:
            identity=r.long();r.end()
            if identity in self.world.entities:self.world.entities[identity].stall=''
            if identity==self.world.own_id:self.finish(now)
        elif command==DELGOODS:
            identity,grid,count=r.long(),r.byte(),r.byte();r.end()
            if identity==self.world.own_id and self.state=='selling':
                updated=[]
                for g,p,n,s in self.stock:
                    if g==grid:self.sold_units+=min(n,count);n=max(0,n-count)
                    if n:updated.append((g,p,n,s))
                self.stock=updated
        elif command==INFO:
            owner,offers=read_offers(payload)
            if self.context is None or owner!=self.context[0] or now>self.context[1]:return
            self.context=None
            entity=self.world.entities.get(owner)
            if not entity or not entity.stall or math.dist(self.world.position(now),entity.position)>300:return
            w=self.world;cash=w.own.values.get(8,0);want=self.needed();free=(w.bag_capacity or 0)-len(w.bag)
            if w.bag_disabled or free<2:return
            budget=max(0,min(cash//5,cash-1000))
            for grid,price,item in offers:
                if not item.valid or price<=0:continue
                identity=item.identity
                desirable=identity in want or self.useful_gear(identity)
                if not desirable or (identity not in want and self.count(identity)>=1):continue
                if not self.fair_cap(identity) or price>self.fair_cap(identity):continue
                # One item at a time. Only bag AND gold changes confirm a purchase.
                if price>budget:continue
                self.send(BUY,buy_request(owner,grid));self.buy_requests+=1
                self.pending=(identity,self.count(identity),cash,now+15)
                self.next_scan=now+120;break
    def opened(self,now):
        self.state='selling';self.trade_until=now+2400;self.confirmed_opens+=1;self.active_confirmed=True
        self.reason='торгует в городском ларьке'
    def finish(self,now):
        self.directory.release(self.name);self.state='idle';self.stock=[];self.pitch=None
        self.next_shift=now+self.rng.uniform(1200,2400);self.reason='';self.active_confirmed=False
    def request_close(self,now):
        if self.state!='closing' or now>=self.deadline:
            self.send(CLOSE,b'');self.close_requests+=1;self.state='closing';self.deadline=now+15
            self.reason='ждёт подтверждения закрытия ларька'
    def learn(self,now,policy):
        w=self.world
        if self.learn_pending:
            count,deadline=self.learn_pending
            if w.skills.get(241,{}).get('level',0)>0 and self.count(3296)<count:
                self.confirmed_learns+=1;self.learn_pending=None
            elif now>=deadline:self.learn_pending=None;self.next_learn=now+300;self.timeouts+=1
            return True
        if now<self.next_learn or w.skills.get(241,{}).get('level',0) or w.own.values.get(13,0)<1:return False
        slot=next((s for s,i in w.bag.items() if i.identity==3296 and i.valid),None)
        if slot is None:return False
        from hunter import action_header
        policy.emit(action_header(w.own_id,policy.sequence,11)+struct.pack('>hh',slot,-1))
        self.learn_pending=self.count(3296),now+15;self.next_learn=now+30
        self.reason='изучает навык торговли';return True
    def tick(self,now,policy,safe,dialogue_busy=False):
        w=self.world
        if self.next_shift is None:self.next_shift=now+self.rng.uniform(60,600)
        if self.state in ('opening','selling','closing'):
            if self.directory.reserve(self.name,w.map,now) is None and self.state!='closing':
                self.request_close(now);return True
            if self.state=='closing':
                if now>=self.deadline:
                    if self.active_confirmed:self.request_close(now)
                    else:self.finish(now)
                return True # Fail closed: no movement until authoritative closure.
            if self.state=='opening' and now>=self.deadline:
                self.timeouts+=1;self.request_close(now);return True
            if self.state=='selling' and (not safe or now>=self.trade_until or not self.stock):self.request_close(now)
            return True
        if self.pending:
            identity,count,cash,deadline=self.pending
            if self.count(identity)>count and w.own.values.get(8,cash)<cash:self.confirmed_buys+=1;self.pending=None
            elif now>=deadline:self.pending=None;self.timeouts+=1;self.next_scan=now+300
            return True
        if self.context:
            if now>=self.context[1]:self.context=None;self.timeouts+=1;self.next_scan=now+120
            return True
        if self.state=='travelling' and not safe:self.finish(now);return False
        if self.disabled or not safe or dialogue_busy or not w.bag_ready or w.bag_disabled:return False
        if self.learn(now,policy):return True
        if self.state=='travelling':
            if self.directory.reserve(self.name,w.map,now) is None:self.finish(now);return False
            if now>=self.deadline:self.finish(now);return False
            if math.dist(policy.position(now),self.pitch)>120:
                self.reason='идёт на городское место торговли'
                if not policy.move_to(self.pitch,now):self.finish(now);return False
                return True
            if any(e.identity!=w.own_id and e.stall and math.dist(e.position,policy.position(now))<350 for e in w.entities.values()):
                self.finish(now);return False
            self.stock=self.offers(policy)
            if not self.stock or not w.skills.get(241,{}).get('level',0):self.finish(now);return False
            self.send(START,start_request('Оружие и находки',self.stock));self.open_requests+=1
            self.state='opening';self.deadline=now+15;return True
        # Scan visible real player/bot stalls only. Never use shared stock as a fake server view.
        can_shop=w.own.values.get(8,0)>1000 and (w.bag_capacity or 0)-len(w.bag)>=2
        if can_shop and now>=self.next_scan:
            self.scanned={k:v for k,v in self.scanned.items() if v>now}
            candidates=[e for e in w.entities.values() if e.identity!=w.own_id and e.stall and e.control==1 and self.scanned.get(e.identity,0)<=now and math.dist(policy.position(now),e.position)<2400]
            if candidates:
                seller=min(candidates,key=lambda e:math.dist(policy.position(now),e.position))
                if math.dist(policy.position(now),seller.position)>220:
                    goal=policy.nav.nearest(seller.position,3)
                    if goal and policy.move_to(goal,now):self.reason='смотрит городские ларьки';return True
                else:
                    self.send(VIEW,struct.pack('>I',seller.identity));self.context=seller.identity,now+10
                    self.scanned[seller.identity]=now+300;self.next_scan=now+30;return True
            self.next_scan=now+30
        if now<self.next_shift or not w.skills.get(241,{}).get('level',0) or not self.offers(policy):return False
        slot=self.directory.reserve(self.name,w.map,now)
        if slot is None:self.next_shift=now+60;return False
        # Separate cells in a ring near the existing home city; never stack stalls on an NPC.
        angle=(slot%10)*2*math.pi/10;radius=1200+600*(slot//10)
        point=(policy.home[0]+int(radius*math.cos(angle)),policy.home[1]+int(radius*math.sin(angle)))
        goal=policy.nav.nearest(point,6)
        if not goal or any(e.control in (2,3) and math.dist(e.position,goal)<350 for e in w.entities.values()):
            self.directory.release(self.name);self.next_shift=now+120;return False
        self.pitch=goal;self.state='travelling';self.deadline=now+300;self.reason='готовит городской ларёк';return True
    def loot_needs(self):return set(self.catalog.items)
    def summary(self):
        return {'state':self.state,'open_requests':self.open_requests,'confirmed_opens':self.confirmed_opens,
                'close_requests':self.close_requests,'purchase_requests':self.buy_requests,'confirmed_purchases':self.confirmed_buys,
                'sold_units_server_notices':self.sold_units,'timeouts':self.timeouts,'stall_skill_learned':bool(self.world.skills.get(241,{}).get('level',0)),
                'confirmed_book_learns':self.confirmed_learns,'goals':self.needed(),'rune_exchange_goal':self.rune_goal(),'black_market_barter_implemented':False}
