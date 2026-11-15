"""Bounded transparent Russian intent rules; uncertain input is clarified."""
import re
from dataclasses import dataclass
ALIASES={'ne':'не','priglashay':'приглашай','skolko':'сколько','stoit':'стоит','fairy':'фея','privet':'привет','priv':'привет','ky':'ку','zdarova':'здарова','gde':'где','ti':'ты','ty':'ты','kak':'как','dela':'дела','chto':'что','delaesh':'делаешь','go':'го','kach':'кач','pati':'пати','party':'пати','invite':'инвайт','lvl':'лвл','level':'уровень','po4em':'почем','pochem':'почем','cena':'цена','kuplyu':'куплю','prodam':'продам','spasibo':'спасибо','spas':'спс','plz':'пожалуйста','heal':'хил','healer':'хил','tank':'танк','npc':'нпс','np':'нп','kvest':'квест','quest':'квест','pomogi':'помоги','nado':'надо','net':'нет','da':'да','bye':'пока','rjulf':'когда','ghbdtn':'привет','clsd':'скилл','здраствуйте':'здравствуйте','превет':'привет','првиет':'привет','пожалуста':'пожалуйста','патию':'пати','инваит':'инвайт','приглоси':'пригласи','коч':'кач','квсет':'квест','перг':'пергамент','пачкулию':'пачкули','хлп':'помоги','скилы':'скиллы'}

def normalize(text):
    words=re.findall(r'[\w]+',str(text)[:240].casefold().replace('ё','е'))
    return ' '.join(ALIASES.get(word,word) for word in words)

@dataclass(frozen=True)
class Intent:
    name:str
    confidence:float
    text:str
    negated:bool=False

class IntentRecognizer:
    def __init__(self,rows):
        self.rows={row['id']:row for row in rows};self.exact={};self.patterns=[]
        for row in rows:
            for example in row['examples']:self.exact[normalize(example)]=row['id']
            self.patterns.append((row['id'],re.compile(row['pattern'])))
    def recognize(self,text):
        cleaned=normalize(text)
        if re.search(r'\bне\s+(?:(?:хочу|буду)\s+)?(?:дружить|в друзья)',cleaned):return Intent('disagree',1,cleaned,True)
        if re.search(r'\bне против\b.*(?:пати|групп|кач)',cleaned):return Intent('hunt_offer',.94,cleaned)
        if re.search(r'\bне\s+(?:(?:надо|хочу|нужно)\s+)?(?:приглаш\w*|зови\w*|инвайт|в пати|в группу)',cleaned):
            return Intent('party_decline',1,cleaned,True)
        if re.search(r'\bне\s+(?:(?:хочу|буду|надо|нужно|собираюсь)\s+)?(?:прода\w*|купить|покуп\w*|меня\w*)',cleaned):return Intent('trade_decline',1,cleaned,True)
        if cleaned in self.exact:
            name=self.exact[cleaned];return Intent(name,1,cleaned,name.endswith('decline'))
        if cleaned.isdecimal() and 1<=int(cleaned)<=200:return Intent('level_answer',.9,cleaned)
        # More specific domain intents precede broad social/question patterns.
        priority=('silence','resume','returned','friend_request','party_decline','trade_decline','fairy_food','fairy_growth','fairy_breed','party_invite','party_leave','hunt_help','hunt_advice','quest_help','quest_reward','quest_marker','combat_help','stop_attack','under_attack','guild_join','guild_recruit','trade_safety','sockets','dark_swamp','demonic_world','abandoned_city','patchouli','buy','sell','exchange','price','discount','parchment','treasure','hunt_offer','healer_search','tank_search','party_search','party_status','mob_location','boss_location','bank_location','merchant_location','port_location')
        patterns=dict(self.patterns)
        for name in priority:
            if patterns[name].search(cleaned):return Intent(name,.94,cleaned)
        generic={'why','where','when','how_many','which','clarify','suggest','invite','advice','everyone','group_address','address','continue_topic','status','unknown'}
        for name,pattern in self.patterns:
            if name not in priority and name not in generic and pattern.search(cleaned):return Intent(name,.82,cleaned)
        for name,pattern in self.patterns:
            if name in generic and pattern.search(cleaned):return Intent(name,.6,cleaned)
        return Intent('unknown',0,cleaned)
