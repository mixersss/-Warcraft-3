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
        capture_output=True, timeout=120, encoding='utf-8', errors='replace')
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
                    or not re.fullmatch(r'[A-Za-z0-9]{9}', bot['password'])):
                raise ValueError()
        return bots
    except (ValueError, TypeError, KeyError):
        raise RuntimeError('Программа подготовки вернула неожиданный ответ.') from None


def connect_bot(bot, report, port):
    sock = socket.create_connection(('127.0.0.1', port), timeout=10)
    client = Client(sock, report)
    try:
        chars = client.login(bot['account'], bot['password'])
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
    client.create_character(bot['character'])
    return None  # Reconnect to retrieve the authoritative server-side character list.


def run_bot(index, bot, port, seconds, stop, report_dir):
    report = Report()
    report.result['version'] = 'AutoAccountsAlpha05'
    report.result['bot_index'] = index
    sock = client = None
    succeeded = False
    try:
        if stop.is_set():
            report.stage('cancelled')
            return False
        sock, client, chars = connect_bot(bot, report, port)
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
        report.write(report_dir / f'bot-report-{index:02d}.json')
    return succeeded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, default=3)
    parser.add_argument('--seconds', type=int, default=60)
    parser.add_argument('--port', type=int, default=1973)
    args = parser.parse_args()
    if not 1 <= args.count <= 10 or not 5 <= args.seconds <= 600 or not 1 <= args.port <= 65535:
        parser.error('count: 1..10; seconds: 5..600; port: 1..65535')
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    print('Пиратия — автоматические аккаунты и персонажи (Alpha 05).')
    print(f'Количество: {args.count}. Логины и пароли вводить не нужно.')
    print(f'Пока проверяем создание и вход: боты стоят в мире {args.seconds} секунд, боевого ИИ ещё нет.\n')
    stop = threading.Event()
    lock = None
    setup_report = Report()
    setup_report.result['version'] = 'AutoAccountsAlpha05'
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
        print('Аккаунты готовы. Создаю недостающих персонажей и подключаю ботов…')
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=args.count)
        try:
            futures = [pool.submit(run_bot, index, bot, args.port, args.seconds, stop, ROOT)
                       for index, bot in enumerate(bots, 1)]
            try:
                results = [future.result() for future in futures]
            except KeyboardInterrupt:
                print('\nОстанавливаю ботов обычным выходом…')
                stop.set()
                results = [future.result() for future in futures]
        finally:
            stop.set()
            pool.shutdown(wait=True)
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
