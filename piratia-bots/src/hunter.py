"""First bounded PvE policy: passive weak mobs, normal attack, retreat and rest."""
import math
import struct
import time
import random
from classic_wire import sequence
from classic_wire import ProtocolError, Reader
from progression import Progression
from social import Social, ChatBudget
from world import World, HP, MAX_HP, LV, ATTACK_DISTANCE


def distance(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


def action_header(actor, number, kind):
    return struct.pack('>IIB', actor, number, kind)


def movement(actor, number, points):
    if not 2 <= len(points) <= 32:
        raise ValueError('Expected 2..32 movement points')
    return action_header(actor, number, 1) + sequence(b''.join(struct.pack('<ii', *p) for p in points))


def normal_attack(actor, number, fight, skill, target, handle, position):
    # Native BeginAction 0x5198b0: chMove=2, fight ID, path, skill, world ID, handle.
    # In-range attacks still include two equal points, as the normal UI does.
    points = sequence(struct.pack('<iiii', *position, *position))
    return action_header(actor, number, 2) + bytes([2, fight & 255]) + points + struct.pack('>III', skill, target, handle)


class Hunter:
    def __init__(self, world, navigation, send, report, tell=print, seed=None):
        self.world, self.nav, self.send = world, navigation, send
        self.report, self.tell = report, tell
        self.home = world.own.position
        self.sequence, self.fight = 1, 0
        self.target = None
        self.next_action = 0
        self.mode = 'observe'
        self.resting = False
        self.cancel_pending = False
        self.waypoint = 0
        self.moves = self.attacks = self.kills = 0
        self.blacklist = {}
        self.last_position = self.home
        self.stuck = 0
        self.last_target_hp = None
        self.target_since = 0
        self.started = time.monotonic()
        self.rng = random.Random(str(seed or world.own.identity))
        self.attack_interval = self.rng.uniform(2.0, 2.5)
        self.route = list(range(len(navigation.waypoints)))
        self.rng.shuffle(self.route)
        self.adventure = None
        self.loot = None
        self.equipment = None
        self.skills = None
        self.recovery = None
        self.dead_since = None
        self.revive_requests = 0
        self.death_attempts = 0
        self.next_revive = 0
        self.region = None
        self.move_goal = None
        self.move_sent = -1e9
        self.move_until = 0
        self.move_revision = -1
        self.move_waits = 0
        self.owner=str(seed or world.own.identity)
        self.coordination=None
        self.target_key=None
        self.combat_since=None
        self.last_damage_at=0
        self.approach_probe=False
        self.approach_angle=self.rng.uniform(0,math.tau)
        self.recoveries=self.no_damage_retargets=self.busy_targets=0
        self.next_recovery=0
        self.search_goal=None
        self.search_started=0
        self.goal_blacklist={}
        self.tactic='quests'

    def drop_target(self,now=None,avoid=False):
        had_target=self.target is not None or self.target_key is not None
        if self.target and avoid and now is not None:
            self.blacklist[self.target]=now+45
            if len(self.blacklist)>256:self.blacklist.pop(next(iter(self.blacklist)))
        if self.coordination:self.coordination.release(self.owner)
        self.target=None
        self.target_key=None
        self.combat_since=None
        self.last_target_hp=None
        if had_target:self.move_goal=None
        self.approach_probe=False

    def clear_zone(self):
        if self.coordination:self.coordination.leave_zone(self.owner)
        self.search_goal=None

    def available_spot(self,point,now):
        return not any(e.identity!=self.world.own_id and e.control==1 and e.alive
                       and distance(point,self.world.position(now,e.identity))<100
                       for e in self.world.entities.values())

    def approach(self,target,reach,now):
        center=self.world.position(now,target.identity)
        radius=max(70,reach-65)
        options=[]
        for i in range(12):
            angle=self.approach_angle+i*math.tau/12
            point=(round(center[0]+math.cos(angle)*radius),round(center[1]+math.sin(angle)*radius))
            point=self.nav.nearest(point,1)
            if (point and distance(point,center)<=reach-20
                    and self.available_spot(point,now)):
                options.append(point)
        for point in sorted(set(options),key=lambda pt:distance(self.position(now),pt)):
            if self.nav.path(self.position(now),point):return point
        return None

    def recover_path(self,now):
        self.drop_target(now,avoid=True)
        if self.search_goal:self.goal_blacklist[self.search_goal]=now+45
        self.clear_zone()
        self.stuck=0
        self.recoveries+=1
        self.next_recovery=now+8
        self.move_sent=-1e9
        origin=self.position(now)
        # Small checked detour, never a coordinate teleport or a forced SQL move.
        for radius in (200,400,600):
            for i in range(8):
                angle=self.approach_angle+(self.recoveries+i)*math.tau/8
                point=self.nav.nearest((round(origin[0]+radius*math.cos(angle)),
                                        round(origin[1]+radius*math.sin(angle))),1)
                if point and self.available_spot(point,now) and self.nav.path(origin,point):
                    self.move_to(point,now)
                    self.next_action=now+1
                    self.change('обход препятствия; повторный поиск цели')
                    return
        self.next_action=now+2
        self.change('ожидание свободного прохода')

    def change(self, value):
        if self.mode != value:
            self.mode = value
            self.tell('Состояние бота: ' + value)

    def emit(self, body):
        self.send(6, body)
        self.sequence = (self.sequence + 1) & 0xffffffff

    def position(self,now):
        return self.world.position(now)

    def move_to(self, goal, now):
        own = self.world.own
        origin = self.position(now)
        same_goal = self.move_goal and distance(self.move_goal,goal)<200
        if now-self.move_sent<.65:
            return True
        if same_goal:
            if self.world.move_revision==self.move_revision and now-self.move_sent<1.5:
                self.move_waits+=1
                return True  # Wait for server acceptance; never extrapolate a requested route.
            if (self.world.move_revision!=self.move_revision and self.world.move_state==0
                    and now<self.move_until-.65):
                self.move_waits+=1
                return True
        path = self.nav.path(origin,goal)
        if len(path)<2:
            return False
        points=path[:32]  # Native maximum, contiguous checked cells, not six-metre bursts.
        travelled=sum(distance(a,b) for a,b in zip(points,points[1:]))
        speed=max(100,min(own.values.get(44,480),3000))
        self.emit(movement(own.identity,self.sequence,points))
        self.moves+=1
        self.move_goal,self.move_sent,self.move_until=tuple(goal),now,now+travelled/speed
        self.move_revision=self.world.move_revision
        self.next_action=now+.15
        if distance(origin,self.last_position)<40:
            self.stuck+=1
        else:
            self.stuck=0
        self.last_position=origin
        return True

    def farm_models(self):
        if not self.region:return (71,75)
        level=self.world.own.values.get(LV,1)
        highest=max((r['level'] for r in self.region['farms'].values() if r['level']<=min(level,15)),default=1)
        return {int(m) for m,r in self.region['farms'].items() if max(1,highest-2)<=r['level']<=highest}

    def eligible(self, entity, now):
        own = self.world.own
        # Only the two passive beginner species from this server's CharacterInfo.
        models = self.adventure.desired_models() if self.adventure else self.farm_models()
        maximum_level = min(15,own.values[LV]) if self.region or self.adventure else min(2,own.values[LV]+1)
        return (entity.control == 5 and entity.model in models and entity.alive
                and 0 < entity.values.get(LV, 9999) <= maximum_level
                and entity.handle != 0 and distance(entity.position, self.home) <= (100000 if self.region else 45000 if self.adventure else 22000)
                and self.blacklist.get(entity.identity, 0) < now)

    def tick(self, now=None):
        now = time.monotonic() if now is None else now
        own = self.world.own
        if own and self.world.map==self.nav.map and not self.nav.free(self.nav.cell(self.position(now))):
            # A server correction can invalidate interpolation; prefer its raw position.
            self.world.motion.pop(self.world.own_id,None)
        if not own or self.world.map != self.nav.map or not self.nav.free(self.nav.cell(self.position(now))):
            self.change('ожидание достоверных данных карты')
            return
        hp, maximum = own.values.get(HP), own.values.get(MAX_HP)
        if hp is None or not maximum:
            self.change('ожидание данных здоровья')
            return
        if hp <= 0 or own.state >= 5:
            self.drop_target()
            self.clear_zone()
            self.change('персонаж погиб; обычное возвращение в город')
            if self.dead_since is None:self.dead_since=now
            if now-self.dead_since>=8 and now>=self.next_revive and self.death_attempts<3:
                self.send(10,b'\x01')
                self.revive_requests+=1
                self.death_attempts+=1
                self.next_revive=now+30
            return
        self.dead_since=None
        self.death_attempts=0
        if self.recovery and self.recovery.tick(now,self):
            self.next_action=now+.3
            return
        if hp / maximum <= .35:
            if not self.resting:
                self.cancel_pending = True
            self.resting = True
            self.drop_target()
            self.clear_zone()
        if self.resting:
            if hp / maximum >= .85:
                self.resting = False
            else:
                self.change('отступление и восстановление')
                if self.cancel_pending:
                    self.emit(movement(own.identity,self.sequence,[self.position(now),self.position(now)]))
                    self.cancel_pending = False
                    self.moves += 1
                    self.next_action = now+1
                if now >= self.next_action and distance(self.position(now), self.home) > 300:
                    self.move_to(self.home, now)
                return
        if now < self.next_action or now-self.started < 2:
            return
        if self.skills and self.skills.tick(now,self,safe=not self.target):
            self.next_action=now+.2
            self.change('изучает навыки своего класса')
            return
        if self.equipment and self.equipment.tick(now,self,safe=not self.target):
            self.next_action=now+.2
            self.change('надевает подходящую экипировку')
            return
        if self.stuck >= 5 and now>=self.next_recovery:
            self.recover_path(now)
            return
        if self.adventure and self.adventure.tick(now,self):
            self.drop_target()
            self.clear_zone()
            self.change(self.adventure.reason)
            return
        if self.loot:
            task = self.adventure.farm() if self.adventure else None
            needed = self.equipment.loot_needs() if self.equipment else set()
            if task and task[1]:needed.add(task[1])
            if self.loot.tick(now,self,needed):
                self.change('подбор квестового трофея')
                return
        target = self.world.entities.get(self.target)
        if self.target and (not target or not target.alive):
            if target and target.values.get(HP,1)<=0:self.kills+=1
            self.drop_target()
            target=None
        if target:
            key=(self.world.map,target.identity,target.handle)
            if (not self.eligible(target,now) or key!=self.target_key
                    or (self.coordination and not self.coordination.claim(self.owner,key,now))):
                self.drop_target(now,avoid=True)
                target=None
            else:
                hp=target.values.get(HP)
                if self.last_target_hp is not None and hp is not None and hp<self.last_target_hp:
                    self.last_damage_at=now
                self.last_target_hp=hp
                # Detect an approach that never completes and attacks that cause no damage.
                stalled=(self.combat_since is not None and now-self.last_damage_at>=14)
                if stalled or (self.combat_since is None and now-self.target_since>25):
                    self.no_damage_retargets+=1
                    self.drop_target(now,avoid=True)
                    target=None
        if not target:
            candidates=[e for e in self.world.entities.values() if self.eligible(e,now)]
            self.rng.shuffle(candidates)  # Distinct tie ordering for each character.
            candidates.sort(key=lambda e:distance(self.position(now),self.world.position(now,e.identity)))
            for candidate in candidates:
                key=(self.world.map,candidate.identity,candidate.handle)
                if self.coordination and not self.coordination.available(self.owner,key,now):
                    self.busy_targets+=1
                    continue
                reach=max(100,min(own.values.get(ATTACK_DISTANCE,150),250))+own.radius+candidate.radius
                in_range=distance(self.position(now),self.world.position(now,candidate.identity))<=reach
                if not in_range and self.approach(candidate,reach,now) is None:continue
                if self.coordination and not self.coordination.claim(self.owner,key,now):continue
                target=candidate
                self.target,self.target_since=target.identity,now
                self.target_key=key
                self.last_target_hp=target.values.get(HP)
                self.last_damage_at=now
                self.combat_since=None
                self.approach_probe=False
                self.clear_zone()
                break
        if target:
            reach = max(100, min(own.values.get(ATTACK_DISTANCE, 150), 250)) + own.radius + target.radius
            if distance(self.position(now),self.world.position(now,target.identity)) > reach:
                self.change('подход к слабому мобу')
                goal=self.approach(target,reach,now)
                if not goal or not self.move_to(goal,now):
                    self.drop_target(now,avoid=True)
                return
            if not self.world.default_skill:
                self.change('ожидание обычной атаки от сервера')
                return
            if self.combat_since is None:self.combat_since=self.last_damage_at=now
            if now-self.last_damage_at>=6 and not self.approach_probe:
                self.approach_probe=True
                self.approach_angle+=math.pi/2
                goal=self.approach(target,max(100,reach-40),now)
                if goal and distance(self.position(now),goal)>80:
                    self.move_goal=None
                    self.move_to(goal,now)
                    self.change('повторный подход: нет подтверждённого урона')
                    return
            self.change('обычная атака')
            self.fight = (self.fight+1) & 255
            self.emit(normal_attack(own.identity, self.sequence, self.fight, self.world.default_skill,
                                    target.identity, target.handle, self.position(now)))
            self.world.freeze_prediction(now)
            self.move_goal=None
            self.attacks += 1
            if self.loot:
                self.loot.note_attack(target.identity,now)
            self.next_action = now+self.attack_interval
            return
        self.change('поиск свободного места фарма')
        if self.adventure:
            raw_goals=self.adventure.farm_goals()
        elif self.region:
            raw_goals=[pt for model in self.farm_models() for pt in self.region['farms'][str(model)]['points']]
        else:
            raw_goals=[self.nav.waypoints[i] for i in self.route]
        goals=list(dict.fromkeys(self.nav.nearest(p) for p in raw_goals))
        goals=[p for p in goals if p and self.goal_blacklist.get(p,0)<=now]
        if not goals:
            self.change('нет свободного проверенного маршрута; повторный поиск')
            self.next_action=now+2
            return
        # Stable per-bot ordering, independent of the order of the JSON species.
        goals.sort(key=lambda pt:((pt[0]*73856093 ^ pt[1]*19349663 ^ int(self.approach_angle*100000)) & 0xffffffff))
        goal=(self.coordination.choose_zone(self.owner,self.world.map,goals,now)
              if self.coordination else goals[self.waypoint%len(goals)])
        if goal!=self.search_goal:self.search_goal,self.search_started=goal,now
        if distance(self.position(now),goal)<300 or now-self.search_started>45:
            self.goal_blacklist[goal]=now+20
            if len(self.goal_blacklist)>128:self.goal_blacklist.pop(next(iter(self.goal_blacklist)))
            self.clear_zone()
            self.waypoint+=1
            self.next_action=now+.5
        elif not self.move_to(goal,now):
            self.goal_blacklist[goal]=now+45
            self.clear_zone()
            self.next_action=now+1

    def summary(self):
        return {'tactic':self.tactic,'state': self.mode,
                'target_id':self.target,'path_recoveries':self.recoveries,
                'no_damage_retargets':self.no_damage_retargets,'reserved_targets_skipped':self.busy_targets, 'move_requests': self.moves, 'attack_requests': self.attacks,
                'revive_requests':self.revive_requests, 'movement_wait_ticks':self.move_waits, 'observed_target_deaths': self.kills, 'world': self.world.summary()}


def hunt(client, seconds, stop, report, navigation, tell=print, bot_name='', chat_budget=None, adventure_mode=False, role_store=None, fleet=None, bot_index=0, tactic='quests'):
    report.stage('reading_world')
    from equipment import ItemCatalog,Equipment
    from pathlib import Path
    catalog=getattr(navigation,'items',None) or ItemCatalog(Path(__file__).resolve().parents[1]/'assets/items.json')
    world = World(catalog.types)
    try:
        world.enter(client.enter_payload)
    except ProtocolError:
        report.result['world_decode'] = world.decode_info
        raise
    report.result['world_decode'] = world.decode_info
    nav=navigation.nav(world.map) if hasattr(navigation,'nav') else navigation
    policy = Hunter(world, nav, client.wire.send, report, tell, bot_name)
    policy.tactic=tactic
    policy.coordination=getattr(navigation,'coordination',None)
    policy.region=navigation.get(world.map) if hasattr(navigation,'get') else None
    policy.equipment=Equipment(world,catalog,client.wire.send,tell)
    from recovery import Recovery
    policy.recovery=Recovery(world)
    progression = Progression(world, client.wire.send)
    social = Social(world, client.wire.send, bot_name, chat_budget or ChatBudget(), bot_name)
    role = None
    if role_store:
        role = role_store.resolve(bot_name,world.own.model,world.own.values.get(4))
        progression.first_job = role['first_job']
        progression.target_job=role['target_job']
        from skills import Skills
        policy.skills=Skills(world,role)
        social.role_label=role['label']
        tell('Закреплённый класс: '+role['label'])
        report.result['class_path'] = role
    if adventure_mode:
        from adventure import Adventure
        from loot import QuestLoot
        if role is None:
            raise ProtocolError('Для квестов требуется сохранённый путь класса.')
        policy.adventure = Adventure(world,client.wire.send,tell,role,policy.region,tactic=tactic)
        policy.loot = QuestLoot(world)

    def snapshot(now):
        report.result['hunt']=policy.summary()
        report.result['progression']=progression.summary()
        report.result['equipment']=policy.equipment.summary()
        report.result['chat']=social.summary()
        report.result['recovery']=policy.recovery.summary()
        if policy.skills:report.result['skills']=policy.skills.summary()
        if policy.adventure:report.result['adventure']=policy.adventure.summary()
        report.write(Path(__file__).resolve().parents[1]/f'bot-report-{bot_index:02d}.json')
        if fleet:
            values=world.own.values
            fleet.update(bot_index,connected=True,map=world.map,level=values.get(0),job=values.get(4),
                         body=world.own.model,state=policy.mode,tactic=policy.tactic,hp=values.get(HP),max_hp=values.get(MAX_HP),
                         moves=policy.moves,attacks=policy.attacks,equips=policy.equipment.confirmed,
                         quests=policy.adventure.delivered if policy.adventure else 0,
                         target_job=role['target_job'] if role else 0)

    def observe(command, payload):
        if command==516:
            world.enter(payload)
            policy.nav=navigation.nav(world.map) if hasattr(navigation,'nav') else nav
            policy.region=navigation.get(world.map) if hasattr(navigation,'get') else None
            policy.home=world.own.position
            policy.drop_target()
            policy.clear_zone()
            policy.move_goal=None
            policy.stuck=0
            policy.resting=False
            policy.cancel_pending=False
            policy.dead_since=None
            policy.death_attempts=0
            policy.equipment.pending=None
            policy.recovery.pending=None
            if policy.skills:policy.skills.pending=None
            if adventure_mode:
                policy.adventure=Adventure(world,client.wire.send,tell,role,policy.region,tactic=tactic)
        elif command in (801,802,803,822,827,828,830,831,832):
            if policy.adventure:
                policy.adventure.observe(command,payload)
        elif command == 501:
            reader = Reader(payload)
            source, text = reader.long(), reader.string()
            social.hear(source, text, time.monotonic())
        else:
            world.observe(command, payload)

    client.world_handler = observe
    try:
        while client.pending_world:
            observe(*client.pending_world.popleft())
        report.stage('hunting')
        tell(f'Данные мира: {world.map}, координаты {world.own.x//100},{world.own.y//100}, '
             f'здоровье {world.own.values[HP]}/{world.own.values[MAX_HP]}.')
        next_snapshot=0
        seen_equips=seen_skills=seen_quests=0
        deadline = time.monotonic()+seconds
        while time.monotonic() < deadline and not stop.is_set():
            try:
                command, payload = client.wire.receive(min(deadline, time.monotonic()+.25))
                client.service(command, payload)
            except TimeoutError:
                pass
            policy.tick()
            now = time.monotonic()
            alive = world.own.alive
            safe = (alive and now-policy.started >= 3 and not policy.resting
                    and world.own.values.get(HP, 0) > world.own.values.get(MAX_HP, 1) * .5)
            progression.tick(now, safe)
            social.activity='quest' if policy.adventure and ('NPC' in policy.mode or 'задани' in policy.mode or 'поручен' in policy.mode) else 'hunt'
            if policy.equipment.confirmed>seen_equips:social.event('equipment',now)
            if policy.skills and policy.skills.confirmed>seen_skills:social.event('skill',now)
            if policy.adventure and policy.adventure.delivered>seen_quests:social.event('quest_done',now)
            seen_equips=policy.equipment.confirmed
            seen_skills=policy.skills.confirmed if policy.skills else 0
            seen_quests=policy.adventure.delivered if policy.adventure else 0
            social.tick(now, policy.resting, alive and now-policy.started >= 3)
            if now>=next_snapshot:
                snapshot(now)
                next_snapshot=now+15
            if time.monotonic()-client.wire.last_send > 2:
                client.wire.heartbeat()
    finally:
        report.result['hunt'] = policy.summary()
        report.result['progression'] = progression.summary()
        report.result['chat'] = social.summary()
        report.result['equipment']=policy.equipment.summary()
        report.result['recovery']=policy.recovery.summary()
        if policy.skills:report.result['skills']=policy.skills.summary()
        if policy.adventure:
            report.result['adventure'] = policy.adventure.summary()
            report.result['adventure']['quest_loot_requests'] = policy.loot.requests
        policy.drop_target()
        policy.clear_zone()
        client.world_handler = None
