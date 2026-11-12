"""Bounded local dialogues; advance only on the peer's real server chat echo."""
import json,math,random,threading
from pathlib import Path

class Conversations:
    def __init__(self,assets,seed='local'):
        self.lock=threading.Lock();self.rng=random.Random(seed)
        assets=Path(assets)
        self.bank=json.loads((assets/'chat-phrases.json').read_text(encoding='utf-8'))
        self.dialogues=json.loads((assets/'bot-dialogues.json').read_text(encoding='utf-8'))
        self.rows={};self.humans={};self.active=None;self.next_start=None;self.serial=0
        self.started=self.completed=self.expired=0
    def register(self,name,map_name,identity,position,now,ready):
        with self.lock:
            old=self.rows.get(name,{})
            self.rows[name]={'map':map_name,'identity':identity,'position':tuple(position),
                             'until':now+15,'ready':ready,'last':old.get('last',-1e9)}
            if self.next_start is None:self.next_start=now+self.rng.uniform(20,40)
    def _end(self,now,completed=False):
        if completed:self.completed+=1
        else:self.expired+=1
        self.active=None;self.next_start=now+self.rng.uniform(30,60)
    def _clean(self,now):
        for key,until in list(self.humans.items()):
            if until<=now:self.humans.pop(key,None)
        for name,row in list(self.rows.items()):
            if row['until']<=now:self.rows.pop(name,None)
        if self.active:
            a=self.rows.get(self.active['a']);b=self.rows.get(self.active['b'])
            if (not a or not b or a['map']!=b['map'] or math.dist(a['position'],b['position'])>2000
                    or now>self.active['expires']):self._end(now)
    def claim_human(self,map_name,source,intent,now):
        with self.lock:
            self._clean(now);key=(map_name,source,intent)
            if key in self.humans:return False
            self.humans[key]=now+30
            while len(self.humans)>256:self.humans.pop(next(iter(self.humans)))
            return True
    def prepare(self,name,visible_ids,now,safe):
        with self.lock:
            self._clean(now)
            if not safe:return None
            if not self.active:
                if self.next_start is None or now<self.next_start:return None
                own=self.rows.get(name)
                if not own or not own['ready'] or now-own['last']<180:return None
                peers=[(n,r) for n,r in self.rows.items() if n!=name and r['ready']
                       and r['map']==own['map'] and r['identity'] in visible_ids and now-r['last']>=180
                       and math.dist(r['position'],own['position'])<=1800]
                if not peers:return None
                self.rng.shuffle(peers);peer,row=peers[0];dialogue=self.rng.choice(self.dialogues)
                lines=[self.bank[k][dialogue[v]] for k,v in (('bot_open','open'),('bot_reply','reply'),('bot_close','close'))]
                self.serial+=1
                self.active={'id':self.serial,'a':name,'b':peer,'stage':0,'lines':lines,
                             'sent':False,'due':now,'expires':now+30}
                own['last']=row['last']=now;self.started+=1
            item=self.active
            speaker=item['b'] if item['stage']==1 else item['a']
            listener=item['a'] if item['stage']==1 else item['b']
            if speaker!=name or item['sent'] or now<item['due']:return None
            receiver=self.rows[listener]
            if receiver['identity'] not in visible_ids:return None
            return (item['id'],item['stage']),listener+', '+item['lines'][item['stage']]
    def sent(self,name,token,now):
        with self.lock:
            item=self.active
            if not item or token!=(item['id'],item['stage']):return False
            speaker=item['b'] if item['stage']==1 else item['a']
            if speaker!=name or item['sent']:return False
            item['sent']=True;item['expires']=now+30
            return True
    def receive(self,name,source,text,now):
        with self.lock:
            self._clean(now);item=self.active
            if not item or not item['sent']:return False
            speaker=item['b'] if item['stage']==1 else item['a']
            listener=item['a'] if item['stage']==1 else item['b']
            if (name!=listener or source!=self.rows[speaker]['identity']
                    or text!=listener+', '+item['lines'][item['stage']]):return False
            if item['stage']==2:self._end(now,completed=True)
            else:
                item['stage']+=1;item['sent']=False;item['due']=now+self.rng.uniform(4,8);item['expires']=now+35
            return True
    def remove(self,name,now):
        with self.lock:
            self.rows.pop(name,None)
            if self.active and name in (self.active['a'],self.active['b']):self._end(now)
    def summary(self):
        with self.lock:return {'dialogues_started':self.started,'dialogues_completed':self.completed,
                               'dialogues_expired':self.expired,'active_dialogues':int(self.active is not None)}
