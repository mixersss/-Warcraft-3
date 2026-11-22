"""Accept only our numeric native XP receipts; no arbitrary chat transcripts."""
import math
import re
from classic_wire import Reader,ProtocolError
LINE=re.compile(r'^OWNER60_XP rate=([-\d.eE+]+) scale=([-\d.eE+]+) base=([-\d.eE+]+) before=([-\d.eE+]+) after=([-\d.eE+]+) monster=(\d+) ok=([01])(?: effective=([-\d.eE+]+))?$')
class XPDiagnostics:
 def __init__(self):self.rows=[];self.receipts=0
 def observe(self,command,payload):
  if command!=517:return False
  try:
   r=Reader(payload);line=r.string();r.end()
  except ProtocolError:return False
  m=LINE.fullmatch(line)
  if not m:return False
  try:values=list(map(float,m.groups()[:5]))
  except ValueError:return False
  if not all(math.isfinite(v) and abs(v)<=1e15 for v in values):return False
  row=dict(zip(('rate','scale','base','before','after'),values));row.update(monster=int(m[6]),native_call_ok=m[7]=='1')
  try:row['effective_scale']=float(m[8]) if m[8] else row['scale']
  except ValueError:return False
  if not math.isfinite(row['effective_scale']) or abs(row['effective_scale'])>1e15:return False
  row['native_xp_delta']=row['after']-row['before'];self.rows.append(row);self.rows=self.rows[-12:];self.receipts+=1
  return True
 def summary(self):
  return {'receipts':self.receipts,'recent':self.rows,'fatigue_zero_observed':any(r['scale']==0 for r in self.rows),'native_error_observed':any(not r['native_call_ok'] for r in self.rows),'no_direct_experience_grants':True,'configured_exp_rate_preserved':True}
