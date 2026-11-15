"""Render a standalone Russian player guide from derived facts and runtime plans."""
import argparse,hashlib,html,json,re,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parent;OUT=REPO/'releases/piratia/guides-51'
MAPS={'garner':'Аскарон / Аргент','magicsea':'Магический океан / Шайтан','darkblue':'Синий океан / Ледынь','jialebi':'Карибы'}
TITLES={'Secretary Message':'Письмо секретарю','A Small Task':'Небольшое поручение','Food for the Navy':'Провизия для флота','Missing Tommy':'Пропавший Томми','Report to General':'Доклад генералу','Food Poisoning':'Пищевое отравление','Quest for Antidote':'Поиск противоядия',"Tommy's Request":'Просьба Томми','A Crazy Reason':'Странная причина','Thorough Investigation':'Тщательное расследование',"Ditto's Report":'Доклад Дитто','A New Task':'Новое поручение','The Lost Tool':'Потерянный инструмент','Kill the Shrooms':'Уничтожить грибы',"Ditto's Request":'Просьба Дитто','Bandit Hideout Map':'Карта логова бандитов','Ambush Bandit':'Засада на бандита','Bounty':'Награда за голову','Desert Visit':'Визит в пустыню'}

def build(make_pdf=False):
    load=lambda p:json.loads((ROOT/p).read_text(encoding='utf8'))
    story=load('assets/story-quests.json');reference=load('assets/story-reference.json');plans=load('assets/skill-guides.json');life=load('assets/life-items.json');npcs=load('assets/world-npcs.json')['npcs'];mobs=load('assets/world-mobs.json')['monsters'];sources=load('knowledge/guide-sources.json')
    items={r['id']:r for r in json.loads((REPO/'piratia-city-shops/native/item-database.json').read_text())};books={int(k):r for k,r in life['books'].items()};byskill={r['skill']:(identity,r) for identity,r in books.items() if identity>=3160}
    def item(i):return items.get(i,{}).get('name_ru') or life['names'].get(str(i)) or f'предмет ID{i}'
    def point(mapname,p):return f'{MAPS.get(mapname,mapname)} ({p[0]//100}, {p[1]//100})'
    def npc(mapname,p):
        names=[n['name'] for n in npcs if n['map']==mapname and n['position']==p]
        return (names[0]+' — ' if names else '')+point(mapname,p)
    def mob(i):
        r=mobs.get(str(i),{});name=r.get('name',f'моб ID{i}');return f"{name} (ID{i}, ур.{r.get('level','?')})"
    def needs(rows):return '; '.join((f"собрать {item(r['id'])} (ID{r['id']})" if r['kind'] in (1,'item') else 'убить '+mob(r['id']))+f" ×{r['count']}" for r in rows) or 'поговорить / проверить описание задания у НПС'
    md=['# Пиратия PKO 1.38 — история и навыки', '', 'Версия справочника: Alpha51, 15.11.2026. Составлен под переданные владельцем файлы сервера. Это наш сводный гайд, а не найденная статья неизвестного сервера. Полные внешние гайды пока не проверены: обычные сайты блокирует сеть облачной среды. Проверенные публичные ссылки перечислены в конце.', '',
        '## Как пользоваться','', 'Открой HTML-файл в браузере: он работает без интернета, есть поиск и печать в PDF. Числа координат совпадают с миникартой; реальные карты/доступность НПС могут зависеть от условий сервера. Названия в скобках оставлены как в исходной сборке. Перевод внутри самой игры не устанавливается.', '',
        '## Исторические квесты: начало в Аргенте','',
        'Начинай с 10 уровня. У Сенны (Newbie Guide - Senna) возьми Secretary Message и иди к секретарю Salvier. Варианты первого письма в других городах сходятся к общей записи завершения200; не пытайся брать все варианты одновременно.', '',
        'История даёт жизненный опыт: через жизненные уровни получаются очки мирных навыков, например для ларька. Это отдельная система от боевых очков навыков. Покупка книги сама по себе очков не создаёт. Размер награды в игре зависит от действующих настроек сервера; здесь рейты не меняются.', '',
        'Дальше следуй шагам ниже. Особое место — Food Poisoning207 и Quest for Antidote208: сначала письмо3966 к Дитто, затем ингредиенты противоядия; после получения противоядия3967 вернись к генералу и заверши207. Их нельзя проходить как независимые задания строго по номеру.', '']
    for number,q in enumerate(story['quests'],1):
        md += [f"### {number}. {TITLES.get(q['title'],q['title'])} — {q['title']} [журнал {q['journal']}]",'',
               'Взять: '+npc(q['map'],q['position'])+'.','', 'Задача: '+needs(q['needs'])+'.','',
               'Сдать: '+npc(q.get('receiver_map',q['map']),q['receiver'])+'.','']
        if q['journal']==207:md += ['Если нет противоядия3967: отнеси полученное письмо3966 Дитто (2250,2770), пройди связанный поиск противоядия208 и затем вернись к этому шагу.','']
        for r in q['needs']:
            if r['kind']!=1:continue
            origins=[(int(k),v) for k,v in mobs.items() if r['id'] in v.get('drops',[])][:3]
            if origins:
                md += ['Источники '+item(r['id'])+': '+('; '.join(mob(k)+' — '+point(v['locations'][0]['map'],v['locations'][0]['rectangle_cm'][0]) if v.get('locations') else mob(k) for k,v in origins))+'. Это области спавна, а не текущая позиция монстра.','']
    md += ['После Desert Visit цепь продолжается в Шайтане. Ниже есть справочник426определений истории из MissionScript02.lua, включая записи сдачи и ответвления. Это не426независимых поручений и не утверждение, что все ветки уже автоматизированы ботами: текущий контроллер ведёт19начальных журналов и промежуточное отравление.','',
        '## Навыки всех классов и восьми билдов','',
        'Первая профессия: мечник→воитель/чемпион; лучник→стрелок; знахарка→целитель/колдунья; исследователь→покоритель морей. Первый класс получает доступную часть соответствующего плана, вторая профессия открывает продолжение. Новичку боевые книги не применяются до получения класса. Существующие статы и изученные навыки не сбрасываются.','',
        'Число после названия — целевой ранг навыка, а не уровень персонажа. Иди по списку; недостающие предпосылки из таблицы внизу учи раньше. Если нужный ранг уже изучен, шаг пропускается. Класс, реальные очки и книги обязательны. Это приоритеты PvE под ТЗ владельца; универсального лучшего PvP-билда здесь не обещается.','']
    for key,p in plans['profiles'].items():
        md += [f"### {p['title']}",'',p['rationale'],'']
        for i,(skill,rank) in enumerate(p['goals'],1):
            identity,record=byskill[skill];md.append(f"{i}. {item(identity)} / {record['name'].strip()} — {rank} (навык {skill}, книга {identity}).")
        md += ['']
    md += ['### Справочник книг и требований','',
        'В таблице — книги четырёх первых и шести основных вторых профессий. Rebirth-книги и экспертные особые навыки не включены в стартовые планы. Уровни и предпосылки взяты из этой сборки. НПС — статически привязанные продавцы; меню и доступность проверяются в игре, отдельная условная ветка может быть закрыта.','',
        '| Навык / книга | Минимальный уровень | Максимум по классам | Перед изучением | Где искать книгу |', '|---|---|---|---|---|']
    known={1,2,4,5,8,9,12,13,14,16};class_names={1:'мечник',2:'лучник',4:'исследователь',5:'знахарка',8:'чемпион',9:'воитель',12:'стрелок',13:'целитель',14:'колдунья',16:'покоритель морей'}
    relevant=[]
    for identity,r in sorted(books.items()):
        if identity<3160 or not known.intersection(map(int,r['jobs'])):continue
        relevant.append(identity)
        suppliers=[n for n in npcs if identity in n['offers'] and n['verified_shop_binding']]
        suppliers.sort(key=lambda n:(n['map'] not in ('garner','magicsea','darkblue'),n['map'],n['key']))
        where='; '.join(n['name']+' — '+point(n['map'],n['position']) for n in suppliers[:3]) or 'подтверждённый статический продавец не найден; проверь меню наставника'
        prerequisites=', '.join((byskill[s][1]['name'].strip() if s in byskill else f'ID{s}')+f' {lv}' for s,lv in r['prerequisites']) or 'нет'
        jobs=', '.join(class_names[int(j)]+':'+str(cap) for j,cap in r['jobs'].items() if int(j) in known)
        md.append(f"| {item(identity)} / {r['name'].strip()} (skill{r['skill']}, book{identity}) | {r['level']} | {jobs} | {prerequisites} | {where} |")
    md += ['', 'Боевые маги используют доступные подтверждённые целевые заклинания с настоящим SP, зарядом коралла и серверным откатом. Изучение навыка в плане не означает, что уже автоматизировано применение каждого баффа, массового заклинания или навыка моря. Новые автоматические пакеты применения в этой версии не добавляются.','',
        '## Расширенный справочник истории','',
        'Каждая строка — отдельное серверное определение: начало, сдача или специальная ветка. Предыдущие записи — требования HasRecord. Их номера не всегда равны ID задания. Условия с именами функций требуют дополнительной проверки; их выполнение здесь не выдумывается. Неизвестное место не заменяется случайной точкой.','',
        '| ID определения / журнал | Название / роль | НПС | Предыдущие записи / уровень | Требования и ограничения |','|---|---|---|---|---|']
    for r in reference['definitions']:
        title=r['title'].replace('|','/')
        where='; '.join(n['name']+' — '+point(n['map'],n['position']) for n in r['static_npcs'][:4]) or 'нет подтверждённой статической привязки'
        previous=', '.join(map(str,r['needs_previous_records'])) or '—'
        level=', '.join('ур.'+x['operator']+str(x['value']) for x in r['level_conditions'])
        role='сдача' if r['completion_entry'] else 'взятие' if r['starts_journals'] else 'особая запись'
        demands=needs(r['needs']) if r['needs'] else 'предметы сдачи: '+', '.join(f"{item(x['id'])} ID{x['id']} ×{x['count']}" for x in r['turnin_items']) if r['turnin_items'] else 'разговор / родное описание'
        if r['custom_condition_names']:demands+='; специальные условия: '+', '.join(r['custom_condition_names'])
        md.append(f"| {r['source_id']} / {r['journal']} | {title} — {role} | {where} | {previous}; {level} | {demands} |")
    md += ['', '## Источники и границы проверки','',
        'Этот файл — оригинальная компиляция фактов присланного сервера и ТЗ. Внешние полные гайды по каждому классу и всей истории не проверены из-за ограничений сети. Прочитанные публичные материалы ниже служат контекстом и не выдаются за готовые билды. Их отличающиеся настройки не перенесены на сервер. Исходные серверные Lua/таблицы и данные персонажей в файл не включены.','',
        '- MissionScript02.lua: SHA256 '+reference['source_sha256']+'.',
        '- skillinfo.txt, ItemInfo и ItemEffect: производная проверенная таблица life-items.json.',
        '- Реальные НПС и спавны: world-npcs.json / world-mobs.json.',
        '- Восемь билдов: ТЗ владельца и runtime-файл assets/skill-guides.json.','']
    for s in sources['sources']:
        if s.get('url'):md.append('- '+s['title']+': '+s['url']+' — '+s['role']+'.')
    md += ['', 'Для400ботов в Alpha51 нужен сохранённый полный data с300персонажами. Start-World.cmd продолжает одно расширение до400. Повторный запуск не создаёт ещё100. Цель500остаётся отдельным этапом;400соединений на Windows здесь не проверялись.','']
    markdown='\n'.join(md)
    # Small renderer: our own headings/lists/tables only; every source value escaped.
    parts=[];in_table=False;in_list=False
    for line in md:
        if not line.startswith('|') and in_table:parts.append('</tbody></table></div>');in_table=False
        if not re.match(r'^\d+\. ',line) and in_list:parts.append('</ol>');in_list=False
        if line.startswith('|'):
            if line.startswith('|---'):continue
            cells=[x.strip() for x in line.strip('|').split('|')]
            if not in_table:parts.append('<div class="table"><table><thead><tr>'+''.join('<th>'+html.escape(c)+'</th>' for c in cells)+'</tr></thead><tbody>');in_table=True
            else:parts.append('<tr data-search>'+''.join('<td>'+html.escape(c)+'</td>' for c in cells)+'</tr>')
        elif line.startswith('### '):parts.append('<h3>'+html.escape(line[4:])+'</h3>')
        elif line.startswith('## '):parts.append('<h2>'+html.escape(line[3:])+'</h2>')
        elif line.startswith('# '):parts.append('<h1>'+html.escape(line[2:])+'</h1>')
        elif re.match(r'^\d+\. ',line):
            if not in_list:parts.append('<ol>');in_list=True
            parts.append('<li>'+html.escape(re.sub(r'^\d+\. ','',line))+'</li>')
        elif line:parts.append('<p>'+html.escape(line)+'</p>')
    body='\n'.join(parts)
    document='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Пиратия — история и навыки</title><style>
body{font:17px/1.65 system-ui,sans-serif;background:#edf3f6;color:#172f3e;margin:0}main{max-width:1120px;margin:auto;padding:32px}h1{font-size:2.3rem;line-height:1.15}h2{margin-top:60px;border-bottom:2px solid #26758b;padding-bottom:12px}h3{color:#125b72;margin-top:32px}li{margin:8px 0}.tools{position:sticky;top:0;background:#122e3e;padding:12px;display:flex;gap:12px;z-index:2;color:white;align-items:center}.tools input{flex:1;min-width:90px;padding:12px;border:0;border-radius:8px;font:inherit}.tools button{padding:12px;border:0;border-radius:8px;background:#d5b673;color:#142e3d;cursor:pointer}.table{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:12px;border:1px solid #c5d5de;text-align:left;vertical-align:top;min-width:130px}th{background:#dce9ef}tr:nth-child(even){background:#e5eef2}p{overflow-wrap:anywhere}@media(max-width:650px){main{padding:18px}h1{font-size:1.8rem}}@page{size:A4;margin:12mm}@media print{td,th{min-width:0;padding:5px;overflow-wrap:anywhere}table{table-layout:fixed}.tools{display:none}body{background:white;font-size:11pt}main{max-width:none;padding:0}table{font-size:8pt}h2,h3{break-after:avoid}}
</style><div class="tools"><input id="search" aria-label="Поиск в таблицах" placeholder="Поиск по таблицам: навык, книга, NPC, квест…"><button onclick="window.print()">Сохранить в PDF</button><span id="count"></span></div><main>'''+body+'''</main><script>const rows=[...document.querySelectorAll('tr[data-search]')];const normalize=s=>s.toLowerCase().replaceAll('ё','е');document.querySelector('#search').addEventListener('input',e=>{const q=normalize(e.target.value.trim());let n=0;for(const r of rows){r.hidden=!normalize(r.textContent).includes(q);if(!r.hidden)n++}document.querySelector('#count').textContent=q?n+' строк':''})</script></html>'''
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'Piratia-History-and-Skills.md').write_text(markdown,encoding='utf8');(OUT/'Piratia-History-and-Skills.html').write_text(document,encoding='utf8')
    if make_pdf:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as browser_api:
            browser=browser_api.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
            page=browser.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.set_content(document,wait_until='load')
            expected=len(relevant)+len(reference['definitions'])
            assert page.locator('tr[data-search]').count()==expected
            page.locator('#search').fill('Conch')
            shown=page.locator('tr[data-search]:visible').count();assert 0<shown<expected
            page.locator('#search').fill('');assert page.locator('tr[data-search]:visible').count()==expected
            assert not errors,errors
            page.pdf(path=str(OUT/'Piratia-History-and-Skills.pdf'),format='A4',print_background=False,display_header_footer=False,prefer_css_page_size=True)
            page.screenshot(path='/tmp/piratia51-guide-preview.png',full_page=False)
            browser.close()
    manifest={'version':51,'initial_walkthrough_steps':len(story['quests']),'history_definition_rows':len(reference['definitions']),'bound_history_rows':sum(bool(r['static_npcs']) for r in reference['definitions']),'build_guides':len(plans['profiles']),'skill_book_rows':len(relevant),'external_complete_guides_verified':False,'basis':'owner server facts and owner eight builds; original compiled guide','source_evidence_sha256':hashlib.sha256((ROOT/'knowledge/guide-sources.json').read_bytes()).hexdigest()}
    (OUT/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
    manifest['files_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir()) if p.suffix in ('.html','.md','.pdf') or p.name=='sources.json'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(OUT/'Piratia-History-and-Skills.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(OUT.iterdir()):
            if p.suffix=='.zip':continue
            info=zipfile.ZipInfo('Piratia-History-and-Skills/'+p.name,date_time=(2026,11,15,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes())
    print(json.dumps(manifest,ensure_ascii=False));print(OUT/'Piratia-History-and-Skills.zip')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--pdf',action='store_true',help='build-only Chromium/Playwright export')
    build(parser.parse_args().pdf)
