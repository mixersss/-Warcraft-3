from pathlib import Path
import hashlib,json,re,argparse
parser=argparse.ArgumentParser(description='Project local mechanics evidence without distributing full server scripts.')
parser.add_argument('resource',type=Path)
args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1]/'knowledge'
ROOT.mkdir(exist_ok=True)
SRC=args.resource
paths=['ItemInfo.txt','ShipInfo.txt','skillinfo.txt','script/calculate/forge.lua','script/calculate/ItemEffect.lua',
       'script/calculate/AttrCalculate.lua','script/calculate/exp_and_level.lua','script/calculate/variable.lua',
       'script/MisScript/NpcScript01.lua','script/MisScript/NpcScript04.lua','script/MisScript/MissionScript01.lua',
       'script/MisScript/MissionScript02.lua','abandonedcity/ctrl.lua','abandonedcity/entry.lua',
       'darkswamp/ctrl.lua','darkswamp/entry.lua','garner2/entry.lua','script/monster/yeguai_guildwar.lua']
sources={}
for i,name in enumerate(paths,1):
 p=SRC/name;data=p.read_bytes();lines=data.decode('gb18030',errors='replace').splitlines()
 sources[name]={'id':f'L{i:02d}','kind':'owner_supplied_server_resource','path':name,'sha256':hashlib.sha256(data).hexdigest(),'lines':len(lines),'encoding':'gb18030 with replacement for inspection','status':'available_local_not_proven_official_classic'}
(ROOT/'sources-local.json').write_text(json.dumps({'as_of':'2026-11-12','provenance':'Owner-supplied PKO138 + Tools/resource, previously uploaded archive. Version/mutations not independently certified. No full original scripts included.','sources':list(sources.values())},ensure_ascii=False,indent=2)+'\n')
def cite(name,pattern):
 lines=(SRC/name).read_bytes().decode('gb18030',errors='replace').splitlines()
 n=next(i for i,l in enumerate(lines,1) if re.search(pattern,l))
 return {'source':sources[name]['id'],'line':n,'match':lines[n-1].strip()[:280]}
rules=[]
def add(i,topic,fact,evidence,status='local_code_audited',caveat=None):
 rules.append({'id':i,'topic':topic,'fact_ru':fact,'status':status,'evidence':evidence,'in_game_validated':False,'caveat_ru':caveat})
forge='script/calculate/forge.lua';item='ItemInfo.txt';npc='script/MisScript/NpcScript01.lua'
add('PET-01','fairies','Мордо — Mordo, предмет 680; его яйцо — 679.',[cite(item,r'^0*680\t'),cite(item,r'^0*679\t')],'catalog_only')
add('PET-02','fairies','Mordo Junior — предмет 681; Egg of Mordo Junior — 910. «Джуны» сопоставляются с Junior, не с обычным Мордо.',[cite(item,r'^0*681\t'),cite(item,r'^0*910\t')],'catalog_only','Русский разговорный термин не верифицирован внешним форумом; соответствие по контексту и каталогу.')
add('PET-03','fairies','Корм Fairy Ration имеет ID 227 и обработчик ItemUse_SiLiao.',[cite(item,r'^0*227\t'),cite('script/calculate/ItemEffect.lua',r'^function ItemUse_SiLiao')])
add('PET-04','fairy_marriage','В can_jlborn_item_main нужны два разных предмета фей типа 59, поколение Part1=0, уровень обоих не ниже 20, минимум две свободные ячейки.',[cite(forge,r'^function can_jlborn_item_main'),cite(forge,r'ItemType_JLone ~=59'),cite(forge,r'lv_JLone < 20'),cite(forge,r'Item_CanGet < 2')])
add('PET-05','fairy_marriage','Список допустимых Demonic Fruit: 3918,3919,3920,3921,3922,3924,3925; дополнительные материалы проверяются отдельно.',[cite(forge,r'if Item_EMstone_ID ~= 3918')])
add('PET-06','fairy_marriage','Lua-цена скрещивания (60-L1)*(60-L2)*100; если хотя бы один уровень выше 60, функция возвращает нулевую цену.',[cite(forge,r'Money_Need = \( 60 - lv_JLone'),cite(forge,r'if lv_JLone>60')],caveat='Это цена конкретной функции в этой сборке, не обещание бесплатной операции на любом классическом сервере.')
add('PET-07','fairy_marriage','Проверка полной stamina дважды сравнивает первого родителя и не сравнивает второго.',[cite(forge,r'if URE_JLone < MAXURE_JLone or URE_JLone < MAXURE_JLone')],caveat='Вероятная ошибка сборки. Для ботов проверять обоих родителей; сервер сейчас не изменять.')
add('PET-08','fairy_marriage','Каждый базовый стат ребёнка вычисляется как floor((стат первого+стат второго)*0.125).', [cite(forge,r'local new_str = math.floor'),cite(forge,r'local new_sta = math.floor')])
add('PET-09','fairy_marriage','В первой ветви плода два родителя Mordo создают 681; смешанные пары зависят от уровней и rad.',[cite(forge,r'if Item_JLone_ID ==680 or Item_JLother_ID ==680'),cite(forge,r'lv_JLone>=20 and lv_JLone<25')],caveat='Ветви >=88, >=50, >=10 при random(1,100) дают 13/51/91 исход из 100, а комментарии пишут 12/50/90. Проверять каждую ветвь/плод отдельно, не переносить числа в общий гайд.')
add('FORGE-01','gems','Refining Gem 885, Gem Composition Scroll 886; камень-рефайнер и статовый камень — разные предметы.',[cite(item,r'^0*885\t'),cite(item,r'^0*886\t')],'catalog_only')
add('FORGE-02','gems','Для объединения проверяются одинаковые ID и уровни двух камней; для камней типа49 входной уровень>=9 отклоняется.',[cite(forge,r'if ItemID2 ~= ItemID3'),cite(forge,r'if Item2_Lv >= 9'),cite(forge,r'if Item2_Lv ~= Item3_Lv')])
add('FORGE-03','gems','В Lua-формуле композиции вероятности различаются для типов49 и50; нельзя использовать одну вероятность для всех камней.',[cite(forge,r'^function Check_CG_HechengBS')])
add('FORGE-04','forging','Расчёт денежной платы форжа: (GetItem_JinglianLv(item)+1)*100000.',[cite(forge,r'^function getforge_money_main'),cite(forge,r'Money_Need = Jinglian_Lv \* 100000')])
add('FORGE-05','forging','Check_CG_Jinglian в предоставленном forge.lua выставляет b=1; формула случайного успеха закомментирована.',[cite(forge,r'^function Check_CG_Jinglian')],caveat='Локальная особенность функции. Не объявлять весь форж гарантированным: проверить вызывающий код, требования, расход и фактический результат.')
add('FORGE-06','forging','Совместимость камня с предметом проверяется по StoneItemType, а не только по прибавке атаки.',[cite(forge,r'^function Check_StoneItemType'),cite('script/calculate/variable.lua',r'StoneAttrType_Num =')])
add('APP-01','apparels','Apparel Fusion и Apparel Upgrade — отдельные операции; Lua реализует can_fusion_item_main и can_beuplv_item_main.',[cite(npc,r'"Apparel Fusion"'),cite(forge,r'^function can_fusion_item_main'),cite(forge,r'^function can_beuplv_item_main')])
add('RUNE-01','runes','В каталоге есть Kal Runestone 3457. Это кандидат на пользовательское название «руна кель».',[cite(item,r'^0*3457\t')],'catalog_only','Точное соответствие русского сленга ещё нужно подтвердить, не путать с Kylin и другими рунами.')
add('RUNE-02','runes','NpcScript04 содержит обмены за Kal Runestone, включая 5 рун в некоторых рецептах; единого назначения у предмета нет.',[cite('script/MisScript/NpcScript04.lua',r'5 Kal Runestones'),cite('script/MisScript/NpcScript04.lua',r'1 Kal Runestone')])
add('DUN-01','dungeons','Вход Forsaken City проверяет уровень30..45 и Ancient Generator1812.',[cite('abandonedcity/entry.lua',r'Lv\(Cha\) >=30'),cite('abandonedcity/entry.lua',r'CheckBagItem\(Cha, 1812\)')])
add('DUN-02','dungeons','Вход Dark Swamp проверяет уровень40..55.',[cite('darkswamp/entry.lua',r'Lv\(Cha\) >=40')])
add('DUN-03','dungeons','Обе карты привязаны к magicsea; записанные интервалы входа0/3/0, исчезновения0/1/0, закрытия0/2/0.',[cite('abandonedcity/ctrl.lua',r'SetMapEntryTime'),cite('darkswamp/ctrl.lua',r'SetMapEntryTime')],caveat='Наличие ctrl.lua не доказывает, что карта запущена. Время интерпретировать по часам/настройкам самого сервера и реальным объявлениям портала.')
add('PVP-01','pvp','Chaos Argent (garner2) запрещает вход в пати; требуется ровно одна Medal of Valor3849, Honor20..30000, репутация>=30, уровень>=20 и золото level*50.',[cite('garner2/entry.lua',r'Team_In == 1'),cite('garner2/entry.lua',r'HonorPoint < 20'),cite('garner2/entry.lua',r'Credit_Garner2 < 30'),cite('garner2/entry.lua',r'Money_Need = lv\*50')])
add('PVP-02','arenas','Получение Medal of Valor у Arena Administrator: Lua LvCheck >25, 50000 золота, свободная ячейка и отсутствие второй медали.',[cite(npc,r'LvCheck, ">", 25'),cite(npc,r'GiveItem, 3849, 1, 97')],caveat='Текст NPC и точная граница условия могут отличаться; для автоматизации использовать код и ответ сервера.')
add('GUILD-01','guilds','В NPC-условиях создания гильдии есть 100000G и Stone of Oath1780, типы Navy0 и Pirate1.',[cite(npc,r'CreateGuild, 0'),cite(npc,r'CreateGuild, 1'),cite(npc,r'HasItem, 1780, 1')],caveat='Требования C++/SQL, ограничения размера, имён и прав ещё не проверены; список NPC-условий не является полным контрактом.')
add('SHIP-01','ships','ShipInfo содержит Guppy с ограничением15, Transporter Type I20, Flying Fish30, Turtle15; документ3988 не идентифицирует уникальный корабль сам по себе.',[cite('ShipInfo.txt',r'^0001\t'),cite('ShipInfo.txt',r'^0002\t'),cite('ShipInfo.txt',r'^0003\t'),cite('ShipInfo.txt',r'^0004\t')],'catalog_only')
add('SHIP-02','ships','BoatLevelUpProc проверяет последовательность уровня, опыт корабля и золото персонажа, затем списывает опыт/деньги и выставляет уровень.',[cite('script/calculate/exp_and_level.lua',r'^function BoatLevelUpProc'),cite('script/calculate/exp_and_level.lua',r'boat_lv ~= lv_up - 1')])
add('SHIP-03','ships','Корабельные атрибуты пересчитываются отдельными функциями ShipAttrRecheck/Ship_ExAttrCheck; нельзя применять сухопутную модель движения к кораблю.',[cite('script/calculate/AttrCalculate.lua',r'^function ShipAttrRecheck')])
add('CLASS-01','leveling','Вторая профессия имеет шесть отдельных целевых цепочек; текущая Alpha13 умеет запросить свою, но полное прохождение/острова ещё не реализованы.',[cite('script/MisScript/MissionScript01.lua',r'DefineMission\( 749,'),cite('script/MisScript/MissionScript01.lua',r'DefineMission\( 758,')],caveat='Статус реализации берётся из исходников проекта Alpha13, не из заявления о тесте в игре.')
(ROOT/'mechanics.json').write_text(json.dumps({'as_of':'2026-11-12','scope':'Local build findings only, not a completed external forum survey. Do not execute as bot policy without native/in-game validation.','rules':rules},ensure_ascii=False,indent=2)+'\n')
print('Sources',len(sources),'rules',len(rules))
# Compact domain indexes, avoiding full item descriptions and proprietary scripts.
items=[]
for line in (SRC/'ItemInfo.txt').read_bytes().decode('gb18030',errors='replace').splitlines():
 a=line.split('\t')
 if a[0].isdigit() and len(a)>90:
  name=a[1].lower()
  if any(term in name for term in ('fairy','mordo','runestone','gem','sealed','fusion','apparel')):
   items.append({'id':int(a[0]),'name':a[1],'type':int(a[10]),'use_handler':a[86]})
ships=[]
for line in (SRC/'ShipInfo.txt').read_bytes().decode('gb18030',errors='replace').splitlines():
 a=line.split('\t')
 if a[0].isdigit() and len(a)>=12:ships.append({'id':int(a[0]),'name':a[1],'deed_item':int(a[2]),'actor_model':int(a[3]),'level_restriction':int(a[10]),'class_restriction':a[11]})
(ROOT/'catalog.json').write_text(json.dumps({'status':'catalog presence is not runtime availability or classical authenticity','items':items,'ships':ships},ensure_ascii=False,indent=2)+'\n')
print('Catalog',len(items),'items',len(ships),'ships')
