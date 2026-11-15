"""Shared finite chat leases/scenes; all turns require actual server echoes."""
import hashlib,math,random,threading,re
from collections import OrderedDict

class BotCoordinator:
    def __init__(self,settings):
        self.lock=threading.RLock();self.rows={};self.claims=OrderedDict();self.settings=settings
        self.scene=None;self.serial=0;self.next_scene=0;self.global_local=0;self.pairs={}
        self.owners=OrderedDict()
        self.rng=random.Random('piratia-social-scheduler50');self.started=self.finished=self.interrupted=0
    def register(self,name,row):
        with self.lock:self.rows[name]=dict(row)
    def remove(self,name):
        with self.lock:
            self.rows.pop(name,None)
            if self.scene and name in self.scene['members']:self.scene=None
    def _clean(self,now):
        self.rows={n:r for n,r in self.rows.items() if r['until']>now}
        self.pairs={k:t for k,t in self.pairs.items() if t>now}
        for key,row in list(self.owners.items()):
            if row[1]<=now:self.owners.pop(key,None)
        if self.scene and now>=self.scene['expires']:self.scene=None;self.finished+=1;self.next_scene=now+90
        while self.claims and (next(iter(self.claims.values()))[1]<=now or len(self.claims)>512):self.claims.popitem(last=False)
    def elect(self,name,channel,map_name,source,text,now,visible=()):
        with self.lock:
            self._clean(now)
            words=set(re.findall(r'\w+',text.casefold()));named=[n for n in self.rows if n.casefold() in words]
            if named and name!=named[0]:return False
            candidates=[n for n,r in self.rows.items() if r['ready'] and
                        (channel!='local' or r['map']==map_name and r['identity'] in visible) and
                        (channel not in ('world','trade') or r['cash']>=(20000 if channel=='trade' else 2000))]
            if named:candidates=[n for n in candidates if n==named[0]]
            if not candidates:return False
            key=(channel,map_name if channel=='local' else '*',str(source),hashlib.sha256(text.encode('utf8')).hexdigest()[:16])
            previous=self.claims.get(key)
            if previous:return False # One observation, not one response per bot.
            owner_key=key[:3];owner=self.owners.get(owner_key)
            chosen=(named[0] if named else owner[0] if owner and owner[0] in candidates else
                    sorted(candidates)[int(hashlib.sha256(repr(key).encode()).hexdigest()[:8],16)%len(candidates)])
            if chosen!=name:return False
            self.claims[key]=(name,now+20)
            self.owners[owner_key]=(name,now+180);self.owners.move_to_end(owner_key)
            while len(self.owners)>512:self.owners.popitem(last=False)
            if self.scene and self.scene['channel']==channel and (channel!='local' or self.scene['map']==map_name):
                self.scene=None;self.interrupted+=1;self.next_scene=now+120
            return True
    def claim_pair(self,name,peer,channel,now):
        with self.lock:
            key=(name,peer,channel)
            if self.pairs.get(key,0)>now:return False
            self.pairs[key]=now+3;return True
    def start(self,name,now):
        with self.lock:
            self._clean(now)
            if self.settings['intensity']=='quiet' or self.scene or now<self.next_scene:return None
            own=self.rows.get(name)
            if not own or not own['ready']:return None
            if self.next_scene==0:self.next_scene=now+self.rng.uniform(45,100);return None
            peers=[n for n,r in self.rows.items() if n!=name and r['ready'] and r['map']==own['map']
                   and r['identity'] in own['visible'] and math.dist(r['position'],own['position'])<=1800]
            if not peers:self.next_scene=now+30;return None
            self.rng.shuffle(peers);members=[name,*peers[:self.rng.randint(1,3)]]
            channel='local';topic=self.rng.choice(('level','activity','fairy'))
            # Paid world conversations are rare and keep the existing global120s spacing.
            if own['cash']>=20000 and all(self.rows[n]['cash']>=20000 for n in members) and self.rng.random()<.04:channel='world'
            self.serial+=1;self.started+=1
            question={'level':'какой у тебя уровень?','activity':'чем сейчас занят?','fairy':'как у тебя с феей?'}[topic]
            text=members[1]+', '+question
            sellers=[(n,r) for n,r in self.rows.items() if n!=name and r['ready'] and r.get('sale') and
                     r['sale'][0] in own.get('wanted',()) and r['sale'][1]<=own['cash']//5 and r['cash']>=20000]
            if own['cash']>=20000 and sellers and self.rng.random()<.2:
                seller,row=self.rng.choice(sellers);members=[name,seller];channel='trade';topic='trade'
                text=seller+f", куплю ID{row['sale'][0]}. Какая цена?"
            self.scene={'id':self.serial,'members':members,'channel':channel,'map':own['map'],'turn':0,
                        'topic':topic,'item':row['sale'][0] if topic=='trade' else None,
                        'sender':name,'receiver':members[1],'text':text,'sent':False,'expires':now+(900 if channel in ('world','trade') else 90)}
            return dict(self.scene)
    def scene_for(self,name,channel,source,text,now):
        with self.lock:
            self._clean(now);s=self.scene
            if not s or not s['sent'] or s['receiver']!=name or s['sender']!=source or s['channel']!=channel or s['text']!=text:return None
            s['turn']+=1
            if s['turn']>=len(s['members']):
                self.scene=None;self.finished+=1;self.next_scene=now+(90 if self.settings['intensity']=='lively' else 180)
                return {'finish':True}
            members=s['members'];index=(members.index(name)+1)%len(members);receiver=members[index]
            s.update(sender=name,receiver=receiver,text=None,sent=False)
            return {'id':s['id'],'receiver':receiver,'channel':channel,'finish':False,'topic':s['topic'],'item':s['item']}
    def prepare_scene_reply(self,token,text):
        with self.lock:
            if self.scene and self.scene['id']==token:self.scene['text']=text
    def sent(self,token,name,text):
        with self.lock:
            if self.scene and self.scene['id']==token and self.scene['sender']==name and self.scene['text']==text:self.scene['sent']=True
    def valid_scene(self,token):
        with self.lock:return bool(self.scene and self.scene['id']==token)
    def summary(self):
        with self.lock:return {'started_scenes':self.started,'completed_or_expired':self.finished,'player_interruptions':self.interrupted,'active_scenes':int(self.scene is not None),'known_clients':len(self.rows)}

class SocialScheduler:
    def __init__(self,coordinator):self.coordinator=coordinator
    def prepare(self,name,now):return self.coordinator.start(name,now)
