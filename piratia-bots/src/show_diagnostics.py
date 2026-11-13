"""Display selected bot quest/travel diagnostics; never inspect the private data folder."""
import json
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
    lines.append(f"  Бой: цель={fight.get('target_id')}; HP={fight.get('target_hp')}; совместная={fight.get('shared_target')}; без урона={fight.get('seconds_since_target_damage')}; смены без урона={fight.get('no_damage_retargets',0)}")
    lines.append(f"  Версия: {report.get('version','не указана')}")
    lines.extend([f"  Продажа: {vendor.get('state','нет данных')}; запросы={vendor.get('sale_requests',0)}; подтверждено={vendor.get('confirmed_sales',0)}; тайм-ауты={vendor.get('confirmation_timeouts',0)}",f"  Предметы: {json.dumps(vendor.get('bag_items',[]),ensure_ascii=False)}"])
    return '\n'.join(lines)


def collect(root):
    lines=['Диагностика квестов и переходов. Папка программы: '+str(root)]
    paths=sorted(root.glob('bot-report-*.json'))
    if not paths:
        lines.append('Отчёты пока не найдены. Запусти ботов из этой же папки и подожди 30 секунд. Не удаляй data.')
    for path in paths:
        try:lines.append(render_report(json.loads(path.read_text(encoding='utf-8-sig'))))
        except (OSError,ValueError,TypeError,AttributeError):lines.append(path.name+': отчёт пока недоступен; повтори позже.')
    return '\n\n'.join(lines)


def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    root=Path(__file__).resolve().parents[1]
    text=collect(root)
    print(text)
    path=root/'bot-diagnostics.log'
    path.write_text(text,encoding='utf-8')
    print('\nКопия диагностики: '+str(path))


if __name__=='__main__':main()
