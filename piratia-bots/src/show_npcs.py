"""Read-only public NPC source catalog; no account data needed."""
import argparse,json,os
from pathlib import Path
from npc_knowledge import NpcKnowledge,CITIES

def render(knowledge,query):
    rows=knowledge.find(query)
    lines=[f'В справочнике: {len(knowledge.rows)} размещений НПС; найдено: {len(rows)}.',
           'Координаты из серверных таблиц; доступность услуг и товаров подтверждает меню сервера.']
    for n in rows:
        x,y=(int(v//100) for v in n['position'])
        lines.append(f"{n['key']} | {n['name']} | {CITIES.get(n['map'],n['map'])} {x},{y} | услуги: {', '.join(n['services']) or 'диалог'}")
        if n['offers']:lines.append('  Товары (базовая цена): '+', '.join(f"{g['id']} {g['name']} [{g['base_price']}G]" for g in knowledge.goods(n)))
        if n['mission_source_ids']:lines.append('  ID привязанных миссий: '+', '.join(map(str,n['mission_source_ids'])))
        if n['conditions_not_evaluated']:lines.append('  Доступность части функций зависит от условий скрипта.')
    return '\n'.join(lines)

def main():
    import sys
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    p=argparse.ArgumentParser();p.add_argument('--query',default='');p.add_argument('--query-env');a=p.parse_args()
    assets=Path(__file__).resolve().parents[1]/'assets'
    types={int(k):v for k,v in json.loads((assets/'items.json').read_text())['types'].items()}
    items=json.loads((assets/'life-items.json').read_text())
    knowledge=NpcKnowledge(assets/'world-npcs.json',types,{int(k):v for k,v in items['names'].items()},{int(k):v for k,v in items['prices'].items()})
    print(render(knowledge,os.environ.get(a.query_env,'') if a.query_env else a.query))

if __name__=='__main__':main()
