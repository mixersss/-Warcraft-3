"""Contextual human LFG replies; native invitation and roster remain authoritative."""
import math,re
from intent_recognizer import normalize
PARTY_REPLY=re.compile(r'\b(?:я рядом|я тут|я здесь|я с тобой|я тоже|возьми меня|можно с вами|есть место|место есть|пойду с вами|пойду с тобой|я хочу в пати)\b')

def response_to_offer(text):return bool(PARTY_REPLY.search(normalize(text)))
def recruitment_text(text):
    clean=normalize(text)
    return bool(re.search(r'(?:ищу|собираю|собираем|набираю).*(?:пати|групп)',clean))

def reply(adapter,text,source,identity,ctx,now,offer=None):
    clean=normalize(text);state=ctx.get('party_dialogue')
    if state and now>=state['until']:ctx.pop('party_dialogue',None);state=None
    if not state and not (response_to_offer(text) or offer and clean in ('да','давай','го','готов','пойду')):return None
    if not state:
        state={'until':now+180,'stage':'level','level':None,'map':None,'offer_confirmed':bool(offer)};ctx['party_dialogue']=state
    else:state['until']=now+180
    relevant=(response_to_offer(text) or state['stage']!='done' and bool(re.search(r'\b(?:да|ага|ок|готов|давай|го|нет|передумал|приглаш|аргент|шайтан|ледынь|ледын|гарнер|garner|magicsea|darkblue|рядом|тут|здесь|ур|лвл)\b|\d',clean)))
    if not relevant:return None
    if re.search(r'\b(?:нет|не хочу|не надо|передумал|отмена)\b',clean):
        ctx.pop('party_dialogue',None);return 'Хорошо, без приглашения. Если передумаешь — напиши.'
    p=adapter.policy;party=p.party;w=adapter.world
    if not party:return 'Я сейчас не могу собрать группу. Скажи уровень — можем обсудить место кача.'
    if len(party.members)>=5:return 'Пати уже полная. Если место освободится, можно будет обсудить новый сбор.'
    if party.members and party.members[0]!=adapter.name:return 'Я сейчас не лидер. Пригласить сможет лидер группы.'
    visible=next((e for e in w.entities.values() if e.name.casefold()==source.casefold() and e.control==1
                  and math.dist(w.position(now),w.position(now,e.identity))<=2000),None)
    if visible:
        state['level']=visible.values.get(0);state['map']=w.map;state['level_source']='server'
    # Only a response in this finite conversation can be treated as a reported level.
    match=re.fullmatch(r'(?:мне |у меня |я )?(\d{1,3})(?: (?:уровень|ур|лвл|левел))?',clean)
    if match and not visible and 1<=int(match[1])<=200:state['level']=int(match[1]);state['level_source']='chat'
    else:
        match=re.search(r'\b(\d{1,3})\s*(?:уровень|ур|лвл|левел)\b',clean)
        if match and not visible:state['level']=int(match[1]);state['level_source']='chat'
    for name,aliases in {'garner':('аргент','гарнер','аскарон','garner'),'magicsea':('шайтан','magicsea'),'darkblue':('ледынь','ледын','darkblue')}.items():
        if any(a in clean.split() for a in aliases):state['map']=name
    own_level=w.own.values.get(0,1);position=w.position(now)
    where=f"Я на {w.map}, {position[0]//100},{position[1]//100}."
    if state['level'] is None:
        state['stage']='level';return f'Отлично, ты про пати на кач? У меня {own_level} уровень. Какой у тебя?'
    if abs(state['level']-own_level)>3:
        state['stage']='done';return f"У меня {own_level}, у тебя {state['level']}. Для кача лучше найти группу с разницей до трёх уровней."
    if state['map'] is None:
        state['stage']='location';return where+' На какой ты карте? Можешь подойти ко мне?'
    if state['map']!=w.map:
        state['stage']='location';return where+' Мы на разных картах. Подойдёшь сюда или пока ищешь группу у себя?'
    ready=state['stage']=='ready' and re.search(r'\b(?:да|ага|ок|готов|давай|го|приглашай)\b',clean)
    explicit=re.search(r'приглас|возьми меня|добавь.*пати|кинь.*инвайт',clean)
    if ready or explicit:
        before=party.invites;answer=party.request_name(source,now)
        if party.invites>before:
            state['stage']='done';ctx['promises']=(ctx['promises']+[{'kind':'party_invite','until':now+15,'state':'requested'}])[-4:]
        return answer
    state['stage']='ready'
    return f"По уровню подходим: я {own_level}, ты {state['level']}. "+('Вижу тебя рядом. Пригласить в пати?' if visible else where+' Пригласить в пати?')
