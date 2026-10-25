"""Instrument dangerous source-NPC operations without changing spell timing or shared callbacks."""
import re

def protect(code):
 current='unknown'
 lines=[]
 for line in code.splitlines():
  match=re.match(r'function (\w+) takes',line)
  if match:current=match[1]
  if current in ('OrigNPC_A2X','OrigNPC_A3X','OrigNPC_NBX','OrigNPC_NCX','OrigNPC_NHX','OrigNPC_NJX','OrigNPC_NPX','OrigNPC_NQX') and line.startswith('return'):
   slot=1 if current in ('OrigNPC_A2X','OrigNPC_A3X') else 0
   line=f'return FoundationAlive(OrigNPC_OR[{slot}]) and FoundationAlive(OrigNPC_RR[{slot}]) and ('+line[6:]+')'
  line=line.replace('call SetUnitVertexColorBJ(', 'call InvasionSourceColor(')
  for old,new in [('RemoveUnit','InvasionSourceRemove'),('ShowUnitHide','InvasionSourceHide'),('PauseUnit','InvasionSourcePause'),('SetWidgetLife','InvasionSourceLife'),('SetUnitLifePercentBJ','InvasionSourceLifePercent')]:
   match=re.fullmatch(r'\s*call '+old+r'\((.*)\)',line)
   if match:
    indent=line[:len(line)-len(line.lstrip())] if old in ('SetWidgetLife','SetUnitLifePercentBJ') else ''
    line=indent+'call '+new+'('+match[1]+',"'+current+'")'
  lines.append(line)
 return '\n'.join(lines)+'\n'
