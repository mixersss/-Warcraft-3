"""Create dedicated local accounts and characters, then run headless connection tests."""
import argparse
import hashlib
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
        sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
        chars = client.login(bot['account'], bot['password'])
        for attempt in range(3):
            try:
                client.ensure_secondary_password(bot['secondary_password'])
                break
            except ServerError as exc:
                if exc.code!=532 or attempt==2:raise
                report.result['secondary_password_busy_retries']=attempt+1
                time.sleep(2*(attempt+1))

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
    if bot.get('preserve_existing'):
        raise ProtocolError('Сохранённый персонаж отсутствует на сервере. Создание замены отключено; '
                            'проверь прежнюю базу сервера и полную папку data.')
    if 'creation_body' in bot:
        from roles import RoleStore
        from regions import birthplace_for
        role=RoleStore(ROOT/'data/bot-roles.json').resolve(bot['character'],bot['creation_body'],0)
        client.create_character(bot['character'],body=bot['creation_body'],birthplace=bot.get('birthplace',birthplace_for(role['first_job'])))
    else:
        client.create_character(bot['character'])
    return None  # Reconnect to retrieve the authoritative server-side character list.


def _run_bot_once(index, bot, port, seconds, stop, report_dir, mode='idle', navigation=None, chat_budget=None, fleet=None, history=None, total_deadline=None):
    report = Report()
    report.result['version'] = 'AutoAccountsAlpha35'
    report.result['bot_index'] = index
    report.result['character_tag'] = hashlib.sha256(bot.get('character','').encode('utf-8')).hexdigest()[:12]
    report.result['session_history']=list(history or [])
    report.result['reconnect_attempts']=(history[-1].get('recovery_number',len(history)) if history else 0)
    started=time.monotonic()
    report.result['entered_world']=False
    sock = client = None
    succeeded = False
    try:
        if stop.is_set():
            report.stage('cancelled')
            return False,report.result
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
                    return False,report.result
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
            return False,report.result
        client.enter(selected_name)
        report.result['entered_world']=True
        if total_deadline is not None and total_deadline!=float('inf'):
            seconds=max(0.01,total_deadline-time.monotonic())
        print(f"Бот {index}: {bot['character']} вошёл в мир без окна игры.")
        if mode in ('hunt','adventure','mixed'):
            from hunter import hunt
            from regions import Regions
            nav = navigation or Regions(ROOT/'assets')
            from roles import RoleStore
            from coordination import tactic_for
            selected_tactic=tactic_for(index,mode)
            print(f'Бот {index}: тактика '+{'quests':'задания и профессия','farm':'фарм и профессия','hybrid':'чередование заданий и фарма'}[selected_tactic])
            hunt(client, seconds, stop, report, nav, lambda text: print(f'Бот {index}: {text}'),
                 bot_name=bot['character'], chat_budget=chat_budget, adventure_mode=True,
                 tactic=selected_tactic,
                 role_store=RoleStore(ROOT / 'data/bot-roles.json'),fleet=fleet,bot_index=index)
        else:
            client.idle(seconds, stop)
        report.stage('interrupted' if stop.is_set() else 'completed')
        report.result['exit_reason']='stop_requested' if stop.is_set() else 'session_duration_elapsed'
        succeeded = True
    except ServerError as exc:
        report.result['error_type'] = 'server_error'
        report.result['exit_reason']='server_refusal'
        report.result['server_error_code'] = exc.code
        print(f'Бот {index}: отказ сервера на этапе {exc.stage}, код {exc.code}.')
    except (OSError, ProtocolError, ValueError) as exc:
        report.result['error_type'] = type(exc).__name__
        report.result['exit_reason']='network_error' if isinstance(exc,OSError) else 'protocol_or_state_error'
        if isinstance(exc,OSError):report.result['network_errno']=getattr(exc,'errno',None)
        import traceback
        report.result['error_locations']=[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)[-3:]]
        print(f'Бот {index}: {exc}')
    except Exception as exc:
        report.result['error_type']=type(exc).__name__;report.result['exit_reason']='unexpected_program_error'
        import traceback
        frames=traceback.extract_tb(exc.__traceback__)[-3:]
        report.result['error_locations']=[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name} for f in frames]
        print(f'Бот {index}: ошибка программы {type(exc).__name__}; подробности в отчёте.')
    finally:
        if client and report.result.get('exit_reason')!='network_error':
            try:
                client.logout()
            except (OSError, ProtocolError):
                pass
        if sock:
            sock.close()
        if fleet:fleet.update(index,connected=False,state=report.result.get('stage','finished'))
        report.result['session_elapsed_seconds']=round(time.monotonic()-started,2)
        report.write(report_dir / f'bot-report-{index:02d}.json')
    return succeeded,report.result


def run_bot(index, bot, port, seconds, stop, report_dir, mode='idle', navigation=None, chat_budget=None, fleet=None):
    deadline=float('inf') if seconds==0 else time.monotonic()+seconds
    history=[];had_entered=False;attempt=0;recoveries=0
    while True:
        if stop.is_set():return False
        remaining=0 if deadline==float('inf') else max(0,deadline-time.monotonic())
        if deadline!=float('inf') and remaining<=0:return True
        success,result=_run_bot_once(index,bot,port,remaining,stop,report_dir,mode,navigation,chat_budget,fleet,history,deadline)
        if success:return True
        had_entered=had_entered or result.get('entered_world',False)
        reason=result.get('exit_reason')
        retryable=reason=='network_error' or (had_entered and result.get('server_error_code')==1104)
        if stop.is_set() or not retryable:return False
        if result.get('entered_world') and result.get('session_elapsed_seconds',0)>=120:attempt=0
        if attempt>=3 and seconds!=0:return False
        history.append({k:result[k] for k in ('stage','exit_reason','error_type','server_error_code','session_elapsed_seconds','error_locations','network_errno','last_receive','last_send') if k in result})
        history[-1]['recovery_number']=recoveries+1
        history=history[-20:]
        delay=(5,15,30)[attempt]+index%5 if attempt<3 else 120+index%15
        attempt+=1;recoveries+=1
        result['reconnect_attempts']=recoveries;result['reconnect_wait_seconds']=delay
        result['stage']='reconnecting';result['session_history']=list(history)
        retry_report_path=report_dir / f'bot-report-{index:02d}.json'
        retry_report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if fleet:fleet.update(index,connected=False,state='reconnecting')
        print(f'Бот {index}: сетевое восстановление {recoveries} через {delay} сек.')
        if stop.wait(delay):
            result['stage']='interrupted';result['exit_reason']='stop_requested'
            retry_report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            return False
    return False


def watch_stop_file(path,stop):
    while not stop.wait(.5):
        if path.is_file():
            try:path.unlink()
            except OSError:pass
            print('Получена команда остановки. Вывожу ботов обычным выходом…')
            stop.set()
            return


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, default=200)
    parser.add_argument('--seconds', type=int, default=7200)
    parser.add_argument('--port', type=int, default=1973)
    parser.add_argument('--mode', choices=('idle', 'hunt', 'adventure', 'mixed'), default='mixed')
    parser.add_argument('--allow-new-bots', action='store_true',
                        help='explicitly allow a new population or extending saved accounts')
    args = parser.parse_args()
    if not 1 <= args.count <= 200 or not (args.seconds==0 or 5 <= args.seconds <= 86400) or not 1 <= args.port <= 65535:
        parser.error('count: 1..200; seconds: 0 (continuous) or 5..86400; port: 1..65535')
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    print('Пиратия — первая профессия с 9 уровня, сохранение текущих ботов (Alpha 35).')
    print(f'Количество: {args.count}. Используются прежние сохранённые аккаунты.')
    duration_label='без ограничения' if args.seconds==0 else str(args.seconds)+' секунд'
    print(f'Режим: {args.mode}. Время: {duration_label}. Остановка — Ctrl+C.\n')
    stop = threading.Event()
    lock = None
    session_guard = None
    setup_report = Report()
    setup_report.result['version'] = 'AutoAccountsAlpha35'
    report_path = ROOT / 'bot-report.json'
    try:
        if os.name != 'nt':
            raise RuntimeError('Запускай Start-Bot.cmd на Windows-ПК, где установлен сервер.')
        import msvcrt
        data = ROOT / 'data'
        from runtime_guard import require_population,SessionGuard
        setup_report.stage('checking_local_data')
        setup_report.result['local_data']=require_population(data,args.count,args.allow_new_bots)
        data.mkdir(exist_ok=True)
        session_guard=SessionGuard(args.port)
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
        stop_file=ROOT/'stop-request.txt'
        if stop_file.exists():stop_file.unlink()
        threading.Thread(target=watch_stop_file,args=(stop_file,stop),daemon=True).start()
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
            bot['preserve_existing'] = not args.allow_new_bots
            bot['creation_body'] = index % 4 + 1
            from city_travel import home_city_for,BIRTHPLACES
            bot['birthplace']=BIRTHPLACES['garner']
        print('Аккаунты готовы. Создаю недостающих персонажей и подключаю ботов…')
        from regions import Regions
        from social import ChatBudget
        navigation = Regions(ROOT/'assets',population_count=args.count)
        chat_budget = ChatBudget(interval=2)
        from fleet import Fleet
        fleet=Fleet(args.count,ROOT/'population-status.json')
        fleet.write()
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
                    setup_report.stage('running')
                    setup_report.result.update(connected_bots=status['connected'],peak_connected=status['peak_connected'])
                    setup_report.write(report_path)
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
        stop.set()
        if lock:
            lock.close()
        if session_guard:session_guard.close()
        setup_report.write(report_path)
        print('Отчёты: bot-report.json и bot-report-01.json, 02, 03…')
        print('Папку data сохраняй на этом ПК и никому не отправляй: это данные ботов.')


if __name__ == '__main__':
    sys.exit(main())
