"""Spend earned attribute points through the classic client command, with confirmation."""
import struct

AP, STR, CON, LV, XP = 6, 25, 28, 0, 15
# Conservative class-specific tendencies; only earned points are requested.
BUILDS={8:{25:1,28:1},9:{25:2,27:1,28:1},12:{26:3,27:1,28:1},
        13:{29:3,28:1},14:{26:2,29:1,28:2},16:{28:3,29:1}}


def attribute_request(attribute, value):
    if attribute not in range(25, 31) or not 0 < value < 0x7fffffff:
        raise ValueError('Invalid base attribute request')
    return b'\x01' + struct.pack('>HI', attribute, value)


class Progression:
    def __init__(self, world, send, first_job=1):
        self.world, self.send = world, send
        self.first_job = first_job
        self.target_job = None
        self.pending = None
        self.disabled = False
        self.confirmed = self.requests = 0
        self.start_level = world.own.values.get(LV)
        self.start_xp = world.own.values.get(XP)
        self.next_action = 0

    def tick(self, now, safe):
        values = self.world.own.values
        if self.pending:
            attribute, target, points_before, deadline = self.pending
            # Both the requested value and point deduction must come from the server.
            if values.get(attribute,0) >= target and values.get(AP, points_before) < points_before:
                self.confirmed += 1
                self.pending = None
                self.next_action = now + 2
            elif now >= deadline:
                self.pending = None
                self.disabled = True
                self.next_action=now+300  # Retry later with real server values, never permanently freeze.
            return
        if not safe or now < self.next_action:return
        if self.disabled:self.disabled=False
        points = values.get(AP, 0)
        primary = {1:25,2:26,4:29,5:29}.get(self.first_job)
        compatible = {1:(1,2),2:(1,3),4:(1,3,4),5:(3,4)}.get(self.first_job,())
        strength, constitution = values.get(primary), values.get(CON)
        # Only the pinned first-profession build; no guesses for advanced classes.
        if (not 0 < points <= 10000 or strength is None or constitution is None
                or self.world.own.model not in compatible or values.get(4) not in ({0, self.first_job} | ({self.target_job} if self.target_job else set()))):
            return
        # Maintain a 2:1 primary:CON tendency using authoritative current values.
        weights=BUILDS.get(self.target_job)
        if weights and all(values.get(attr) is not None for attr in weights):
            attribute=min(weights,key=lambda attr:values[attr]/weights[attr])
        else:
            attribute = CON if strength > constitution * 2 else primary
        target = values[attribute] + 1
        self.send(8, attribute_request(attribute, 1))  # Server expects an INCREMENT, not the desired total.
        self.requests += 1
        self.pending = attribute, target, points, now + 10

    def summary(self):
        values = self.world.own.values
        return {'target_class_build':self.target_job,'attribute_weights':BUILDS.get(self.target_job), 'first_job_build': self.first_job, 'start_level': self.start_level, 'level': values.get(LV),
                'start_experience': self.start_xp, 'experience': values.get(XP),
                'free_attribute_points': values.get(AP), 'attribute_requests': self.requests,
                'confirmed_point_spends': self.confirmed, 'awaiting_confirmation': bool(self.pending),
                'allocation_paused': self.disabled}
