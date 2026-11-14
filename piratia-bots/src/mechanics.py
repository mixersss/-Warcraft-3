"""Shared source-backed mechanic knowledge and read-only plans from native item state.

Knowing a recipe or condition never marks the corresponding native action as
implemented, successful or affordable without the actual character's resources.
"""
import json,math,re
from pathlib import Path
from collections import defaultdict

def forge_parts(value):
    if type(value) is not int or not -2147483648<=value<=4294967295:raise ValueError('Unsupported native forge parameter')
    value&=0xffffffff
    parts=[value//1000000000,(value//10000000)%100,(value//1000000)%10,
           (value//10000)%100,(value//1000)%10,(value//10)%100,value%10]
    return {'sockets':parts[0],'slots':[{'stone_type':parts[i],'level':parts[i+1]} for i in (1,3,5)],
            'total_level':sum(parts[i] for i in (2,4,6))}

def result(mechanic,**fields):
    return {'mechanic':mechanic,'planning_only':True,'automatic_execution_implemented':False,
            'missing':[],'unobserved':[],**fields}

class MechanicsKnowledge:
    def __init__(self,path,npcs=None,mobs=None):
        data=json.loads(Path(path).read_text(encoding='utf-8'));self.data=data
        if not isinstance(data,dict) or data.get('version')!=1 or not isinstance(data.get('cards'),list) or not isinstance(data.get('functions'),list):
            raise ValueError('Unsupported mechanic knowledge schema')
        for key in ('item_bases','stones','ships','ship_parts','coverage','map_rules',
                    'item_attribute_ids','fairy_breeding_materials','literal_item_flows'):
            if not isinstance(data.get(key),dict):raise ValueError('Invalid mechanic knowledge: '+key)
        if any(not isinstance(c,dict) for c in data['cards']+data['functions']):
            raise ValueError('Invalid mechanic knowledge records')
        self.load_origin='bundled_uploaded_snapshot';self.load_problem=None
        self.cards={c['id']:c for c in data['cards']};self.npcs=npcs;self.mobs=mobs
        self.items={int(k):v for k,v in data['item_bases'].items()}
        self.stones={int(k):v for k,v in data['stones'].items()}
        self.stone_items={s['item_id']:dict(s,stone_type=identity) for identity,s in self.stones.items()}
        self.ships={int(k):v for k,v in data['ships'].items()}
        self.parts={int(k):v for k,v in data['ship_parts'].items()}
        self.functions={f['key']:f for f in data['functions']};self.by_name=defaultdict(list)
        required={'forge','gem_combine','manufacturing','crafting','cooking','fairy_breeding',
                  'ship_build','demonic_world','dark_swamp','forsaken_city'}
        if not required.issubset(self.cards) or not isinstance(data.get('forgeable_item_kinds'),list):
            raise ValueError('Incomplete mechanic knowledge')
        for card in self.cards.values():
            if card['review_status'] not in ('reviewed_rules','requires_reaudit','indexed_needs_review'):
                raise ValueError('Invalid review status')
            if any(key not in self.functions for key in card['evidence']):raise ValueError('Missing mechanic evidence')
        for f in self.functions.values():self.by_name[f['name']].append(f)
        self.droppers=defaultdict(list)
        if mobs:
            for identity,record in mobs.monsters.items():
                for item in record['drops']:self.droppers[item].append(identity)

    def search(self,query):
        query=query.casefold().replace('ё','е').strip();words=set(re.findall(r'\w+',query));scored=[]
        for card in self.cards.values():
            matches=[a for a in [card['id'],card['title']]+card['aliases']
                     if (a.casefold().replace('ё','е') in words if len(a)<=3 else a.casefold().replace('ё','е') in query)]
            if matches:scored.append((max(map(len,matches)),card))
        return [c for _,c in sorted(scored,key=lambda pair:(-pair[0],pair[1]['id']))]

    def explain(self,identity,map_name=None,position=None):
        card=self.cards[identity]
        rows=[self.npcs.by_key[k] for k in card['npc_keys'] if self.npcs and k in self.npcs.by_key]
        rows.sort(key=lambda n:(n['map']!=map_name,math.dist(position,n['position']) if position and n['map']==map_name else 0,n['key']))
        return {**card,'source_evidence':[self.functions[k] for k in card['evidence']],
                'candidate_npcs':[{'key':n['key'],'name':n['name'],'map':n['map'],'position_cm':n['position'],
                                   'live_menu_required':True} for n in rows],
                'native_action_success_verified':False}

    def sources_for_item(self,identity,map_name=None,position=None,level=None):
        identity=int(identity);monsters=[]
        if self.mobs:
            for model in self.droppers.get(identity,()):
                record=self.mobs.get(model)
                locations=record['locations']
                local=self.mobs.nearest(model,map_name,position) if map_name and position else None
                monsters.append({'model':model,'name':record['name'],'level':record['level'],
                                 'territory':record['territory'],'locations':locations,'nearest_local':local,
                                 'drop_probability_known':False,'live_spawn_verified':False})
        monsters.sort(key=lambda r:(abs(r['level']-level) if level is not None else 0,
                                    0 if r['nearest_local'] else 1,r['model']))
        return {'item_id':identity,'item':self.items.get(identity),'monster_sources':monsters,
                'npc_sources':self.npcs.sellers(identity) if self.npcs else [],
                'script_reward_candidates':[f for f in self.data['literal_item_flows'].get(str(identity),[]) if f['kind']!='requirement'],
                'complete_dynamic_acquisition_graph':False}

    def inspect_equipment(self,item):
        state=forge_parts(item.parameters[0]);effects=defaultdict(int);unknown=[]
        for slot in state['slots']:
            stone=self.stones.get(slot['stone_type'])
            if not slot['stone_type']:continue
            if not stone or not 1<=slot['level']<=9:
                unknown.append(slot);continue
            effects[stone['attribute_id']]+=stone['bonus_per_level']*slot['level']
            if stone['attack_adds_min_and_max']:effects[stone['attribute_id']+1]+=stone['bonus_per_level']*slot['level']
        return {'item_id':item.identity,'forge':state,'source_gem_effects':dict(effects),
                'unknown_slots':unknown,'server_final_attributes_still_authoritative':True}

    def dungeon_requirements(self,world,map_name):
        plan=result('dungeon_entry');plan['map']=map_name
        known={'puzzleworld':('demonic_world',50,None,{}),'darkswamp':('dark_swamp',40,55,{}),
               'abandonedcity':('forsaken_city',30,45,{1812:1})}
        if map_name not in known:
            plan['unobserved'].append('entry_logic_not_fully_reviewed');plan['source']=self.data['map_rules'].get(map_name);return plan
        card,low,high,items=known[map_name]
        if self.cards[card]['review_status']!='reviewed_rules':plan['unobserved'].append('source_rules_need_reaudit');return plan
        plan['level_range']=[low,high];plan['required_items']=items
        level=world.own.values.get(0,0)
        if level<low or high is not None and level>high:plan['missing'].append('character_level')
        for identity,count in items.items():
            if sum(i.count for i in world.bag.values() if i.identity==identity)<count:plan['missing'].append('item_'+str(identity))
        plan['unobserved']+=['live_portal_open','server_time_and_instance_phase','native_entry_and_return_route']
        plan['source']=self.data['map_rules'].get(map_name)
        return plan

    def craft_reservations(self,world):
        """Only one observed usable recipe with already learned skills/fairy/tool.

        This saves its finite materials from a junk sale, without collecting all
        possible craft ingredients or claiming a craft action has been executed.
        """
        if not world.bag_ready or world.bag_disabled:return {}
        candidates=[]
        for slot,item in world.bag.items():
            recipe=self.inspect_blueprint(item)
            if not recipe or not recipe['recipe_observed'] or not recipe['remaining_uses']:continue
            if world.skills.get(recipe['character_skill'],{}).get('level',0)<recipe['required_skill_level']:continue
            fairy_slots=[s for s,i in world.bag.items() if self.items.get(i.identity,{}).get('kind')==59 and i.valid and i.endurance>0]
            tool_slots=[s for s,i in world.bag.items() if i.identity==recipe['tool_id'] and i.valid and i.endurance>0]
            if not fairy_slots or not tool_slots:continue
            plan=self.plan_blueprint(world,slot,fairy_slots[0],tool_slots[0])
            if plan['unobserved'] or set(plan['missing'])-{'materials_or_fairy_coins','free_inventory_slot'}:continue
            candidates.append((sum(plan['shortfalls'].values()),slot,plan['requirements']))
        return min(candidates,key=lambda r:(r[0],r[1]))[2] if candidates else {}

    def item_answer(self,words,world):
        query=' '.join(words).casefold();numbers=re.findall(r'(?<!\w)(?:id)?(\d+)\b',query)
        identities=[int(i) for i in numbers if int(i) in self.items]
        if not identities:
            identities=[i for i,r in self.items.items() if r['name'].casefold() in query and len(r['name'])>=4]
        if not identities and any('сияющ' in w for w in words):identities=[883]
        if not identities and any(w in words for w in ('каль','кал','кель')):identities=[3457]
        if not identities:return None
        identity=identities[0];sources=self.sources_for_item(identity,world.map,world.own.position,world.own.values.get(0))
        if sources['npc_sources']:
            npc=min(sources['npc_sources'],key=lambda n:(n['map']!=world.map,math.dist(world.own.position,n['position']) if n['map']==world.map else 0))
            return f"В справочнике ID{identity}: {npc['name'][:26]}, {npc['map']}, {npc['position'][0]//100},{npc['position'][1]//100}."
        monsters=sources['monster_sources']
        if monsters:
            normal=[m for m in monsters if m['level']>0] or monsters;m=normal[0]
            maps=sorted({l['map'] for l in m['locations']});map_text=','.join(maps[:2]) if maps else 'место не найдено'
            return f"Возможный дроп ID{identity}: {m['name'][:27]}, ур.{m['level']}, {map_text}."
        return f'ID{identity}: точный источник пока не подтверждён. Нужна проверка наград, обменов или динамических скриптов.'

    def item_attribute(self,item,name):
        identity=self.data['item_attribute_ids'].get(name)
        if identity is None:return None
        overrides=dict(item.instance_attributes)
        if identity in overrides:return overrides[identity]
        return self.items.get(item.identity,{}).get('constant_attributes',{}).get(str(identity))

    def inspect_fairy(self,item,desired_stat=None):
        if self.items.get(item.identity,{}).get('kind')!=59:return None
        stats={key:self.item_attribute(item,'ITEMATTR_VAL_'+key) for key in ('STR','AGI','DEX','CON','STA')}
        level=sum(stats.values()) if all(type(n) is int for n in stats.values()) else None
        parts=forge_parts(item.parameters[0]);mono=None
        if desired_stat in stats and level is not None:mono=all(v==0 for k,v in stats.items() if k!=desired_stat)
        return {'item_id':item.identity,'level':level,'stats':stats,'stamina':item.endurance,'maximum_stamina':item.max_endurance,
                'growth':item.energy,'maximum_growth':item.max_energy,'skills':parts['slots'],
                'desired_stat':desired_stat,'monostat_matches_owner_policy':mono,'requires_food':item.endurance<item.max_endurance,
                'breeding_minimum_level_met':level>=20 if level is not None else None}

    def inspect_blueprint(self,item):
        settings={2300:('manufacturing',1068,338,13),2301:('crafting',1069,340,14),2302:('cooking',1067,339,16)}
        if item.identity not in settings:return None
        mode,tool,skill,fairy_skill=settings[item.identity];parts=forge_parts(item.parameters[0])
        ids=[self.item_attribute(item,'ITEMATTR_VAL_'+key) for key in ('STR','CON','DEX')]
        materials=[{'item_id':identity,'quantity':parts['slots'][i]['stone_type']} for i,identity in enumerate(ids)]
        known=all(type(m['item_id']) is int and m['item_id'] in self.items and m['quantity']>0 for m in materials)
        return {'item_id':item.identity,'mechanic':mode,'tool_id':tool,'character_skill':skill,'fairy_skill':fairy_skill,
                'required_skill_level':item.endurance,'remaining_uses':self.item_attribute(item,'ITEMATTR_VAL_STA'),
                'fairy_coin_id':855,'fairy_coin_quantity':item.max_endurance,'materials':materials,
                'recipe_observed':known,'recipe_comes_from_instance':True}

    def plan_blueprint(self,world,blueprint_slot,fairy_slot,tool_slot):
        plan=result('craft_recipe');bag=world.bag
        if not world.bag_ready or world.bag_disabled:
            plan['unobserved'].append('native_inventory');return plan
        if len({blueprint_slot,fairy_slot,tool_slot})!=3 or any(s not in bag for s in (blueprint_slot,fairy_slot,tool_slot)):
            plan['missing'].append('three_distinct_owned_items');return plan
        blueprint,fairy,tool=[bag[s] for s in (blueprint_slot,fairy_slot,tool_slot)]
        recipe=self.inspect_blueprint(blueprint);plan['recipe']=recipe
        if not recipe:plan['missing'].append('supported_blueprint');return plan
        plan['mechanic']=recipe['mechanic']
        if self.cards[recipe['mechanic']]['review_status']!='reviewed_rules':
            plan['unobserved'].append('source_rules_need_reaudit');return plan
        if not recipe['recipe_observed']:plan['unobserved'].append('blueprint_material_parameters')
        if recipe['remaining_uses'] is None:plan['unobserved'].append('blueprint_uses')
        elif recipe['remaining_uses']<=0:plan['missing'].append('usable_blueprint')
        if not all(i.valid for i in (blueprint,fairy,tool)):plan['missing'].append('valid_items')
        if self.items.get(fairy.identity,{}).get('kind')!=59 or fairy.endurance<=0:plan['missing'].append('living_fairy')
        if tool.identity!=recipe['tool_id'] or tool.endurance<=0:plan['missing'].append('working_correct_tool')
        character_skill=world.skills.get(recipe['character_skill'],{}).get('level',0)
        if character_skill<recipe['required_skill_level']:plan['missing'].append('character_life_skill_level')
        tool_level=self.item_attribute(tool,'ITEMATTR_VAL_STR')
        pet_skills=forge_parts(fairy.parameters[0])['slots']
        pet_level=max((s['level'] for s in pet_skills if s['stone_type']==recipe['fairy_skill']),default=0)
        if tool_level is None:plan['unobserved'].append('tool_skill_level')
        elif not pet_level or pet_level<tool_level:plan['missing'].append('fairy_life_skill_level')
        if (world.bag_capacity or 0)-len(bag)<1:plan['missing'].append('free_inventory_slot')
        required=defaultdict(int)
        if recipe['recipe_observed']:
            for material in recipe['materials']:required[material['item_id']]+=material['quantity']
        required[855]+=recipe['fairy_coin_quantity'];plan['requirements']=dict(required)
        plan['shortfalls']={identity:count-sum(i.count for i in bag.values() if i.identity==identity)
                            for identity,count in required.items() if sum(i.count for i in bag.values() if i.identity==identity)<count}
        if plan['shortfalls']:plan['missing'].append('materials_or_fairy_coins')
        plan['resources_ready']=not plan['missing'] and not plan['unobserved']
        return plan

    def plan_forge(self,world,target_slot,gem_slot,refining_slot):
        plan=result('forge')
        if not world.bag_ready or world.bag_disabled:plan['unobserved'].append('native_inventory');return plan
        slots=(target_slot,gem_slot,refining_slot)
        if len(set(slots))!=3 or any(s not in world.bag for s in slots):
            plan['missing'].append('three_distinct_owned_items');return plan
        target,gem,refining=[world.bag[s] for s in slots]
        kind=self.items.get(target.identity,{}).get('kind');stone=self.stone_items.get(gem.identity)
        state=forge_parts(target.parameters[0]);plan['target_forge']=state
        if self.cards['forge']['review_status']!='reviewed_rules':
            plan['unobserved'].append('source_rules_need_reaudit');return plan
        if state['sockets']>3 or sum(s['stone_type']!=0 for s in state['slots'])>state['sockets']:
            plan['unobserved'].append('inconsistent_equipment_forge_state')
        if not all(i.valid for i in (target,gem,refining)):plan['missing'].append('valid_items')
        if kind not in self.data['forgeable_item_kinds']:plan['missing'].append('forgeable_equipment_type')
        if not stone or self.items.get(gem.identity,{}).get('kind')!=49:plan['missing'].append('known_normal_gem')
        if self.items.get(refining.identity,{}).get('kind')!=50:plan['missing'].append('refining_gem')
        if stone and kind not in stone['compatible_item_kinds']:plan['missing'].append('gem_equipment_compatibility')
        existing=next((s for s in state['slots'] if stone and s['stone_type']==stone['stone_type']),None)
        if not existing and sum(s['stone_type']!=0 for s in state['slots'])>=state['sockets']:plan['missing'].append('free_socket')
        needed=existing['level']+1 if existing else 0
        plan['minimum_input_level']=needed;plan['next_embedded_level']=existing['level']+1 if existing else 1
        # Get_StoneLv reads ITEMATTR_VAL_BaoshiLV, alias MAXENERGY, not STR.
        for name,item in (('gem',gem),('refining',refining)):
            if item.max_energy<needed:plan['missing'].append(name+'_level')
        plan['gold']=(state['total_level']+1)*100000
        if world.own.values.get(8,0)<plan['gold']:plan['missing'].append('gold')
        plan['source_success_roll']=1.0
        plan['resources_ready']=not plan['missing'] and not plan['unobserved']
        return plan

    def plan_ship(self,world,ship_type,selection):
        plan=result('ship_build');ship=self.ships.get(ship_type)
        if self.cards['ship_build']['review_status']!='reviewed_rules':plan['unobserved'].append('source_rules_need_reaudit');return plan
        if not ship:plan['missing'].append('known_ship_type');return plan
        plan['ship']=ship['name']
        if world.own.values.get(0,0)<ship['minimum_level']:plan['missing'].append('character_level')
        if ship['jobs']!=[-1] and world.own.values.get(4) not in ship['jobs']:plan['missing'].append('character_job')
        total=0
        for component in ('hull','mobility','fore','artillery','component'):
            identity=selection.get(component)
            if identity not in ship[component] or identity not in self.parts:plan['missing'].append('compatible_'+component)
            else:total+=self.parts[identity]['price']
        plan['selected_parts_price']=total
        plan['unobserved']=['native_shipyard_quote','available_ship_contract_slot','native_ship_creation_protocol']
        if world.own.values.get(8,0)<total:plan['missing'].append('gold')
        return plan

    def plan_gem_combine(self,world,scroll_slot,first_slot,second_slot,bonus_state_level=None):
        plan=result('gem_combine');slots=(scroll_slot,first_slot,second_slot)
        if not world.bag_ready or world.bag_disabled:plan['unobserved'].append('native_inventory');return plan
        if self.cards['gem_combine']['review_status']!='reviewed_rules':plan['unobserved'].append('source_rules_need_reaudit');return plan
        if len(set(slots))!=3 or any(s not in world.bag for s in slots):plan['missing'].append('three_distinct_owned_items');return plan
        scroll,first,second=[world.bag[s] for s in slots];kind=self.items.get(first.identity,{}).get('kind')
        if self.items.get(scroll.identity,{}).get('kind')!=47:plan['missing'].append('combining_scroll')
        if kind not in (49,50) or first.identity!=second.identity:plan['missing'].append('two_identical_gems')
        if first.max_energy!=second.max_energy:plan['missing'].append('same_gem_level')
        if kind==49 and first.max_energy>=9:plan['missing'].append('normal_gem_level_cap')
        if not all(i.valid for i in (scroll,first,second)):plan['missing'].append('valid_items')
        plan['gold']=50000;plan['output_level_on_success']=first.max_energy+1
        plan['failure_consumes_both_gems_and_scroll']=True
        if kind==49 and first.max_energy<3:plan['success_probability']=1.0
        elif type(bonus_state_level) is int and bonus_state_level>=0:
            skill=1+bonus_state_level
            plan['success_probability']=max(0,min(1,1-first.max_energy*(.10 if kind==49 else .05)+skill*(.10 if kind==49 else .15)))
        else:plan['success_probability']=None;plan['unobserved'].append('combination_bonus_state')
        if world.own.values.get(8,0)<50000:plan['missing'].append('gold')
        plan['resources_ready']=not plan['missing']
        return plan

    def plan_fairy_breeding(self,world,fruit_slot,first_slot,second_slot):
        plan=result('fairy_breeding');slots=(fruit_slot,first_slot,second_slot)
        if not world.bag_ready or world.bag_disabled:plan['unobserved'].append('native_inventory');return plan
        if self.cards['fairy_breeding']['review_status']!='reviewed_rules':plan['unobserved'].append('source_rules_need_reaudit');return plan
        if len(set(slots))!=3 or any(s not in world.bag for s in slots):plan['missing'].append('distinct_fruit_and_two_parents');return plan
        fruit,first,second=[world.bag[s] for s in slots]
        materials=self.data['fairy_breeding_materials'].get(str(fruit.identity))
        if not materials:plan['missing'].append('supported_fruit')
        parents=[self.inspect_fairy(i) for i in (first,second)]
        if any(p is None for p in parents):plan['missing'].append('two_fairies');return plan
        if any(p['level'] is None for p in parents):plan['unobserved'].append('native_parent_stats');return plan
        if any(p['level']<20 for p in parents):plan['missing'].append('parent_level_20')
        if any(forge_parts(i.parameters[0])['sockets']!=0 for i in (first,second)):plan['missing'].append('normal_parent_generation')
        # Owner policy guards both parents; this source accidentally repeats the first-parent stamina check.
        plan['policy_additional_guard']='both_parent_stamina_full'
        if any(i.endurance<i.max_endurance for i in (first,second)):plan['missing'].append('full_parent_stamina')
        if not all(i.valid for i in (fruit,first,second)):plan['missing'].append('valid_items')
        levels=[p['level'] for p in parents]
        plan['gold']=0 if max(levels)>60 else (60-levels[0])*(60-levels[1])*100
        if world.own.values.get(8,0)<plan['gold']:plan['missing'].append('gold')
        if (world.bag_capacity or 0)-len(world.bag)<2:plan['missing'].append('two_free_inventory_slots')
        plan['materials']=materials or []
        for identity,count in materials or []:
            if sum(i.count for i in world.bag.values() if i.identity==identity and i.valid)<count:plan['missing'].append('item_'+str(identity))
        plan['resources_ready']=not plan['missing'] and not plan['unobserved']
        plan['child_identity_and_traits']='must_be_observed_from_server'
        return plan

    def answer(self,words,world=None):
        if not any(w in words for w in ('как','зачем','нужно','работает','работают','умеешь','что','объясни','подскажи','где','добыть','падает')):return None
        if 'где' in words and any(w in words for w in ('купить','продают','продается','продаётся')):return None
        if world and any(w in words for w in ('где','добыть','падает')):
            answer=self.item_answer(words,world)
            if answer:return answer.encode('cp1251',errors='replace')[:120].decode('cp1251')
        matches=self.search(' '.join(words))
        if not matches:return None
        if matches[0]['review_status']!='reviewed_rules':
            text='Правила этой механики требуют проверки по текущим файлам сервера; точный расчёт пока не подтверждён.'
        elif any(w in words for w in ('умеешь','сам','сделай')):
            text=('Исторические задания и ларёк уже осваиваю; производство и кулинарию пока сам не выполняю.'
                  if matches[0]['id']=='life_skills' else
                  'Условия знаю; автоматической операции пока нет. Могу объяснить ресурсы, совместимость и цену.')
        else:text=matches[0]['short_answer']
        return text.encode('cp1251',errors='replace')[:120].decode('cp1251')

    def summary(self):
        return {**{k:v for k,v in self.data['coverage'].items() if k!='native_or_dynamic_call_names'},
                'known_stones':len(self.stones),'known_ship_types':len(self.ships),'known_ship_parts':len(self.parts),
                'map_rules':len(self.data['map_rules']),'knowledge_is_not_automatic_execution':True,
                'load_origin':self.load_origin,'local_knowledge_problem':self.load_problem}

    def owned_summary(self,world):
        if not world.bag_ready or world.bag_disabled:return {'inventory_observed':False}
        recipes=[];fairies=[];equipment=[]
        for slot,item in world.bag.items():
            if not item.valid:continue
            recipe=self.inspect_blueprint(item)
            if recipe and len(recipes)<3:recipes.append(dict(recipe,bag_slot=slot))
            fairy=self.inspect_fairy(item)
            if fairy and len(fairies)<3:fairies.append(dict(fairy,bag_slot=slot))
            if self.items.get(item.identity,{}).get('kind') in self.data['forgeable_item_kinds'] and len(equipment)<3:
                equipment.append(dict(self.inspect_equipment(item),bag_slot=slot))
        return {'inventory_observed':True,'blueprints':recipes,'fairies':fairies,'equipment':equipment,
                'reserved_recipe_materials':self.craft_reservations(world)}

def load_knowledge(assets,npcs=None,mobs=None):
    assets=Path(assets);private=assets.parent/'data'/'knowledge'/'mechanics.json';problem=None
    if private.is_file():
        try:
            if private.stat().st_size>64*1024*1024:raise ValueError('Local knowledge file too large')
            knowledge=MechanicsKnowledge(private,npcs,mobs);knowledge.load_origin='private_local_resource';return knowledge
        except (OSError,ValueError,KeyError,TypeError,AttributeError) as error:problem=type(error).__name__
    knowledge=MechanicsKnowledge(assets/'mechanics.json',npcs,mobs);knowledge.load_problem=problem
    return knowledge
