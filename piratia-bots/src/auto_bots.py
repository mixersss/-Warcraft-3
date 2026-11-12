"""Create dedicated local accounts and characters, then run headless connection tests."""
import argparse
import concurrent.futures
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from classic_wire import ProtocolError
from headless import Client, Report, ServerError

ROOT = Path(__file__).resolve().parents[1]


def prepare_accounts(count):
    if os.name != 'nt':
        raise RuntimeError('Автосоздание аккаунтов запускается на Windows-ПК с твоим сервером.')
    powershell = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    result = subprocess.run(
        [str(powershell), '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy',
         'Bypass', '-File', str(ROOT / 'src/provision.ps1'), '-Count', str(count)],
        capture_output=True, timeout=600, encoding='utf-8', errors='replace')
    if result.returncode:
        # Helper stderr contains only a stage/type/SQL number, never SQL or credentials.
        reason = result.stderr.strip()[:300]
        raise RuntimeError('Не удалось подготовить аккаунты. ' + reason)
    try:
        bots = json.loads(result.stdout.lstrip('\ufeff'))['bots']
        if not isinstance(bots, list) or len(bots) != count:
            raise ValueError()
        for bot in bots:
            if (not re.fullmatch(r'PB[0-9a-f]{12}', bot['account'])
                    or not re.fullmatch(r'Bot[0-9a-f]{8}', bot['character'])
                    or not re.fullmatch(r'[A-Za-z0-9]{9}', bot['password'])
                    or not re.fullmatch(r'[A-Za-z0-9]{9}', bot['secondary_password'])):
                raise ValueError()
        return bots
    except (ValueError, TypeError, KeyError):
        raise RuntimeError('Программа подготовки вернула неожиданный ответ.') from None


def connect_bot(bot, report, port):
    sock = socket.create_connection(('127.0.0.1', port), timeout=10)
    client = Client(sock, report)
    try:
        chars = client.login(bot['account'], bot['password'])
        client.ensure_secondary_password(bot['secondary_password'])
        return sock, client, chars
    except BaseException:
        sock.close()
        raise


def ensure_character(bot, client, chars):
    """Never take control of an unrelated character, even on a saved bot account."""
    matching = [char for char in chars if char['name'] == bot['character']]
    if matching:
        return matching[0]['name']
    if chars:
        raise ProtocolError('На аккаунте бота найден другой персонаж. Автосоздание остановлено.')
    if 'creation_body' in bot:
        from roles import RoleStore
        from regions import birthplace_for
        role=RoleStore(ROOT/'data/bot-roles.json').resolve(bot['character'],bot['creation_body'],0)
        client.create_character(bot['character'],body=bot['creation_body'],birthplace=birthplace_for(role['first_job']))
    else:
        client.create_character(bot['character'])
    return None  # Reconnect to retrieve the authoritative server-side character list.


def run_bot(index, bot, port, seconds, stop, report_dir, mode='idle', navigation=None, chat_budget=None, fleet=None):
    report = Report()
    report.result['version'] = 'AutoAccountsAlpha12'
    report.result['bot_index'] = index
    sock = client = None
    succeeded = False
    try:
        if stop.is_set():
            report.stage('cancelled')
            return False
        sock, client, chars = connect_bot(bot, report, port)
        if report.result.get('secondary_password_created'):
            print(f'Бот {index}: второй пароль задан автоматически.')
        selected_name = ensure_character(bot, client, chars)
        if selected_name is None:
            print(f'Бот {index}: персонаж создан автоматически.')
            client.logout()
            sock.close()
            sock = client = None
            # Let AccountServer process the normal logout; never reset login flags in SQL.
            for attempt in range(3):
                if stop.wait(1 + attempt):
                    return False
                try:
                    sock, client, chars = connect_bot(bot, report, port)
                    break
                except ServerError:
                    if attempt == 2:
                        raise
            matching = [char for char in chars if char['name'] == bot['character']]
            if not matching:
                raise ProtocolError('Сервер принял создание, но персонаж отсутствует в списке после входа.')
            selected_name = matching[0]['name']
        if stop.is_set():
            report.stage('cancelled')
            return False
        client.enter(selected_name)
        print(f"Бот {index}: {bot['character']} вошёл в мир без окна игры.")
        if mode in ('hunt','adventure','mixed'):
            from hunter import hunt
            from regions import Regions
            nav = navigation or Regions(ROOT/'assets')
            from roles import RoleStore
            from coordination import tactic_for
            selected_tactic=tactic_for(index,mode)
            print(f'Бот {index}: тактика '+('задания и профессия' if selected_tactic=='quests' else 'фарм и профессия'))
            hunt(client, seconds, stop, report, nav, lambda text: print(f'Бот {index}: {text}'),
                 bot_name=bot['character'], chat_budget=chat_budget, adventure_mode=True,
                 tactic=selected_tactic,
                 role_store=RoleStore(ROOT / 'data/bot-roles.json'),fleet=fleet,bot_index=index)
        else:
            client.idle(seconds, stop)
        report.stage('interrupted' if stop.is_set() else 'completed')
        succeeded = True
    except ServerError as exc:
        report.result['error_type'] = 'server_error'
        report.result['server_error_code'] = exc.code
        print(f'Бот {index}: отказ сервера на этапе {exc.stage}, код {exc.code}.')
    except (OSError, ProtocolError, ValueError) as exc:
        report.result['error_type'] = type(exc).__name__
        print(f'Бот {index}: {exc}')
    finally:
        if client:
            try:
                client.logout()
            except (OSError, ProtocolError):
                pass
        if sock:
            sock.close()
        if fleet:fleet.update(index,connected=False,state=report.result.get('stage','finished'))
        report.write(report_dir / f'bot-report-{index:02d}.json')
    return succeeded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, default=30)
    parser.add_argument('--seconds', type=int, default=3600)
    parser.add_argument('--port', type=int, default=1973)
    parser.add_argument('--mode', choices=('idle', 'hunt', 'adventure', 'mixed'), default='mixed')
    args = parser.parse_args()
    if not 1 <= args.count <= 60 or not 5 <= args.seconds <= 86400 or not 1 <= args.port <= 65535:
        parser.error('count: 1..60; seconds: 5..86400; port: 1..65535')
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    print('Пиратия — классы, задания и фарм без окна игры (Alpha 12).')
    print(f'Количество: {args.count}. Логины и пароли вводить не нужно.')
    print(f'Режим: {args.mode}. Время: {args.seconds} секунд. Остановка — Ctrl+C.\n')
    stop = threading.Event()
    lock = None
    setup_report = Report()
    setup_report.result['version'] = 'AutoAccountsAlpha12'
    report_path = ROOT / 'bot-report.json'
    try:
        if os.name != 'nt':
            raise RuntimeError('Запускай Start-Bot.cmd на Windows-ПК, где установлен сервер.')
        import msvcrt
        data = ROOT / 'data'
        data.mkdir(exist_ok=True)
        lock = (data / 'run.lock').open('a+b')
        lock.seek(0)
        if not lock.read(1):
            lock.write(b'0')
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise RuntimeError('Этот набор ботов уже запущен. Закрой предыдущее окно программы.') from None
        setup_report.stage('checking_gate')
        # Refuse to create accounts if the local GateServer is not listening.
        with socket.create_connection(('127.0.0.1', args.port), timeout=5):
            pass
        setup_report.stage('preparing_accounts')
        print('Проверяю SQL Server и подготавливаю отдельные аккаунты ботов…')
        bots = prepare_accounts(args.count)
        setup_report.stage('accounts_ready')
        setup_report.result['bot_count'] = len(bots)
        setup_report.write(report_path)
        for index, bot in enumerate(bots):
            bot['creation_body'] = index % 4 + 1
        print('Аккаунты готовы. Создаю недостающих персонажей и подключаю ботов…')
        from regions import Regions
        from social import ChatBudget
        navigation = Regions(ROOT/'assets')
        chat_budget = ChatBudget()
        from fleet import Fleet
        fleet=Fleet(args.count,ROOT/'population-status.json')
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=args.count)
        try:
            futures = []
            try:
                for index, bot in enumerate(bots, 1):
                    if index > 1 and stop.wait(1.5):
                        break
                    futures.append(pool.submit(run_bot, index, bot, args.port, args.seconds, stop,
                                               ROOT, args.mode, navigation, chat_budget, fleet))
                remaining=set(futures)
                while remaining:
                    _,remaining=concurrent.futures.wait(remaining,timeout=30)
                    status=fleet.write()
                    print(f"В мире: {status['connected']}/{args.count}; города: {status['cities']}")
                results = [future.result() for future in futures]
            except KeyboardInterrupt:
                print('\nОстанавливаю ботов обычным выходом…')
                stop.set()
                results = [future.result() for future in futures]
        finally:
            stop.set()
            pool.shutdown(wait=True)
            fleet.write()
        setup_report.stage('completed' if all(results) else 'some_bots_failed')
        setup_report.result['successful_bots'] = sum(results)
        print(f'Проверку завершили: {sum(results)} из {len(bots)} ботов.')
        return 0 if all(results) else 1
    except (OSError, RuntimeError, subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
        setup_report.result['error_type'] = type(exc).__name__
        if isinstance(exc, KeyboardInterrupt):
            print('\nОстановлено.')
        else:
            print(str(exc))
        return 1
    finally:
        if lock:
            lock.close()
        setup_report.write(report_path)
        print('Отчёты: bot-report.json и bot-report-01.json, 02, 03…')
        print('Папку data сохраняй на этом ПК и никому не отправляй: это данные ботов.')


if __name__ == '__main__':
    sys.exit(main())
