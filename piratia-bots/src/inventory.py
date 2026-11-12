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
    parameters: tuple = (0,0)
    instance_attributes: tuple = ()


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
        parameters=(reader.long(),reader.long())  # Native forge/instance parameters.
        instance=reader.byte()
        if instance not in (0,1):raise ProtocolError('Invalid item instance flag')
        instance_attributes=tuple((reader.short(),reader.short()) for _ in range(5)) if instance else ()
        changed[slot]=BagItem(identity,count,endurance,max_endurance,energy,max_energy,forge,bool(valid),parameters,instance_attributes)
    raise ProtocolError('Too many kitbag entries')
