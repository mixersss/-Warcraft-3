"""Occasional native world/trade requests with earned cash and fleet-wide spacing."""
import random,threading
from social import say_request,PHRASES
from classic_wire import Reader,ProtocolError
class PublicBudget:
 def __init__(self):self.lock=threading.Lock();self.next={'world':0,'trade':0};self.scale=1
 def claim(self,channel,now):
  with self.lock:
   if now<self.next[channel]:return False
   self.next[channel]=now+(120 if channel=='world' else 180)*self.scale;return True
class PublicChat:
 def __init__(self,world,send,budget,seed):
  self.world,self.send,self.budget=world,send,budget;self.rng=random.Random(seed+':public')
  self.next_world=self.next_trade=None;self.world_requests=self.trade_requests=0;self.confirmed_world=self.confirmed_trade=0;self.pending={}
  self.context_provider=None
  self.recruitment_provider=None;self.expired_echoes=0
 def tick(self,now,safe,market=None):
  if self.next_world is None:self.next_world=now+self.rng.uniform(180,420);self.next_trade=now+self.rng.uniform(120,360)
  for command,expected in list(self.pending.items()):
   if now>expected[1]:self.pending.pop(command,None);self.expired_echoes+=1
  cash=self.world.own.values.get(8,0)
  if not safe or cash<2000:return
  if cash>=20000 and market and market.state=='selling' and market.stock and now>=self.next_trade:
   text=self.context_provider('trade') if self.context_provider else self.rng.choice(PHRASES['trade_channel'])
   if text and self.budget.claim('trade',now):
    self.send(6401,say_request(text));self.pending[5401]=(text,now+30);self.trade_requests+=1;self.next_trade=now+1800;return
  if now>=self.next_world:
   recruitment=self.recruitment_provider(now) if self.recruitment_provider else None
   text=recruitment or (self.context_provider('world') if self.context_provider else self.rng.choice(PHRASES['world']))
   if text and cash>=(2000 if recruitment else 20000) and self.budget.claim('world',now):
    self.send(6402,say_request(text));self.pending[5402]=(text,now+30);self.world_requests+=1;self.next_world=now+1800
 def observe(self,command,payload,now):
  expected=self.pending.get(command)
  if not expected or now>expected[1]:return
  r=Reader(payload);source,text=r.string(),r.string()
  if source==self.world.own.name and text==expected[0]:
   if command==5401:self.confirmed_trade+=1
   elif command==5402:self.confirmed_world+=1
   self.pending.pop(command,None)
 def reply(self,channel,text,now):
  if channel not in ('world','trade'):return False
  if self.world.own.values.get(8,0)<(2000 if channel=='world' else 20000):return False
  if not self.budget.claim(channel,now):return False
  command=6402 if channel=='world' else 6401;echo=5402 if channel=='world' else 5401
  self.send(command,say_request(text));self.pending[echo]=(text,now+30)
  if channel=='world':self.world_requests+=1;self.next_world=max(self.next_world or 0,now+1800)
  else:self.trade_requests+=1;self.next_trade=max(self.next_trade or 0,now+1800)
  return True
 def summary(self):return {'world_requests':self.world_requests,'trade_requests':self.trade_requests,'confirmed_world_echoes':self.confirmed_world,'confirmed_trade_echoes':self.confirmed_trade,'unconfirmed_echo_timeouts':self.expired_echoes,'recruitment_cash_gate':2000,'ordinary_public_chat_cash_gate':20000,'fee_determined_by_server':True}

