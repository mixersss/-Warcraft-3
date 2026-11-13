"""Display selected bot quest/travel diagnostics; never inspect the private data folder."""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path


def render_report(report):
    quest=report.get('adventure',{})
    travel=report.get('travel',{})
    role=report.get('class_path',{})
    vendor=report.get('vendor',{})
    lines=[f"Бот {report.get('bot_index','?')}: класс {role.get('label','?')}",
           f"  Уровень={quest.get('level','?')}; золото={quest.get('gold','?')}; состояние={report.get('hunt',{}).get('state','?')}",
           f"  Сумка: {quest.get('bag_used','?')}/{quest.get('bag_capacity','?')}; свободно={quest.get('free_bag_slots','?')}",
           f"  Миссии: {json.dumps(quest.get('active_missions',{}),ensure_ascii=False)}; принятия={quest.get('accepted_confirmed',0)}; сдачи={quest.get('deliveries_confirmed',0)}",
           f"  Квест: {quest.get('state','нет данных')}; NPC={quest.get('destination_npc','?')}; этап={quest.get('dialogue_stage')}",
           f"  Причина: {quest.get('last_problem') or 'не указана'}; журнал={quest.get('journal_received')}; расстояние={quest.get('npc_distance')}",
           f"  Предложения NPC: {json.dumps(quest.get('last_offers',[]),ensure_ascii=False)}",
           f"  Переход: {travel.get('state','нет данных')}; город={travel.get('destination')}; этап={travel.get('dialogue_stage')}; прибытия={travel.get('confirmed_arrivals',0)}",
           f"  Меню телепортера: {json.dumps(travel.get('last_menu',[]),ensure_ascii=False)}"]
    fight=report.get('hunt',{})
    obstacles=fight.get('movement_obstacles',{})
    lines.append(f"  Препятствия: неожиданных остановок={obstacles.get('unexpected_stops',0)}; последний шаг={json.dumps(obstacles.get('last_step'),ensure_ascii=False)}")
    world=fight.get('world',{})
    lines.append(f"  Персонаж: метка={report.get('character_tag','не указана')}; HP={world.get('hp')}/{world.get('max_hp')}; карта={world.get('map')}; позиция={world.get('position')}; состояние длится={fight.get('state_seconds')} сек.")
    lines.append(f"  Сумка мешает NPC: {fight.get('inventory_blocker') or 'нет'}; подбор={json.dumps(report.get('loot',{}),ensure_ascii=False)}")
    lines.append(f"  Бой: цель={fight.get('target_id')}; HP={fight.get('target_hp')}; совместная={fight.get('shared_target')}; без урона={fight.get('seconds_since_target_damage')}; смены без урона={fight.get('no_damage_retargets',0)}")
    lines.append(f"  Версия: {report.get('version','не указана')}")
    lines.extend([f"  Продажа: {vendor.get('state','нет данных')}; запросы={vendor.get('sale_requests',0)}; подтверждено={vendor.get('confirmed_sales',0)}; тайм-ауты={vendor.get('confirmation_timeouts',0)}",f"  Предметы: {json.dumps(vendor.get('bag_items',[]),ensure_ascii=False)}"])
    return '\n'.join(lines)


def character_tag(name):
    name=name.strip()
    if not re.fullmatch(r'bot[0-9a-f]{8}',name,re.IGNORECASE):raise ValueError('Ожидается ник вида Bot38977e75')
    canonical='Bot'+name[3:].lower()
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:12]


def collect(root,name=None):
    lines=['Диагностика квестов и переходов. Папка программы: '+str(root)]
    paths=sorted(root.glob('bot-report-*.json'))
    if not paths:
        lines.append('Отчёты пока не найдены. Запусти ботов из этой же папки и подожди 30 секунд. Не удаляй data.')
    wanted=character_tag(name) if name is not None else None
    found=0
    for path in paths:
        try:
            report=json.loads(path.read_text(encoding='utf-8-sig'))
            if wanted and report.get('character_tag')!=wanted:continue
            found+=1
            if wanted:lines.append('Отчёт нужного бота: '+path.name)
            lines.append(render_report(report))
        except (OSError,ValueError,TypeError,AttributeError):lines.append(path.name+': отчёт пока недоступен; повтори позже.')
    if wanted and not found:lines.append('Ник не найден среди отчётов. Метки доступны с Alpha34: запусти обновлённых ботов, подожди 30 секунд и повтори поиск. Не удаляй data.')
    return '\n\n'.join(lines)


def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--name')
    group.add_argument('--name-env')
    args=parser.parse_args()
    name=os.environ.get(args.name_env,'') if args.name_env else args.name
    try:text=collect(root,name)
    except ValueError as error:print(str(error));return
    print(text)
    path=root/('selected-bot-diagnostics.log' if name is not None else 'bot-diagnostics.log')
    path.write_text(text,encoding='utf-8')
    print('\nКопия диагностики: '+str(path))


if __name__=='__main__':main()
