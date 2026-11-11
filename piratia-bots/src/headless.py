"""Connection alpha for the owner's classic PKO server; no game window or AI yet."""
import argparse
import getpass
import json
import socket
import struct
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from classic_crypto import PacketCipher, login_proof, noise_seed, password_key, session_key
from classic_wire import ProtocolError, Reader, Wire, sequence, string


class ServerError(ProtocolError):
    def __init__(self, stage, code):
        self.stage, self.code = stage, code
        super().__init__(f'{stage}: server error {code}')


class Report:
    """Allowlist diagnostics: no credentials, character names or packet contents."""
    def __init__(self):
        self.result = {'version': 'ConnectionAlpha01', 'stage': 'start', 'events': []}

    def stage(self, value):
        self.result['stage'] = value

    def event(self, direction, command, length):
        events = self.result['events']
        if len(events) < 1000:
            events.append({'direction': direction, 'command': command, 'bytes': length})

    def write(self, path):
        self.result['time_utc'] = datetime.now(timezone.utc).isoformat()
        Path(path).write_text(json.dumps(self.result, ensure_ascii=False, indent=2), encoding='utf-8')


class Client:
    def __init__(self, sock, report):
        self.wire, self.report = Wire(sock, report.event), report
        self.authenticated = self.entered = self.begin_requested = False
        self.has_secondary_password = False

    def wait(self, wanted, timeout=20):
        deadline = time.monotonic() + timeout
        while True:
            command, payload = self.wire.receive(deadline)
            if command in wanted:
                return command, payload
            self.service(command, payload)

    def service(self, command, payload):
        if command == 537:  # Gate ping challenge, no arguments in the response.
            self.wire.send(17)
        elif command == 515:  # GameServer ping: echo five uint32 values.
            if len(payload) < 20:
                raise ProtocolError('Truncated ping')
            self.wire.send(15, payload[:20])

    def login(self, account, password):
        self.report.stage('challenge')
        _, payload = self.wait({940})
        reader = Reader(payload)
        challenge = reader.string_bytes()
        reader.end()
        if not 4 <= len(challenge) <= 128:
            raise ProtocolError('Unexpected challenge size')
        seed = noise_seed(challenge, 136)
        self.report.result['header_bytes'] = self.wire.header_size
        self.report.stage('login')
        request = (string(b'') + string(account) + sequence(login_proof(challenge, password))
                   + string(b'Unknown') + struct.pack('>HH', 911, 136))
        self.wire.send(431, request)
        _, payload = self.wait({931})
        reader = Reader(payload)
        code = reader.short()
        if code:
            raise ServerError('login', code)
        key = session_key(reader.sequence(), password)
        count = reader.byte()
        if count > 3:
            raise ProtocolError('Unexpected character slot count')
        characters = []
        for slot in range(count):
            present = reader.byte()
            if present not in (0, 1):
                raise ProtocolError('Invalid character presence flag')
            if present:
                name, job, level = reader.string(), reader.string(), reader.short()
                reader.sequence()  # Native character look; no renderer needed.
                characters.append({'slot': slot, 'name': name, 'job': job, 'level': level})
        secondary_flag = reader.byte()
        if secondary_flag not in (0, 1):
            raise ProtocolError('Invalid secondary-password flag')
        self.has_secondary_password = bool(secondary_flag)
        self.report.result['secondary_password_set'] = self.has_secondary_password
        encryption = reader.long()
        reader.long()  # Native response trailer.
        reader.end()
        if encryption not in (0, 1):
            raise ProtocolError('Unsupported communication encryption mode')
        if encryption:
            self.wire.in_cipher = PacketCipher(seed, key)
            self.wire.out_cipher = PacketCipher(seed, key)
        self.authenticated = True
        self.report.result['communication_encryption'] = encryption
        self.report.stage('character_selection')
        return characters

    def ensure_secondary_password(self, secret):
        """Create an absent PIN via the classic client's normal request, never reset one.

        Native UI 0x46390e hashes to uppercase MD5; CS_CreatePassword2 at
        0x507e40 sends command 346 and the hash string. Reply: 941 + u16 error.
        """
        if self.has_secondary_password:
            return False
        import re
        if not isinstance(secret, str) or not re.fullmatch(r'[A-Za-z0-9]{9}', secret):
            raise ValueError('Expected the saved nine-character bot secondary password')
        self.report.stage('creating_secondary_password')
        self.wire.send(346, string(password_key(secret)))
        _, payload = self.wait({941}, timeout=30)
        code = Reader(payload).short()
        if code:
            raise ServerError('create_secondary_password', code)
        self.has_secondary_password = True
        self.report.result['secondary_password_set'] = True
        self.report.result['secondary_password_created'] = True
        self.report.stage('character_selection')
        return True

    def enter(self, name):
        # Native classic BeginPlay 0x51a4d0 -> WriteString 0x54f330.
        # Later source revisions use a slot byte; this supplied EXE uses a name.
        if not isinstance(name, str) or not 1 <= len(name.encode('cp1251')) <= 16:
            raise ValueError('Expected a character name of 1..16 encoded bytes')
        self.report.stage('entering_map')
        self.report.result['begin_play_format'] = 'character_name_string'
        self.wire.send(433, string(name))
        self.begin_requested = True
        deadline = time.monotonic() + 30
        while True:
            command, payload = self.wire.receive(deadline)
            if command in (516, 933):
                code = Reader(payload).short()
                if code:
                    raise ServerError('enter_map', code)
                if command == 516:
                    self.entered = True
                    self.report.stage('in_world')
                    return
            else:
                self.service(command, payload)

    def create_character(self, name):
        """Exact classic client layout: two strings and a packed 1626-byte LOOK.

        Native SendChaToServ 0x4c16c0: type +2, face item +0xa6,
        hair +0x658. NewCha 0x51a5c0 sends the LOOK as a sequence, not three ints.
        """
        import re
        if not re.fullmatch(r'Bot[0-9a-f]{8}', name):
            raise ValueError('Character name must be an automatically generated bot name')
        look = bytearray(1626)
        struct.pack_into('<H', look, 2, 1)       # Lance type.
        # CCreateChaScene's selection tables in THIS client's .data, not the
        # CharacterInfo renderer mesh IDs: nHairTestCnt[0]=2000, nFaceTestCnt[0]=2554.
        struct.pack_into('<H', look, 0x658, 2000)
        struct.pack_into('<H', look, 0xa6, 2554)
        look[0xa6 + 0xa0] = 1                   # SItemGrid constructor availability.
        self.report.stage('creating_character')
        self.report.result['creation_appearance'] = {'type': 1, 'hair': 2000, 'face': 2554, 'look_bytes': 1626}
        self.wire.send(435, string(name) + string('Argent City') + sequence(look))
        _, payload = self.wait({935}, timeout=35)
        code = Reader(payload).short()
        if code:
            raise ServerError('create_character', code)
        self.report.stage('character_created')

    def idle(self, seconds, stop=None):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline and not (stop and stop.is_set()):
            try:
                command, payload = self.wire.receive(min(deadline, time.monotonic() + 1))
                self.service(command, payload)
            except TimeoutError:
                pass
            if time.monotonic() - self.wire.last_send > 2:
                self.wire.heartbeat()

    def logout(self):
        if not self.authenticated:
            return
        if self.begin_requested:
            self.wire.send(434)  # EndPlay; let server save and return to selection.
            try:
                self.wait({934}, timeout=12)
            except (TimeoutError, ConnectionError):
                return  # Closing TCP also invokes the server's normal disconnect path.
        self.wire.send(432)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=1973)
    parser.add_argument('--seconds', type=int, default=60)
    parser.add_argument('--report', default='bot-report.json')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535 or not 5 <= args.seconds <= 600:
        parser.error('Port: 1..65535; seconds: 5..600')
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    print('Пиратия — проверка подключения бота без окна игры (Alpha 01).')
    print('Запусти сервер на этом ПК. Нужен отдельный обычный игровой аккаунт')
    print('с уже созданным персонажем. Выйди из этого аккаунта в обычном клиенте.')
    print('Пока бот только входит в мир и стоит 60 секунд; боевого ИИ ещё нет.\n')
    report, client, sock = Report(), None, None
    exit_code = 1
    try:
        account = input('Логин игрового аккаунта бота: ').strip()
        password = getpass.getpass('Пароль (при вводе не отображается): ')
        if not account or not password or len(account) > 32 or len(password) > 32:
            raise ValueError('Логин и пароль должны содержать от 1 до 32 символов.')
        # First compatibility run is deliberately restricted to ASCII credentials.
        account.encode('ascii')
        password.encode('ascii')
        report.stage('connect')
        sock = socket.create_connection(('127.0.0.1', args.port), timeout=10)
        client = Client(sock, report)
        characters = client.login(account, password)
        password = None
        if not characters:
            raise ProtocolError('На аккаунте нет персонажей. Создай одного в обычном клиенте.')
        print('\nВход выполнен. Персонажи:')
        for char in characters:
            print(f"  {char['slot'] + 1}. {char['name']} — уровень {char['level']}")
        if len(characters) == 1:
            slot = characters[0]['slot']
        else:
            slot = int(input('Номер персонажа: ')) - 1
            if slot not in {char['slot'] for char in characters}:
                raise ValueError('Нет персонажа с таким номером.')
        selected = next(char for char in characters if char['slot'] == slot)
        client.enter(selected['name'])
        print(f'Сервер подтвердил вход в мир. Персонаж стоит {args.seconds} секунд.')
        print('Можешь найти его своим основным персонажем. Для выхода — Ctrl+C.')
        client.idle(args.seconds)
        report.stage('completed')
        exit_code = 0
    except KeyboardInterrupt:
        print('\nОстанавливаю подключение…')
        report.stage('interrupted')
        exit_code = 0
    except ServerError as exc:
        report.result['error_type'] = 'server_error'
        report.result['server_error_code'] = exc.code
        print(f'Сервер отказал на этапе {exc.stage}, код {exc.code}.')
    except (OSError, ProtocolError, ValueError, EOFError) as exc:
        report.result['error_type'] = type(exc).__name__
        print(f'Не удалось завершить проверку: {exc}')
    finally:
        if client:
            try:
                client.logout()
            except (OSError, ProtocolError, TimeoutError, KeyboardInterrupt):
                pass
        if sock:
            sock.close()
        report.write(args.report)
        print(f'Отчёт: {args.report}. Пароли и содержимое пакетов в него не записываются.')
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
