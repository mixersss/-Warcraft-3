import json
import socket
import struct
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from classic_crypto import (Noise, PacketCipher, des, login_proof, noise_seed,
                            packet_b, password_key, session_key, triple_des)
from classic_wire import ProtocolError, Reader, Wire, sequence, string
from headless import Client, Report, ServerError


class CryptoTests(unittest.TestCase):
    def test_des_published_vector(self):
        key = bytes.fromhex('133457799BBCDFF1')
        plaintext = bytes.fromhex('0123456789ABCDEF')
        ciphertext = bytes.fromhex('85E813540F0AB405')
        self.assertEqual(des(plaintext, key), ciphertext)
        self.assertEqual(des(ciphertext, key, True), plaintext)

    def test_native_gate_triple_des_vectors(self):
        # Extracted by emulating the uploaded GateServer RunDes, not this codec.
        data = bytes(range(24))
        key = password_key('test12345')
        self.assertEqual(triple_des(data, key).hex(),
                         '3f08f6cfc423d6ed06755d299e5290c91c7a22312e49a258')
        self.assertEqual(triple_des(data, key, True).hex(),
                         'c5cd465545a239b6c0b9a89fa6ef2e41934dd99e5b8fc956')

    def test_native_gate_b_signed_key_vector(self):
        key = bytes.fromhex('83f12a007f92')
        expected = bytes.fromhex(
            'e0c35006edbc61db4412d5cce3f3481ebd1c648b7c2aa52ce6a360368d7c67bb'
            '1442758de953184e5ddd6a6b0c5a45edec0330662d3d6d1b2472154def33287efc9e70')
        self.assertEqual(packet_b(bytes(range(67)), key), expected)
        self.assertEqual(packet_b(expected, key, True), bytes(range(67)))

    def test_native_noise_vector(self):
        original = bytes(range(67))
        expected = bytes.fromhex(
            '080500020c010406000d080a04090c0e181510121c111416101d181a14191c1e'
            '202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f404142')
        noise = Noise(bytes([1, 2, 4, 8]))
        self.assertEqual(noise.transform(original), expected)
        self.assertEqual(noise.key, bytes.fromhex('05060700'))
        noise = Noise(bytes([1, 2, 4, 8]))
        self.assertEqual(noise.transform(expected, True), original)
        self.assertEqual(noise.key, bytes.fromhex('05060700'))

    def test_padding_and_session(self):
        self.assertEqual(len(login_proof(b'12345678', 'test12345')), 16)
        encrypted = triple_des(b'ABCDEF\0\0', password_key('test12345'))
        self.assertEqual(session_key(encrypted, 'test12345'), b'ABCDEF')


def frame(command, payload=b'', cipher=None, rpc=True):
    body = struct.pack('>H', command) + payload
    if cipher:
        body = cipher.encrypt(body)
    body = (b'\x80\0\0\0' if rpc else b'') + body
    return struct.pack('>H', len(body) + 2) + body


class WireTests(unittest.TestCase):
    def setUp(self):
        self.a, self.b = socket.socketpair()
        self.addCleanup(self.a.close)
        self.addCleanup(self.b.close)

    def test_partial_frames_heartbeat_and_coalesced_frames(self):
        wire = Wire(self.a)
        data = frame(940, string(b'[11-11 17:00:00:123]'))
        self.b.sendall(data[:1])
        with self.assertRaises(TimeoutError):
            wire.receive(time.monotonic() + .01)
        self.b.sendall(data[1:7])
        with self.assertRaises(TimeoutError):
            wire.receive(time.monotonic() + .01)
        self.b.sendall(data[7:] + b'\0\x02' + frame(931, b'test'))
        self.assertEqual(wire.receive(time.monotonic() + 1)[0], 940)
        self.assertEqual(wire.receive(time.monotonic() + 1), (931, b'test'))

    def test_non_rpc_handshake(self):
        self.b.sendall(frame(940, string(b'challenge'), rpc=False))
        wire = Wire(self.a)
        self.assertEqual(wire.receive(time.monotonic() + 1)[0], 940)
        self.assertEqual(wire.header_size, 2)

    def test_malformed_frames_and_fields(self):
        self.b.sendall(b'\0\x01')
        with self.assertRaises(ProtocolError):
            Wire(self.a).receive(time.monotonic() + 1)
        for data in (b'', b'\0\x04ab', b'\0\x01a'):
            with self.assertRaises(ProtocolError):
                Reader(data).string()


class LoginTests(unittest.TestCase):
    def exercise(self, error=0, populated=True):
        a, b = socket.socketpair()
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        failures = []
        challenge, password = b'[11-11 17:00:00:123]', 'test12345'
        key = bytes.fromhex('83f12a007f92')

        def server():
            try:
                b.sendall(frame(940, string(challenge)))
                wire = Wire(b)
                wire.header_size = 6
                cmd, payload = wire.receive(time.monotonic() + 2)
                self.assertEqual(cmd, 431)
                r = Reader(payload)
                self.assertEqual(r.string_bytes(), b'')
                self.assertEqual(r.string_bytes(), b'bot_test')
                self.assertEqual(r.sequence(), login_proof(challenge, password))
                self.assertEqual(r.string_bytes(), b'Unknown')
                self.assertEqual((r.short(), r.short()), (911, 136))
                r.end()
                if error:
                    b.sendall(frame(931, struct.pack('>H', error) + string(b'error')))
                    return
                reply = b'\0\0' + sequence(triple_des(key + b'\0\0', password_key(password)))
                reply += b'\x03'
                if populated:
                    reply += b'\0\x01' + string('Бот') + string(b'Swordsman')
                    reply += struct.pack('>H', 12) + sequence(bytes(1626)) + b'\0'
                else:
                    reply += b'\0\0\0'
                reply += b'\0' + struct.pack('>II', 1, 0x3214)
                seed = noise_seed(challenge)
                wire.in_cipher, wire.out_cipher = PacketCipher(seed, key), PacketCipher(seed, key)
                # Two different modes in a single TCP write checks encryption activation boundary.
                b.sendall(frame(931, reply) + frame(537, cipher=wire.out_cipher))
                if not populated:
                    return
                # Native classic BeginPlay transmits the character name, not slot 1.
                self.assertEqual(wire.receive(time.monotonic() + 2), (433, string('Бот')))
                wire.send(933, b'\0\0')
                wire.send(516, b'\0\0' + bytes(128))
                self.assertEqual(wire.receive(time.monotonic() + 2), (17, b''))
                wire.send(515, bytes(range(20)))
                self.assertEqual(wire.receive(time.monotonic() + 2), (15, bytes(range(20))))
                self.assertEqual(wire.receive(time.monotonic() + 2), (434, b''))
                wire.send(934, b'\0\0')
                self.assertEqual(wire.receive(time.monotonic() + 2), (432, b''))
            except BaseException as exc:
                failures.append(exc)
                b.shutdown(socket.SHUT_RDWR)

        worker = threading.Thread(target=server, daemon=True)
        worker.start()
        report = Report()
        client = Client(a, report)
        if error:
            with self.assertRaises(ServerError) as caught:
                client.login('bot_test', password)
            self.assertEqual(caught.exception.code, error)
        else:
            chars = client.login('bot_test', password)
            self.assertEqual(len(chars), int(populated))
            if populated:
                self.assertEqual(chars[0]['slot'], 1)
                client.enter(chars[0]['name'])
                self.assertTrue(client.entered)
                client.idle(.05)
                client.logout()
                self.assertEqual(report.result['stage'], 'in_world')
        worker.join(3)
        self.assertFalse(worker.is_alive())
        if failures:
            raise failures[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            report.write(path)
            text = path.read_text()
            self.assertNotIn(password, text)
            self.assertNotIn('bot_test', text)
            self.assertNotIn(challenge.decode(), text)
            self.assertIn('events', json.loads(text))

    def test_encrypted_login_enter_ping_logout(self):
        self.exercise()

    def test_rejected_login(self):
        self.exercise(error=1001)

    def test_empty_account(self):
        self.exercise(populated=False)


if __name__ == '__main__':
    unittest.main()
