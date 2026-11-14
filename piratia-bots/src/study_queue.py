"""Fair finite quest-study turns; queued characters continue their other work."""
import threading
from collections import OrderedDict

class StudyQueue:
    def __init__(self,limit=20,seconds=600,rest_seconds=900):
        self.limit,self.seconds,self.rest_seconds=limit,seconds,rest_seconds
        self.lock=threading.Lock();self.waiting=OrderedDict();self.active={};self.rest={}

    def turn(self,name,now):
        with self.lock:
            for owner,until in list(self.active.items()):
                if until<=now:
                    self.active.pop(owner);self.rest[owner]=now+self.rest_seconds
            self.waiting=OrderedDict((n,t) for n,t in self.waiting.items() if now-t<120)
            if name in self.active:return True
            if now<self.rest.get(name,0):return False
            self.waiting[name]=now
            while len(self.active)<self.limit and self.waiting:
                owner,_=self.waiting.popitem(last=False)
                self.active[owner]=now+self.seconds
            return name in self.active

    def release(self,name,now):
        with self.lock:
            self.active.pop(name,None);self.waiting.pop(name,None);self.rest[name]=now+self.rest_seconds
