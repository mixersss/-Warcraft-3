"""Explain source-backed mechanics/items; never read credentials or execute game actions."""
import argparse,json,os,sys
from pathlib import Path
from mechanics import MechanicsKnowledge,load_knowledge
from life import LifeItems
from mob_knowledge import MobKnowledge

def render(knowledge,query):
    if query.strip().isdigit():
        data=knowledge.sources_for_item(int(query));item=data['item']
        if not item:return 'Неизвестный ID предмета.'
        lines=[f"ID{query}: {item['name']}",f"Тип={item['kind']}; стопка={item['stack']}; базовая цена таблицы={item['price']}"]
        lines.extend(f"НПС: {n['name']} — {n['map']} {n['position'][0]//100},{n['position'][1]//100}; требуется настоящее меню" for n in data['npc_sources'])
        for m in data['monster_sources']:
            maps=sorted({p['map'] for p in m['locations']})
            lines.append(f"Возможный дроп: {m['name']}, ур.{m['level']}, карты={','.join(maps) or 'места не найдены'}; вероятность не подтверждена")
        lines.append('Кандидаты наград скриптов: '+str(len(data['script_reward_candidates']))+'; условия требуют отдельной проверки.')
        return '\n'.join(lines)
    cards=knowledge.search(query) if query.strip() else list(knowledge.cards.values())
    if not cards:return 'Механика не найдена. Попробуй: форж, корабли, феи, кулинария, ДВ, топи или ID предмета.'
    lines=[]
    for card in cards:
        info=knowledge.explain(card['id']);lines.extend([card['title']+' ['+card['id']+']',
            ('Внимание: описание относится к прежней сверке; текущие правила требуют повторной проверки. ' if card['review_status']=='requires_reaudit' else '')+card['explanation'],
            'Проверка правил: '+card['review_status']+'; автоматическая операция: не включена этой базой знаний.'])
        lines.extend(f"НПС: {n['name']} — {n['map']} {n['position_cm'][0]//100},{n['position_cm'][1]//100}" for n in info['candidate_npcs'])
        lines.append('Опорных функций: '+str(len(info['source_evidence'])))
        lines.append('')
    return '\n'.join(lines)

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('query',nargs='?',default='');p.add_argument('--query-env')
    a=p.parse_args();assets=Path(__file__).resolve().parents[1]/'assets';life=LifeItems(assets)
    knowledge=load_knowledge(assets,life.npcs,MobKnowledge(assets/'world-mobs.json'))
    print(render(knowledge,os.environ.get(a.query_env,'') if a.query_env else a.query))
    print('\nПокрытие: '+json.dumps(knowledge.summary(),ensure_ascii=False))

if __name__=='__main__':main()
