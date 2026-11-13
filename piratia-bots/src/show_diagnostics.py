"""Display selected bot quest/travel diagnostics; never inspect the private data folder."""
import json
import sys
from pathlib import Path


def render_report(report):
    quest=report.get('adventure',{})
    travel=report.get('travel',{})
    role=report.get('class_path',{})
    lines=[f"Бот {report.get('bot_index','?')}: класс {role.get('label','?')}",
           f"  Квест: {quest.get('state','нет данных')}; NPC={quest.get('destination_npc','?')}; этап={quest.get('dialogue_stage')}",
           f"  Причина: {quest.get('last_problem') or 'не указана'}; журнал={quest.get('journal_received')}; расстояние={quest.get('npc_distance')}",
           f"  Предложения NPC: {json.dumps(quest.get('last_offers',[]),ensure_ascii=False)}",
           f"  Переход: {travel.get('state','нет данных')}; город={travel.get('destination')}; этап={travel.get('dialogue_stage')}; прибытия={travel.get('confirmed_arrivals',0)}",
           f"  Меню телепортера: {json.dumps(travel.get('last_menu',[]),ensure_ascii=False)}"]
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
