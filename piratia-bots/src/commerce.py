"""Grounded item/price/meeting conversations backed by owned stock and live trades."""
import re,random
from inventory import BagItem

ALIASES={684:('новый пергамент','нового пергамента'),1092:('старый пергамент','старого пергамента'),
         885:('камень улучшения','камень заточки'),3457:('кал','каль')}
KINDS={'меч':(1,2),'мечи':(1,2),'посох':(9,),'лук':(3,),'ружье':(4,),'ружьё':(4,),
       'кольцо':(26,),'ожерелье':(25,),'руки':(23,),'перчатки':(23,),'ботинки':(24,),
       'голова':(20,21),'шлем':(20,21),'броня':(22,),'коралл':(29,)}

class Commerce:
    def __init__(self,policy,trade,life,name):
        self.policy,self.trade,self.life=policy,trade,life
        self.rng=random.Random(name+':commerce');self.last_ad=0;self.replies=0
        self.next_reply={}
        self.next_ad=None

    def due_advertisement(self,now):
        market=self.policy.market
        if not market or market.state!='selling':self.next_ad=None;return None
        if self.next_ad is None:self.next_ad=now+self.rng.uniform(20,140)
        return self.advertisement(now) if now>=self.next_ad else None

    def advertised(self,now):self.last_ad=now;self.next_ad=now+900

    def match(self,text,identities):
        words=set(re.findall(r'\w+',text));numbers=set(re.findall(r'(?<!\w)(?:id)?(\d+)\b',text))
        exact=[i for i in identities if str(i) in numbers]
        if exact:return exact
        exact=[i for i in identities if self.life.names.get(i,'').casefold() in text
               and self.life.names.get(i)]
        if exact:return exact
        exact=[i for i in identities if any(a in text for a in ALIASES.get(i,()))]
        if exact:return exact
        kinds={k for word,kinds in KINDS.items() if word in words for k in kinds}
        if kinds:return [i for i in identities if self.policy.market.gear.types.get(i) in kinds]
        if any(w in words for w in ('чертеж','чертёж','чертежи')):
            return [i for i in identities if self.policy.market.catalog.items.get(i,{}).get('category')=='blueprint']
        if any(w in words for w in ('руна','руны')):
            return [i for i in identities if self.policy.market.catalog.items.get(i,{}).get('category')=='rune']
        return []

    def location(self,now):
        w=self.policy.world;x,y=w.position(now)
        city={'garner':'Аргент','magicsea':'Шайтан','darkblue':'Ледынь'}.get(w.map,w.map)
        return f'{city}, {int(x//100)},{int(y//100)}'

    def label(self,identity):
        known={684:'Новый пергамент',1092:'Старый пергамент',885:'Камень улучшения'}
        if identity in known:return known[identity]
        kind=self.policy.market.gear.types.get(identity)
        labels={1:'Меч',2:'Двуручный меч',3:'Лук',4:'Ружьё',9:'Посох',20:'Головной убор',21:'Головной убор',
                22:'Доспех',23:'Перчатки',24:'Обувь',25:'Ожерелье',26:'Кольцо',29:'Коралл'}
        category=self.policy.market.catalog.items.get(identity,{}).get('category')
        return labels.get(kind) or {'blueprint':'Чертёж','rune':'Руна','gem':'Гем','kal':'Каль'}.get(category) or self.life.names.get(identity,'Предмет')[:20]

    def answer(self,name,text,now):
        text=text.casefold();words=set(re.findall(r'\w+',text))
        quote=self.trade.quotes.get(name.casefold())
        trade_words={'куплю','купить','купим','продам','продай','продашь','продаешь','продаёшь','продаете','продаёте',
                     'цена','цену','почем','почём','торг','торговать','обмен','дорого','дешевле','скидка'}
        if 'где' in words and 'купить' in words and not quote:return None
        meeting=bool(words & {'встретимся','встретиться','встреча','подойти'})
        if not words&trade_words and not (quote and meeting):return None
        if self.next_reply.get(name,0)>now:return None
        self.next_reply={k:v for k,v in self.next_reply.items() if v>now}
        if len(self.next_reply)<128:self.next_reply[name]=now+3
        self.replies+=1
        if meeting:
            from trade_dialogue import render
            return render(self.rng,'meeting',place=self.location(now))
        market=self.policy.market;w=self.policy.world
        if words&{'дорого','дешевле','скидка','торг'} and quote and quote['until']>now:
            return f"Пока цена {quote['price']}G за {quote['count']} шт. Если подходит, открой «Торговать»."
        if words&{'продам','продаю'}:
            ids=self.match(text,market.catalog.items)
            if not ids:return 'Что предлагаешь? Напиши название или ID предмета и цену, например: продам 684 за 5000.'
            identity=ids[0];wanted=identity in market.needed() or market.useful_gear(identity)
            cap=min(market.fair_cap(identity),max(0,w.own.values.get(8,0)//5),max(0,w.own.values.get(8,0)-1000))
            requested=re.search(r'(?:за|цена)\s*(\d+)',text)
            if not wanted:return f'Предмет ID{identity} сейчас мне не нужен. Ищу то, что улучшит мой комплект или нужно для развития.'
            if cap<=0:return 'Сейчас не хватает свободных денег на покупку.'
            price=int(requested.group(1)) if requested else cap
            if price<=0 or price>cap:return f'За ID{identity} могу заплатить до {cap}G за штуку.'
            item=BagItem(identity,1,0,0,0,0,0,True)
            self.trade.quote_item(name,item,1,price,'buy',now)
            return f'Куплю ID{identity}, 1 шт. за {price}G. Нужна обычная вещь без заточки. Подойди и нажми «Торговать».'
        offers=market.offers(self.policy)
        stock={w.bag[slot].identity:(price,count,slot) for _,price,count,slot in offers}
        identities=self.match(text,stock)
        identity=identities[0] if identities else quote['item'].identity if quote and quote['until']>now and quote['mode']=='sell' else next(iter(stock),None)
        if identity not in stock:return 'Подходящего товара в сумке сейчас нет. Напиши точное название или ID, чтобы я проверил.'
        price,count,slot=stock[identity];item=w.bag[slot]
        count=count if 'все' in words or 'всё' in words else 1
        self.trade.quote_item(name,item,count,price*count,'sell',now)
        if market.state in ('opening','selling') and words&{'куплю','купить','торговать','обмен'}:
            market.request_close(now)
            return f'ID{identity}: {count} шт. за {price*count}G. Закрываю ларёк; после закрытия нажми «Торговать».'
        return f'{self.label(identity)} ID{identity}: {count} шт. за {price*count}G. Я: {self.location(now)}. «Торговать».'

    def advertisement(self,now):
        p=self.policy;market=p.market
        if not market or market.state!='selling' or not market.active_confirmed or not market.stock:return None
        available=[]
        for grid,price,count,slot in market.stock:
            item=p.world.bag.get(slot)
            if item and item.count>=count:available.append((item.identity,count,price))
        if not available:return None
        identity,count,price=self.rng.choice(available)
        # All variable facts are server-observed; wording never invents stock, actions or discounts.
        from trade_dialogue import render
        return render(self.rng,'sale',item=identity,count=count,price=price,place=self.location(now),label=self.label(identity))
