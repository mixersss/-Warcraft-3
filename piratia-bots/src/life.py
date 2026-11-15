"""Audited progression metadata and owned beginner chest use."""
import json,struct
from pathlib import Path

class LifeItems:
    def __init__(self,assets):
        data=json.loads((Path(assets)/'life-items.json').read_text(encoding='utf-8'))
        self.books={int(k):v for k,v in data['books'].items()}
        self.chests={int(k):v for k,v in data['chests'].items()}
        self.names={int(k):v for k,v in data['names'].items()}
        self.prices={int(k):v for k,v in data['prices'].items()}
        goal_path=Path(assets)/'equipment-goals.json'
        self.equipment_goals=json.loads(goal_path.read_text()) if goal_path.exists() else None
        self.skill_guides=None
        guide=Path(assets)/'skill-guides.json'
        if guide.exists():
            from skill_plan import validate_guides
            self.skill_guides=validate_guides(json.loads(guide.read_text(encoding='utf8')),self.books)
        from owner_shops import read_overlay
        self.owner_shops=None;self.owner_shop_problem=None
        try:self.owner_shops=read_overlay(assets)
        except (OSError,ValueError,TypeError,KeyError,AttributeError) as error:self.owner_shop_problem=type(error).__name__
        if self.owner_shops:
            self.prices.update({int(k):v for k,v in self.owner_shops['prices'].items()})
            self.names.update({int(k):v for k,v in self.owner_shops['names'].items()})
        self.services=json.loads((Path(assets)/'town-services.json').read_text(encoding='utf-8'))
        self.npcs=None
        if (Path(assets)/'world-npcs.json').exists():
            from npc_knowledge import NpcKnowledge
            item_types={int(k):v for k,v in json.loads((Path(assets)/'items.json').read_text())['types'].items()}
            self.npcs=NpcKnowledge(Path(assets)/'world-npcs.json',item_types,self.names,self.prices,
                                   self.owner_shops['npcs'] if self.owner_shops else ())
            for npc in self.npcs.shops():
                shops=self.services['shops'].setdefault(npc['map'],[])
                if not any(s['position']==npc['position'] and s['name']==npc['name'] for s in shops):
                    shops.append({'name':npc['name'],'position':npc['position'],'offers':npc['offers'],'region':npc['region']})
                    if npc.get('menu_pages'):shops[-1]['menu_pages']=npc['menu_pages']
                    if npc.get('menu_labels'):shops[-1]['menu_labels']=npc['menu_labels']

    def can_learn(self,world,book):
        own=world.own
        if own.values.get(0,0)<book['level'] or str(own.values.get(4)) not in book['jobs']:return False
        return all(world.skills.get(skill,{}).get('level',0)>=level for skill,level in book['prerequisites'])

class Chests:
    def __init__(self,world,catalog):
        self.world,self.catalog=world,catalog
        self.pending=None;self.next_use=0;self.requests=self.confirmed=self.timeouts=0
    def tick(self,now,policy,safe):
        w=self.world
        if self.pending:
            slot,identity,count,deadline=self.pending
            item=w.bag.get(slot)
            if not item or item.identity!=identity or item.count<count:
                self.confirmed+=1;self.pending=None
            elif now>deadline:
                self.timeouts+=1;self.pending=None;self.next_use=now+300
            return False
        if not safe or now<self.next_use or not w.bag_ready or w.bag_disabled:return False
        free=(w.bag_capacity or 0)-len(w.bag)
        for slot,item in w.bag.items():
            rule=self.catalog.chests.get(item.identity)
            if (rule and item.valid and w.own.values.get(0,0)>=rule['level'] and free>=rule['free_slots']
                    and (not rule['job_required'] or w.own.values.get(4,0)!=0)):
                from hunter import action_header
                policy.emit(action_header(w.own_id,policy.sequence,11)+struct.pack('>hh',slot,-1))
                self.pending=slot,item.identity,item.count,now+12
                self.next_use=now+5;self.requests+=1
                return True
        return False
    def summary(self):return {'requests':self.requests,'confirmed_consumptions':self.confirmed,'timeouts':self.timeouts}
