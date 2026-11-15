"""Shared immutable source knowledge, independent of currently visible NPC actors."""
import json,math,re
from pathlib import Path

SERVICES={'торговец':'trade','торговля':'trade','магазин':'trade','банк':'bank','банкир':'bank',
          'ремонт':'repair','кузнец':'repair','телепорт':'teleport','портал':'teleport','портальщица':'teleport',
          'парикмахер':'hair','прическа':'hair','причёска':'hair','квест':'quest','задание':'quest',
          'корабль':'ship_build','верфь':'ship_build','пристань':'ship_launch','гильдия':'guild','заточка':'forge'}
KINDS={'посох':9,'посохи':9,'лук':3,'луки':3,'пистолет':4,'ружье':4,'ружьё':4,
       'кольцо':26,'кольца':26,'ожерелье':25,'ожерелья':25,'коралл':29,'кораллы':29,
       'броня':22,'доспех':22,'доспехи':22,'перчатки':23,'ботинки':24,'обувь':24}
CITIES={'garner':'Аргент','magicsea':'Шайтан','darkblue':'Ледынь'}

class NpcKnowledge:
    def __init__(self,path,item_types=None,item_names=None,prices=None,extra_rows=()):
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        self.rows=tuple(data['npcs'])+tuple(extra_rows);self.by_key={n['key']:n for n in self.rows};self.by_map={};self.by_item={};self.by_service={}
        if len(self.by_key)!=len(self.rows):raise ValueError('Duplicate NPC identity')
        self.item_names=item_names or {};self.prices=prices or {}
        self.item_types=item_types or {};self.model_count=len(data['model_definitions'])
        self.unlocated=tuple(data['models_without_static_placement']);self.table_count=len(data['tables_sha256'])
        for npc in self.rows:
            self.by_map.setdefault(npc['map'],[]).append(npc)
            for service in npc['services']:self.by_service.setdefault(service,[]).append(npc)
            if npc['verified_shop_binding']:
                for identity in npc['offers']:self.by_item.setdefault(identity,[]).append(npc)

    def goods(self,npc):
        return [{'id':i,'name':self.item_names.get(i,str(i)),'base_price':self.prices.get(i)} for i in npc['offers']]

    def sellers(self,identity,map_name=None):
        return [n for n in self.by_item.get(identity,()) if map_name is None or n['map']==map_name]

    def shops(self,map_name=None):
        return [n for n in (self.rows if map_name is None else self.by_map.get(map_name,())) if n['verified_shop_binding']]

    def find(self,query,map_name=None,position=None):
        query=query.casefold().strip();words=re.findall(r'[\w]+',query)
        service=next((SERVICES[w] for w in words if w in SERVICES),None)
        kind=next((KINDS[w] for w in words if w in KINDS),None)
        if query.isdigit():rows=self.sellers(int(query))
        elif kind is not None:
            rows=[n for n in self.shops() if any(self.item_types.get(i)==kind for i in n['offers'])]
        elif service:rows=list(self.by_service.get(service,()))
        elif not query:rows=list(self.rows)
        else:rows=[n for n in self.rows if query in n['name'].casefold() or query==n['key'].casefold()]
        return sorted(rows,key=lambda n:(n['map']!=map_name,
            math.dist(position,n['position']) if position is not None and n['map']==map_name else 0,n['key']))

    def answer(self,words,map_name,position):
        if not any(w in words for w in ('где','найти','купить','продает','продаёт','продают')):return None
        query=next((w for w in words if w in SERVICES or w in KINDS),None)
        aliases={'ня':3844,'зя':3845,'мордо':680,'фея':232,'феи':232,'джун':681,'джуниор':681,'пасеха':609,'пасеху':609}
        identity=next((aliases[w] for w in words if w in aliases),None)
        if identity is not None:query=str(identity)
        if query is None:
            candidates=[n for n in self.rows if any(len(w)>=3 and w in n['name'].casefold().split() for w in words)]
            if not candidates:return None
            query=min(candidates,key=lambda n:n['map']!=map_name)['name']
        rows=self.find(query,map_name,position)
        if not rows:return None
        npc=rows[0];x,y=(int(v//100) for v in npc['position'])
        answer=f"В справочнике: {npc['name'][:34]}. {CITIES.get(npc['map'],npc['map'])[:18]}, {x},{y}."
        return answer.encode('cp1251',errors='replace')[:120].decode('cp1251')

    def summary(self,map_name,position):
        nearby=sorted(self.by_map.get(map_name,()),key=lambda n:math.dist(position,n['position']))[:5]
        return {'known_static_npcs':len(self.rows),'source_tables':self.table_count,'maps_with_npcs':len(self.by_map),
                'known_npc_model_definitions':self.model_count,'models_without_verified_static_coordinates':len(self.unlocated),
                'known_shops':len(self.shops()),'available_service_categories':sorted(self.by_service),
                'nearby_source_placements':[{'key':n['key'],'name':n['name'],'position':n['position'],
                    'services':n['services'],'conditional':n['conditions_not_evaluated']} for n in nearby],
                'dynamic_spawns_exhaustively_known':False,'service_knowledge_is_not_automation':True,
                'live_menu_required':True}
