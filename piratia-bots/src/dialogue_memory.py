"""Finite per-channel/per-person memory; no transcript is saved to disk."""
from collections import OrderedDict,deque

class DialogueManager:
    def __init__(self,settings):
        self.contexts=OrderedDict();self.turns=settings['memory_turns'];self.capacity=settings['memory_contexts']
        self.ttl=min(1800,max(60,settings.get('memory_ttl_seconds',900)))
    def context(self,channel,map_name,peer,now):
        for key,row in list(self.contexts.items()):
            if now>=row['until']:self.contexts.pop(key,None)
        key=(channel,map_name if channel=='local' else '*',peer.casefold())
        if key not in self.contexts:
            while len(self.contexts)>=self.capacity:self.contexts.popitem(last=False)
            self.contexts[key]={'messages':deque(maxlen=self.turns),'topic':None,'awaiting':None,'last_reply':None,'item':None,'level':None,'promises':[],'until':now+self.ttl,'muted_until':0}
        self.contexts.move_to_end(key);self.contexts[key]['until']=now+self.ttl
        return self.contexts[key]
    def remember(self,row,speaker,text):row['messages'].append((speaker,text[:240]))
    def clear(self):self.contexts.clear()
