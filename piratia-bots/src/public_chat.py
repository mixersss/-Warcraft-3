"""Occasional native world/trade requests with earned cash and fleet-wide spacing."""
import random,threading
from social import say_request,PHRASES
from classic_wire import Reader,ProtocolError
class PublicBudget:
 def __init__(self):self.lock=threading.Lock();self.next={'world':0,'trade':0}
 def claim(self,channel,now):
  with self.lock:
   if now<self.next[channel]:return False
   self.next[channel]=now+(120 if channel=='world' else 180);return True
class PublicChat:
 def __init__(self,world,send,budget,seed):
  self.world,self.send,self.budget=world,send,budget;self.rng=random.Random(seed+':public')
  self.next_world=self.next_trade=None;self.world_requests=self.trade_requests=0;self.confirmed_world=self.confirmed_trade=0;self.pending={}
 def tick(self,now,safe,market=None):
  if self.next_world is None:self.next_world=now+self.rng.uniform(180,420);self.next_trade=now+self.rng.uniform(120,360)
  if not safe or self.world.own.values.get(8,0)<20000:return
  if market and market.state=='selling' and market.stock and now>=self.next_trade and self.budget.claim('trade',now):
   text=self.rng.choice(PHRASES['trade_channel']);self.send(6401,say_request(text));self.pending[5401]=(text,now+30);self.trade_requests+=1;self.next_trade=now+1800;return
  if now>=self.next_world and self.budget.claim('world',now):
   text=self.rng.choice(PHRASES['world']);self.send(6402,say_request(text));self.pending[5402]=(text,now+30);self.world_requests+=1;self.next_world=now+1800
 def observe(self,command,payload,now):
  expected=self.pending.get(command)
  if not expected or now>expected[1]:return
  r=Reader(payload);source,text=r.string(),r.string()
  if source==self.world.own.name and text==expected[0]:
   if command==5401:self.confirmed_trade+=1
   elif command==5402:self.confirmed_world+=1
   self.pending.pop(command,None)
 def summary(self):return {'world_requests':self.world_requests,'trade_requests':self.trade_requests,'confirmed_world_echoes':self.confirmed_world,'confirmed_trade_echoes':self.confirmed_trade}

