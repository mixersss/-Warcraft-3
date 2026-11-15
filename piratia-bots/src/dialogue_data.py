"""Shared, validated UTF-8 dialogue data and bounded factual lookup indexes."""
import json,re,string
from pathlib import Path
from collections import defaultdict
from intent_recognizer import IntentRecognizer,normalize

class DialogueData:
    def __init__(self,assets):
        assets=Path(assets)
        load=lambda name:json.loads((assets/name).read_text(encoding='utf8'))
        self.rows=load('dialogue-intents.json')['intents'];self.profiles=load('dialogue-personalities.json')['profiles']
        self.settings=load('dialogue-settings.json');self.facts=load('dialogue-facts.json')['items']
        if self.settings.get('intensity') not in ('quiet','normal','lively'):raise ValueError('Unknown dialogue intensity')
        if not 10<=self.settings.get('memory_turns',0)<=20:raise ValueError('Invalid memory length')
        if not 1<=self.settings.get('memory_contexts',0)<=64:raise ValueError('Invalid context count')
        if len(self.rows)<100 or len(self.profiles)<12:raise ValueError('Incomplete dialogue catalog')
        self.by_intent={};self.item_by_id={};self.tokens=defaultdict(set);unique=set()
        allowed={'activity','map','position','level','class','build','party_size','quest','fairy','free_slots','stall','personality'}
        for row in self.rows:
            if row['id'] in self.by_intent:raise ValueError('Duplicate intent')
            re.compile(row['pattern']);self.by_intent[row['id']]=row
            for text in row['responses']:
                fields={f for _,f,_,_ in string.Formatter().parse(text) if f}
                if not fields<=allowed:raise ValueError('Unknown fact placeholder')
                if any(ord(c)<32 for c in text):raise ValueError('Unsafe response')
                unique.add(text)
        self.recognizer=IntentRecognizer(self.rows)
        self.aliases={}
        for fact in self.facts:
            identity=fact['id'];text=fact['text']
            if identity in self.item_by_id or len(text.encode('cp1251'))>120:raise ValueError('Invalid fact row')
            self.item_by_id[identity]=fact;unique.add(text)
            for alias in fact['aliases']:
                key=normalize(alias)
                if len(key)>=3:
                    self.aliases[key]=identity
                    for token in key.split():
                        if len(token)>=3:self.tokens[token].add(identity)
        if len(unique)<5000:raise ValueError('Fewer than5000 distinct replies')
        self.unique_lines=len(unique)
    def item(self,text):
        cleaned=normalize(text)
        match=re.search(r'\bid\s*(\d+)\b',cleaned)
        if match:return self.item_by_id.get(int(match[1]))
        if cleaned.isdecimal():return self.item_by_id.get(int(cleaned))
        if cleaned in self.aliases:return self.item_by_id[self.aliases[cleaned]]
        ids=set()
        for token in cleaned.split():
            candidates=self.tokens.get(token,())
            if len(candidates)<=100:ids.update(candidates)
        matches=[]
        for identity in sorted(ids)[:160]:
            fact=self.item_by_id[identity]
            for alias in fact['aliases']:
                key=normalize(alias)
                if len(key)>=4 and re.search(r'(?<!\w)'+re.escape(key)+r'(?!\w)',cleaned):matches.append((len(key),identity))
        return self.item_by_id[max(matches)[1]] if matches else None
    def summary(self):return {'intent_count':len(self.rows),'unique_reply_lines':self.unique_lines,'authored_conversation_lines':sum(len(r['responses']) for r in self.rows),'distinct_item_facts':len(self.facts),'profiles':len(self.profiles)}
