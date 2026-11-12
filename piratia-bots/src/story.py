"""Audited initial Argent story chain; real life EXP/points, no synthetic rewards."""
from career import Career
from classic_wire import Reader

STEPS=[
 {'map':'garner','title':'Secretary Message','journal':200,'position':[222375,278525],
  'receiver':[221925,274925],'needs':[],'talk':True},
 {'map':'garner','title':'A Small Task','journal':203,'position':[221925,274925],
  'receiver':[227789,283199],'needs':[],'talk':True},
 {'map':'garner','title':'Food for the Navy','journal':204,'position':[227789,283199],
  'receiver':[227789,283199],'needs':[{'kind':1,'id':3963,'count':5},
                                    {'kind':1,'id':3964,'count':10},{'kind':1,'id':3116,'count':10}]}]

class Story(Career):
    def __init__(self,world,send,role,life,regions):
        super().__init__(world,send,role,life,regions)
        self.step=0;self.quest=dict(STEPS[0]);self.finished=False
        self.start_points=world.own.values.get(13);self.start_life_level=world.own.values.get(12)
    def eligible(self):
        return (not self.finished and self.world.map=='garner' and self.world.own.values.get(0,0)>=10
                and self.world.own.values.get(4,0)!=0)
    def select_step(self):
        active=next((i for i,q in enumerate(STEPS) if q['journal'] in self.journal),None)
        if active is not None:self.step=active
        self.quest=dict(STEPS[self.step])
        if self.quest['journal'] in self.journal:self.quest['position']=self.quest['receiver']
    def observe(self,command,payload,now):
        old=self.quest['journal'];previous=self.context;before_delivered=self.delivered
        used=super().observe(command,payload,now)
        if command in (828,830,832):self.select_step()
        if command==831 and self.delivered>before_delivered and old==int.from_bytes(payload[:2],'big'):
            if self.step==len(STEPS)-1:self.finished=True
            else:self.step+=1;self.select_step();self.next_visit=now+15
        # On restart, unknown completed records are resolved through real NPC offers.
        if command==802 and previous and not self.context:
            self.step=(self.step+1)%len(STEPS);self.select_step();self.next_visit=now+120
        return used
    def summary(self):
        result=super().summary()
        result.update(start_life_points=self.start_points,life_points=self.world.own.values.get(13),
                      start_life_level=self.start_life_level,life_level=self.world.own.values.get(12),
                      chain_finished=self.finished)
        return result
