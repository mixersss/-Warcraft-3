"""Local situational speech; no external AI, transcripts, or player-name logging."""
from collections import deque, OrderedDict
import random
import re
import threading
from classic_wire import sequence


def say_request(text):
    encoded = text.encode('cp1251')
    if not encoded or len(encoded) > 120 or any(ord(c) < 32 for c in text):
        raise ValueError('Invalid local chat message')
    return sequence(encoded + b'\0')


class ChatBudget:
    """Shared by every bot in this process, including eventual larger populations."""
    def __init__(self):
        self.next_send = 0
        self.lock = threading.Lock()

    def claim(self, now):
        with self.lock:
            if now < self.next_send:
                return False
            self.next_send = now + 15
            return True


PHRASES = {
    'level': ('Новый уровень :)', 'Ещё уровень, потихоньку расту.'),
    'rest': ('Передохну немного.', 'Отойду, надо восстановиться.'),
    'hunt': ('Пойду ещё поохочусь.', 'Пока побью улиток рядом с Аргентом.'),
}


class Social:
    def __init__(self, world, send, name, budget, seed):
        self.world, self.send, self.name, self.budget = world, send, name, budget
        self.rng = random.Random(str(seed) + ':chat')
        self.next_send = 0
        self.next_situation = None
        self.pending = None
        self.replied = OrderedDict()
        self.sent = self.replies = 0
        self.level = world.own.values.get(0)
        self.resting = False

    def visible_humans(self):
        return [e for e in self.world.entities.values() if e.control == 1
                and e.identity != self.world.own_id and e.name and not e.name.lower().startswith('bot')]

    def hear(self, source, text, now):
        if source not in {e.identity for e in self.visible_humans()} or self.pending:
            return
        if len(text) > 240 or any(ord(c) < 32 for c in text):
            return
        words = re.findall(r'[\w]+', text.casefold())
        if self.name.casefold() not in words or self.replied.get(source, 0) > now:
            return  # No broadcast greetings or bot-to-bot reply loops.
        if any(w in words for w in ('привет', 'здравствуй', 'ку', 'hello', 'hi')):
            reply = self.rng.choice(('Привет :)', 'Привет, удачной охоты!'))
        elif 'бот' in words or 'bot' in words:
            reply = 'Да, я местный игровой бот :)'
        elif any(w in words for w in ('уровень', 'лвл', 'level')):
            reply = f'Сейчас у меня {self.world.own.values.get(0, 1)} уровень.'
        elif any(w in words for w in ('делаешь', 'занят', 'охотишься')):
            reply = 'Охочусь возле Аргента, пока учусь.'
        elif 'спасибо' in words:
            reply = 'Удачи :)'
        else:
            return
        self.pending = (source, reply, now + self.rng.uniform(2, 5), now + 20)

    def tick(self, now, resting, safe):
        if self.next_situation is None:
            self.next_situation = now + self.rng.uniform(90, 180)
        humans = self.visible_humans()
        level = self.world.own.values.get(0)
        event = 'level' if level and self.level and level > self.level else ('rest' if resting else 'hunt')
        self.level, self.resting = level, resting
        if self.pending:
            source, text, due, expires = self.pending
            if now > expires or source not in {e.identity for e in humans}:
                self.pending = None
            elif safe and now >= due and now >= self.next_send and self.budget.claim(now):
                self.send(1, say_request(text))
                self.sent += 1
                self.replies += 1
                self.pending = None
                self.next_send = now + 90
                self.replied[source] = now + 300
                self.replied.move_to_end(source)
                while len(self.replied) > 128:
                    self.replied.popitem(last=False)
            return
        if safe and humans and now >= self.next_send and now >= self.next_situation:
            if self.budget.claim(now):
                self.send(1, say_request(self.rng.choice(PHRASES[event])))
                self.sent += 1
                self.next_send = now + 90
                self.next_situation = now + self.rng.uniform(180, 360)

    def summary(self):
        return {'messages_sent': self.sent, 'simple_replies_sent': self.replies,
                'external_ai': False}
