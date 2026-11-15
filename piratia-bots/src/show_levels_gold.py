"""Read local fleet snapshots without reading account identities or credentials."""
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time


def collect(root, now=None):
    now = time.time() if now is None else now
    root = Path(root)
    data = json.loads((root / 'population-status.json').read_text(encoding='utf-8-sig'))
    rows = []
    requested = data.get('requested', 0)
    indices = set(data.get('bots', {}))
    if type(requested) is int and 0 <= requested <= 10000:
        indices.update(map(str, range(1, requested + 1)))
    for index in sorted(indices, key=int):
        row = data.get('bots', {}).get(index, {})
        gold, level = row.get('gold'), row.get('level')
        stamp = data.get('updated_unix')
        source = 'population-status.json'
        if gold is None or level is None:
            path = root / f'bot-report-{int(index):02d}.json'
            try:
                report = json.loads(path.read_text(encoding='utf-8-sig'))
                world = report.get('hunt', {}).get('world', report.get('world', {}))
                fallback_gold = world.get('gold', report.get('petcare', {}).get('cash'))
                report_stamp = datetime.fromisoformat(report['time_utc'].replace('Z', '+00:00')).timestamp()
                # Do not mix a recent level with old money without indicating its age.
                if gold is None and type(fallback_gold) is int:
                    gold, level, stamp, source = fallback_gold, world.get('level', level), report_stamp, path.name
                elif level is None:
                    level, stamp, source = world.get('level'), report_stamp, path.name
            except (OSError, ValueError, TypeError, KeyError, AttributeError):
                pass
        rows.append({'bot': int(index), 'level': level if type(level) is int else None,
                     'gold': gold if type(gold) is int and gold >= 0 else None,
                     'connected': row.get('connected'), 'map': row.get('map', ''),
                     'snapshot_age_seconds': max(0, int(now-stamp)) if type(stamp) in (int, float) else None,
                     'source': source})
    return rows


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    root = Path(__file__).resolve().parents[1]
    try:
        rows = collect(root)
        print('№ бота | ЛВЛ | Золото | В сети | Возраст снимка, сек.')
        display = lambda v: '?' if v is None else str(v)
        for row in rows:
            connected = {True: 'да', False: 'нет', None: '?'}[row['connected']]
            print(f"{row['bot']:6} | {display(row['level']):>3} | {display(row['gold']):>10} | {connected:>6} | {display(row['snapshot_age_seconds'])}")
        known = [r['gold'] for r in rows if r['gold'] is not None]
        print(f'Сумма известных остатков: {sum(known)} G; данных о золоте нет у {len(rows)-len(known)} ботов.')
        print('Это последние снимки. После остановки сервера значения не обновляются.')
        target = root / 'bot-levels-and-gold.csv'
        with target.open('w', newline='', encoding='utf-8-sig') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ['bot', 'level', 'gold'])
            writer.writeheader()
            writer.writerows(rows)
        print('CSV для Excel: ' + str(target))
    except (OSError, ValueError, TypeError) as error:
        print('Не удалось прочитать/сохранить отчёт. Запусти ботов и повтори. ' + type(error).__name__)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
