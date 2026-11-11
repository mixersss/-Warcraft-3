"""Classic 2008 kitbag codec; no modern DBID, expiration or tradable fields."""
from dataclasses import dataclass
from classic_wire import ProtocolError


@dataclass(frozen=True)
class BagItem:
    identity: int
    count: int
    endurance: int
    max_endurance: int
    energy: int
    max_energy: int
    forge: int
    valid: bool


def kitbag(reader, item_types):
    synchronization=reader.byte()
    if synchronization>32:raise ProtocolError('Unknown kitbag synchronization')
    capacity=reader.short() if synchronization==0 else None
    if capacity is not None and not 1<=capacity<=256:raise ProtocolError('Invalid kitbag capacity')
    changed={}
    for _ in range(257):
        slot=reader.short()
        if slot==65535:return synchronization,capacity,changed
        if slot>255 or slot in changed:raise ProtocolError('Invalid kitbag slot')
        identity=reader.short()
        if not identity:
            changed[slot]=None;continue
        count,endurance,max_endurance,energy,max_energy=[reader.short() for _ in range(5)]
        forge,valid=reader.byte(),reader.byte()
        if not count or valid not in (0,1):raise ProtocolError('Invalid classic bag item')
        kind=item_types.get(identity)
        if kind is None:raise ProtocolError('Unknown item type; inventory actions paused')
        if kind==43:reader.long()  # Boat owner/world ID, only for boat deeds.
        reader.take(8)  # Two item DB parameters, not modern item DBID/expiry.
        instance=reader.byte()
        if instance not in (0,1):raise ProtocolError('Invalid item instance flag')
        if instance:reader.take(20)  # Exactly five (u16 ID,u16 value) pairs.
        changed[slot]=BagItem(identity,count,endurance,max_endurance,energy,max_energy,forge,bool(valid))
    raise ProtocolError('Too many kitbag entries')
