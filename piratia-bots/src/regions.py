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
        self.mob_knowledge=MobKnowledge(knowledge,self.assets.parent/'data/server-spawns.json') if knowledge.exists() else None
        from mechanics import load_knowledge
        mechanics=self.assets/'mechanics.json'
        self.mechanics=load_knowledge(self.assets,self.npc_knowledge,self.mob_knowledge) if mechanics.exists() else None
        portals=self.assets/'portals.json'
        self.portal_catalog=json.loads(portals.read_text(encoding='utf-8')) if portals.exists() else None
        self.data=json.loads((self.assets/'regions.json').read_text(encoding='utf-8'))
        catalog=self.assets/'world-navigation.json'
        self.map_catalog=json.loads(catalog.read_text(encoding='utf-8')).get('maps',{}) if catalog.exists() else {}
        self.navigation_lock=threading.Lock()
        self.region_lock=threading.Lock()
        from hunt_observations import HuntObservations
        self.hunt_observations=HuntObservations(self.assets.parent/'data/hunting-observations.json')
        self.observed_regions={}
        self.island_scout_cooldowns={}
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
                for identity,locations in self.mob_knowledge.by_map.get(name,{}).items():
                    if str(identity) in region['farms']:continue
                    mob=self.mob_knowledge.get(identity)
                    if mob.get('territory')!=0:continue
                    points=scout_points(nav,locations,[])
                    if points:
                        region['farms'][str(identity)]={**{k:mob[k] for k in ('level','hp','drops','base_xp','defence','attack_max')},
                                                       'territory':0,'points':points,'source_region_scouting':True}
        if self.abandoned_mine_one_component:
            for farm in self.data['garner']['farms'].values():
                farm['points']=[p for p in farm['points'] if not self.abandoned_mine_one('garner',p)]

    def get(self,name):
        if name not in self.data and getattr(self,'full_regions',False) and name in self.map_catalog and self.mob_knowledge:
            with self.region_lock:
                if name in self.data:return self.data[name]
                from farm_scouting import scout_points
                farms={}
                nav=self.nav(name)
                for identity,locations in self.mob_knowledge.by_map.get(name,{}).items():
                    mob=self.mob_knowledge.get(identity)
                    if mob.get('territory')!=0:continue # Ships remain a separate native control mode.
                    ordinary=[location for location in locations if not location.get('conditions_not_evaluated')]
                    points=scout_points(nav,ordinary,[])
                    if not ordinary:
                        # Preserve hints when already inside a conditional room.
                        # These hints cannot qualify a destination for an automatic trip.
                        for location in locations:
                            lo,hi=location['rectangle_cm']
                            points.extend([(int((lo[0]+hi[0])/2),int((lo[1]+hi[1])/2)),tuple(lo),tuple(hi),(lo[0],hi[1]),(hi[0],lo[1])])
                    farms[str(identity)]={**{k:mob[k] for k in ('level','hp','drops','base_xp','defence','attack_max')},'territory':0,'points':list(dict.fromkeys(points)),'conditional_only':not ordinary,'source_regions_not_live_positions':True}
                births=(self.hunting_travel_data or {}).get('birthplaces',{})
                spawns=list(dict.fromkeys(tuple(p) for b in births.values() if b['map']==name for p in b['points']))
                self.data.setdefault(name,{'birthplace':name,'label':name,'spawns':spawns,'farms':farms,'navigation':self.map_catalog[name]['navigation']})
        return self.data.get(name)

    def record_hunting_observation(self,name,model,point,identity):
        mob=self.mob_knowledge.get(model)
        if name not in self.map_catalog or not mob or mob['territory']!=0 or self.abandoned_mine_one(name,point):
            return
        if model in self.mob_knowledge.by_map.get(name,{}) and any(
                not location.get('conditions_not_evaluated')
                and all(a<=x<=b for a,x,b in zip(location['rectangle_cm'][0],point,location['rectangle_cm'][1]))
                for location in self.mob_knowledge.by_map[name][model]):
            return
        nav=self.nav(name)
        if nav.land_component(point) and nav.combat_allowed(point):
            self.hunt_observations.record(name,model,point,identity)

    def hunting_region(self,name):
        region=self.get(name)
        points=self.hunt_observations.points(name)
        if not region or not points:
            return region
        with self.region_lock:
            cached=self.observed_regions.get(name)
            if cached and cached[0] is points:
                return cached[1]
            farms=dict(region['farms'])
            nav=self.nav(name)
            for model,locations in points.items():
                mob=self.mob_knowledge.get(model)
                if not mob or mob['territory']!=0:
                    continue
                verified=[p for p in locations if nav.land_component(p) and nav.combat_allowed(p)
                          and not self.abandoned_mine_one(name,p)]
                if verified:
                    key=str(model)
                    farm=farms.get(key,{k:mob[k] for k in ('level','hp','drops','base_xp','defence','attack_max','territory')})
                    farms[key]=dict(farm,points=list(dict.fromkeys([*farm.get('points',()),*verified])))
            result=dict(region,farms=farms)
            self.observed_regions[name]=(points,result)
            return result

    @lru_cache(maxsize=32)
    def island_scout_sites(self,name,arrival):
        nav=self.nav(name)
        component=nav.land_component(arrival)
        sites={}
        if not component:
            return sites
        for model,locations in self.mob_knowledge.by_map.get(name,{}).items():
            if self.mob_knowledge.get(model)['territory']!=0:
                continue
            for area in locations:
                lo,hi=area['rectangle_cm']
                if not area.get('conditions_not_evaluated') or lo!=hi:
                    continue
                distance=math.dist(arrival,lo)
                if (distance<sites.get(model,(25001,None))[0] and distance<=25000
                        and nav.land_component(lo)==component and nav.combat_allowed(lo)):
                    sites[model]=(distance,tuple(lo))
        return sites

    def reserve_island_scout(self,name,arrival,now):
        key=name,arrival
        with self.region_lock:
            if self.island_scout_cooldowns.get(key,0)>now:
                return False
            self.island_scout_cooldowns[key]=now+1800
            return True

    def hunting_arrival_sites(self,map_name,arrival):
        if self.abandoned_mine_one(map_name,arrival):return {}
        sites=self._source_arrival_sites(map_name,arrival)
        observations=self.hunt_observations.points(map_name)
        if not observations:
            return sites
        nav=self.nav(map_name)
        component=nav.land_component(arrival)
        if not component:
            return sites
        merged=dict(sites)
        for model,points in observations.items():
            mob=self.mob_knowledge.get(model)
            if not mob or mob['territory']!=0:
                continue
            closest=min((math.dist(arrival,p) for p in points
                         if nav.land_component(p)==component and nav.combat_allowed(p)),default=math.inf)
            if closest<=25000:
                merged[model]=min(closest,merged.get(model,math.inf))
        return merged

    @lru_cache(maxsize=512)
    def _source_arrival_sites(self,map_name,arrival):
        """Known camps on the same land component as a native arrival."""
        region=self.get(map_name)
        if not region:return {}
        nav=self.nav(map_name)
        component=nav.land_component(arrival)
        if not component:
            recovery=nav.recovery_path(arrival,radius=6,static=True)
            if not recovery or nav.needs_recovery(recovery[-1],ignore_temporary=True):return {}
            if sum(math.dist(a,b) for a,b in zip(recovery,recovery[1:]))>550:return {}
            arrival=recovery[-1]
            component=nav.land_component(arrival)
            if not component:return {}
        sites={}
        for identity,farm in region['farms'].items():
            if farm.get('conditional_only'):continue
            closest=min((math.dist(arrival,p) for p in farm['points']
                         if nav.land_component(p)==component and nav.combat_allowed(p)),default=math.inf)
            if closest<=25000:sites[int(identity)]=closest
        return sites

    @cached_property
    def mine_exit_entrance(self):
        return next((e for e in (self.hunting_travel_data or {}).get('entrances',[])
                     if e['name']=='Abandoned Mine 1 - Abandoned Mine 2'),None)

    @cached_property
    def abandoned_mine_one_component(self):
        entry=self.mine_exit_entrance
        return self.nav('garner').land_component(entry['position']) if entry and 'garner' in self.navigation else None

    def abandoned_mine_one(self,map_name,point):
        return bool(map_name=='garner' and self.abandoned_mine_one_component
                    and self.nav('garner').land_component(point)==self.abandoned_mine_one_component)

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
            if component!=self.abandoned_mine_one_component:return None
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
