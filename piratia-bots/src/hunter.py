"""First bounded PvE policy: passive weak mobs, normal attack, retreat and rest."""
import math
import struct
import time
from classic_wire import sequence
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
    def __init__(self, world, navigation, send, report, tell=print):
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

    def change(self, value):
        if self.mode != value:
            self.mode = value
            self.tell('Состояние бота: ' + value)

    def emit(self, body):
        self.send(6, body)
        self.sequence = (self.sequence + 1) & 0xffffffff

    def move_to(self, goal, now):
        own = self.world.own
        path = self.nav.path(own.position, goal)
        if len(path) < 2:
            return False
        # At most six metres per request; every cell is checked against map obstacles.
        points, travelled = [path[0]], 0
        for point in path[1:7]:
            step = distance(points[-1],point)
            if travelled+step > 600 and len(points) >= 2:
                break
            points.append(point)
            travelled += step
        self.emit(movement(own.identity, self.sequence, points))
        self.moves += 1
        self.next_action = now + 2.5
        if distance(own.position, self.last_position) < 40:
            self.stuck += 1
        else:
            self.stuck = 0
        self.last_position = own.position
        return True

    def eligible(self, entity, now):
        own = self.world.own
        # Only the two passive beginner species from this server's CharacterInfo.
        return (entity.control == 5 and entity.model in (71, 75) and entity.alive
                and 0 < entity.values.get(LV, 9999) <= min(2, own.values[LV]+1)
                and entity.handle != 0 and distance(entity.position, self.home) <= 22000
                and self.blacklist.get(entity.identity, 0) < now)

    def tick(self, now=None):
        now = time.monotonic() if now is None else now
        own = self.world.own
        if not own or self.world.map != 'garner' or not self.nav.free(self.nav.cell(own.position)):
            self.change('ожидание достоверных данных карты')
            return
        hp, maximum = own.values.get(HP), own.values.get(MAX_HP)
        if hp is None or not maximum:
            self.change('ожидание данных здоровья')
            return
        if hp <= 0 or own.state >= 5:
            self.change('персонаж погиб; требуется обычное возрождение')
            return
        if hp / maximum <= .35:
            if not self.resting:
                self.cancel_pending = True
            self.resting = True
            self.target = None
        if self.resting:
            if hp / maximum >= .85:
                self.resting = False
            else:
                self.change('отступление и восстановление')
                if self.cancel_pending:
                    self.emit(movement(own.identity,self.sequence,[own.position,own.position]))
                    self.cancel_pending = False
                    self.moves += 1
                    self.next_action = now+1
                if now >= self.next_action and distance(own.position, self.home) > 300:
                    self.move_to(self.home, now)
                return
        if now < self.next_action or now-self.started < 2:
            return
        if self.stuck >= 5:
            self.change('путь заблокирован; остановка движения')
            return
        target = self.world.entities.get(self.target)
        if self.target and (not target or not target.alive):
            if target and target.values.get(HP, 1) <= 0:
                self.kills += 1  # Observed target death, not proof of kill credit.
            self.target = None
            target = None
        if target and (not self.eligible(target, now) or now-self.target_since > 35):
            self.blacklist[target.identity] = now+45
            self.target = None
            target = None
        if not target:
            candidates = sorted((e for e in self.world.entities.values() if self.eligible(e, now)),
                                key=lambda e: distance(own.position, e.position))
            for candidate in candidates:
                if self.nav.path(own.position, candidate.position):
                    target = candidate
                    self.target, self.target_since = target.identity, now
                    break
        if target:
            reach = max(100, min(own.values.get(ATTACK_DISTANCE, 150), 250)) + own.radius + target.radius
            if distance(own.position, target.position) > reach:
                self.change('подход к слабому мобу')
                if not self.move_to(target.position, now):
                    self.blacklist[target.identity] = now+45
                    self.target = None
                return
            if not self.world.default_skill:
                self.change('ожидание обычной атаки от сервера')
                return
            self.change('обычная атака')
            self.fight = (self.fight+1) & 255
            self.emit(normal_attack(own.identity, self.sequence, self.fight, self.world.default_skill,
                                    target.identity, target.handle, own.position))
            self.attacks += 1
            self.next_action = now+2  # no spam or attack-speed override
            return
        self.change('поиск мобов у Аргента')
        goal = self.nav.waypoints[self.waypoint % len(self.nav.waypoints)]
        if distance(own.position, goal) < 300 or not self.move_to(goal, now):
            self.waypoint += 1
            self.next_action = now+2

    def summary(self):
        return {'state': self.mode, 'move_requests': self.moves, 'attack_requests': self.attacks,
                'observed_target_deaths': self.kills, 'world': self.world.summary()}


def hunt(client, seconds, stop, report, navigation, tell=print):
    report.stage('reading_world')
    world = World()
    world.enter(client.enter_payload)
    policy = Hunter(world, navigation, client.wire.send, report, tell)
    client.world_handler = world.observe
    try:
        while client.pending_world:
            world.observe(*client.pending_world.popleft())
        report.stage('hunting')
        tell(f'Данные мира: {world.map}, координаты {world.own.x//100},{world.own.y//100}, '
             f'здоровье {world.own.values[HP]}/{world.own.values[MAX_HP]}.')
        deadline = time.monotonic()+seconds
        while time.monotonic() < deadline and not stop.is_set():
            try:
                command, payload = client.wire.receive(min(deadline, time.monotonic()+.25))
                client.service(command, payload)
            except TimeoutError:
                pass
            policy.tick()
            if time.monotonic()-client.wire.last_send > 2:
                client.wire.heartbeat()
    finally:
        report.result['hunt'] = policy.summary()
        client.world_handler = None
