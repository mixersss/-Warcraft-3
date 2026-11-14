"""Classic Argent tutorial/first Swordsman quest pilot; native NPC and journal actions.

Server owns all conditions, kill/item counts, rewards and profession changes.
"""
import math
import struct
from collections import deque
from classic_wire import Reader, ProtocolError

# Numeric positions from supplied garnernpc.txt; no game assets or credentials.
NPCS = {'senna': (222375,278525), 'goldie': (219312,270612),
        'nila': (226781,270475), 'ditto': (225075,277025),
        'daniel': (219350,273050), 'peter': (219220,276700), 'william': (227789,283199)}
TITLES = {'Welcome', "Blacksmith's Greetings", "Tailor's Greetings",
          "Physician's Greetings", 'Battle training', 'Swordsman Promotion','Hunter Promotion','Herbalist Promotion','Explorer Promotion'}
# Native journal IDs differ from the mission script IDs used by AddNpcMission!
DESTINATIONS = {1:'senna',701:'senna',702:'senna',703:'senna',704:'senna',
                58:'peter',62:'peter',63:'william',64:'william',65:'peter'}
LETTER_STOPS = {701:'goldie',702:'nila',703:'ditto'}
# Numeric requirements audited from the owner's MissionScript01; hints only.
# The server's NPC button/conditions remain the sole delivery authority.
PROFESSION_OBJECTIVES={62:('kill',237,12),158:('kill',237,12),98:('kill',240,12),
                       80:('kill',43,2),64:('item',1678,3),160:('item',1595,2),
                       150:('item',1779,3),82:('item',3129,3)}
GRIND = {704:(103,1620),62:(237,None),64:(125,1678)}
# Model: real level, practical search points inside the audited navigation crop.
FARMS = {75:(1,[(213050,269050)]),71:(2,[(219050,263950)]),
         103:(3,[(213050,271050),(219050,263950)]),
         185:(4,[(212050,264050),(222050,264050)]),
         206:(5,[(207050,274050)]),184:(6,[(219050,256050)]),
         104:(9,[(196050,270050)]),119:(7,[(210050,257050)]),125:(8,[(205750,263850),(196050,270050)]),
         237:(10,[(198050,259050)])}
QUEST_COMMANDS = (801,802,803,822,827,828,830,831,832)


def talk_request(npc):
    return struct.pack('>IHB',npc,302,0)


def select_request(npc, index):
    if not 0 <= index < 64:
        raise ValueError('Invalid NPC mission index')
    return struct.pack('>IHBB',npc,322,4,index)


def commit_request(npc, button, reward=0):
    if button not in (6,7) or not 0 <= reward < 64:
        raise ValueError('Only native accept/deliver actions are supported')
    return struct.pack('>IHBBB',npc,322,button,reward,0)


def mission_page(payload):
    r = Reader(payload)
    button, npc, title = r.byte(), r.long(), r.string()
    if button not in (6,7,8):
        raise ProtocolError('Unsupported mission page button')
    count = r.byte()
    if count > 32:
        raise ProtocolError('Too many mission needs')
    needs = []
    for _ in range(count):
        kind = r.byte()
        if kind in (0,1):
            needs.append((kind,r.short(),r.short(),r.byte()))
        elif kind == 5:
            r.string_bytes()  # Do not execute instructions or parse arbitrary text.
        else:
            raise ProtocolError('Unsupported mission need')
    choice, count = r.byte(), r.byte()
    if count > 32 or choice not in (0,1):
        raise ProtocolError('Unsupported mission rewards')
    prizes = [(r.byte(),r.short(),r.short()) for _ in range(count)]
    r.string_bytes()
    r.end()
    return button,npc,title,needs,choice,prizes


class Adventure:
    def __init__(self, world, send, tell=lambda text:None, role=None, region=None, tactic='quests'):
        if tactic not in ('quests','farm','hybrid'):raise ValueError('Unknown tactic')
        self.configured_tactic=tactic
        self.tactic='quests' if tactic=='hybrid' else tactic
        self.world, self.send, self.tell = world, send, tell
        self.role = role or {'first_job':1,'target_job':9,'promotion':'Swordsman Promotion','label':'крестоносец'}
        self.destinations = {k:v for k,v in DESTINATIONS.items() if k in (1,701,702,703,704)}
        if self.role['first_job']==1:
            self.destinations.update({k:v for k,v in DESTINATIONS.items() if k<100})
        elif self.role['first_job'] in (2,5):
            self.destinations[59 if self.role['first_job']==2 else 60] = 'other_map'
        elif self.role['first_job']==4:
            self.destinations.update({61:'daniel',158:'daniel',159:'william',160:'william',161:'daniel'})
        self.grind = {704:(103,1620)}
        self.grind.update({62:(237,None),64:(125,1678)} if self.role['first_job']==1 else
                          {158:(237,None),160:(104,1595)} if self.role['first_job']==4 else {})
        self.region = region
        self.npcs = dict(NPCS)
        self.letter_stops = dict(LETTER_STOPS)
        self.trainer = 'daniel' if self.role['first_job']==4 else 'peter'
        self.assistant = 'william'
        self.profession_local = self.role['first_job'] in (1,4)
        if world.map=='magicsea':
            self.npcs.update(senna=(87614,357250),goldie=(90260,349526),nila=(89463,360213),
                             ditto=(90311,364658),gannon=(86299,350092),nic=(86507,364804))
            self.destinations={2:'senna',707:'senna',708:'senna',709:'senna',710:'senna'}
            self.letter_stops={707:'goldie',708:'nila',709:'ditto'}
            self.grind={710:(188,1691)}
            self.profession_local=self.role['first_job']==5
            if self.profession_local:
                self.destinations.update({60:'gannon',80:'gannon',81:'nic',82:'nic',83:'gannon'})
                self.grind.update({80:(43,None),82:(62,3129)})
                self.trainer,self.assistant='gannon','nic'
        elif world.map=='darkblue':
            self.npcs.update(senna=(131577,50700),goldie=(134423,52988),nila=(134926,53992),
                             ditto=(135298,49926),ray=(136573,57078),mo=(123788,61340))
            self.destinations={3:'senna',713:'senna',714:'senna',715:'senna',716:'senna'}
            self.letter_stops={713:'goldie',714:'nila',715:'ditto'}
            self.grind={716:(234,1597)}
            self.profession_local=self.role['first_job']==2
            if self.profession_local:
                self.destinations.update({59:'ray',98:'ray',99:'mo',150:'mo',151:'ray'})
                self.grind.update({98:(240,None),150:(234,1779)})
                self.trainer,self.assistant='ray','mo'
        if not self.profession_local:
            self.destinations[{1:58,2:59,4:61,5:60}[self.role['first_job']]]='other_map'
        self.tutorial_ids=set(self.letter_stops) | {1,2,3,704,710,716}
        self.accepted_here=set()
        self.review_identity=None;self.review_started=None;self.review_last=None
        self.review_after=0;self.review_seen=set();self.review_deaths=0;self.review_baseline=0
        self.verification_task=None;self.review_reconnect_pending=False
        self.journal = {}
        self.journal_ready = False
        self.journal_snapshot_received = False
        self.events = deque(maxlen=64)
        self.deadline = self.next_visit = self.next_log = 0
        self.context = None
        self.pending = None
        self.destination = 'senna'
        self.subvisit = None
        self.started = None
        self.disabled = False
        self.accepted = self.delivered = self.requests = self.timeouts = 0
        self.seen_pages = 0
        self.missing_offers = 0
        self.last_needs = []
        self.start_job = world.own.values.get(4)
        self.reason = 'чтение журнала заданий'
        self.priority_started = False
        self.last_offers = []
        self.last_functions = []
        self.last_response = None
        self.last_problem = ''
        self.npc_seen = False
        self.npc_distance = None
        self.commit_journal_before = {}
        self.commit_resync_sent = False

    def observe(self, command, payload):
        self.last_response = command
        r = Reader(payload)
        if command == 828:
            count = r.byte()
            if count > 64:
                raise ProtocolError('Too many active missions')
            entries = [(r.short(),r.byte()) for _ in range(count)]
            r.end()
            self.journal = dict(entries)
            self.journal_ready = True
            self.journal_snapshot_received = True
            if self.pending:
                button,identity,deadline=self.pending
                added=set(self.journal)-set(self.commit_journal_before)
                expected=set(self.destinations)
                if self.context and self.context[3]==self.role['promotion']:expected-=self.tutorial_ids
                else:expected&=self.tutorial_ids
                if button==6 and added.intersection(expected):
                    self.accepted_here.update(added.intersection(expected))
                    self.accepted+=1;self.pending=None;self.context=None;self.next_visit=0
                elif button==7 and identity is not None and identity in self.commit_journal_before and identity not in self.journal:
                    # Reuse the same state transition as a native clear notice.
                    self.observe(831,struct.pack('>H',identity))
        elif command in (830,832):
            identity, state = r.short(),r.byte()
            r.end()
            self.journal[identity] = state
            if command==832:self.accepted_here.add(identity)
            self.journal_ready = True
            if command == 832 and self.pending and self.pending[0] == 6:
                self.accepted += 1
                self.pending = None
                self.context = None
                self.next_visit = 0
        elif command == 831:
            identity = r.short()
            r.end()
            self.journal.pop(identity,None)
            if self.pending and self.pending[0] == 7 and self.pending[1] == identity:
                self.delivered += 1
                self.pending = None
                self.context = None
                self.destination = {58:'peter',62:'peter',63:'william',64:'william',61:'daniel',158:'daniel',159:'william',160:'william',59:'ray',98:'ray',99:'mo',150:'mo',60:'gannon',80:'gannon',81:'nic',82:'nic'}.get(identity,'senna')
                self.subvisit = None
                self.next_visit = 0
        elif command in (801,802,803,822,827):
            self.events.append((command,payload))

    def profession_priority(self):
        return self.world.own.values.get(4)==0 and self.world.own.values.get(0,1)>=9

    def prepare_priority(self):
        if not self.profession_priority() or self.priority_started:
            return False
        self.priority_started = True
        # A tutorial delay or an unfinished tutorial dialogue must not postpone
        # the first profession. Journal notifications remain authoritative.
        if self.context and self.context[3] != self.role['promotion']:
            self.context = self.pending = None
            self.events.clear()
        self.next_visit = self.next_log = 0
        self.subvisit = None
        return True

    def active(self):
        profession=[identity for identity in self.destinations
                    if identity not in self.tutorial_ids and identity in self.journal]
        if profession:return profession[0]
        if self.tactic=='farm' or self.profession_priority():return None
        return next((identity for identity in self.destinations if identity in self.journal),None)

    def pause_for_travel(self):
        # Journal notifications remain authoritative across the transfer.
        self.context = self.pending = None
        self.events.clear()
        self.next_visit = 0
        self.reason = 'первая профессия: сначала переход в город наставника'

    def review_objective(self,now,busy=False):
        """Choose NPC verification from evidence/time, never fake a journal flag.

        A reconnect may already have completed a saved objective. New tasks first
        collect genuine evidence; an NPC refusal returns to farming between checks.
        """
        identity=self.active()
        objective=PROFESSION_OBJECTIVES.get(identity)
        if (self.disabled or not self.profession_priority() or identity not in self.grind
                or objective is None or self.journal.get(identity)!=0):
            self.verification_task=None
            return
        kind,model,count=objective
        evidence={(actor,hit[0]) for actor,hit in self.world.own_hits.items()
                  if hit[1] and 0<=now-hit[0]<=180
                  and self.world.entities.get(actor) is not None
                  and self.world.entities[actor].model==model}
        # Only identifiable species count as evidence. Periodic NPC checks
        # cover deaths whose source entity already disappeared.
        if self.review_identity!=identity:
            self.review_identity=identity;self.review_started=now;self.review_last=now
            self.review_seen=evidence;self.review_deaths=self.review_baseline=0;self.review_after=0
            self.review_reconnect_pending=self.journal_snapshot_received and identity not in self.accepted_here
        else:
            self.review_deaths+=len(evidence-self.review_seen)
            self.review_seen=evidence
        if self.verification_task==identity or busy or now<self.review_after:return
        if self.review_reconnect_pending:
            self.review_reconnect_pending=False;self.verification_task=identity
            self.reason='проверяет сохранённое задание у NPC после подключения'
            return
        enough=(sum(item.count for item in self.world.bag.values() if item.identity==model)>=count
                if kind=='item' else self.review_deaths-self.review_baseline>=count)
        if enough or now-self.review_last>=180:
            self.verification_task=identity
            self.reason='проверяет готовность задания у NPC по фактическому прогрессу'

    def defer_verification(self,now,delay=60):
        if self.verification_task is None:return
        self.verification_task=None;self.review_last=now
        self.review_baseline=self.review_deaths;self.review_after=now+max(30,delay)

    def farm(self):
        if self.world.own.values.get(4) in (self.role['first_job'],self.role['target_job']):return None
        active = self.active()
        return self.grind.get(active) if active in self.grind and self.journal[active] == 0 and self.verification_task!=active else None

    def desired_models(self):
        level=self.world.own.values.get(0,1)
        farms = ({int(m):(r['level'],r['points']) for m,r in self.region['farms'].items() if r['points']}
                 if self.region else FARMS)
        task=self.farm()
        wanted=set()
        if task:
            if task[0] in farms and farms[task[0]][0]<=level:wanted.add(task[0])
            if task[1] and self.region:
                droppers=[int(m) for m,r in self.region['farms'].items() if r['points'] and task[1] in r['drops'] and r['level']<=level]
                if droppers:
                    wanted.add(min(droppers,key=lambda m:farms[m][0]))
            if wanted:return wanted
        highest=max((lv for lv,_ in farms.values() if lv<=level),default=1)
        return {model for model,(lv,_) in farms.items() if max(1,highest-2)<=lv<=highest}

    def farm_goals(self):
        farms=({int(m):(r['level'],r['points']) for m,r in self.region['farms'].items()}
               if self.region else FARMS)
        return [p for model in sorted(self.desired_models()) for p in farms[model][1]]

    def choose_destination(self):
        active = self.active()
        if active:
            if active in self.letter_stops and self.subvisit == active:
                return self.letter_stops[active]
            return self.destinations[active]
        return self.destination

    def settle(self, now, delay=3):
        self.defer_verification(now,delay)
        self.context = None
        self.next_visit = now + delay
        self.events.clear()

    def process_event(self, command, payload, now):
        if not self.context:
            return
        npc, key, stage, selected_title = self.context
        if command == 802 and stage == 'talk':
            r = Reader(payload)
            source, page = r.long(),r.byte()
            r.string_bytes()
            if source != npc:
                return
            functions = r.byte()
            if functions > 64:
                raise ProtocolError('Too many NPC functions')
            self.last_functions = [r.string()[:160] for _ in range(functions)]
            count = r.byte()
            if count > 64:
                raise ProtocolError('Too many NPC missions')
            offers = [(r.string(),r.byte()) for _ in range(count)]
            self.last_offers = [(title[:160],state) for title,state in offers]
            r.end()
            self.seen_pages += 1
            allowed = {'Welcome',"Blacksmith's Greetings","Tailor's Greetings","Physician's Greetings",'Battle training'} if key == 'senna' else set()
            active = self.active()
            if self.world.own.values.get(0,1) >= 9 and self.world.own.values.get(4) == 0:
                allowed.add(self.role['promotion'])
            if key in ('goldie','nila','ditto'):
                allowed = { { 'goldie':"Blacksmith's Greetings", 'nila':"Tailor's Greetings", 'ditto':"Physician's Greetings"}[key] }
            if self.tactic=='farm' or self.profession_priority():
                allowed &= {self.role['promotion']}
            candidates = [(i,title,state) for i,(title,state) in enumerate(offers)
                          if title in allowed and (state & 3 or
                              (active is not None and title==self.role['promotion'] and state & 4))]
            # Complete ready work before accepting another task.
            candidates.sort(key=lambda item: not bool(item[2]&2))
            if candidates:
                index,title,state = candidates[0]
                self.send(301,select_request(npc,index))
                self.requests += 1
                self.context = npc,key,'select',title
                self.deadline = now+8
            else:
                self.missing_offers += 1
                self.last_problem = 'NPC не предложил доступный квест '+self.role['promotion']
                self.reason = self.last_problem
                if active in self.letter_stops:
                    self.subvisit = active if key == 'senna' else None
                    self.settle(now)
                elif not active and not self.profession_local:
                    self.destination = 'senna'
                    self.settle(now,120)
                elif not active and self.world.own.values.get(0,1) >= 9:
                    trainer = self.trainer
                    self.destination = {'senna':trainer,trainer:self.assistant,self.assistant:'senna'}.get(key,'senna')
                    self.settle(now,20)
                else:
                    self.settle(now,120)
        elif command == 827 and stage == 'select':
            button,source,title,needs,choice,prizes = mission_page(payload)
            if source != npc or title != selected_title or title not in TITLES or ('Promotion' in title and title != self.role['promotion']):
                self.last_problem = 'ответ задания не совпал с выбранным NPC/названием'
                return
            if ((self.tactic=='farm' or self.profession_priority()) and title!=self.role['promotion']):
                self.settle(now,10)
                return
            self.last_needs = needs
            if button == 8:
                self.last_problem='NPC подтверждает: условия задания ещё не выполнены'
                self.reason=self.last_problem
                active = self.active()
                if active in self.letter_stops and key == 'senna': self.subvisit = active
                self.settle(now,5 if active in self.letter_stops else 60)
                return
            # These audited quests have no item reward selection. Unknown choices pause.
            if choice == 0 and len(prizes) > 1:
                self.reason = 'неизвестный выбор награды; задание отложено'
                self.settle(now,120)
                return
            self.send(301,commit_request(npc,button))
            self.requests += 1
            self.commit_journal_before=dict(self.journal)
            self.commit_resync_sent=False
            self.pending = button,self.active(),now+8
            self.context = npc,key,'commit',title
            self.deadline = now+8
        elif command in (801,803) and stage == 'commit':
            # Some intermediate greeting pages set a quest flag without clearing its journal row.
            source = Reader(payload).long()
            if source == npc and key in ('goldie','nila','ditto'):
                self.pending = None
                self.subvisit = None
                self.settle(now)

    def tick(self, now, policy):
        if self.started is None: self.started = now
        self.prepare_priority()
        if self.disabled: return False
        if self.world.own.values.get(4) in (self.role['first_job'],self.role['target_job']):
            self.context=None;self.pending=None;self.verification_task=None
            self.reason = 'первая профессия подтверждена сервером; охота'
            return False
        if self.world.own.values.get(4) != 0:
            self.reason = 'другая раса/профессия; автоматическая цепочка не выбрана'
            return False
        foreign = ({58,62,63,64,65,59,98,99,150,151,60,80,81,82,83,61,158,159,160,161}
                   - set(self.destinations)) & set(self.journal)
        if foreign:
            self.reason = 'обнаружен квест другой профессии; автоматические квесты приостановлены'
            return False
        if not self.profession_local and self.active() in (58,59,60,61):
            self.reason = 'путь '+self.role['label']+': переход на другую карту ещё не реализован'
            return False
        while self.events:
            try:
                self.process_event(*self.events.popleft(),now)
            except ProtocolError:
                self.disabled = True
                self.reason = 'неизвестный формат задания; квесты остановлены'
                return False
        if self.context:
            if (self.pending and self.context[2]=='commit' and not self.commit_resync_sent
                    and now>=self.deadline-6):
                self.send(325,b'');self.commit_resync_sent=True
            if now < self.deadline:
                return True
            self.timeouts += 1
            self.last_problem = 'нет подтверждения NPC на этапе '+self.context[2]
            self.reason = self.last_problem
            key = self.context[1]
            if key in ('goldie','nila','ditto'):
                self.subvisit = None
            self.pending = None
            self.settle(now,120)
            return False
        if not self.journal_ready:
            if now >= self.next_log:
                self.send(325,b'')
                self.next_log = now+30
            self.reason = 'ожидает журнал заданий; повторный запрос каждые 30 секунд'
            return False
        if self.tactic=='farm' and not self.profession_priority() and self.active() is None:
            self.reason='фарм до уровня задания профессии'
            return False
        if now < self.next_visit or self.farm():
            return False
        key = self.choose_destination()
        position = self.npcs[key]
        # Use only a real visible NPC at the audited location, never a saved world ID.
        npc = next((e for e in self.world.entities.values() if e.control in (2,3)
                    and math.dist(e.position,position)<450),None)
        self.npc_seen = npc is not None
        self.npc_distance = round(math.dist(npc.position,policy.position(now))) if npc else None
        self.reason = 'задание: путь к '+key
        if policy.target:
            from hunter import movement
            policy.emit(movement(self.world.own_id,policy.sequence,[policy.position(now)]*2))
            policy.target = None
            policy.next_action = now+1
            return True
        if npc and math.dist(npc.position,policy.position(now)) <= 220:
            self.send(301,talk_request(npc.identity))
            self.requests += 1
            self.context = npc.identity,key,'talk',None
            self.deadline = now+8
            self.reason = 'задание: разговор с '+key
            return True
        goal = policy.nav.nearest(position,6)
        if not goal or not policy.move_to(goal,now):
            self.reason = 'NPC недоступен по проверенной карте'
            self.next_visit = now+120
            return False
        return True

    def summary(self):
        return {'cohort':self.configured_tactic,'tactic':self.tactic,'state':self.reason,'journal_received':self.journal_ready,
                'active_missions':dict(self.journal),'accepted_confirmed':self.accepted,
                'deliveries_confirmed':self.delivered,'npc_requests':self.requests,
                'npc_pages':self.seen_pages,'missing_offers':self.missing_offers,
                'dialogue_timeouts':self.timeouts,'disabled':self.disabled,
                'start_profession':self.start_job,'profession':self.world.own.values.get(4),
                'profession_confirmed':self.world.own.values.get(4) in (self.role['first_job'],self.role['target_job']),
                'objective_review':{'mission':self.review_identity,'verification_due':self.verification_task is not None,
                                    'observed_credited_deaths':self.review_deaths,'not_a_server_completion_count':True},
                'target_class':self.role['label'],'target_job':self.role['target_job'],
                'first_job':self.role['first_job'],
                'last_objectives':[list(n) for n in self.last_needs],
                'destination_npc':self.choose_destination(),'npc_seen':self.npc_seen,
                'level':self.world.own.values.get(0),'gold':self.world.own.values.get(8),
                'bag_capacity':self.world.bag_capacity,'bag_used':len(self.world.bag),
                'free_bag_slots':max(0,self.world.bag_capacity-len(self.world.bag)) if self.world.bag_capacity is not None else None,
                'npc_distance':self.npc_distance,'dialogue_stage':self.context[2] if self.context else None,
                'expected_promotion':self.role['promotion'],'last_problem':self.last_problem,
                'last_response_command':self.last_response,'last_offers':self.last_offers,
                'last_functions':self.last_functions}
