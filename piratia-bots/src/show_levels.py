"""Read-only, credential-free view of the running bot population."""
import json,sys
from pathlib import Path

def render(data):
 rows=data.get('bots',{})
 lines=[f"В сети: {data.get('connected',0)} / {data.get('requested',0)}",'Номер | Уровень | Опыт | Удары-запросы | Занятие']
 for key,row in sorted(rows.items(),key=lambda item:int(item[0])):
  level=row.get('level');level=level if isinstance(level,int) else '?'
  lines.append(f"{int(key):3} | {level:>7} | {row.get('experience','?')} | {row.get('attacks',0):>6} | {row.get('state','нет данных')}")
 return '\n'.join(lines)

def main():
 if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
 path=Path(__file__).resolve().parents[1]/'population-status.json'
 try:print(render(json.loads(path.read_text(encoding='utf-8-sig'))))
 except (OSError,ValueError,TypeError):print('Сначала запусти ботов. Статус появится примерно через 30 секунд.')
if __name__=='__main__':main()
