"""Instrument dangerous source-NPC operations without changing spell timing or shared callbacks."""
import re

def protect(code):
 current='unknown'
 lines=[]
 for line in code.splitlines():
  match=re.match(r'function (\w+) takes',line)
  if match:current=match[1]
  line=line.replace('call SetUnitVertexColorBJ(', 'call InvasionSourceColor(')
  for old,new in [('RemoveUnit','InvasionSourceRemove'),('ShowUnitHide','InvasionSourceHide'),('PauseUnit','InvasionSourcePause')]:
   match=re.fullmatch(r'\s*call '+old+r'\((.*)\)',line)
   if match:line='call '+new+'('+match[1]+',"'+current+'")'
  lines.append(line)
 return '\n'.join(lines)+'\n'
