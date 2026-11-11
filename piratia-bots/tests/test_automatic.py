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
    def test_character_reused_without_creation(self):
        client = Mock()
        bot = {'character': 'Bot12345678'}
        chars = [{'slot': 2, 'name': bot['character']}]
        self.assertEqual(ensure_character(bot, client, chars), 2)
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
        # all zero except (offset,value): 2=1,166=208,167=7,326=1,1624=100.
        golden = bytearray(1626)
        for index, value in ((2, 1), (166, 208), (167, 7), (326, 1), (1624, 100)):
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
            second.enter.assert_called_once_with(0)
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
