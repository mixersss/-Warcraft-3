"""Audited initial Argent story chain; real life EXP/points, no synthetic rewards."""
from career import Career
from classic_wire import Reader
import json
from pathlib import Path

CATALOG=json.loads((Path(__file__).resolve().parents[1]/'assets/story-quests.json').read_text())
STEPS=CATALOG['quests']


class Story(Career):
    def __init__(self,world,send,role,life,regions):
        super().__init__(world,send,role,life,regions)
        self.step=0;self.quest=dict(STEPS[0]);self.finished=False
        self.start_points=world.own.values.get(13);self.start_life_level=world.own.values.get(12)
        self.completed=set();self.path=None;self.save_errors=0
        self.queue=getattr(regions,'study_queue',None);self.owner=str(world.own_id)
        self.intermediate_wait=None
    def load(self,path):
        self.path=Path(path)
        try:
            data=json.loads(self.path.read_text())
            if data.get('version')==1:
                self.completed={i for i in data.get('confirmed_completed',[]) if type(i) is int and i in {q['journal'] for q in STEPS}}
                self.finished=(len(self.completed)==len(STEPS) or
                    data.get('end_journal')==STEPS[-1]['journal'] and STEPS[-1]['journal'] in self.completed)
                self.step=next((i for i,q in enumerate(STEPS) if q['journal'] not in self.completed),len(STEPS)-1)
                self.select_step()
        except (OSError,ValueError,TypeError,AttributeError):pass
    def save(self):
        if not self.path:return
        try:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            temp=self.path.with_suffix('.tmp')
            temp.write_text(json.dumps({'version':1,'confirmed_completed':sorted(self.completed),
                                      'end_journal':STEPS[-1]['journal'] if self.finished else None}))
            temp.replace(self.path)
        except OSError:self.save_errors+=1
    def study_turn(self,now):
        if not self.eligible():
            if self.queue:self.queue.release(self.owner,now)
            return False
        if self.context or self.pending:return True # Finish the current native exchange first.
        return self.queue.turn(self.owner,now) if self.queue else True
    def eligible(self):
        return (not self.finished and self.world.own.values.get(0,0)>=10
                and self.world.own.values.get(4,0)!=0)
    def select_step(self):
        if self.intermediate_wait:return
        active=next((i for i,q in enumerate(STEPS) if q['journal'] in self.journal),None)
        if active is not None:self.step=active
        if 207 in self.journal and not any(i.identity==3967 and i.count for i in self.world.bag.values()):
            intermediate=CATALOG['intermediates']['207']
            if any(i.identity==3966 and i.count for i in self.world.bag.values()):
                self.quest=dict(intermediate);return
            if 208 not in self.completed:
                self.step=next(i for i,q in enumerate(STEPS) if q['journal']==208)
        self.quest=dict(STEPS[self.step])
        if self.quest['journal'] in self.journal:
            self.quest['position']=self.quest['receiver']
            self.quest['map']=self.quest.get('receiver_map',self.quest['map'])
    def tick(self,now,policy,safe,dialogue_busy=False):
        if self.intermediate_wait:
            identity,before,deadline=self.intermediate_wait
            count=sum(i.count for i in self.world.bag.values() if i.identity==identity)
            if count<before:
                self.intermediate_wait=None;self.context=None;self.pending=None;self.next_visit=now+1
            elif now>=deadline:
                self.intermediate_wait=None;self.context=None;self.pending=None;self.next_visit=now+120;self.timeouts+=1
        if not self.context:self.select_step()
        return super().tick(now,policy,safe,dialogue_busy)
    def observe(self,command,payload,now):
        old=self.quest['journal'];previous=self.context;before_delivered=self.delivered
        used=super().observe(command,payload,now)
        if command==827 and self.pending==7 and self.quest.get('intermediate'):
            self.intermediate_wait=(3966,sum(i.count for i in self.world.bag.values() if i.identity==3966),now+12)
        if command in (828,830,832):self.select_step()
        if command==831 and self.delivered>before_delivered and old==int.from_bytes(payload[:2],'big'):
            self.completed.add(old)
            if self.step==len(STEPS)-1:self.finished=True
            else:self.step+=1;self.select_step();self.next_visit=now+15
            self.save()
        # On restart, unknown completed records are resolved through real NPC offers.
        if command==802 and previous and not self.context:
            self.step=(self.step+1)%len(STEPS);self.select_step();self.next_visit=now+120
        return used
    def summary(self):
        result=super().summary()
        result.update(start_life_points=self.start_points,life_points=self.world.own.values.get(13),
                      start_life_level=self.start_life_level,life_level=self.world.own.values.get(12),
                      chain_finished=self.finished)
        result.update(confirmed_history=sorted(self.completed),progress_save_errors=self.save_errors,
                      supported_history_steps=len(STEPS))
        return result
