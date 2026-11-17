"""Classic real-inventory stalls: finite shifts, authoritative confirmations and earned budgets."""
import hashlib,json,math,random,struct,threading
from pathlib import Path
from classic_wire import Reader,ProtocolError,string
from inventory import BagItem

START,VIEW,BUY,CLOSE=330,331,332,333
INFO,DELGOODS,CLOSED,STARTED,NAME=854,856,857,858,859

def start_request(title,goods):
    if not 1<=len(goods)<=18 or len(title.encode('cp1251'))>20:raise ValueError('Invalid stall title or size')
    rows=[];slots=set()
    for grid,price,count,slot in goods:
        if not 0<=grid<18 or grid in slots or not 0<=slot<256 or not 1<=count<=99 or not 1<=price<=2000000000:raise ValueError('Invalid stall offer')
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
        if 1000 in self.items:self.items[1000]=dict(self.items[1000],reference_price=1500)
        self.owner_price_floor={}
        from owner_shops import read_overlay
        try:owner=read_overlay(assets)
        except (OSError,ValueError,TypeError,KeyError,AttributeError):owner=None
        if owner:self.owner_price_floor={int(k):price*3//4 for k,price in owner['prices'].items()}
        self.prices=None;self.broad_catalog=False;self.npc_purchase_prices={}
        audit=Path(assets)/'useful-loot.json'
        self.useful_audit=json.loads(audit.read_text()) if audit.exists() else {'items':{}}
        curated=Path(assets)/'stall-goods.json'
        self.curated=json.loads(curated.read_text()) if curated.exists() else None;self.curated_mode=False
        facts=json.loads((Path(assets)/'life-items.json').read_text())
        npc_source=Path(assets)/'world-npcs.json'
        if npc_source.exists():
            for npc in json.loads(npc_source.read_text())['npcs']:
                if npc.get('verified_shop_binding'):
                    for identity in npc['offers']:
                        value=int(facts['prices'].get(str(identity),0))
                        if value>0:self.npc_purchase_prices[identity]=value
        if owner:self.npc_purchase_prices.update({int(i):v for i,v in owner['prices'].items()})
        self.focused=bool(owner and owner.get('catalog_revision',0)>=56)
        self.focused_prices={860:60000,861:60000,862:70000,863:80000,864:150000,865:150000,866:120000,1012:100000}
    def enable_broad_catalog(self):
        self.broad_catalog=True;self.items.update({int(i):r for i,r in self.useful_audit['items'].items()})
    def enable_curated_catalog(self):
        if not self.curated:return
        self.broad_catalog=True;self.curated_mode=True;self.items={int(i):r for i,r in self.curated['items'].items()}
        if self.focused:
            for identity,price in self.focused_prices.items():
                self.items[identity]={'name':str(identity),'category':'gem','reference_price':price,'npc_buyback':0,'keep':0}
            self.items={i:r for i,r in self.items.items() if i in self.focused_prices or i==684}
    def enable_forging_catalog(self,gear,life):
        for identity,g in gear.gear.items():
            if g['level']>=35 and g['kind'] in (1,2,3,4,7,9,11,20,22,23,24,27):
                self.items[identity]={'name':life.names.get(identity,str(identity)),'category':'gear','reference_price':max(1,life.prices.get(identity,0)),'keep':0}
        for identity,g in gear.gear.items():
            if 5000<identity<6000 and g['kind'] in (1,2,3,4,7,9,11,22,23,24,27):
                self.items[identity]={'name':life.names.get(identity,str(identity)),'category':'gear','reference_price':max(1,life.prices.get(identity,0)),'keep':0}
    def price(self,identity):
        if self.focused and identity in self.focused_prices:
            reference=self.focused_prices[identity]
            return max(60000,min(150000,self.prices.guide(identity,reference) if self.prices else reference))
        if identity==1000:return 1500
        base=self.items.get(identity,{}).get('reference_price',0)
        native=self.npc_purchase_prices.get(identity,0) if self.broad_catalog else 0
        if native:base=min(base,max(1,round(native*.85)))
        value=max(self.owner_price_floor.get(identity,0),self.prices.guide(identity,base) if self.prices else base)
        if native:value=max(round(native*.65),min(round(native*.95),value))
        return value
    def confirmed_price(self,identity,price):
        if self.prices:self.prices.confirmed(identity,price,self.items.get(identity,{}).get('reference_price',0))

class MarketDirectory:
    """One live lease per character and one spaced city pitch, bounded by 200 workers."""
    def __init__(self,limit=10,city_limits=None,live_count=None,argent_target=None):
        self.lock=threading.Lock();self.rows={};self.limit=limit;self.city_limits=city_limits;self.live_count=live_count
        self.argent_target=argent_target
        self.pitch_cache={}
    def pitches(self,city,home,nav,npcs,spawns):
        from stall_pitches import city_pitches
        if spawns:home=spawns[0]
        key=(city,tuple(home))
        with self.lock:
            if key not in self.pitch_cache:self.pitch_cache[key]=city_pitches(city,home,nav,npcs,spawns)
            return self.pitch_cache[key]
    def reserve(self,name,city,now):
        with self.lock:
            self.rows={k:v for k,v in self.rows.items() if v['until']>now}
            limits=self.city_limits
            if self.live_count:
                total=self.live_count(now)//10;argent=round(total*.75);rest=total-argent
                limits={'garner':argent,'magicsea':(rest+1)//2,'darkblue':rest//2}
                if self.argent_target is not None:limits['garner']=min(self.argent_target,self.live_count(now))
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
        self.minimum_level=15
        self.keep_stall_stock=False
        self.focused_goods=False;self.broad_goods=False;self.policy_reference=None;self.progression_first=False
        self.is_crafter=int.from_bytes(hashlib.sha256((name+':life-profession').encode()).digest()[:8],'big')%100<15
        self.forging_economy=False;self.gem_seller=False;self.crafting=None
        self.pending_shape=None
        self.close_started=None;self.close_states_revision=None;self.close_resyncs=0;self.state_confirmed_closes=0
    def count(self,identity):return sum(i.count for i in self.world.bag.values() if i.identity==identity)
    @property
    def busy(self):return self.state!='idle' or self.pending is not None or self.context is not None or self.learn_pending is not None
    def protected(self,policy):
        result={3296,1847,3141}
        for feature in (policy.career,policy.story):
            if feature:
                result.update(feature.needed_items())
                quest=getattr(feature,'quest',None)
                if isinstance(quest,dict) and feature.active():
                    result.update(n['id'] for n in quest.get('needs',[]) if n['kind']==1)
        if policy.chests:result.update(policy.chests.catalog.chests)
        if policy.adventure:
            task=policy.adventure.farm()
            if task and task[1]:result.add(task[1])
            for identity in policy.adventure.journal:
                objective=policy.adventure.grind.get(identity)
                if objective and objective[1]:result.add(objective[1])
        if not self.broad_goods:result.update(self.life.books)
        from pet_care import PROTECTED
        result.update(PROTECTED-({227,2312,276,277,278,279,280} if self.broad_goods else set()))
        from life_professions import PROTECTED as LIFE_PROTECTED
        result.update(LIFE_PROTECTED)
        from treasure_hunt import PROTECTED as TREASURE_PROTECTED
        result.update(TREASURE_PROTECTED)
        return result
    def useful_gear(self,identity):
        w=self.world;g=self.gear.gear.get(identity)
        if not g or w.own.model not in g['bodies'] or g['level']>w.own.values.get(0,0)+5:return False
        if g['jobs']!=[-1] and w.own.values.get(4) not in g['jobs']:return False
        return any(g['score']>self.gear.gear.get(w.own.equipment.get(link),{}).get('score',0) for link in g['links'])
    def ordinary_gear(self,item):
        return bool(item.valid and (item.max_endurance<=0 or item.endurance>0) and self.catalog.items.get(item.identity,{}).get('category')=='gear' and not item.forge
                    and item.parameters[0] in (0,1000000000,2000000000,3000000000) and item.parameters[1]==0 and all((key==value==0) or (1<=key<=47 and 0<=value<=2000)
                                                         for key,value in item.instance_attributes))
    def item_ask_price(self,item):
        if self.forging_economy and item.identity in self.catalog.focused_prices:
            units=2**max(0,min(8,item.max_energy-1))
            return min(2000000000,self.ask_price(item.identity)*units+50000*(units-1))
        if self.forging_economy and self.safe_forged(item):
            from mechanics import forge_parts
            state=forge_parts(item.parameters[0]);base=self.gear.effective(item.identity,item)
            value=max(1,self.life.prices.get((item.parameters[1]>>16)&65535 or item.identity,0))
            n=state['total_level'];value+=100000*n*(n+1)//2+50000*state['sockets']*(state['sockets']+1)//2
            for stone in state['slots']:
                rule=self.gear.gems.get(str(stone['stone_type']))
                if rule and stone['level']:
                    units=2**(stone['level']-1);value+=self.catalog.focused_prices.get(rule['item_id'],0)*units+50000*(units-1)
            if item.parameters[1]>>16:value+=50000+base['level']*1000
            value+=sum(10000*k*k for k in range(1,min(15,item.parameters[1]&65535)+1))
            return min(2000000000,max(1,round(value*self.rng.uniform(.9,1.05))))
        base=self.ask_price(item.identity)
        if self.focused_goods and self.ordinary_gear(item):
            bonus=sum(v for k,v in item.instance_attributes if 26<=k<=30)
            return min(2000000000,round(base*(1+min(2,bonus/20))))
        return base
    def safe_forged(self,item):
        from mechanics import forge_parts
        g=self.gear.effective(item.identity,item)
        if not g or g['level']<35 or not item.valid or item.max_endurance>0 and item.endurance<=0:return False
        state=forge_parts(item.parameters[0]);base=(item.parameters[1]>>16)&65535
        if item.forge>27 or state['sockets']>3 or any((s['stone_type'] and (str(s['stone_type']) not in self.gear.gems or not 1<=s['level']<=9)) or (not s['stone_type'] and s['level']) for s in state['slots']):return False
        if sum(s['stone_type']!=0 for s in state['slots'])>state['sockets']:return False
        if item.parameters[1] and (not 5000<item.identity<6000 or base not in self.gear.gear or item.parameters[1]&65535>15):return False
        return bool(state['total_level'] or base)
    def gem_goals(self):
        # A conservative build policy using actual owner-table gem IDs, not forging automation.
        if self.world.own.values.get(0,0)<30:return {}
        job=self.world.own.values.get(4,0)
        ids=(863,862) if job in (1,8,9) else (861,860) if job in (2,12) else (1012,862) if job in (4,5,13,14,16) else ()
        return {i:1 for i in ids if i in self.catalog.items}
    def reserve_count(self,identity):
        if self.forging_economy and identity in self.catalog.focused_prices:
            return self.count(identity) if self.crafting and identity in self.crafting.stone_needs() else (1 if identity in self.gem_goals() else 0)
        if self.catalog.focused and identity in self.catalog.focused_prices:return 0
        if self.broad_goods:
            if identity==2312:return 6
            if identity==227:return 2
            if identity in (276,277,278,279,280):return 1
            book=self.life.books.get(identity)
            if book:
                from roles import FIRST_JOB
                target=getattr(self.world.own,'build_id',None)
                from builds import PROFILES
                job=PROFILES.get(target,{}).get('job',self.world.own.values.get(4))
                compatible=str(job) in book['jobs'] or str(FIRST_JOB.get(job,job)) in book['jobs']
                return 1 if compatible and self.world.skills.get(book['skill'],{}).get('level',0)==0 else 0
        lv=self.world.own.values.get(0,0)
        if identity==1000 and self.focused_goods:return 0
        if identity==684 and self.focused_goods and 15<=lv<=40:return 1
        if identity==1000 and (self.is_crafter or any(self.world.skills.get(i,{}).get('level',0) for i in (338,339,340))):return 2
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
        capacity=min(18,max(6,w.skills.get(241,{}).get('level',0)*6))
        if not w.bag_ready or w.bag_disabled:return []
        priority={'kal':0,'refining':0,'gem':0,'rune':0,'scroll':0,'blueprint':0,'sealed':1,'gear':2}
        for slot,item in sorted(w.bag.items(),key=lambda pair:(priority.get(self.catalog.items.get(pair[1].identity,{}).get('category'),9),pair[0])):
            meta=self.catalog.items.get(item.identity)
            if self.focused_goods and not self.broad_goods and item.identity!=684 and (not meta or meta['category']!='gear'):continue
            useful=bool(self.gear.upgrade(w.own,item.identity,max(0,(w.bag_capacity or 0)-len(w.bag)),item)) if self.forging_economy and item.identity in self.gear.gear else self.useful_gear(item.identity)
            if not meta or item.identity==1000 and self.focused_goods or not item.valid or item.identity in protected or useful:continue
            # Never sell enhanced, instanced, equipped or potentially valuable personalized items cheaply.
            ordinary=self.focused_goods and self.ordinary_gear(item)
            forged=self.forging_economy and self.safe_forged(item)
            gem=self.forging_economy and item.identity in self.catalog.focused_prices and not any(item.parameters) and 1<=item.max_energy<=9
            if (item.forge or (any(item.parameters) and not ordinary) or (any(a or b for a,b in item.instance_attributes) and not ordinary)) and not (forged or gem):continue
            if meta['category'] in ('gem','refining') and item.max_energy>1 and not gem:continue
            if item.identity in w.own.equipment.values() and not self.broad_goods:continue
            keep=max(0,self.reserve_count(item.identity)-reserved.get(item.identity,0))
            reserved[item.identity]=reserved.get(item.identity,0)+min(item.count,keep)
            count=min(99,item.count-keep)
            if count<=0 or (self.broad_goods and meta["category"] in ("quest_material","requested_material","care_supply","craft_material","material") and count<10):continue
            result.append((len(result),self.item_ask_price(item),count,slot))
            if len(result)==capacity:break
        return result
    def ask_price(self,identity):
        if identity==1000:return 1500
        price=self.catalog.price(identity)
        if not self.catalog.prices:return price
        # Stable per-seller negotiation margins plus current surplus; no personality reset.
        digest=hashlib.sha256(f'{self.name}:{identity}'.encode()).digest()
        margin=.95+digest[0]/255*.10
        surplus=min(.10,self.count(identity)/1000)
        value=max(1,min(2000000000,round(price*(margin-surplus))))
        return max(60000,min(150000,value)) if self.catalog.focused and identity in self.catalog.focused_prices else value
    def needed(self):
        w=self.world;wanted={}
        if self.forging_economy and self.crafting:
            wanted.update(self.crafting.stone_needs())
        # The life-profession cohort prepares a small owned supply, not speculative hoarding.
        if (self.is_crafter or any(w.skills.get(i,{}).get('level',0) for i in (338,339,340))) and w.own.values.get(0,0)>=15 and self.count(1000)<2:
            wanted[1000]=2-self.count(1000)
        if not w.skills.get(241,{}).get('level',0) and not self.count(3296) and w.own.values.get(13,0)>0:wanted[3296]=1
        if self.count(1847)<5:wanted[1847]=5-self.count(1847)
        for goal in self.catalog.data['goals'].values():
            missing=goal['keep']-self.count(goal['identity'])
            if w.own.values.get(0,0)>=goal['min_level'] and missing>0:wanted[goal['identity']]=missing
        for identity,count in {**self.rune_goal(),**self.gem_goals()}.items():
            identity=int(identity)
            if self.count(identity)<count:wanted[identity]=max(wanted.get(identity,0),count-self.count(identity))
        for identity,book in self.life.books.items():
            if (self.life.can_learn(w,book) and w.own.values.get(7,0)>=book['cost']
                    and not w.skills.get(book['skill'],{}).get('level',0) and not self.count(identity)):
                wanted[identity]=1
        if self.focused_goods:
            wanted.pop(1000,None)
            if 15<=w.own.values.get(0,0)<=40 and not self.count(684) and not self.count(682):wanted[684]=1
        if self.broad_goods and self.policy_reference:
            for feature in (self.policy_reference.career,self.policy_reference.story):
                if feature and feature.active():
                    for requirement in feature.quest.get('needs',[]):
                        identity=requirement['id']
                        if requirement['kind']==1 and identity in self.catalog.items:
                            missing=requirement['count']-self.count(identity)
                            if missing>0:wanted[identity]=max(wanted.get(identity,0),missing)
            pet=getattr(self.policy_reference,'petcare',None)
            if pet and pet.any_fairy():
                for identity in (227,2312):
                    if self.count(identity)<2:wanted[identity]=2-self.count(identity)
        return wanted
    def fair_cap(self,identity):
        if identity==1000:return 1500
        # Explicit ceilings prevent players setting a huge price from draining bots.
        price=self.catalog.price(identity) or self.life.prices.get(identity,0)
        return round(price*1.1) if self.catalog.prices else price
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
            pet=getattr(self.policy_reference,'petcare',None) if self.policy_reference else None
            if pet:budget=min(budget,max(0,cash-1000-pet.savings()))
            town=getattr(self.policy_reference,'town',None) if self.policy_reference else None
            if town:budget=min(budget,max(0,cash-1000-town.equipment_savings()))
            for grid,price,item in offers:
                if not item.valid or price<=0:continue
                identity=item.identity
                if self.forging_economy and identity in self.catalog.focused_prices and not 1<=item.max_energy<=9:continue
                if identity in self.gear.gear and item.max_endurance>0 and item.endurance<=0:continue
                upgrade=self.gear.upgrade(w.own,identity,free,item) if self.focused_goods and identity in self.gear.gear else None
                desirable=identity in want or (bool(upgrade) if self.focused_goods else self.useful_gear(identity))
                if not desirable or (identity not in want and self.count(identity)>=1):continue
                cap=self.fair_cap(identity)
                if self.forging_economy and identity in self.catalog.focused_prices:
                    units=2**max(0,min(8,item.max_energy-1));cap=cap*units+50000*(units-1)
                    if self.crafting and identity in self.crafting.required_levels and item.max_energy>self.crafting.required_levels[identity]:continue
                if self.forging_economy and self.safe_forged(item):cap=self.item_ask_price(item)*1.1
                if self.focused_goods and self.ordinary_gear(item):cap=round(cap*(1+min(2,sum(v for k,v in item.instance_attributes if 26<=k<=30)/20)))
                if not cap or price>cap:continue
                # Bound quantity by actual need, native stock and earned budget.
                if price>budget:continue
                quantity=min(item.count,max(1,want.get(identity,1)),budget//price,99)
                if self.forging_economy and self.crafting and identity in self.crafting.gem_units_needed:
                    units=2**max(0,item.max_energy-1);quantity=min(quantity,math.ceil(self.crafting.gem_units_needed[identity]/units))
                if quantity<1:continue
                self.send(BUY,buy_request(owner,grid,quantity));self.buy_requests+=1
                self.pending=(identity,self.count(identity),cash,now+15,price,quantity)
                if self.forging_economy:self.pending_shape=(item.parameters,item.max_energy,sum(i.count for i in w.bag.values() if i.identity==identity and i.parameters==item.parameters and i.max_energy==item.max_energy))
                self.next_scan=now+120;break
    def opened(self,now):
        self.state='selling';self.trade_until=now+(120 if getattr(self,'focused',False) else 3600);self.confirmed_opens+=1;self.active_confirmed=True
        self.reason='торгует в городском ларьке'
    def finish(self,now):
        self.directory.release(self.name);self.state='idle';self.stock=[];self.pitch=None
        self.close_started=None;self.close_states_revision=None
        self.next_shift=now+self.rng.uniform(120,240) if self.forging_economy and self.gem_seller else now+self.rng.uniform(600,1200) if self.broad_goods else now+self.rng.uniform(1200,2400);self.reason='';self.active_confirmed=False
    def request_close(self,now):
        if self.state!='closing' or now>=self.deadline:
            if self.close_started is None:
                self.close_started=now;self.close_states_revision=getattr(self.world,'own_states_revision',0)
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
        if self.next_shift is None:self.next_shift=now+self.rng.uniform(20,120) if self.broad_goods else now+self.rng.uniform(60,600)
        if self.state in ('opening','selling','closing'):
            if self.directory.reserve(self.name,w.map,now) is None and self.state!='closing':
                self.request_close(now);return True
            if self.state=='closing':
                # Native StallAction(false) removes SSTATE_STALL=99. Require a
                # NEW own state snapshot, never stale startup/other-player data.
                if (getattr(w,'own_states_revision',0)>(self.close_states_revision or 0)
                        and not getattr(w,'own_states',{}).get(99) and w.bag_ready and not w.bag_disabled):
                    self.state_confirmed_closes+=1;self.finish(now);return False
                if self.close_started is not None and now-self.close_started>=60:
                    rescue=getattr(policy,'escape_plan',None)
                    if rescue and rescue.directory.claim(self.name,w.map,w.own.position,now):
                        from escape_plan import RecoveryResync
                        self.close_resyncs+=1;self.directory.release(self.name)
                        raise RecoveryResync('Нет подтверждения закрытия ларька60с; повторный вход для сверки состояния')
                if now>=self.deadline:
                    if self.active_confirmed:self.request_close(now)
                    else:self.finish(now)
                return True # Fail closed: no movement until authoritative closure.
            if self.state=='opening' and now>=self.deadline:
                self.timeouts+=1;self.request_close(now);return True
            if self.state=='selling' and (not safe or now>=self.trade_until or not self.stock):self.request_close(now)
            return True
        if self.pending:
            identity,count,cash,deadline,price=self.pending[:5]
            quantity=self.pending[5] if len(self.pending)>5 else 1
            if self.count(identity)==count+quantity and w.own.values.get(8,cash)==cash-price*quantity:
                shape_ok=True
                if self.pending_shape:
                    params,level,old=self.pending_shape
                    shape_ok=sum(i.count for i in w.bag.values() if i.identity==identity and i.parameters==params and i.max_energy==level)>=old+quantity
                if shape_ok:
                    self.confirmed_buys+=1;self.pending=None
                    if not self.pending_shape or self.pending_shape[1]<=1 and not any(self.pending_shape[0]):self.catalog.confirmed_price(identity,price)
                    self.pending_shape=None
                elif now>=deadline:self.pending=None;self.pending_shape=None;self.timeouts+=1
            elif now>=deadline:self.pending=None;self.pending_shape=None;self.timeouts+=1;self.next_scan=now+300
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
            titles=('Находки с охоты','Одежда и НП','Обнови свой шмот','Пергаменты и вещи','Снаряжение рядом','Трофеи в продаже','Лавка странника','С миру по нитке','Загляни за вещами','Добыча искателя','Шмот по карману','Трофеи без пыли')
            if self.forging_economy:titles=tuple(t[:15]+' '+self.name[-3:] for t in ('Камни кузнеца','Самоцветы на выбор','Гемы для твоего сета','Добыча с охоты','Камни и снаряжение','Свежие самоцветы','Для новой заточки','Мастерская у дороги','Есть что вставить','Полезные улучшения','Улучшайся со мной','Кузнечная лавка'))
            self.send(START,start_request(self.rng.choice(titles),self.stock));self.open_requests+=1
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
        if self.progression_first and not self.shift_allowed(policy,now):return False
        if now<self.next_shift or w.own.values.get(0,0)<self.minimum_level or not w.skills.get(241,{}).get('level',0) or not self.offers(policy):return False
        slot=self.directory.reserve(self.name,w.map,now)
        if slot is None:self.next_shift=now+60;return False
        if self.directory.argent_target is not None and self.life.npcs:
            pitches=self.directory.pitches(w.map,policy.home,policy.nav,self.life.npcs,
                                          (getattr(policy,'region',None) or {}).get('spawns',()))
            goal=pitches[slot] if slot<len(pitches) else None
        else:
            angle=(slot%10)*2*math.pi/10;radius=1200+600*(slot//10)
            point=(policy.home[0]+int(radius*math.cos(angle)),policy.home[1]+int(radius*math.sin(angle)))
            goal=policy.nav.nearest(point,6)
        if not goal or any(e.control in (2,3) and math.dist(e.position,goal)<350 for e in w.entities.values()):
            self.directory.release(self.name);self.next_shift=now+120;return False
        self.pitch=goal;self.state='travelling';self.deadline=now+300;self.reason='готовит городской ларёк';return True
    def shift_allowed(self,policy,now):
        if self.forging_economy:
            return now-policy.started>=120 and bool(getattr(policy,'economy',None) and policy.economy.phase(self.world,now)=='trade')
        # Hour-long shifts start after productive play, never immediately at login.
        return now-policy.started>=900 and bool(getattr(policy,'economy',None) and policy.economy.phase(self.world,now)=='trade')
    def loot_needs(self):return set(self.catalog.items)
    def summary(self):
        return {'state_confirmed_closes':self.state_confirmed_closes,'closure_resyncs':self.close_resyncs,'economic_role':'gem_seller' if self.forging_economy and self.gem_seller else 'developer' if self.forging_economy else None,'broad_useful_goods':self.broad_goods,'saleable_catalog_items':len(self.catalog.items),'minimum_level':self.minimum_level,'level_eligible':self.world.own.values.get(0,0)>=self.minimum_level,'owned_stall_books':self.count(3296),'unspent_life_points':self.world.own.values.get(13,0),'next_shift':self.next_shift,'state':self.state,'open_requests':self.open_requests,'confirmed_opens':self.confirmed_opens,
                'close_requests':self.close_requests,'purchase_requests':self.buy_requests,'confirmed_purchases':self.confirmed_buys,
                'sold_units_server_notices':self.sold_units,'timeouts':self.timeouts,'stall_skill_learned':bool(self.world.skills.get(241,{}).get('level',0)),
                'confirmed_book_learns':self.confirmed_learns,'goals':self.needed(),'rune_exchange_goal':self.rune_goal(),'black_market_barter_implemented':False}
