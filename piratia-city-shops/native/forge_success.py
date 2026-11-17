"""Change only audited success rolls inside four existing native forge functions."""
from pathlib import Path
import hashlib
import re

FUNCTION=re.compile(rb'(?m)^function[ \t]+([A-Za-z_][A-Za-z0-9_]*)[ \t]*\(')
RULES={
 'begin_forge_item':(rb'local[ \t]+CheckFaild[ \t]*=[ \t]*Percentage_Random[ \t]*\([ \t]*Check_A[ \t]*\)',b'local CheckFaild = 1',1),
 'Check_CG_HechengBS':(rb'(?m)^([ \t]*)b[ \t]*=[ \t]*Percentage_Random[ \t]*\([ \t]*a[ \t]*\)',rb'\1b = 1',2),
 'Check_CG_damo':(rb'local[ \t]+b[ \t]*=[ \t]*Percentage_Random[ \t]*\([ \t]*a[ \t]*\)',b'local b = 1',1),
 'Check_CG_beuplv':(rb'local[ \t]+ran[ \t]*=[ \t]*math\.random[ \t]*\([ \t]*1[ \t]*,[ \t]*100[ \t]*\)',b'local ran = 1',1),
}

def patch(raw):
 matches=list(FUNCTION.finditer(raw));spans={};parts={};report={}
 for index,m in enumerate(matches):
  name=m[1].decode()
  if name in RULES:
   if name in spans:raise ValueError('Повторяется функция ковки: '+name)
   spans[name]=(m.start(),matches[index+1].start() if index+1<len(matches) else len(raw))
 for name,(pattern,replacement,count) in RULES.items():
  if name not in spans:raise ValueError('Отсутствует функция ковки: '+name)
  start,end=spans[name];body=raw[start:end];tag=b' -- OWNER58_SUCCESS_'+name.encode()
  if tag in body:
   assignment=(rb'local CheckFaild = 1' if name=='begin_forge_item' else rb'local ran = 1' if name=='Check_CG_beuplv' else rb'local b = 1' if name=='Check_CG_damo' else rb'b = 1')
   if body.count(tag)!=count or re.search(pattern,body) or len(re.findall(assignment+re.escape(tag),body))!=count:raise ValueError('Изменён патч шанса ковки: '+name)
   out=body
  else:
   if len(re.findall(pattern,body))!=count:raise ValueError('Неизвестная проверка шанса ковки: '+name)
   out,n=re.subn(pattern,replacement+tag,body)
   if n!=count:raise ValueError('Неполное изменение ковки: '+name)
  parts[(start,end)]=out
  report[name]={'success':1.0,'before_sha256':hashlib.sha256(body).hexdigest(),'after_sha256':hashlib.sha256(out).hexdigest()}
 result=raw
 for (start,end),out in sorted(parts.items(),reverse=True):result=result[:start]+out+result[end:]
 return result,report

def plan(resource):
 path=Path(resource)/'script/calculate/forge.lua'
 if not path.is_file():raise ValueError('Нужен исходный серверный script/calculate/forge.lua для100%ковки.')
 before=path.read_bytes();after,functions=patch(before)
 return ({path:after} if after!=before else {}),{'installed_sha256':hashlib.sha256(after).hexdigest(),'functions':functions,'materials_and_gold_preserved':True,'source_file':path.relative_to(resource).as_posix()}
