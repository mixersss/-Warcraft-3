"""Shared ground navigation for paired maps and beginner farms for three home cities."""
import json
import math
import threading
from functools import cached_property,lru_cache
from pathlib import Path
from navigation import Navigation


class Regions:
    def __init__(self,assets,population_count=200):
        self.assets=Path(assets)
        from coordination import Coordination
        self.coordination=Coordination(population_count)
        from party import BotDirectory
        self.directory=BotDirectory()
        from escape_plan import RescueDirectory
        self.rescue_resyncs=RescueDirectory()
        from cooperation import HelpDirectory
        self.help_directory=HelpDirectory()
        from conversations import Conversations
        self.conversations=Conversations(self.assets)
        from public_chat import PublicBudget
        self.public_chat_budget=PublicBudget()
        self.dialogue_data=None;self.chat_coordinator=None;self.dialogue_error=None
        try:
            from dialogue_data import DialogueData
            from chat_coordinator import BotCoordinator
            self.dialogue_data=DialogueData(self.assets)
            if self.dialogue_data.scenes:
                from social_scenes import SocialBotCoordinator
                self.chat_coordinator=SocialBotCoordinator(self.dialogue_data.settings,self.dialogue_data.scenes)
            else:self.chat_coordinator=BotCoordinator(self.dialogue_data.settings)
            self.public_chat_budget.scale=2 if self.dialogue_data.settings['intensity']=='quiet' else 1
        except Exception as exc:self.dialogue_error=type(exc).__name__
        from equipment import ItemCatalog
        self.items=ItemCatalog(self.assets/'items.json')
        from life import LifeItems
        self.life=LifeItems(self.assets)
        self.npc_knowledge=self.life.npcs
        from study_queue import StudyQueue
        self.study_queue=StudyQueue(limit=max(1,min(20,population_count//10)))
        from market import MarketCatalog,MarketDirectory
        self.market_catalog=MarketCatalog(self.assets);self.market_catalog.enable_broad_catalog()
        self.market_catalog.enable_curated_catalog()
        from market_prices import MarketPrices
        self.market_catalog.prices=MarketPrices(self.assets.parent/'data'/'market-prices.json')
        total=population_count//10
        argent=round(total*.75);remaining=total-argent
        forging_economy=bool(self.life.owner_shops and self.life.owner_shops.get('catalog_revision',0)>=58)
        if forging_economy:self.market_catalog.enable_forging_catalog(self.items,self.life)
        self.market_directory=MarketDirectory(city_limits={'garner':argent,'magicsea':(remaining+1)//2,'darkblue':remaining//2},live_count=self.directory.active_count,argent_target=120 if forging_economy else 60)
        from activity_slots import ActivitySlots
        self.rest_directory=ActivitySlots(population_count,live_count=self.directory.active_count)
        from mob_knowledge import MobKnowledge
        knowledge=self.assets/'world-mobs.json'
        self.mob_knowledge=MobKnowledge(knowledge) if knowledge.exists() else None
        from mechanics import load_knowledge
        mechanics=self.assets/'mechanics.json'
        self.mechanics=load_knowledge(self.assets,self.npc_knowledge,self.mob_knowledge) if mechanics.exists() else None
        portals=self.assets/'portals.json'
        self.portal_catalog=json.loads(portals.read_text(encoding='utf-8')) if portals.exists() else None
        self.data=json.loads((self.assets/'regions.json').read_text(encoding='utf-8'))
        catalog=self.assets/'world-navigation.json'
        self.map_catalog=json.loads(catalog.read_text(encoding='utf-8')).get('maps',{}) if catalog.exists() else {}
        self.navigation_lock=threading.Lock()
        travel=self.assets/'hunting-travel58.json'
        self.hunting_travel_data=json.loads(travel.read_text()) if travel.exists() else None
        self.full_regions=forging_economy
        # Home-city tables predate the land/sea audit. A dry point inside a
        # huge sea spawn rectangle does not make its monster a ground target.
        if self.mob_knowledge:
            for region in self.data.values():
                region['farms']={identity:dict(farm,territory=0)
                    for identity,farm in region['farms'].items()
                    if (self.mob_knowledge.get(int(identity)) or {}).get('territory')==0}
        self.navigation={name:Navigation(self.assets/info['navigation']) for name,info in self.data.items()}
        for nav in self.navigation.values():nav.enable_incremental()
        if self.life.owner_shops and self.life.owner_shops.get('catalog_revision',0)>=60 and self.mob_knowledge:
            from farm_scouting import scout_points
            for name,region in self.data.items():
                nav=self.navigation[name]
                for identity,farm in region['farms'].items():
                    locations=self.mob_knowledge.by_map.get(name,{}).get(int(identity),[])
                    farm['points']=scout_points(nav,locations,farm['points'])
                    farm['source_region_scouting']=True

    def get(self,name):
        if name not in self.data and getattr(self,'full_regions',False) and name in self.map_catalog and self.mob_knowledge:
            farms={}
            for identity,locations in self.mob_knowledge.by_map.get(name,{}).items():
                mob=self.mob_knowledge.get(identity)
                if mob.get('territory')!=0:continue # Ships remain a separate native control mode.
                points=[]
                for location in locations:
                    lo,hi=location['rectangle_cm']
                    points.extend([(int((lo[0]+hi[0])/2),int((lo[1]+hi[1])/2)),tuple(lo),tuple(hi),(lo[0],hi[1]),(hi[0],lo[1])])
                farms[str(identity)]={**{k:mob[k] for k in ('level','hp','drops','base_xp','defence','attack_max')},'territory':0,'points':list(dict.fromkeys(points)),'source_regions_not_live_positions':True}
            births=(self.hunting_travel_data or {}).get('birthplaces',{})
            spawns=list(dict.fromkeys(tuple(p) for b in births.values() if b['map']==name for p in b['points']))
            self.data.setdefault(name,{'birthplace':name,'label':name,'spawns':spawns,'farms':farms,'navigation':self.map_catalog[name]['navigation']})
        return self.data.get(name)

    @lru_cache(maxsize=512)
    def hunting_arrival_sites(self,map_name,arrival):
        """Known camps on the same land component as a native arrival."""
        region=self.get(map_name)
        if not region:return {}
        nav=self.nav(map_name)
        component=nav.land_component(arrival)
        if not component:return {}
        sites={}
        for identity,farm in region['farms'].items():
            closest=min((math.dist(arrival,p) for p in farm['points']
                         if nav.land_component(p)==component and nav.combat_allowed(p)),default=math.inf)
            if closest<=25000:sites[int(identity)]=closest
        return sites

    @cached_property
    def mine_exit_entrance(self):
        return next((e for e in (self.hunting_travel_data or {}).get('entrances',[])
                     if e['name']=='Abandoned Mine 1 - Abandoned Mine 2'),None)

    @cached_property
    def mine_exit_steps(self):
        # Source-backed exits from the detached Abandoned Mine 1 to the
        # walkable Garner side of Silver Mine 1. Other mines retain normal travel.
        names=('Abandoned Mine 1 - Abandoned Mine 2','Abandoned Mine 2 - Silver Mine 3',
               'Silver Mine 3 - Silver Mine 2','Silver Mine 2 - Silver Mine 1')
        by_name={row['name']:row for row in (self.hunting_travel_data or {}).get('entrances',[])}
        if not all(name in by_name for name in names):return {}
        result={};previous=None
        for name in names:
            entry=by_name[name]
            source=self.nav(entry['map']).land_component(entry['position'])
            target=self.nav(entry['to_map']).land_component(entry['arrival_cm'])
            if not source or not target or (previous and previous!=(entry['map'],source)):return {}
            result[entry['map'],source]=dict(entry,arrival_component=target)
            previous=(entry['to_map'],target)
        return result

    def mine_exit_step(self,map_name,position,continuing):
        if map_name not in (('garner','eastgoaf') if continuing else ('garner',)):return None
        nav=self.nav(map_name)
        # Do not load interior navigation on every outdoor decision.
        component=nav.land_component(position)
        if not component:return None
        if not continuing:
            start=self.mine_exit_entrance
            if not start or component!=nav.land_component(start['position']):return None
        return self.mine_exit_steps.get((map_name,component))

    def nav(self,name):
        if name not in self.navigation and name in self.map_catalog:
            # Additional verified maps load only after an actual map entry.
            # Their geometry does not imply a verified dungeon quest or teleport.
            with self.navigation_lock:
                if name not in self.navigation:
                    filename=self.map_catalog[name]['navigation']
                    if Path(filename).name!=filename:raise ValueError('Invalid navigation filename')
                    nav=Navigation(self.assets/filename);nav.enable_incremental()
                    self.navigation[name]=nav
        if name not in self.navigation:raise ValueError('Нет проверенной навигации для карты '+name)
        return self.navigation[name]


def birthplace_for(first_job):
    return {1:'Argent City',4:'Argent City',2:'Icicle Castle',5:'Shaitan City'}[first_job]
