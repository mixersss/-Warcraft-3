import json
import socket
import struct
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from auto_bots import ensure_character, prepare_accounts, run_bot
from classic_crypto import PacketCipher, noise_seed, password_key, triple_des
from classic_wire import ProtocolError, Reader, Wire, sequence, string
from headless import Client, Report, ServerError
from test_classic import frame


class AutomaticCreationTests(unittest.TestCase):
    def test_secondary_password_uses_classic_md5_string(self):
        report = Report()
        client = Client(Mock(), report)
        client.wire = Mock()
        client.wait = Mock(return_value=(941, b'\0\0'))
        self.assertTrue(client.ensure_secondary_password('123456789'))
        client.wire.send.assert_called_once_with(346, b'\x00\x2125F9E794323B453885F5181F1B624D0B\x00')
        self.assertTrue(client.has_secondary_password)
        self.assertNotIn('25F9E794', json.dumps(report.result))
        self.assertNotIn('123456789', json.dumps(report.result))

    def test_existing_secondary_password_is_never_overwritten(self):
        client = Client(Mock(), Report())
        client.has_secondary_password = True
        client.wire = Mock()
        self.assertFalse(client.ensure_secondary_password('123456789'))
        client.wire.send.assert_not_called()

    def test_secondary_password_refusal_stops_before_entry(self):
        client = Client(Mock(), Report())
        client.wire = Mock()
        client.wait = Mock(return_value=(941, struct.pack('>H', 534)))
        with self.assertRaises(ServerError) as caught:
            client.ensure_secondary_password('123456789')
        self.assertEqual(caught.exception.stage, 'create_secondary_password')
        self.assertFalse(client.has_secondary_password)
        self.assertFalse(client.begin_requested)
        self.assertEqual(client.wire.send.call_count, 1)

    def test_classic_begin_play_uses_native_name_string(self):
        report = Report()
        client = Client(Mock(), report)
        client.wire = Mock()
        client.wire.receive.side_effect = [(933, b'\0\0'), (516, b'\0\0')]
        client.enter('Bot12345678')
        # Golden encoding from native BeginPlay -> WriteString, not a slot byte.
        client.wire.send.assert_called_once_with(433, b'\x00\x0cBot12345678\x00')
        self.assertTrue(client.entered)
        self.assertEqual(report.result['begin_play_format'], 'character_name_string')
        self.assertNotIn('Bot12345678', json.dumps(report.result))

    def test_begin_play_refusal_does_not_select_other_characters(self):
        client = Client(Mock(), Report())
        client.wire = Mock()
        client.wire.receive.return_value = (933, struct.pack('>H', 524))
        with self.assertRaises(ServerError) as caught:
            client.enter('Bot12345678')
        self.assertEqual(caught.exception.code, 524)
        self.assertFalse(client.entered)
        client.wire.send.assert_called_once_with(433, b'\x00\x0cBot12345678\x00')

    def test_character_reused_without_creation(self):
        client = Mock()
        bot = {'character': 'Bot12345678'}
        chars = [{'slot': 2, 'name': bot['character']}]
        self.assertEqual(ensure_character(bot, client, chars), 'Bot12345678')
        client.create_character.assert_not_called()

    def test_unrelated_character_is_never_selected_or_modified(self):
        client = Mock()
        with self.assertRaises(ProtocolError):
            ensure_character({'character': 'Bot12345678'}, client, [{'slot': 0, 'name': 'MyMain'}])
        client.create_character.assert_not_called()

    def test_empty_account_requests_native_creation(self):
        client = Mock()
        self.assertIsNone(ensure_character({'character': 'Bot12345678'}, client, []))
        client.create_character.assert_called_once_with('Bot12345678')

    def test_creation_payload_matches_native_ui_look(self):
        a, b = socket.socketpair()
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        report = Report()
        client = Client(a, report)
        client.wire.header_size = 6
        seed, key = bytes([1, 2, 4, 8]), bytes.fromhex('83f12a007f92')
        client.wire.in_cipher = PacketCipher(seed, key)
        client.wire.out_cipher = PacketCipher(seed, key)
        wire = Wire(b)
        wire.header_size = 6
        wire.in_cipher, wire.out_cipher = PacketCipher(seed, key), PacketCipher(seed, key)
        # Native UI SendChaToServ capture (client 0x4c16c0), default Lance:
        # Creator menu tables: hair=2000, face=2554 (not renderer mesh IDs).
        # all zero except (offset,value): 2=1,166=250,167=9,326=1,1624=208,1625=7.
        golden = bytearray(1626)
        for index, value in ((2, 1), (166, 250), (167, 9), (326, 1), (1624, 208), (1625, 7)):
            golden[index] = value
        # Reply may be queued before the client sends; encryption state is independent.
        wire.send(935, b'\0\0')
        client.create_character('Bot12345678')
        cmd, payload = wire.receive(time.monotonic() + 1)
        self.assertEqual(cmd, 435)
        reader = Reader(payload)
        self.assertEqual(reader.string(), 'Bot12345678')
        self.assertEqual(reader.string(), 'Argent City')
        self.assertEqual(reader.sequence(), bytes(golden))
        reader.end()
        self.assertEqual(report.result['creation_appearance'],
                         {'type': 1, 'hair': 2000, 'face': 2554, 'look_bytes': 1626})

    def test_creation_refusal_stops_without_entering(self):
        client = Client(Mock(), Report())
        client.wire = Mock()
        client.wait = Mock(return_value=(935, struct.pack('>H', 102)))
        with self.assertRaises(ServerError) as caught:
            client.create_character('Bot12345678')
        self.assertEqual(caught.exception.code, 102)
        self.assertFalse(client.begin_requested)
        self.assertEqual(client.wire.send.call_args.args[0], 435)

    def test_creation_worker_reconnects_and_preserves_private_data(self):
        first, second = Mock(), Mock()
        first_sock, second_sock = Mock(), Mock()
        bot = {'account': 'PB123456789abc', 'password': 'dummy1234', 'character': 'Bot12345678'}
        with tempfile.TemporaryDirectory() as temporary:
            with patch('auto_bots.connect_bot', side_effect=[
                (first_sock, first, []), (second_sock, second, [{'name': bot['character'], 'slot': 0}])
            ]), patch('auto_bots.print'):
                stop = Mock()
                stop.is_set.return_value = False
                stop.wait.return_value = False
                self.assertTrue(run_bot(1, bot, 1973, 60, stop, Path(temporary)))
            first.create_character.assert_called_once_with(bot['character'])
            first.logout.assert_called_once()
            first_sock.close.assert_called_once()
            second.enter.assert_called_once_with('Bot12345678')
            second.logout.assert_called_once()
            saved = (Path(temporary) / 'bot-report-01.json').read_text()
            for value in bot.values():
                self.assertNotIn(value, saved)
            self.assertEqual(json.loads(saved)['stage'], 'completed')

    def test_private_helper_output_is_validated(self):
        # Only native Windows SQL/DPAPI require a Windows run; never emulate them
        # as a passing real-database test here.
        with patch('auto_bots.os.name', 'nt'), patch('auto_bots.Path', return_value=Path('C:/Windows')):
            with patch('auto_bots.subprocess.run', return_value=Mock(returncode=0, stdout='{"bots": []}', stderr='')):
                with self.assertRaises(RuntimeError):
                    prepare_accounts(3)


if __name__ == '__main__':
    unittest.main()
