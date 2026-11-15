"""New parchment684 -> native Caribbean map682 -> ticket2445 -> real digging.

Audited owner ItemUse_Map_JLBYPJ/ItemUse_JLB_GoldenMap/CheckGetMapPos.
No generated coordinates, invented rewards, free tickets or local teleport.
"""
import re
import struct
from classic_wire import Reader,ProtocolError
PROTECTED={682,1093,2445}

class TreasureHunt:
    def __init__(self,world,economy):
        self.world,self.economy=world,economy
        self.pending=None;self.point=None;self.origin=None;self.next_try=0;self.trip_until=None
        self.requests=self.maps_created=self.completed=self.timeouts=0;self.reason=''
    def count(self,identity):return sum(i.count for i in self.world.bag.values() if i.identity==identity)
    def eligible(self):return bool(self.world.own.values.get(4) and 15<=self.world.own.values.get(0,0)<=40)
    def purchase_goals(self):
        w=self.world
        if not self.eligible() or not (self.count(684) or self.count(682)):return []
        result=[]
        if w.map!='jialebi':
            if not self.count(2445):result.append((2445,1,'билет для настоящего поиска сокровищ'))
            home={'garner':4602,'magicsea':4603,'darkblue':4604}.get(w.map)
            if home and not self.count(home):result.append((home,1,'обратный билет из Карибов'))
        return result
    def observe(self,command,payload):
        if command!=517 or not self.pending or self.pending[0]!='locate':return
        try:
            r=Reader(payload);text=r.string();r.end()
        except (ProtocolError,UnicodeError):return
        match=re.fullmatch(r'Treasure is hidden at Treasure GulfRegion(\d+),(\d+) nearby',text)
        if match and all(0<int(v)<4096 for v in match.groups()):self.point=tuple(int(v)*100 for v in match.groups())
    def use(self,kind,slot,now,policy):
        from hunter import action_header
        before=(self.count(684),self.count(682))
        policy.emit(action_header(self.world.own_id,policy.sequence,11)+struct.pack('>hh',slot,-1))
        self.pending=(kind,before,now+12);self.requests+=1
    def tick(self,now,policy,safe,dialogue_busy=False):
        w=self.world
        if not w.bag_ready or w.bag_disabled:return False
        if self.origin==w.map and self.trip_until is not None and not policy.stuck_return.pending:
            self.origin=None;self.trip_until=None;self.point=None;self.next_try=now+900
            self.reason='возврат завершён; продолжает обычные дела';return False
        if self.pending:
            kind,before,deadline=self.pending
            if kind=='create' and self.count(684)<before[0] and self.count(682)>before[1]:
                self.maps_created+=1;self.pending=None
            elif kind=='dig' and self.count(682)<before[1]:
                self.completed+=1;self.pending=None;self.trip_until=now
                self.reason='карта израсходована сервером; результат раскопки получен'
            elif kind=='locate':
                item=next((i for i in w.bag.values() if i.identity==682),None)
                if item and item.endurance==1 and item.max_endurance and item.max_energy:
                    self.point=(item.max_endurance*100,item.max_energy*100)
                if self.point:self.pending=None
            if self.pending:
                if now>=deadline:
                    self.pending=None;self.timeouts+=1;self.next_try=now+30
                    if kind=='dig':self.next_try=now+3 # Native dig has a real 1/3 success chance.
                    self.reason='нет подтверждения раскопки/карты; ограниченный повтор'
                    return False
                return True
        if (not safe or dialogue_busy or now<self.next_try or not self.eligible()
                or policy.transaction_busy()):return False
        if w.map=='jialebi' and self.origin and (not self.count(682) or (self.trip_until and now>=self.trip_until)):
            self.reason='возвращается после поиска сокровищ'
            return policy.stuck_return.tick(now,policy,self.origin)
        if not self.count(682) and not self.count(684):return False
        if not self.trip_until and self.economy.phase(w,now)!='income':return False
        if (w.bag_capacity or 0)-len(w.bag)<2:return False
        if not self.count(682):
            slot=next((s for s,i in w.bag.items() if i.identity==684 and i.valid),None)
            if slot is None:return False
            self.use('create',slot,now,policy);self.reason='раскрывает собственный новый пергамент';return True
        slot,item=next(((s,i) for s,i in w.bag.items() if i.identity==682 and i.valid),(None,None))
        if item is None or self.count(682)!=1:return False
        if not self.point:
            self.use('locate',slot,now,policy);self.reason='читает настоящие координаты карты';return True
        if w.map!='jialebi':
            home={'garner':4602,'magicsea':4603,'darkblue':4604}.get(w.map)
            if not home or not self.count(home) or not self.count(2445):
                self.reason='нужны оплаченные билет в Карибы и обратный билет';return False
            self.origin=w.map;self.trip_until=now+300
            self.reason='использует собственный билет к карте сокровищ'
            return policy.stuck_return.tick(now,policy,'jialebi')
        import math
        if math.dist(w.position(now),self.point)>350:
            goal=policy.nav.nearest(self.point,3)
            if goal and math.dist(goal,self.point)<=350 and policy.move_to(goal,now):
                self.reason='идёт к координатам собственной карты';return True
            self.trip_until=now;self.reason='нет проверенного пути к кладу; возвращается';return False
        self.use('dig',slot,now,policy);self.reason='копает по собственной карте; ждёт результат сервера';return True
    def summary(self):return {'state':self.reason,'native_use_requests':self.requests,'confirmed_maps':self.maps_created,'maps_consumed':self.completed,'timeouts':self.timeouts,'map_point':self.point,'required_level':[15,40],'rewards_never_invented':True}
