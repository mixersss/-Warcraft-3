"""Shared expiring leisure quota; slots are earned by completed tasks, not filled forcibly."""
import threading
class ActivitySlots:
 def __init__(self,population,live_count=None):self.limit=max(0,int(population)//10);self.live_count=live_count;self.lock=threading.Lock();self.rows={}
 def acquire(self,owner,now):
  with self.lock:
   self.rows={k:v for k,v in self.rows.items() if v>now}
   limit=min(self.limit,self.live_count(now)//10) if self.live_count else self.limit
   if owner in self.rows and list(self.rows).index(owner)>=limit:self.rows.pop(owner,None);return False
   if owner not in self.rows and len(self.rows)>=limit:return False
   self.rows[owner]=now+30;return True
 def release(self,owner):
  with self.lock:self.rows.pop(owner,None)
