"""Spend earned attribute points through the classic client command, with confirmation."""
import struct

AP, STR, CON, LV, XP = 6, 25, 28, 0, 15


def attribute_request(attribute, value):
    if attribute not in range(25, 31) or not 0 < value < 0x7fffffff:
        raise ValueError('Invalid base attribute request')
    return b'\x01' + struct.pack('>HI', attribute, value)


class Progression:
    def __init__(self, world, send):
        self.world, self.send = world, send
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
            if values.get(attribute) == target and values.get(AP, points_before) < points_before:
                self.confirmed += 1
                self.pending = None
                self.next_action = now + 2
            elif now >= deadline:
                self.pending = None
                self.disabled = True  # Refusal/unknown response must not trigger a retry storm.
            return
        if self.disabled or not safe or now < self.next_action:
            return
        points = values.get(AP, 0)
        strength, constitution = values.get(STR), values.get(CON)
        # Alpha09 remains a beginner Lance melee hunter; do not guess builds for other jobs.
        if (not 0 < points <= 10000 or strength is None or constitution is None
                or self.world.own.model != 1 or values.get(4) != 0):
            return
        # Maintain a 2:1 STR:CON investment tendency using authoritative current values.
        attribute = CON if strength > constitution * 2 else STR
        target = values[attribute] + 1
        self.send(8, attribute_request(attribute, target))
        self.requests += 1
        self.pending = attribute, target, points, now + 10

    def summary(self):
        values = self.world.own.values
        return {'start_level': self.start_level, 'level': values.get(LV),
                'start_experience': self.start_xp, 'experience': values.get(XP),
                'free_attribute_points': values.get(AP), 'attribute_requests': self.requests,
                'confirmed_point_spends': self.confirmed, 'awaiting_confirmation': bool(self.pending),
                'allocation_paused': self.disabled}
