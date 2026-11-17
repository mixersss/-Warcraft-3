"""Classic native config uses seconds; zero would NEVER release protected loot."""
from pathlib import Path
import re

KEY=re.compile(rb'(?mi)^[ \t]*item_prot_time[ \t]*=')
VALUE=re.compile(rb'(?mi)^([ \t]*item_prot_time[ \t]*=[ \t]*)[+-]?[0-9]+([ \t]*(?:(?://|#|;)[^\r\n]*)?)(?=\r?$)')

def plan(game,proposed=None):
 game=Path(game);proposed=proposed or {};changes={}
 files=[game/'GameServer.cfg']+sorted(p for p in game.glob('GameServer*.cfg') if re.fullmatch(r'GameServer[0-9]+\.cfg',p.name))
 if not files[0].is_file():raise ValueError('Не найдена папка с GameServer.cfg для исправления защиты добычи.')
 for path in files:
  raw=proposed.get(path,path.read_bytes())
  if len(KEY.findall(raw))!=len(VALUE.findall(raw)):raise ValueError('Неизвестный формат item_prot_time: '+path.name)
  if len(KEY.findall(raw))>1:raise ValueError('Повторяется item_prot_time: '+path.name)
  if KEY.search(raw):out=VALUE.sub(lambda m:m[1]+b'1'+m[2],raw)
  else:
   nl=b'\r\n' if b'\r\n' in raw else b'\n'
   out=raw+(b'' if raw.endswith(b'\n') else nl)+b'// Owner57: native loot protection in SECONDS; zero never expires.'+nl+b'item_prot_time = 1'+nl
  if out!=raw:changes[path]=out
 return changes,{'seconds':1,'scope':'All ground loot in these GameServer processes','configured_files':[p.name for p in files],'zero_means_permanent':True}
