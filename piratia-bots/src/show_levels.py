"""Read-only, credential-free view of the running bot population."""
import json,sys,time
from pathlib import Path

def render(data):
 rows=data.get('bots',{})
 lines=[f"В сети: {data.get('connected',0)} / {data.get('requested',0)}",'По картам: '+', '.join(f'{name}: {count}' for name,count in data.get('cities',{}).items()),'Номер | Уровень | Опыт | Удары-запросы | Карта / координаты | Занятие']
 if type(data.get('updated_unix')) in (int,float):lines.insert(1,'Возраст снимка: '+str(max(0,int(time.time()-data['updated_unix'])))+' сек. Координаты — по последнему отчёту, не непрерывный трек.')
 for key,row in sorted(rows.items(),key=lambda item:int(item[0])):
  level=row.get('level');level=level if isinstance(level,int) else '?'
  point=row.get('position');where=str(row.get('map','?'))
  if isinstance(point,(list,tuple)) and len(point)==2 and all(type(x) in (int,float) for x in point):where+=' '+str(int(point[0]//100))+','+str(int(point[1]//100))
  if row.get('connected') is False:where+=' (не в сети)'
  lines.append(f"{int(key):3} | {level:>7} | {row.get('experience','?')} | {row.get('attacks',0):>6} | {where} | {row.get('state','нет данных')}")
 return '\n'.join(lines)

def main():
 if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
 path=Path(__file__).resolve().parents[1]/'population-status.json'
 try:print(render(json.loads(path.read_text(encoding='utf-8-sig'))))
 except (OSError,ValueError,TypeError):print('Сначала запусти ботов. Статус появится примерно через 30 секунд.')
if __name__=='__main__':main()
