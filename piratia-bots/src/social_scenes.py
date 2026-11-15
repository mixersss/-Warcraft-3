"""A few independent, finite nearby conversations; native echoes advance each turn."""
import math
from collections import OrderedDict
from chat_coordinator import BotCoordinator

class SocialBotCoordinator(BotCoordinator):
    def __init__(self,settings,scripts):
        super().__init__(settings);self.scripts=scripts;self.scenes=OrderedDict();self.area_delays=OrderedDict()
        self.next_start=0;self.next_world_question=0;self.scene_limit=3
    def _clean_scenes(self,now):
        self._clean(now)
        for token,s in list(self.scenes.items()):
            if now>=s['expires'] or any(n not in self.rows for n in s['members']):
                self.scenes.pop(token,None);self.finished+=1
        while len(self.area_delays)>256:self.area_delays.popitem(last=False)
    def remove(self,name):
        super().remove(name)
        with self.lock:
            for token,s in list(self.scenes.items()):
                if name in s['members']:self.scenes.pop(token,None)
    def elect(self,*args,**kwargs):
        won=super().elect(*args,**kwargs)
        if won:
            name,channel,map_name=args[:3]
            with self.lock:
                own=self.rows.get(name)
                for token,s in list(self.scenes.items()):
                    nearby=own and math.dist(own['position'],s['position'])<=4000
                    if s['channel']==channel and (channel!='local' or s['map']==map_name and nearby):
                        self.scenes.pop(token,None);self.interrupted+=1
        return won
    def start(self,name,now):
        with self.lock:
            self._clean_scenes(now)
            if self.settings['intensity']=='quiet' or len(self.scenes)>=self.scene_limit or now<self.next_start:return None
            own=self.rows.get(name)
            busy={n for s in self.scenes.values() for n in s['members']}
            if not own or not own['ready'] or name in busy:return None
            area=(own['map'],int(own['position'][0]//3000),int(own['position'][1]//3000))
            if area not in self.area_delays:
                self.area_delays[area]=now+self.rng.uniform(15,40);return None
            if now<self.area_delays[area]:return None
            peers=[n for n,r in self.rows.items() if n!=name and n not in busy and r['ready'] and r['map']==own['map']
                   and r['identity'] in own['visible'] and math.dist(r['position'],own['position'])<=1800]
            channel='local'
            if now>=self.next_world_question and own['cash']>=20000 and self.rng.random()<.12:
                distant=[n for n,r in self.rows.items() if n!=name and n not in busy and r['ready'] and r['cash']>=20000]
                if distant:peers=distant;channel='world';self.next_world_question=now+420
            if not peers:self.area_delays[area]=now+30;return None
            self.rng.shuffle(peers);members=[name,*peers[:1 if channel=='world' else self.rng.randint(1,3)]]
            topic=self.rng.choice([*self.scripts['topics'],'joke'])
            if topic=='joke':body=self.rng.choice(self.scripts['jokes'])
            else:body=self.rng.choice(self.scripts['topics'][topic]['questions'])
            text=('Народ, ' if channel=='world' else members[1]+', ')+body
            self.serial+=1;self.started+=1;self.next_start=now+5
            self.area_delays[area]=now+(45 if self.settings['intensity']=='lively' else 75)+self.rng.uniform(0,30)
            s={'id':self.serial,'members':members,'channel':channel,'map':own['map'],'position':own['position'],
               'topic':topic,'item':None,'turn':0,'max_turns':2 if channel=='world' else len(members)*2,
               'sender':name,'receiver':members[1],'text':text,'sent':False,'expires':now+(360 if channel=='world' else 120)}
            self.scenes[self.serial]=s;return dict(s)
    def scene_for(self,name,channel,source,text,now):
        with self.lock:
            self._clean_scenes(now)
            s=next((s for s in self.scenes.values() if s['sent'] and s['receiver']==name and s['sender']==source and s['channel']==channel and s['text']==text),None)
            if not s:return None
            s['turn']+=1
            if s['turn']>=s['max_turns']:
                self.scenes.pop(s['id']);self.finished+=1;return {'finish':True}
            receiver=s['members'][(s['members'].index(name)+1)%len(s['members'])]
            s.update(sender=name,receiver=receiver,text=None,sent=False)
            return {'id':s['id'],'receiver':receiver,'channel':channel,'finish':False,'topic':s['topic'],'item':None,
                    'closing':s['turn']>=len(s['members'])}
    def prepare_scene_reply(self,token,text):
        with self.lock:
            if token in self.scenes:self.scenes[token]['text']=text
    def sent(self,token,name,text):
        with self.lock:
            s=self.scenes.get(token)
            if s and s['sender']==name and s['text']==text:s['sent']=True
    def valid_scene(self,token):
        with self.lock:return token in self.scenes
    def summary(self):
        with self.lock:return {'started_scenes':self.started,'completed_or_expired':self.finished,'player_interruptions':self.interrupted,
                              'active_scenes':len(self.scenes),'maximum_parallel_scenes':self.scene_limit,'known_clients':len(self.rows),
                              'topics':len(self.scripts['topics'])+1,'native_echo_required':True}
