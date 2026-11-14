"""Shared ground navigation for paired maps and beginner farms for three home cities."""
import json
import threading
from pathlib import Path
from navigation import Navigation


class Regions:
    def __init__(self,assets,population_count=200):
        self.assets=Path(assets)
        from coordination import Coordination
        self.coordination=Coordination(population_count)
        from party import BotDirectory
        self.directory=BotDirectory()
        from cooperation import HelpDirectory
        self.help_directory=HelpDirectory()
        from conversations import Conversations
        self.conversations=Conversations(self.assets)
        from public_chat import PublicBudget
        self.public_chat_budget=PublicBudget()
        from equipment import ItemCatalog
        self.items=ItemCatalog(self.assets/'items.json')
        from life import LifeItems
        self.life=LifeItems(self.assets)
        from market import MarketCatalog,MarketDirectory
        self.market_catalog=MarketCatalog(self.assets)
        total=population_count//10
        argent=round(total*.75);remaining=total-argent
        self.market_directory=MarketDirectory(city_limits={'garner':argent,'magicsea':(remaining+1)//2,'darkblue':remaining//2},live_count=self.directory.active_count)
        from activity_slots import ActivitySlots
        self.rest_directory=ActivitySlots(population_count,live_count=self.directory.active_count)
        self.data=json.loads((self.assets/'regions.json').read_text(encoding='utf-8'))
        catalog=self.assets/'world-navigation.json'
        self.map_catalog=json.loads(catalog.read_text(encoding='utf-8')).get('maps',{}) if catalog.exists() else {}
        self.navigation_lock=threading.Lock()
        self.navigation={name:Navigation(self.assets/info['navigation']) for name,info in self.data.items()}
        for nav in self.navigation.values():nav.enable_incremental()

    def get(self,name):
        return self.data.get(name)

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
