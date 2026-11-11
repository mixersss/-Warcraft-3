"""Shared numerical navigation and legal beginner farm data for three home cities."""
import json
from pathlib import Path
from navigation import Navigation


class Regions:
    def __init__(self,assets):
        self.assets=Path(assets)
        from equipment import ItemCatalog
        self.items=ItemCatalog(self.assets/'items.json')
        self.data=json.loads((self.assets/'regions.json').read_text(encoding='utf-8'))
        self.navigation={name:Navigation(self.assets/info['navigation']) for name,info in self.data.items()}

    def get(self,name):
        return self.data.get(name)

    def nav(self,name):
        if name not in self.navigation:raise ValueError('Нет проверенной навигации для карты '+name)
        return self.navigation[name]


def birthplace_for(first_job):
    return {1:'Argent City',4:'Argent City',2:'Icicle Castle',5:'Shaitan City'}[first_job]
