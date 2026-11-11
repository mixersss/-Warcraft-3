"""Bounded world packets for the supplied 2008 GameServer, not modern layouts."""
import struct
import time
from dataclasses import dataclass, field
from classic_wire import Reader, ProtocolError

LV, HP, MAX_HP, ATTACK_DISTANCE, SPEED = 0, 1, 31, 43, 44


def signed(value):
    return value if value < 0x80000000 else value - 0x100000000


def attrs(reader):
    reader.byte()  # synchronization reason
    count = reader.short()
    if count > 256:
        raise ProtocolError('Too many world attributes')
    result = {}
    for _ in range(count):
        index, value = reader.byte(), signed(reader.long())
        if index in result:
            raise ProtocolError('Duplicate world attribute')
        result[index] = value
    return result


def skip_look(reader):
    synchronization, model, boat = reader.byte(), reader.short(), reader.byte()
    if synchronization not in (0, 1) or boat not in (0, 1):
        raise ProtocolError('Unsupported classic appearance')
    if boat:
        reader.take(14)
        return model
    reader.short()  # hair
    # Native WriteLookData 0x4e5d60 uses TEN slots, no modern DBID/level fields.
    for _ in range(10):
        item = reader.short()
        if not item:
            continue
        if synchronization == 1:
            reader.take(5)  # current endurance/energy, valid
            continue
        reader.take(12)  # count, endurance pair, energy pair, forge, valid
        detail = reader.byte()
        if detail not in (0, 1):
            raise ProtocolError('Invalid appearance detail flag')
        if detail:
            reader.take(8)  # forge and instance parameters
            instance = reader.byte()
            if instance not in (0, 1):
                raise ProtocolError('Invalid instance flag')
            if instance:
                reader.take(20)  # FIVE attribute pairs in this classic build
    return model


@dataclass
class Entity:
    model: int
    identity: int
    handle: int
    control: int
    state: int
    x: int
    y: int
    radius: int
    values: dict = field(default_factory=dict)
    seen_at: float = field(default_factory=time.monotonic)
    name: str = ''  # Transient for addressed chat; never included in reports.

    @property
    def position(self):
        return self.x, self.y

    @property
    def alive(self):
        return self.state < 5 and self.values.get(HP, 0) > 0


def entity(reader):
    model, identity = reader.long(), reader.long()
    reader.long()  # main character's communication ID
    reader.string_bytes()  # names deliberately not retained in world reports
    reader.byte()  # GM level
    handle, control = reader.long(), reader.byte()
    name = reader.string()
    reader.string_bytes()
    reader.short()  # icon
    reader.long()  # guild ID
    reader.string_bytes()
    reader.string_bytes()
    reader.string_bytes()  # stall; NO modern guild-permission long
    state = reader.short()
    x, y, radius = reader.long(), reader.long(), reader.long()
    reader.short()  # angle
    reader.long()  # team leader; NO modern is-player byte
    reader.byte()  # side
    reader.long()  # event world ID
    reader.byte()  # event object type
    reader.short()  # event ID
    reader.string_bytes()
    skip_look(reader)
    reader.byte()  # PK control
    # Append-look is a separate FOUR-slot block (defESPE_KBGRID_NUM), not
    # the ten normal equipment slots consumed by skip_look above.
    for _ in range(4):
        if reader.short():
            reader.byte()
    if not identity or not 0 < model < 100000 or control not in (0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 17):
        raise ProtocolError('Unrecognized classic entity fields')
    if not 0 <= x < 409600 or not 0 <= y < 409600 or radius > 2000 or state > 16:
        raise ProtocolError('Unrecognized classic position/state')
    return Entity(model, identity, handle, control, state, x, y, radius, name=name)


class World:
    def __init__(self):
        self.entities = {}
        self.own_id = None
        self.map = None
        self.default_skill = None
        self.updates = 0
        self.damage_events = 0
        self.failed_actions = 0
        self.decode_info = {}

    @property
    def own(self):
        return self.entities.get(self.own_id)

    def enter(self, payload):
        reader = Reader(payload)
        self.decode_info = {'phase':'entry_header', 'packet_bytes':len(payload)}
        if reader.short():
            raise ProtocolError('Map entry refused')
        reader.take(4)  # auto-lock, bag-lock, enter type, new character
        map_name = reader.string()
        reader.byte()  # can team; NO modern IMP uint32
        self.decode_info.update(phase='entity',offset=reader.position)
        own = entity(reader)
        if own.control != 1:
            raise ProtocolError('Expected the main player character')
        self.decode_info.update(phase='skills',offset=reader.position,append_look_slots=4)
        default_skill = reader.short()
        reader.byte()
        count = reader.short()
        if count > 256:
            raise ProtocolError('Too many initial skills')
        self.decode_info['skill_count'] = count
        for _ in range(count):
            reader.take(14)
            if reader.short():
                reader.take(6)  # range[1..3], not modern extended ranges
        self.decode_info.update(phase='skill_states',offset=reader.position)
        state_count = reader.byte()
        self.decode_info['skill_state_count'] = state_count
        reader.take(state_count * 2)  # classic state count + (ID,level); no timestamps
        self.decode_info.update(phase='attributes',offset=reader.position)
        own.values = attrs(reader)
        if not 0 < own.values.get(MAX_HP, 0) < 2000000000 or not 0 < own.values.get(LV, 0) < 2000:
            raise ProtocolError('Initial health/level could not be decoded')
        # Inventory/shortcuts/boats follow; this prototype does not manipulate them.
        self.entities = {own.identity: own}
        self.own_id, self.map, self.default_skill = own.identity, map_name, default_skill
        self.decode_info.update(phase='complete',offset=reader.position,attribute_count=len(own.values))

    def observe(self, command, payload):
        reader = Reader(payload)
        if command == 504:
            reader.byte()
            seen = entity(reader)
            reader.take(2)  # NPC show flags
            pose = reader.short()
            if pose == 1:
                reader.take(21)
            elif pose == 2:
                reader.take(4)
            seen.values = attrs(reader)
            if len(self.entities) < 2048 or seen.identity in self.entities:
                self.entities[seen.identity] = seen
        elif command == 505:
            reader.byte()
            identity = reader.long()
            if identity != self.own_id:
                self.entities.pop(identity, None)
        elif command == 509:
            identity = reader.long()
            values = attrs(reader)
            if identity in self.entities:
                self.entities[identity].values.update(values)
        elif command == 508:
            identity, packet_id, action = reader.long(), reader.long(), reader.byte()
            current = self.entities.get(identity)
            if action == 1:
                state = reader.short()
                stop = reader.short() if state else None
                points = reader.sequence()
                if not points or len(points) % 8 or len(points) > 256:
                    raise ProtocolError('Invalid classic movement points')
                # The FIRST point is the server's current position. The rest are a route.
                x, y = struct.unpack_from('<ii', points)
                if not 0 <= x < 409600 or not 0 <= y < 409600:
                    raise ProtocolError('Invalid authoritative movement position')
                if current:
                    current.x, current.y = x, y
                    if stop is not None:
                        current.state = stop
                    current.seen_at = time.monotonic()
            elif action == 4:
                reader.byte()  # fight ID
                state = reader.short()
                reader.take(2)  # critical, miss
                if reader.byte():
                    x, y = reader.long(), reader.long()
                    if current:
                        current.x, current.y = x, y
                reader.take(24)  # source, source position, skill, two target fields
                reader.short()  # effect time
                values = attrs(reader)
                if current:
                    current.values.update(values)
                    if state & 0x100:
                        current.state = 7
                self.damage_events += 1
        elif command == 520:
            self.failed_actions += 1
        self.updates += 1

    def summary(self):
        own = self.own
        return {'map': self.map, 'entities': len(self.entities),
                'monsters': sum(e.control == 5 for e in self.entities.values()),
                'position': list(own.position) if own else None,
                'hp': own.values.get(HP) if own else None,
                'max_hp': own.values.get(MAX_HP) if own else None,
                'level': own.values.get(LV) if own else None,
                'default_skill': self.default_skill, 'updates': self.updates,
                'damage_events': self.damage_events, 'failed_actions': self.failed_actions}
