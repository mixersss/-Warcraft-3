"""Opt-in human contacts: native friend requests and bounded private replies."""
import re,struct
from collections import deque
from classic_wire import Reader,ProtocolError,string

def private_request(name,text):
 if not name or len(name.encode('cp1251'))>32 or any(ord(c)<32 for c in name+text):raise ValueError('Invalid private message')
 return string(name)+string(text.encode('cp1251',errors='replace')[:120])

class Contacts:
 def __init__(self,world,send,social,personality,party):
  self.world,self.send,self.social,self.personality,self.party=world,send,social,personality,party
  self.queue=deque(maxlen=8);self.next_reply={};self.friend_cooldown={};self.next_send=0
  self.private_replies=self.friend_requests=self.friend_accepts=self.friend_refreshes=self.unsupported=0
 def invite_friend(self,name,now):
  if not name or name.lower().startswith('bot') or len(name.encode('cp1251',errors='replace'))>32:return 'Не могу отправить это приглашение.'
  if self.friend_cooldown.get(name,0)>now:return 'Приглашение уже отправлено, проверь список друзей.'
  self.send(6011,string(name));self.friend_requests+=1;self.friend_cooldown[name]=now+300
  if len(self.friend_cooldown)>128:self.friend_cooldown.pop(next(iter(self.friend_cooldown)))
  return 'Отправил приглашение в друзья. Подтверди его в игре.'
 def local_friend(self,source,now):
  person=self.world.entities.get(source)
  return self.invite_friend(person.name,now) if person else 'Подойди ближе или напиши мне в ЛС.'
 def hear(self,command,payload,now):
  try:
   r=Reader(payload)
   if command==5011:
    name,identity=r.string(),r.long();r.short();r.end()
    if name and len(name.encode('cp1251',errors='replace'))<=32 and not any(ord(c)<32 for c in name) and not name.lower().startswith('bot'):
     self.send(6012,struct.pack('>I',identity));self.friend_accepts+=1
    return
   if command==5012:self.friend_refreshes+=1;return
   if command!=5403:return
   sender,receiver,text=r.string(),r.string(),r.string()
   if len(r.data)-r.position==4:r.long()
   r.end()
   if receiver.casefold()!=self.social.name.casefold() or not sender or sender.lower().startswith('bot') or len(text)>240 or any(ord(c)<32 for c in sender+text):return
   if self.next_reply.get(sender,0)>now:return
   self.next_reply[sender]=now+20
   if len(self.next_reply)>128:self.next_reply.pop(next(iter(self.next_reply)))
   words=re.findall(r'[\w]+',text.casefold());reply=self.social.reply(words)
   if any(w in words for w in ('друзья','друзься','друг','друзей','дружить')):answer=self.invite_friend(sender,now)
   elif reply and reply[0]=='party':answer=self.party.request_name(sender,now)
   elif reply:answer=reply[1]
   else:answer='Я отвечаю простыми правилами. Можешь спросить про уровень, занятие, пати или друзей.'
   self.queue.append((sender,answer,now+self.personality.rng.uniform(2,5),now+30))
  except (ProtocolError,ValueError,UnicodeError):self.unsupported+=1
 def tick(self,now):
  while self.queue and self.queue[0][3]<now:self.queue.popleft()
  if self.queue and now>=self.queue[0][2] and now>=self.next_send and self.social.budget.claim(now):
   name,text,_,_=self.queue.popleft();self.send(6403,private_request(name,text));self.private_replies+=1;self.next_send=now+10
 def summary(self):return {'private_replies':self.private_replies,'friend_invites_sent':self.friend_requests,'friend_accept_requests':self.friend_accepts,'friend_refresh_notices':self.friend_refreshes,'unsupported_packets':self.unsupported}
