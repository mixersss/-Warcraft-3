"""Source inventory and read-only plans use native parameters, not invented items."""
import copy,dataclasses,json,random,sys,unittest
import hashlib,tempfile
from pathlib import Path
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tools'))
from lua_inventory import functions,tokens,literal_calls
from mechanics import MechanicsKnowledge,forge_parts
from life import LifeItems
from mob_knowledge import MobKnowledge
from inventory import BagItem
from test_development import scene
from social import Social,ChatBudget
LIFE=LifeItems(ROOT/'assets');MOBS=MobKnowledge(ROOT/'assets/world-mobs.json')
K=MechanicsKnowledge(ROOT/'assets/mechanics.json',LIFE.npcs,MOBS)

def item(identity,count=1,parameter=0,attributes=(),level=1,endurance=100,maxendurance=100):
    return BagItem(identity,count,endurance,maxendurance,0,level,0,True,(parameter,0),attributes)

def actor():
    w=scene();w.own.values.update({0:30,4:1,8:1000000});w.bag_ready=True;w.bag_disabled=False;w.bag_capacity=24
    return w

def craft_actor():
    w=actor();fairy=next(i for i,r in K.items.items() if r['kind']==59);w.skills={338:{'level':2}}
    w.bag={0:item(2300,parameter=1020030040,attributes=((26,1779),(29,1774),(28,3116),(30,3),(0,0)),endurance=2,maxendurance=5),
           1:item(fairy,parameter=132000000,attributes=((26,20),(27,0),(28,0),(29,0),(30,0))),
           2:item(1068,attributes=((26,1),(0,0),(0,0),(0,0),(0,0))),
           3:item(1779,2),4:item(1774,3),5:item(3116,4),6:item(855,5)}
    return w

class InventoryTests(unittest.TestCase):
    def test_lexer_ignores_strings_comments_and_tracks_nested_blocks(self):
        source='''-- function Fake() end
local s="function Nope() -- not comment end"
--[=[ function Hidden() end ]=]
local z=[==[function AlsoHidden() end]==]
function Real(a)
 for i=1,3 do if a then ping() elseif a==false then pong() end end
 repeat a=a-1 until a==0
 do local f=function() nested() end end
 Real(0)
end
function Next() return 1 end
'''
        records,issues=functions(source)
        self.assertEqual(issues,[]);self.assertEqual([r['name'] for r in records],['Real','Next'])
        self.assertEqual(records[0]['calls'],['Real','nested','ping','pong']);self.assertEqual(records[1]['calls'],[])

    def test_literal_call_variables_are_not_turned_into_constants(self):
        self.assertEqual(literal_calls(tokens('SetTime(map,"0/3/0",n+1,-2,0x10) -- SetTime(0)'), 'SetTime'),
                         [[{'variable':'map'},'0/3/0',{'dynamic':True},-2,16]])

    def test_bad_source_is_reported_instead_of_claiming_coverage(self):
        self.assertTrue(functions('function broken() if a then x() end')[1])
        with self.assertRaises(ValueError):tokens('local x="unclosed')

    def test_all_supplied_lua_indexed_without_claiming_all_engine_mechanics_understood(self):
        c=K.summary();self.assertEqual((c['lua_files'],c['named_functions'],c['structural_errors']),(242,4135,0))
        self.assertEqual(c['requires_reaudit'],0);self.assertFalse(c['all_game_mechanics_exhaustively_understood'])
        self.assertFalse(c['runtime_loading_and_dynamic_branches_verified'])

    def test_original_source_bodies_and_private_absolute_paths_not_packaged(self):
        for f in K.functions.values():
            self.assertFalse(any(k.startswith('_') for k in f));self.assertFalse(Path(f['path']).is_absolute());self.assertNotIn('body',f)

    def test_server_sixteenth_gem_missing_from_tooltip_table_is_known(self):
        self.assertEqual(len(K.stones),16);self.assertEqual(len(K.data['tooltip_stones']),15)
        s=K.stones[16];self.assertEqual(s['item_id'],1012);self.assertFalse(s['tooltip_present'])
        self.assertEqual(s['bonus_per_level'],5);self.assertEqual(s['attribute'],'ITEMATTR_VAL_STA')

    def test_reviewed_forge_links_real_functions_and_actual_shaitan_npc(self):
        c=K.explain('forge');self.assertEqual(len(c['source_evidence']),6)
        self.assertTrue(any(n['name']=='Blacksmith - Smithy' and n['map']=='magicsea' for n in c['candidate_npcs']))
        self.assertFalse(c['automatic_execution_implemented'])

    def test_unbound_forge_table_not_treated_as_gem_probability(self):
        self.assertTrue(K.data['forge_table']);self.assertTrue(all(not r['runtime_hook_binding_verified'] for r in K.data['forge_table']))

class ForgeTests(unittest.TestCase):
    def make(self):
        w=actor();w.bag={0:item(1,parameter=1000000000),1:item(878),2:item(885)};return w

    def test_unsigned_classic_decimal_socket_layout(self):
        raw=3000000000+120000000+3000000+10000+2000+160+1;state=forge_parts(raw-4294967296)
        self.assertEqual(state['sockets'],3)
        self.assertEqual(state['slots'],[{'stone_type':12,'level':3},{'stone_type':1,'level':2},{'stone_type':16,'level':1}])
        self.assertEqual(state['total_level'],6)

    def test_actual_owned_inventory_quote_does_not_spend_resources(self):
        w=self.make();before=(dict(w.bag),dict(w.own.values));p=K.plan_forge(w,0,1,2)
        self.assertTrue(p['resources_ready']);self.assertEqual(p['gold'],100000);self.assertEqual(p['source_success_roll'],1.0)
        self.assertFalse(p['automatic_execution_implemented']);self.assertEqual((w.bag,w.own.values),before)

    def test_socket_and_gem_equipment_compatibility_required(self):
        w=self.make();w.bag[0]=item(1);self.assertIn('free_socket',K.plan_forge(w,0,1,2)['missing'])
        w=self.make();w.bag[1]=item(860);self.assertIn('gem_equipment_compatibility',K.plan_forge(w,0,1,2)['missing'])

    def test_existing_type_upgrade_uses_its_level_and_total_forge_fee(self):
        w=self.make();w.bag[0]=item(1,parameter=1012000000);p=K.plan_forge(w,0,1,2)
        self.assertEqual(p['gold'],300000);self.assertEqual(p['minimum_input_level'],3)
        self.assertIn('gem_level',p['missing']);self.assertIn('refining_level',p['missing'])
        w.bag[1]=item(878,level=3);w.bag[2]=item(885,level=3);self.assertTrue(K.plan_forge(w,0,1,2)['resources_ready'])

    def test_native_gem_level_is_maxenergy_and_not_strength(self):
        w=self.make();w.bag[0]=item(1,parameter=1012000000)
        w.bag[1]=item(878,level=1,attributes=((26,99),));w.bag[2]=item(885,level=3)
        self.assertIn('gem_level',K.plan_forge(w,0,1,2)['missing'])

    def test_reused_slots_gold_shortfall_and_changed_source_cannot_be_ready(self):
        w=self.make();self.assertIn('three_distinct_owned_items',K.plan_forge(w,0,1,1)['missing'])
        w.own.values[8]=99999;self.assertIn('gold',K.plan_forge(w,0,1,2)['missing'])
        k=copy.copy(K);k.cards=dict(k.cards);k.cards['forge']=dict(k.cards['forge'],review_status='requires_reaudit')
        p=k.plan_forge(self.make(),0,1,2);self.assertIn('source_rules_need_reaudit',p['unobserved']);self.assertNotIn('source_success_roll',p)

    def test_gem_effects_include_both_attack_bounds_and_stat_gems(self):
        data=K.inspect_equipment(item(1,parameter=2123012000));attrs=K.data['item_attribute_ids']
        self.assertEqual(data['source_gem_effects'][attrs['ITEMATTR_VAL_STR']],15)
        self.assertEqual(data['source_gem_effects'][attrs['ITEMATTR_VAL_MNATK']],8)
        self.assertEqual(data['source_gem_effects'][attrs['ITEMATTR_VAL_MXATK']],8)

class RecipeTests(unittest.TestCase):
    def test_specific_blueprint_ingredients_counts_currency_and_uses_are_observed(self):
        w=craft_actor();r=K.inspect_blueprint(w.bag[0]);self.assertTrue(r['recipe_observed'])
        self.assertEqual(r['materials'],[{'item_id':1779,'quantity':2},{'item_id':1774,'quantity':3},{'item_id':3116,'quantity':4}])
        self.assertEqual((r['fairy_coin_quantity'],r['remaining_uses']),(5,3))
        w.bag[0]=dataclasses.replace(w.bag[0],parameters=(1030040050,0));self.assertNotEqual(K.inspect_blueprint(w.bag[0])['materials'],r['materials'])

    def test_complete_recipe_requires_owned_fairy_tool_and_learned_skills_without_local_action(self):
        w=craft_actor();before=(dict(w.bag),dict(w.own.values));p=K.plan_blueprint(w,0,1,2)
        self.assertTrue(p['resources_ready']);self.assertEqual(p['requirements'],{1779:2,1774:3,3116:4,855:5})
        self.assertEqual((w.bag,w.own.values),before);self.assertFalse(p['automatic_execution_implemented'])

    def test_wrong_tool_depleted_fairy_missing_skill_uses_and_materials_are_not_ignored(self):
        for case in ('tool','fairy','skill','uses','materials'):
            with self.subTest(case=case):
                w=craft_actor()
                if case=='tool':w.bag[2]=item(1069)
                elif case=='fairy':w.bag[1]=dataclasses.replace(w.bag[1],endurance=0)
                elif case=='skill':w.skills={}
                elif case=='uses':w.bag[0]=dataclasses.replace(w.bag[0],instance_attributes=((26,1779),(29,1774),(28,3116),(30,0),(0,0)))
                else:w.bag.pop(6)
                self.assertFalse(K.plan_blueprint(w,0,1,2)['resources_ready'])

    def test_unobserved_recipe_or_inventory_not_fabricated(self):
        w=craft_actor();w.bag[0]=item(2300);self.assertIn('blueprint_material_parameters',K.plan_blueprint(w,0,1,2)['unobserved'])
        w.bag_ready=False;self.assertIn('native_inventory',K.plan_blueprint(w,0,1,2)['unobserved'])

    def test_vendor_reserves_finite_materials_only_when_recipe_skills_fairy_and_tool_exist(self):
        import test_market
        from vendor import Vendor
        w=craft_actor();w.bag[3]=item(1779,12);w.bag[5]=item(3116,14)
        _,_,m,p=test_market.MarketTests().make();p.world=w;m.world=w;p.market=m;p.mechanics=K
        v=Vendor(w,LIFE,m.gear,None,random.Random(1),w.own.position,ROOT/'assets')
        self.assertIn((3,1779,10),v.choices(p));self.assertIn((5,3116,10),v.choices(p))
        w.skills={};self.assertIn((3,1779,12),v.choices(p));self.assertEqual(K.craft_reservations(w),{})

    def test_fairy_level_growth_stamina_and_monostat_policy_are_distinct(self):
        w=craft_actor();f=K.inspect_fairy(w.bag[1],'STR')
        self.assertEqual(f['level'],20);self.assertTrue(f['monostat_matches_owner_policy']);self.assertTrue(f['breeding_minimum_level_met'])
        self.assertEqual(f['skills'][0],{'stone_type':13,'level':2});self.assertEqual((f['growth'],f['stamina']),(0,100))

class WorldTests(unittest.TestCase):
    def test_demonic_world_is_different_from_forsaken_city_and_their_entry_items(self):
        w=actor();dw=K.dungeon_requirements(w,'puzzleworld');fc=K.dungeon_requirements(w,'abandonedcity')
        self.assertEqual(dw['level_range'],[50,None]);self.assertIn('character_level',dw['missing'])
        self.assertEqual(fc['level_range'],[30,45]);self.assertIn('item_1812',fc['missing'])
        self.assertEqual(K.search('ДВ')[0]['id'],'demonic_world')

    def test_level_alone_never_proves_portal_open_or_valid_return_route(self):
        w=actor();w.own.values[0]=50;p=K.dungeon_requirements(w,'puzzleworld');self.assertEqual(p['missing'],[])
        self.assertIn('live_portal_open',p['unobserved']);self.assertIn('native_entry_and_return_route',p['unobserved'])
        self.assertFalse(p['automatic_execution_implemented'])

    def test_source_schedule_pvp_and_swamp_range_are_kept(self):
        d=K.data['map_rules']['darkswamp'];self.assertEqual(d['literal_calls']['MapCanPK'][0][1],1)
        self.assertEqual(d['literal_calls']['SetMapEntryTime'][0][2:],['0/3/0','0/1/0','0/2/0'])
        w=actor();w.own.values[0]=56;self.assertIn('character_level',K.dungeon_requirements(w,'darkswamp')['missing'])

    def test_ship_quote_checks_compatible_parts_and_never_spends_gold(self):
        w=actor();ship=K.ships[1];selection={key:ship[key][0] for key in ('hull','mobility','fore','artillery','component')}
        before=dict(w.own.values);p=K.plan_ship(w,1,selection)
        self.assertEqual(p['missing'],[]);self.assertEqual(p['selected_parts_price'],sum(K.parts[i]['price'] for i in selection.values()))
        self.assertIn('native_shipyard_quote',p['unobserved']);self.assertEqual(w.own.values,before)
        selection['artillery']=999999;self.assertIn('compatible_artillery',K.plan_ship(w,1,selection)['missing'])

    def test_drop_sources_keep_chests_and_unknown_positions_distinct(self):
        d=K.sources_for_item(3457);self.assertEqual(len(d['monster_sources']),2)
        self.assertTrue(any('Demonic' in m['name'] for m in d['monster_sources']))
        self.assertTrue(all(not m['live_spawn_verified'] and not m['drop_probability_known'] for m in d['monster_sources']))
        self.assertEqual(K.sources_for_item(1774)['monster_sources'][0]['locations'],[])

    def test_chat_explains_mechanics_without_breaking_existing_npc_questions(self):
        w=actor();s=Social(w,Mock(),w.own.name,ChatBudget(),1);s.mechanics_provider=lambda words:K.answer(words,w)
        s.npc_provider=lambda words:LIFE.npcs.answer(words,w.map,w.own.position)
        self.assertEqual(s.reply(['как','работает','форж'])[0],'mechanics');self.assertEqual(s.reply(['где','купить','лук'])[0],'npc')
        self.assertEqual(s.reply(['где','купить','кораллы'])[0],'npc')
        answer=K.answer(['где','добыть','сияющий','камень'],w);self.assertIn('ID883',answer);self.assertLessEqual(len(answer.encode('cp1251')),120)

    def test_operator_view_and_ability_answers_do_not_claim_automatic_execution(self):
        from show_mechanics import render
        self.assertIn('автоматическая операция',render(K,'корабли'));self.assertIn('пока нет',K.answer(['умеешь','сам','форж']))

class AdditionalPlansTests(unittest.TestCase):
    def test_combine_fee_and_failure_model_do_not_confuse_ui_zero_fee_with_backend(self):
        w=actor();scroll=next(i for i,r in K.items.items() if r['kind']==47)
        w.bag={0:item(scroll),1:item(878,level=3),2:item(878,level=3)}
        before=dict(w.bag);p=K.plan_gem_combine(w,0,1,2,bonus_state_level=0)
        self.assertTrue(p['resources_ready']);self.assertEqual(p['gold'],50000)
        self.assertAlmostEqual(p['success_probability'],.8);self.assertEqual(w.bag,before)
        self.assertTrue(p['failure_consumes_both_gems_and_scroll'])

    def test_unobserved_bonus_same_level_and_gem_cap_are_not_guessed(self):
        w=actor();scroll=next(i for i,r in K.items.items() if r['kind']==47)
        w.bag={0:item(scroll),1:item(878,level=3),2:item(878,level=3)}
        self.assertIsNone(K.plan_gem_combine(w,0,1,2)['success_probability'])
        w.bag[2]=item(878,level=2);self.assertIn('same_gem_level',K.plan_gem_combine(w,0,1,2)['missing'])
        w.bag[1]=item(878,level=9);w.bag[2]=item(878,level=9)
        self.assertIn('normal_gem_level_cap',K.plan_gem_combine(w,0,1,2)['missing'])

    def test_breeding_requires_two_real_distinct_parents_and_native_materials(self):
        w=craft_actor();parent=w.bag[1]
        w.bag={0:item(3918),1:parent,2:dataclasses.replace(parent),3:item(4530,10),4:item(3434,10)}
        before=(dict(w.bag),dict(w.own.values));p=K.plan_fairy_breeding(w,0,1,2)
        self.assertTrue(p['resources_ready']);self.assertEqual(p['gold'],160000)
        self.assertEqual(p['child_identity_and_traits'],'must_be_observed_from_server')
        self.assertEqual((w.bag,w.own.values),before)
        self.assertIn('distinct_fruit_and_two_parents',K.plan_fairy_breeding(w,0,1,1)['missing'])

    def test_breeding_parent_stamina_and_space_are_checked_without_changing_server_bug(self):
        w=craft_actor();parent=w.bag[1]
        w.bag={0:item(3918),1:parent,2:dataclasses.replace(parent,endurance=20),3:item(4530,10),4:item(3434,10)}
        w.bag_capacity=len(w.bag)+1;p=K.plan_fairy_breeding(w,0,1,2)
        self.assertIn('full_parent_stamina',p['missing']);self.assertIn('two_free_inventory_slots',p['missing'])
        self.assertEqual(w.bag[2].endurance,20)

class AuditTests(unittest.TestCase):
    def data(self):
        return {'source_files':{'script/test.lua':{'sha256':hashlib.sha256(b'original').hexdigest()}},'source_tables':{},
                'functions':[{'key':'fn','path':'script/test.lua'}],'cards':[{'id':'forge','evidence':['fn']}]}

    def test_matches_changed_and_missing_are_distinguished_without_exporting_source(self):
        from audit_mechanics import audit
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'script').mkdir();file=root/'script/test.lua';file.write_bytes(b'original')
            self.assertTrue(audit(root,self.data())['source_snapshot_matches'])
            file.write_bytes(b'changed private content');report=audit(root,self.data())
            self.assertEqual(report['changed'],1);self.assertEqual(report['mechanics_requiring_source_review'],['forge'])
            self.assertNotIn('changed private content',json.dumps(report));file.unlink()
            self.assertEqual(audit(root,self.data())['missing'],1)
            file.write_bytes(b'original');(root/'script/extra.lua').write_bytes(b'new private logic')
            extra=audit(root,self.data())
            self.assertFalse(extra['source_snapshot_matches']);self.assertEqual(extra['additional_lua_files'],['script/extra.lua'])

    def test_paths_outside_selected_resource_are_refused(self):
        from audit_mechanics import audit
        data=self.data();data['source_files']={'../escape':{'sha256':'x'}}
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):audit(d,data)

    def test_resource_or_parent_server_folder_are_both_accepted(self):
        from audit_mechanics import locate
        with tempfile.TemporaryDirectory() as d:
            resource=Path(d)/'resource';(resource/'script').mkdir(parents=True)
            self.assertEqual(locate(d),resource);self.assertEqual(locate(resource),resource)

class LocalKnowledgeTests(unittest.TestCase):
    def test_private_knowledge_wins_and_corrupt_cache_falls_back(self):
        from mechanics import load_knowledge
        with tempfile.TemporaryDirectory() as d:
            assets=Path(d)/'assets';assets.mkdir();bundled=assets/'mechanics.json'
            bundled.write_bytes((ROOT/'assets/mechanics.json').read_bytes())
            private=Path(d)/'data/knowledge/mechanics.json';private.parent.mkdir(parents=True)
            private.write_bytes(bundled.read_bytes())
            self.assertEqual(load_knowledge(assets).load_origin,'private_local_resource')
            for invalid in ('[]','{"version":1,"cards":[null],"functions":[]}', '{bad'):
                private.write_text(invalid)
                knowledge=load_knowledge(assets)
                self.assertEqual(knowledge.load_origin,'bundled_uploaded_snapshot')
                self.assertIsNotNone(knowledge.load_problem)
            incomplete=json.loads(bundled.read_text());incomplete['cards']=[]
            private.write_text(json.dumps(incomplete))
            self.assertEqual(load_knowledge(assets).load_origin,'bundled_uploaded_snapshot')

    def test_local_learning_swaps_only_valid_knowledge_and_preserves_bot_data_on_failure(self):
        from learn_mechanics import learn
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);old=root/'data/knowledge/mechanics.json';old.parent.mkdir(parents=True)
            old.write_bytes((ROOT/'assets/mechanics.json').read_bytes())
            accounts=root/'data/accounts.json';accounts.write_bytes(b'private saved identities')
            before=old.read_bytes()
            def failed(resource,output):output.write_text('[]')
            with self.assertRaises(ValueError):learn(root,old,failed)
            self.assertEqual(old.read_bytes(),before);self.assertEqual(list(old.parent.glob('*.tmp')),[])
            def valid(resource,output):output.write_bytes(before)
            self.assertEqual(learn(root,old,valid)['named_functions'],4135)
            self.assertEqual(accounts.read_bytes(),b'private saved identities')

    def test_stale_source_blocks_chat_cost_and_ship_or_dungeon_plans(self):
        stale=copy.copy(K);stale.cards=copy.deepcopy(K.cards)
        for card in stale.cards.values():card['review_status']='requires_reaudit'
        self.assertIn('требуют проверки',stale.answer(['как','работает','форж']))
        self.assertNotIn('level_range',stale.dungeon_requirements(actor(),'darkswamp'))
        self.assertIn('source_rules_need_reaudit',stale.plan_ship(actor(),1,{})['unobserved'])

if __name__=='__main__':unittest.main()
