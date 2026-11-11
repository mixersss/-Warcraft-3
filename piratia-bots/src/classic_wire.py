"""Bounded classic PKO packets. Header and payload byte order are big endian."""
import socket
import struct
import time


class ProtocolError(Exception):
    pass


def sequence(value):
    if len(value) > 65535:
        raise ProtocolError('Field is too long')
    return struct.pack('>H', len(value)) + value


def string(value):
    if isinstance(value, str):
        value = value.encode('cp1251')
    if b'\0' in value:
        raise ProtocolError('Embedded NUL in string')
    return sequence(value + b'\0')


class Reader:
    def __init__(self, data):
        self.data, self.position = bytes(data), 0

    def take(self, count):
        if count < 0 or self.position + count > len(self.data):
            raise ProtocolError('Truncated packet')
        out = self.data[self.position:self.position + count]
        self.position += count
        return out

    def byte(self):
        return self.take(1)[0]

    def short(self):
        return struct.unpack('>H', self.take(2))[0]

    def long(self):
        return struct.unpack('>I', self.take(4))[0]

    def sequence(self):
        return self.take(self.short())

    def string_bytes(self):
        value = self.sequence()
        if not value.endswith(b'\0'):
            raise ProtocolError('Unterminated string')
        return value[:-1]

    def string(self):
        return self.string_bytes().decode('cp1251', errors='replace')

    def end(self):
        if self.position != len(self.data):
            raise ProtocolError('Unexpected trailing fields')


class Wire:
    def __init__(self, sock, report=None):
        self.sock = sock
        self.buffer = bytearray()
        self.header_size = None
        self.in_cipher = self.out_cipher = None
        self.report = report or (lambda *args: None)
        self.last_send = time.monotonic()

    def frame(self, deadline):
        while True:
            if len(self.buffer) >= 2:
                size = int.from_bytes(self.buffer[:2], 'big')
                if size != 2 and not 4 <= size <= 65535:
                    raise ProtocolError('Invalid frame length')
                if len(self.buffer) >= size:
                    result = bytes(self.buffer[2:size])
                    del self.buffer[:size]
                    return result
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Timed out waiting for a complete packet')
            self.sock.settimeout(remaining)
            try:
                data = self.sock.recv(65536)
            except socket.timeout as exc:
                raise TimeoutError('Timed out waiting for server') from exc
            if not data:
                raise ConnectionError('Server closed connection')
            self.buffer.extend(data)

    def receive(self, deadline):
        while True:
            frame = self.frame(deadline)
            if not frame:  # SDK keepalive: length=2, no RPC or command.
                continue
            if self.header_size is None:
                # Detect RPC header using the known plaintext challenge opcode.
                if len(frame) >= 6 and frame[4:6] == b'\x03\xac':
                    self.header_size = 6
                elif frame[:2] == b'\x03\xac':
                    self.header_size = 2
                else:
                    raise ProtocolError('Expected classic CHAP challenge (940)')
            body = frame[self.header_size - 2:]
            if self.in_cipher:
                body = self.in_cipher.decrypt(body)
            if len(body) < 2:
                raise ProtocolError('Missing command')
            command = int.from_bytes(body[:2], 'big')
            self.report('receive', command, len(body) - 2)
            return command, body[2:]

    def send(self, command, payload=b''):
        if self.header_size is None:
            raise ProtocolError('No server handshake yet')
        body = struct.pack('>H', command) + payload
        if self.out_cipher:
            body = self.out_cipher.encrypt(body)
        rpc = b'\x80\0\0\0' if self.header_size == 6 else b''
        packet = rpc + body
        if len(packet) + 2 > 65535:
            raise ProtocolError('Packet is too large')
        self.sock.sendall(struct.pack('>H', len(packet) + 2) + packet)
        self.last_send = time.monotonic()
        self.report('send', command, len(payload))

    def heartbeat(self):
        self.sock.sendall(b'\0\x02')
        self.last_send = time.monotonic()
