"""Project a source inventory and reviewed mechanic facts, never bundle/execute owner Lua."""
import argparse,hashlib,json,re
from collections import defaultdict
from pathlib import Path
from lua_inventory import functions,tokens,literal_calls
ROOT=Path(__file__).resolve().parents[1]
FORGE='script/calculate/forge.lua'
FUNCTIONS='script/calculate/functions.lua'
ITEMS='script/calculate/ItemEffect.lua'

def cards():
    # Descriptions are reviewed explanations; existence/evidence links are checked at build time.
    definitions=[
      ('gem_combine','Объединение гемов',['гемы','объединение','combine'],FORGE,
       ['can_unite_item_main','begin_unite_item','getunite_money_main','Check_CG_HechengBS'],['OpenUnite'],
       'Нужны свиток типа47 и два одинаковых гема одного уровня. Списание идёт при попытке; неудача уничтожает гем.',
       'Два одинаковых гема одного уровня и свиток; цена50000G. Успех зависит от типа, уровня и бонуса.',True),
      ('forge','Вставка гемов и форж',['форж','фордж','заточка','forge'],FORGE,
       ['can_forge_item_main','CheckItem_HaveHole','Check_StoneLv','Check_StoneItemType','getforge_money_main','Check_CG_Jinglian'],['OpenForge'],
       'Проверяются тип экипировки, сокет или уже вставленный такой гем, серверная совместимость StoneItemType и уровни гема/камня улучшения. Цена зависит от суммарной заточки. В этом исходнике проверка случайного успеха разрешает операцию всегда; остальные проверки остаются.',
       'Форж требует подходящий гем, камень улучшения, сокет и золото. Уровни и совместимость проверяются отдельно.',True),
      ('sockets','Создание сокетов',['сокеты','дырки','отверстия','проточка'],FORGE,
       ['can_milling_item_main','Check_Jiaguji','Check_Cuihuafen','Check_CG_damo','get_milling_money_main'],['OpenMilling'],
       'Нужны Equipment Stabilizer890 и Equipment Catalyst891. Этот обработчик не разрешает добавлять сокет при уже двух; наличие предметов с тремя сокетами не доказывает возможность сделать третий здесь.',
       'Для сокета нужны ID890 и891; цена(сокеты+1)×50000G. При двух сокетах этот обработчик отказывает.',True),
      ('gem_extract','Извлечение гемов',['извлечение','вытащить гем','extract'],FORGE,
       ['can_getstone_item_main','getstone_money_main','getstone_item'],['OpenGetStone'],
       'Извлечение работает по существующему форжу; требуются инструмент, деньги и место. Порядок и понижение уровня сверять по действию getstone_item, не путать с простым удалением сокета.',
       'Извлечение требует инструмент и место; цена зависит от суммы уровней вставленных гемов.',True),
      ('apparel_fusion','Слияние внешнего вида',['аппарель','внешний вид','apparel','слияние'],FORGE,
       ['can_fusion_item_main','ronghe_item','getfusion_money_main'],['OpenFusion'],
       'Слияние использует отдельные предметы внешнего вида и характеристик; допустимость, переносимые данные и стоимость задаются этими обработчиками. Это отдельная операция от сокетов и вставки гемов.',
       'Слияние внешнего вида и форж — разные операции. Перед слиянием нужны совместимые вещи и проверка переноса.',False),
      ('apparel_upgrade','Усиление слияния',['апгрейд внешнего вида','apparel upgrade'],FORGE,
       ['can_beuplv_item_main','Check_CG_beuplv','getupgrade_money_main'],['OpenUpgrade'],
       'Усиление слияния имеет собственные уровни и вероятность, не вероятность вставки гема. Стоимость квадратичная по следующему уровню.',
       'Усиление слияния имеет свою вероятность и стоимость; успех обычного форжа к нему не применяется.',True),
      ('special_upgrade','Улучшение особых комплектов',['ансилы','особые комплекты','black dragon','kylin'],FORGE,
       ['can_tichun_item_main','tichun_item','gettichun_money_main'],['OpenItemTiChun'],
       'Проверяются конкретные ID исходного комплекта и материала улучшения; для образов требуется исходный fusionID. Не заменять это общей заточкой любого оружия.',
       'Особые комплекты улучшаются отдельным материалом под конкретный ID; обычный гем его не заменяет.',True),
      ('coral_recharge','Перезарядка кораллов',['кораллы','заряд коралла','батарейки'],FORGE,
       ['can_energy_item_main','energy_money_main','energy_item'],['OpenItemEnergy'],
       'Коралл типа29 заряжается батареей1022 или1024. Уже полный коралл отвергается; нужны деньги и свободная ячейка. В этом исходнике энергия устанавливается в максимум: расчёт50..1000/1500 ниже не применяется, несмотря на старое описание НПС.',
       'Коралл: батарея1022/1024, цена300/1000G. В этом скрипте заряд становится полным; описание НПС устарело.',True),
      ('tool_repair','Ремонт мирных инструментов',['ремонт инструмента','инструменты'],FORGE,
       ['can_shtool_item_main','shtool_money_main','shtool_item'],['OpenItemFix'],
       'Ремонт мирных инструментов отделён от ремонта оружия и корабля. Нужен подходящий инструмент ремонта и200G.',
       'Ремонт мирного инструмента — отдельная услуга печи: нужен материал ремонта и200G.',True),
      ('manufacturing','Производство',['производство','manufacturing','крафтовые камни'],FORGE,
       ['can_manufacture_item_main','Read_manufacture','end_manufacture_item'],['LifeSkillBegin'],
       'Для чертежа2300 нужны живая фея типа59 с навыком13, инструмент1068 и навык персонажа338. Реальные ингредиенты, количества, уровень, число использований и Fairy Coins читаются из параметров именно этого чертежа.',
       'Производство: чертёж2300, инструмент1068, фея с навыком13 и навык338. Материалы записаны в чертеже.',True),
      ('crafting','Ремесло',['ремесло','crafting','чертежи','чертёж'],FORGE,
       ['can_manufacture_item_main','Read_manufacture','end_manufacture_item'],['LifeSkillBegin'],
       'Для чертежа2301 нужны фея с навыком14, инструмент1069 и навык персонажа340. Ингредиенты берутся из STR/CON/DEX чертежа, количества из частей его forge-параметра; нужны Fairy Coins855.',
       'Ремесло: чертёж2301, инструмент1069, фея с навыком14 и навык340. Нужны материалы чертежа и монеты855.',True),
      ('cooking','Кулинария',['кулинария','готовка','cooking'],FORGE,
       ['can_manufacture_item_main','Read_manufacture','end_manufacture_item'],['LifeSkillBegin'],
       'Для чертежа2302 нужны фея с навыком16, инструмент1067 и навык персонажа339. Проверяются жизнь феи, износ инструмента, уровни, материалы, оставшиеся использования чертежа и монеты855.',
       'Кулинария: чертёж2302, инструмент1067, фея с навыком16 и навык339; ингредиенты зависят от чертежа.',True),
      ('decomposition','Разбор предметов',['разбор','разобрать','декомпозиция'],FORGE,
       ['can_fenjie_item_main','end_fenjie_item'],[],
       'Разбор имеет отдельную проверку феи, её навыка, инструмента и результата. Нельзя считать любой мусор пригодным сырьём без этой проверки.',
       'Разбор требует подходящую фею и инструмент; возможность разобрать вещь проверяется отдельно.',False),
      ('fairy_feed','Кормление феи',['кормление','кормить','корм феи'],ITEMS,
       ['ItemUse_SiLiao','ItemUse_CWSiLiao'],[],
       'Корм типа57 используется на фее типа59 при неполной выносливости. В этих обработчиках кормить во время плавания нельзя. Восстановление2500 или250 зависит от функции предмета, не от названия.',
       'Корм типа57 восстанавливает выносливость феи59. Полную фею и фею во время плавания кормить нельзя.',True),
      ('fairy_growth','Рост и моностатная фея',['феи','фея','fairy','моностат'],FUNCTIONS,
       ['Elf_LvUp','Elf_LvUp_1','Give_ElfEXP_MISSION'],[],
       'Уровень феи — сумма пяти характеристик. Выносливость и рост отдельны; ветки повышения используют выбранную характеристику и вероятность. Политика владельца: одна развиваемая характеристика, без скрытого перераспределения остальных.',
       'Уровень феи равен сумме статов. Рост и выносливость различаются; по нашему ТЗ развиваем один стат.',True),
      ('fairy_breeding','Разведение и Мордо',['мордо','разведение','скрещивание','брак фей'],FORGE,
       ['can_jlborn_item_main','getjlborn_money_main','jlborn_item'],['OpenEidolonMetempsychosis'],
       'Нужны две разные феи типа59 минимум20уровня, подходящий плод, требуемые материалы, минимум две свободные ячейки и деньги. Для плодов3918..3925 разные пары материалов. Данные родителей и результат не выдумывать; исходник содержит собственные проверки состояния.',
       'Разведение: две разные феи20+, плод, его материалы, деньги и2свободных места. Мордо не выдаётся по обещанию.',True),
      ('ship_build','Покупка и сборка корабля',['корабли','корабль','судно','ship'],None,[],['CreateBoat'],
       'Тип судна задаёт допустимые корпус, двигатель, нос, пушки, компонент, уровень и класс. Полная стоимость зависит от выбранных частей; строит реальный судостроитель с подтверждением договора.',
       'Корабль выбирается по уровню и классу, затем по совместимым частям; цена складывается из выбранных деталей.',True),
      ('ship_level','Развитие корабля',['уровень корабля','прокачка корабля','boat level'], 'script/calculate/exp_and_level.lua',
       ['BoatLevelUpProc','Ship_Tran'],['BoatLevelBerthList'],
       'Для повышения требуются ровно следующий уровень, собственный опыт судна и золото персонажа. Успешный серверный обработчик списывает оба ресурса и синхронизирует лодку и героя.',
       'Кораблю нужны свой опыт и золото хозяина; повышается следующий уровень, а ресурсы списывает сервер.',True),
      ('ship_supply','Топливо, ремонт и выход в море',['топливо','верфь','ремонт корабля','плавание'],None,[],
       ['SupplyBoat','SupplyBerthList','RepairBoat','RepairBerthList','LuanchBerthList','SalvageBerthList'],
       'Запас топлива, прочность и портовые операции отдельны от HP и SP героя. Нужны реальный договор, выбранное судно, деньги и корректная стоянка; подтверждение выхода в море требуется от сервера.',
       'У судна свои топливо и прочность. Снабжение, ремонт и спуск выполняются в порту по настоящему договору.',False),
      ('pvp','PvP и безопасные зоны',['пвп','pvp','дуэль','pk'],None,[],[],
       'Разрешение PvP задаётся картой, а конкретная атака зависит от состояния игроков, команды, режима и безопасной зоны. MapCanPK=1 само по себе не означает, что любую цель можно атаковать. Текущий PvE-контроллер не заменять атакой людей без реализации режима.',
       'PvP зависит от карты, режима, группы и защиты зоны. Одного разрешения MapCanPK недостаточно.',True),
      ('demonic_world','ДВ / Demonic World',['дв','demonic world','демонический мир'], 'puzzleworld/entry.lua',
       ['check_can_enter_puzzleworld','begin_enter_puzzleworld'],[],
       'ДВ — puzzleworld/puzzleworld2, не abandonedcity. Первый вход минимум50уровня; источник вgarner. Время и доступность проверяются отдельно по живому порталу и серверному времени.',
       'ДВ — puzzleworld: вход50+, портал наgarner. Наличие расписания в файле не доказывает, что портал открыт сейчас.',True),
      ('dark_swamp','Топи / Dark Swamp',['топи','болото','darkswamp'], 'darkswamp/entry.lua',
       ['check_can_enter_darkswamp','begin_enter_darkswamp'],[],
       'В этом ресурсе Топи принимают40–55уровни. Источник входаmagicsea; карта допускаетPvP. Нужно знать расписание, выход и реальные цели, а не только отправить вход.',
       'Топи в этом ресурсе:40–55уровни, вход изmagicsea. PvP разрешён; расписание и открытый портал проверяем отдельно.',True),
      ('forsaken_city','Forsaken City',['forsaken city','abandonedcity'], 'abandonedcity/entry.lua',
       ['check_can_enter_abandonedcity','begin_enter_abandonedcity'],[],
       'Первый вход30–45уровней, нужен Ancient Generator1812; при входе один расходуется. Не путать с ДВ50+.',
       'Forsaken City:30–45уровни иAncient Generator1812, который расходуется. Это другая карта, не ДВ.',True),
      ('materials','Гемы, руны, каль и материалы',['камни','сияющие','очищающие','руны','кель','каль','добыча'],None,[],[],
       'Названия связываются с ID, типом и StoneInfo. Источники — реальные магазины, таблицы дропа/области появления и буквальные награды скриптов. Условный спавн не считать живой целью; неизвестную вероятность не выдумывать.',
       'Камень ищем по ID: магазин, реальный дроп и карта. Руна и каль — разные предметы; название не заменяет проверку.',True),
      ('unsealing','Ансилы и запечатанные вещи',['ансил','запечатанные','unseal'],None,[],['SendExchangeData','SendExchangeXData'],
       'Снятие печати, обмен рун и усиление комплектов — отдельные системы. Нужны конкретные ID и условия соответствующего NPC; универсальную выдачу любого ансила не предполагать.',
       'Ансил, обмен рун и форж — разные операции. Сначала нужен конкретный предмет и условия соответствующего НПС.',False),
      ('treasure','Карты сокровищ',['сокровища','пергамент','карты сокровищ'],ITEMS,
       ['ItemUse_Map_JLBYPJ','ItemUse_JLB_GoldenMap'],[],
       'Карта имеет индивидуальные параметры и проверки; награда/координаты могут вычисляться динамически. Один ID карты не доказывает одинаковое место и награду.',
       'У карты сокровищ собственные параметры. Координаты и награда не определяются одним названием предмета.',False),
      ('guilds','Гильдии и войны',['гильдии','гильдия','война гильдий'],None,[],['CreateGuild','ListAllGuild','GuildBank'],
       'Создание, членство, гильдейский банк и войны имеют разные серверные проверки. Все найденныеguildwar*обработчики индексируются; действия требуют отдельного нативного контроллера.',
       'Гильдия, её банк и война — разные проверки. Для операций нужны реальное членство и ответ сервера.',False),
      ('life_skills','Мирные навыки и исторические квесты',['мирные профессии','мирные навыки','исторические'],None,[],['LifeSkillBegin'],
       'Уровни опыта мирных навыков берутся изlifelvup, реальные очки из атрибутов персонажа. Производство, ремесло, кулинария, сбор и ларёк — разные навыки; наличие очков не означает изученный навык.',
       'Мирный опыт, очки и изученный навык различаются. Исторические задания дают реальные награды; книги изучаются отдельно.',True),
    ]
    result=[]
    for identity,title,aliases,path,fn,hooks,explanation,short,reviewed in definitions:
        result.append({'id':identity,'title':title,'aliases':aliases,'source_path':path,'functions':fn,'npc_hooks':hooks,
                       'explanation':explanation,'short_answer':short,'review_status':'reviewed_rules' if reviewed else 'indexed_needs_review',
                       'automatic_execution_implemented':False})
    return result

def table_rows(path):
    for line in path.read_bytes().decode('gb18030',errors='replace').splitlines():
        row=line.split('\t')
        if row[0].isdigit():yield row

def project(resource,out,refresh_reviewed_lock=False):
    files={};index=[];private={};function_names=set();item_flows=defaultdict(list);maps={}
    for path in sorted(resource.rglob('*.lua')):
        relative=path.relative_to(resource).as_posix();raw=path.read_bytes();source=raw.decode('gb18030',errors='replace')
        definitions,issues=functions(source)
        if issues:raise ValueError('Lua structural inventory failed: '+relative+' '+str(issues))
        files[relative]={'sha256':hashlib.sha256(raw).hexdigest(),'functions':len(definitions),'runtime_loaded_verified':False}
        for definition in definitions:
            key=relative+':'+str(definition['line'])+':'+definition['name'];definition['key']=key
            private[key]=definition;function_names.add(definition['name'])
            record={k:v for k,v in definition.items() if not k.startswith('_')};record['path']=relative
            index.append(record)
            for name in ('GiveItem','TakeItem','CheckBagItem'):
                for args in literal_calls(definition['_tokens'],name):
                    pos=2 if name=='GiveItem' else 2 if name=='TakeItem' else 1
                    if len(args)>pos and type(args[pos]) is int:
                        item_flows[args[pos]].append({'function':key,'kind':'reward' if name=='GiveItem' else 'requirement',
                                                     'literal_quantity':args[pos+1] if len(args)>pos+1 and type(args[pos+1]) is int else None,
                                                     'conditions_not_evaluated':True})
            for name in ('MisResultAction','TriggerAction','MisBeginAction'):
                for args in literal_calls(definition['_tokens'],name):
                    pos=0 if name.startswith('Mis') else 1
                    if len(args)>pos+2 and args[pos]=={'variable':'GiveItem'} and type(args[pos+1]) is int:
                        item_flows[args[pos+1]].append({'function':key,'kind':'quest_or_trigger_reward','literal_quantity':args[pos+2] if type(args[pos+2]) is int else None,'conditions_not_evaluated':True})
        if path.name in ('ctrl.lua','entry.lua') and path.parent.parent==resource:
            mapname=path.parent.name;mapdata=maps.setdefault(mapname,{'sources':[],'literal_calls':{},'entry_level_conditions':[]})
            mapdata['sources'].append(relative);stream=tokens(source)
            for name in ('MapCanPK','MapCanTeam','MapCanSavePos','MapCopyNum','SingleMapCopyPlyNum','MapType',
                         'SetMapEntryMapName','SetMapEntryTime','SetMapEntryEntiID'):
                values=literal_calls(stream,name)
                if values:mapdata['literal_calls'].setdefault(name,[]).extend(values)
            for d in definitions:
                if d['name'].startswith('check_can_enter'):
                    body=' '.join(t[1] for t in d['_tokens'] if t[0]!='string')
                    bounds=re.findall(r'\bLv\s*\([^)]*\)\s*(>=|<=|>|<|==)\s*(\d+)',body)
                    mapdata['entry_level_conditions'].extend({'operator':op,'level':int(n),'function':d['key'],'logical_gate_exhaustively_proven':False} for op,n in bounds)
                    mapdata.setdefault('required_item_candidates',[]).extend(a[1] for a in literal_calls(d['_tokens'],'CheckBagItem') if len(a)>1 and type(a[1]) is int)
            xs=re.findall(r'local\s+POS_X\s*=\s*(\d+)',source);ys=re.findall(r'local\s+POS_Y\s*=\s*(\d+)',source)
            if len(xs)==len(ys)==1:mapdata['entry_position_m']=[int(xs[0]),int(ys[0])]
    npcs=json.loads((ROOT/'assets/world-npcs.json').read_text())['npcs'];by_name=defaultdict(list)
    for d in index:by_name[(d['path'],d['name'])].append(d)
    mechanic_cards=cards()
    for card in mechanic_cards:
        evidence=[]
        for name in card['functions']:
            rows=by_name.get((card['source_path'],name),[])
            if len(rows)!=1:raise ValueError('Missing/ambiguous mechanic evidence '+str((card['id'],name)))
            evidence.append(rows[0]['key'])
        card['evidence']=evidence;card['npc_keys']=[]
        for npc in npcs:
            rows=[d for d in index if d['name']==npc['script_function'] and d['path'].startswith('script/MisScript/NpcScript')]
            if any(set(card['npc_hooks']) & {t[1] for t in private[d['key']]['_tokens'] if t[0]=='identifier'} for d in rows):
                card['npc_keys'].append(npc['key'])
    stones={int(r[0]):{'name':r[1],'item_id':int(r[2]),'compatible_item_kinds':[int(n) for n in r[3].split(',')],
                         'category':int(r[4]),'hint_function':r[5]} for r in table_rows(resource/'StoneInfo.txt')}
    ships={int(r[0]):{'name':r[1],'deed':int(r[2]),'model':int(r[3]),'hull':[int(n) for n in r[5].split(',')],
             'mobility':[int(n) for n in r[6].split(',')],'fore':[int(n) for n in r[7].split(',')],
             'artillery':[int(n) for n in r[8].split(',')],'component':[int(n) for n in r[9].split(',')],
             'minimum_level':int(r[10]),'jobs':[int(n) for n in r[11].split(',')],'cargo_base':int(r[21])}
             for r in table_rows(resource/'ShipInfo.txt')}
    parts={int(r[0]):{'name':r[1],'price':int(r[7]),'durability':int(r[8]),'defence':int(r[10]),
                       'min_attack':int(r[12]),'max_attack':int(r[13]),'fuel':int(r[18]),'speed':int(r[21])}
             for r in table_rows(resource/'ShipItemInfo.txt')}
    forge_rows=[{'level':int(r[0]),'failure_level':int(r[1]),'success_percent':int(r[2]),
                 'materials':[list(map(int,p.split(','))) for p in r[3:9] if p!='0,0'],'gold':int(r[9]),
                 'runtime_hook_binding_verified':False} for r in table_rows(resource/'forgeitem.txt')]
    life_levels={int(r[1]):int(r[2]) for r in table_rows(resource/'lifelvup.txt')}
    # Item attributes needed to read a specific blueprint/fairy from confirmed native item data.
    attributes={};variable=(resource/'script/calculate/ItemAttrType.lua').read_bytes().decode('gb18030',errors='replace')
    for line in variable.splitlines():
        m=re.match(r'\s*(ITEMATTR_\w+)\s*=\s*(\d+|ITEMATTR_\w+)(?:\s*\+\s*(\d+))?\s*(?:;|--|$)',line)
        if m:
            base=int(m[2]) if m[2].isdigit() else attributes.get(m[2])
            if base is not None:attributes[m[1]]=base+int(m[3] or 0)
    all_calls={name for d in index for name in d['calls']}
    item_bases={}
    for row in table_rows(resource/'ItemInfo.txt'):
        if len(row)<65:continue
        values={}
        for name,column in (('STR',52),('AGI',53),('DEX',54),('CON',55),('STA',56)):
            numbers=row[column].split(',')
            if all(re.fullmatch(r'-?\d+',n) for n in numbers) and len(set(numbers))==1:
                values[str(attributes['ITEMATTR_VAL_'+name])]=int(numbers[0])
        item_bases[int(row[0])]={'name':row[1],'kind':int(row[10]),'stack':int(row[20]),'price':int(row[22]),
                                  'constant_attributes':values,'hooks':sorted({value for value in row if value in function_names})}
    varsource=(resource/'script/calculate/variable.lua').read_bytes().decode('gb18030',errors='replace')
    forgeable=[int(n) for n in re.findall(r'Item_CanJinglian_ID\s*\[\d+\]\s*=\s*(\d+)',varsource)]
    variable_tokens=tokens(varsource)
    variable_code=' '.join(t[1] for t in variable_tokens if t[0]!='string')
    ids={int(k):int(v) for k,v in re.findall(r'StoneTpye_ID\s*\[\s*(\d+)\s*\]\s*=\s*(\d+)',variable_code) if int(k)>0}
    effects={int(k):int(v) for k,v in re.findall(r'StoneEff\s*\[\s*(\d+)\s*\]\s*=\s*(\d+)',variable_code)}
    statnames={int(k):v for k,v in re.findall(r'StoneAttrType\s*\[\s*(\d+)\s*\]\s*=\s*(ITEMATTR_\w+)',variable_code)}
    compatible={int(k):[int(v) for v in re.findall(r'\d+',values) if int(v)>0]
                for k,values in re.findall(r'StoneItemType\s*\[\s*(\d+)\s*\]\s*=\s*\{([^}]+)\}',variable_code)}
    tooltip_stones=stones
    stones={index:{'name':item_bases[identity]['name'],'item_id':identity,
                   'compatible_item_kinds':compatible[index],'attribute':statnames[index],
                   'attribute_id':attributes[statnames[index]],'bonus_per_level':effects[index],
                   'attack_adds_min_and_max':statnames[index]=='ITEMATTR_VAL_MNATK',
                   'tooltip_present':index in tooltip_stones,'rule_source':'script/calculate/variable.lua'} for index,identity in ids.items()}
    projection_hash=hashlib.sha256(json.dumps({'stones':stones,'forgeable':forgeable,'attributes':attributes},sort_keys=True).encode()).hexdigest()
    lock_path=ROOT/'knowledge/mechanics-evidence-lock.json'
    lock=json.loads(lock_path.read_text()) if lock_path.exists() else {}
    source_tables={name:hashlib.sha256((resource/name).read_bytes()).hexdigest()
                   for name in ('StoneInfo.txt','ShipInfo.txt','ShipItemInfo.txt','ItemInfo.txt','forgeitem.txt','lifelvup.txt')}
    # Helpers can call native/dynamic/global functions: a partial call graph cannot
    # prove an unrelated change harmless. Conservatively invalidate reviewed rules.
    snapshot=hashlib.sha256(json.dumps({'lua':files,'tables':source_tables},sort_keys=True).encode()).hexdigest()
    reviewed={}
    for card in mechanic_cards:
        if card['review_status']!='reviewed_rules':continue
        records=[next(d for d in index if d['key']==key) for key in card['evidence']]
        evidence={d['path']+':'+d['name']:d['sha256'] for d in records}
        evidence['constant_projection']=projection_hash
        evidence['source_snapshot']=snapshot
        reviewed[card['id']]=evidence
        if not refresh_reviewed_lock and lock.get(card['id'])!=evidence:card['review_status']='requires_reaudit'
    if refresh_reviewed_lock:lock_path.write_text(json.dumps(reviewed,ensure_ascii=False,indent=2)+'\n')
    breeding_materials={}
    breeding=next(d for d in private.values() if d['name']=='can_jlborn_item_main' and d['key'].startswith(FORGE+':'))
    body=' '.join(t[1] for t in breeding['_tokens'] if t[0]!='string')
    for match in re.finditer(r'if\s+Item_EMstone_ID\s*==\s*(\d+)\s+then(.*?)(?=if\s+Item_EMstone_ID\s*==|local\s+ItemType_JLone|$)',body):
        ids_found=re.findall(r'CheckBagItem\s*\(\s*role\s*,\s*(\d+)\s*\)',match[2])
        amounts=re.search(r'if\s+i1\s*<\s*(\d+)\s+or\s+i2\s*<\s*(\d+)',match[2])
        if len(ids_found)==2 and amounts:breeding_materials[int(match[1])]=[[int(ids_found[0]),int(amounts[1])],[int(ids_found[1]),int(amounts[2])]]
    coverage={'lua_files':len(files),'named_functions':len(index),'structural_errors':0,
              'reviewed_mechanics':sum(c['review_status']=='reviewed_rules' for c in mechanic_cards),
              'indexed_only_mechanics':sum(c['review_status']=='indexed_needs_review' for c in mechanic_cards),
              'requires_reaudit':sum(c['review_status']=='requires_reaudit' for c in mechanic_cards),
              'all_game_mechanics_exhaustively_understood':False,'owner_engine_binaries_available_for_full_audit':False,
              'runtime_loading_and_dynamic_branches_verified':False,
              'native_or_dynamic_call_names':sorted(all_calls-function_names)}
    result={'version':1,'coverage':coverage,'cards':mechanic_cards,'stones':stones,'ships':ships,'ship_parts':parts,
            'forge_table':forge_rows,'forgeable_item_kinds':forgeable,'life_levels':life_levels,'fairy_breeding_materials':breeding_materials,
            'item_attribute_ids':attributes,'item_bases':item_bases,'map_rules':maps,
            'source_files':files,'source_tables':source_tables,
            'tooltip_stones':tooltip_stones,'functions':index,'literal_item_flows':item_flows,
            'knowledge_does_not_authorize_unimplemented_native_actions':True}
    out.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({**{k:v for k,v in coverage.items() if k!='native_or_dynamic_call_names'},
                      'stones':len(stones),'ship_types':len(ships),'ship_parts':len(parts),'maps':len(maps)},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('resource',type=Path);p.add_argument('--out',type=Path,default=ROOT/'assets/mechanics.json')
    p.add_argument('--refresh-reviewed-lock',action='store_true',help='Only after reviewing changed source rules')
    a=p.parse_args();project(a.resource,a.out,a.refresh_reviewed_lock)
