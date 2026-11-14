"""Bounded world packets for the supplied 2008 GameServer, not modern layouts."""
import struct
import time
import math
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


def skip_look(reader, equipment=None):
    synchronization, model, boat = reader.byte(), reader.short(), reader.byte()
    if synchronization not in (0, 1) or boat not in (0, 1):
        raise ProtocolError('Unsupported classic appearance')
    if boat:
        reader.take(14)
        return model
    reader.short()  # hair
    if equipment is not None:
        equipment.clear()
    # Native WriteLookData 0x4e5d60 uses TEN slots, no modern DBID/level fields.
    for slot in range(10):
        item = reader.short()
        if not item:
            continue
        if equipment is not None:
            equipment[slot] = item
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
    equipment: dict = field(default_factory=dict)
    stall: str = ''

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
    stall = reader.string()  # NO modern guild-permission long
    state = reader.short()
    x, y, radius = reader.long(), reader.long(), reader.long()
    reader.short()  # angle
    reader.long()  # team leader; NO modern is-player byte
    reader.byte()  # side
    reader.long()  # event world ID
    reader.byte()  # event object type
    reader.short()  # event ID
    reader.string_bytes()
    equipment = {}
    skip_look(reader, equipment)
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
    return Entity(model, identity, handle, control, state, x, y, radius, name=name, equipment=equipment, stall=stall)


class World:
    def __init__(self, item_types=None):
        self.entities = {}
        self.items = {}
        self.own_id = None
        self.map = None
        self.default_skill = None
        self.updates = 0
        self.damage_events = 0
        self.failed_actions = 0
        self.last_failed_action=None
        self.failed_action_counts={};self.default_skill_updates=0;self.stop_revision=0;self.stop_packet_number=None;self.skill_action_state=None
        self.decode_info = {}
        self.item_types = item_types or {}
        self.bag = {}
        self.bag_ready = self.bag_disabled = False
        self.bag_capacity = None
        self.motion = {}
        self.move_revision = 0
        self.move_state = 0
        self.move_packet_number = None
        self.stop_packet_kind = None
        self.skill_packet_number = None
        self.skill_revision = 0
        self.own_hits = {}
        self.look_revision = 0
        self.skills = {}
        self.seated=False;self.pose_packet_number=None;self.pose_revision=0

    def position(self, now=None, identity=None):
        """Bounded prediction along the SERVER's route; raw x/y remain authoritative."""
        identity = self.own_id if identity is None else identity
        actor = self.entities.get(identity)
        if actor is None:
            return None
        moving = self.motion.get(identity)
        if not moving:
            return actor.position
        points, started, speed = moving
        remaining = max(0,(time.monotonic() if now is None else now)-started)*speed
        for a,b in zip(points,points[1:]):
            length=math.dist(a,b)
            if length and remaining<length:
                ratio=remaining/length
                return round(a[0]+(b[0]-a[0])*ratio),round(a[1]+(b[1]-a[1])*ratio)
            remaining-=length
        return points[-1]

    def freeze_prediction(self, now):
        point = self.position(now)
        if point:
            self.motion[self.own_id] = ([point],now,0)

    def read_skills(self, reader):
        self.default_skill=reader.short()
        sync,count=reader.byte(),reader.short()
        if count>256:raise ProtocolError('Too many skills')
        if sync==0:self.skills={}
        for _ in range(count):
            identity,state,level=reader.short(),reader.byte(),reader.byte()
            sp,endurance,energy=reader.short(),reader.short(),reader.short()
            interval=reader.long()
            if reader.short():reader.take(6)
            if level:self.skills[identity]={'level':level,'state':state,'sp':sp,'interval_ms':interval}
            else:self.skills.pop(identity,None)
        self.decode_info['skill_count']=count

    def read_bag(self, reader):
        if self.bag_disabled:
            return
        from inventory import kitbag
        try:
            sync,capacity,changes=kitbag(reader,self.item_types)
            if sync==0:
                self.bag={}
                self.bag_capacity=capacity
                self.bag_ready=True
            for slot,item in changes.items():
                if self.bag_capacity is not None and slot>=self.bag_capacity:
                    raise ProtocolError('Bag slot exceeds capacity')
                if item is None:self.bag.pop(slot,None)
                else:self.bag[slot]=item
        except ProtocolError:
            self.bag_disabled=True
            self.decode_info['inventory']='unsupported_packet'

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
        self.read_skills(reader)
        default_skill=self.default_skill
        self.decode_info.update(phase='skill_states',offset=reader.position)
        state_count = reader.byte()
        self.decode_info['skill_state_count'] = state_count
        reader.take(state_count * 2)  # classic state count + (ID,level); no timestamps
        self.decode_info.update(phase='attributes',offset=reader.position)
        own.values = attrs(reader)
        if not 0 < own.values.get(MAX_HP, 0) < 2000000000 or not 0 < own.values.get(LV, 0) < 2000:
            raise ProtocolError('Initial health/level could not be decoded')
        self.seated=False;self.pose_packet_number=None;self.pose_revision+=1
        self.motion.clear()
        self.own_hits.clear()
        self.items.clear()
        self.move_revision += 1
        self.move_state = 1
        self.bag = {}
        self.bag_ready = self.bag_disabled = False
        self.bag_capacity = None
        self.entities = {own.identity: own}
        self.own_id, self.map, self.default_skill = own.identity, map_name, default_skill
        self.decode_info.update(phase='complete',offset=reader.position,attribute_count=len(own.values))
        if reader.position < len(reader.data):
            self.read_bag(reader)

    def observe(self, command, payload):
        reader = Reader(payload)
        if command == 506:
            identity,handle,model = reader.long(),reader.long(),reader.long()
            position = reader.long(),reader.long()
            reader.short()  # angle
            count,kind,source = reader.short(),reader.byte(),reader.long()
            if not count or kind not in (0,1,2) or not all(0<=v<409600 for v in position):
                raise ProtocolError('Invalid classic item appearance')
            if len(self.items)<1024 or identity in self.items:
                self.items[identity] = (model,handle,position,kind,source,time.monotonic())
        elif command == 507:
            self.items.pop(reader.long(),None)
        elif command == 504:
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
                self.motion.pop(seen.identity,None)
                self.entities[seen.identity] = seen
        elif command == 505:
            reader.byte()
            identity = reader.long()
            if identity != self.own_id:
                self.entities.pop(identity, None)
                self.motion.pop(identity,None)
        elif command == 509:
            identity = reader.long()
            values = attrs(reader)
            if identity in self.entities:
                self.entities[identity].values.update(values)
                if values.get(HP,1)<=0 and identity in self.own_hits:
                    self.own_hits[identity]=(self.own_hits[identity][0],True)
        elif command == 510:
            identity=reader.long()
            if identity==self.own_id:
                self.read_skills(reader);reader.end();self.default_skill_updates+=1
        elif command == 531:
            identity,skill=reader.long(),reader.short();reader.end()
            if identity==self.own_id:self.default_skill=skill;self.default_skill_updates+=1
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
                    route=list(struct.iter_unpack('<ii',points))
                    if any(not 0<=v<409600 for point in route for v in point):
                        raise ProtocolError('Invalid server movement route')
                    stamp=time.monotonic()
                    self.motion[identity]=(route if not state else [route[-1]],stamp,
                                           max(1,min(current.values.get(SPEED,480),3000)))
                    if identity==self.own_id:
                        self.move_revision+=1
                        self.move_state=state
                        self.move_packet_number=packet_id
                        if state:
                            self.stop_revision+=1;self.stop_packet_number=packet_id;self.stop_packet_kind=1
                    current.x, current.y = x, y
                    if stop is not None:
                        current.state = stop
                    current.seen_at = time.monotonic()
            elif action == 21:
                angle,pose=reader.short(),reader.short();reader.end()
                if identity==self.own_id:
                    self.seated=pose==16;self.pose_packet_number=packet_id;self.pose_revision+=1
            elif action == 3:
                reader.byte();reader.short();state=reader.short()
                if state:reader.short()
                if identity==self.own_id:
                    self.skill_action_state=state
                    self.skill_packet_number=packet_id
                    self.skill_revision+=1
                    if state:
                        self.stop_revision+=1;self.stop_packet_number=packet_id;self.stop_packet_kind=3
            elif action == 4:
                reader.byte()  # fight ID
                state = reader.short()
                reader.take(2)  # critical, miss
                if reader.byte():
                    x, y = reader.long(), reader.long()
                    if current:
                        current.x, current.y = x, y
                        self.motion.pop(identity,None)
                source=reader.long()
                reader.take(20)  # source position, skill, two target fields
                reader.short()  # effect time
                values = attrs(reader)
                if current:
                    before=current.values.get(HP)
                    current.values.update(values)
                    if (source==self.own_id and current.control==5 and before is not None
                            and HP in values and values[HP]<before):
                        self.own_hits[identity]=(time.monotonic(),values[HP]<=0 or bool(state & 0x100))
                        if len(self.own_hits)>128:self.own_hits.pop(next(iter(self.own_hits)))
                    if (values.get(HP,1)<=0 or state & 0x100) and identity in self.own_hits:
                        self.own_hits[identity]=(self.own_hits[identity][0],True)
                    if state & 0x100:
                        current.state = 7
                self.damage_events += 1
            elif action == 5 and current:
                skip_look(reader,current.equipment)
                if identity==self.own_id:self.look_revision+=1
            elif action == 7 and identity==self.own_id:
                self.read_skills(reader)
            elif action == 6 and identity==self.own_id:
                self.read_bag(reader)
        elif command == 520:
            self.failed_actions += 1
            if len(payload)==6:
                self.last_failed_action={'actor':reader.long(),'action':reader.byte(),'reason':reader.byte()}
                key=str(self.last_failed_action['action'])+':'+str(self.last_failed_action['reason'])
                self.failed_action_counts[key]=self.failed_action_counts.get(key,0)+1

        self.updates += 1

    def summary(self):
        own = self.own
        return {'map': self.map, 'profession':own.values.get(4) if own else None, 'entities': len(self.entities),
                'monsters': sum(e.control == 5 for e in self.entities.values()),
                'position': list(own.position) if own else None,
                'hp': own.values.get(HP) if own else None,
                'max_hp': own.values.get(MAX_HP) if own else None,
                'existence_state':own.state if own else None,
                'level': own.values.get(LV) if own else None,
                'default_skill': self.default_skill, 'updates': self.updates,
                'damage_events': self.damage_events, 'failed_actions': self.failed_actions,'last_failed_action':self.last_failed_action,'failed_action_counts':self.failed_action_counts,'default_skill_updates':self.default_skill_updates,'stop_revision':self.stop_revision,'skill_action_state':self.skill_action_state}
