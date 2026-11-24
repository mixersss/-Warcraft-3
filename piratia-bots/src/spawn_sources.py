"""Read supported server spawn declarations without executing server Lua."""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from diagnostic_io import write_snapshot

MAP_BLOCK = re.compile(
    r'^(?:local +)?m\s*=\s*SetCurMap\(["\'](\w+)["\']\)\s*\n'
    r'if\s+m\s*==\s*1\s+then\s*\n(.*?)^end\s*$', re.M | re.S)
INCLUDE = re.compile(r'PM\s*\(\s*["\']([\w-]+)["\']\s*\)\s*;?')
SPAWN = re.compile(r'(?:local\s+(\w+)\s*=\s*)?CreateCha\s*\(\s*'
                   r'(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*-?\d+\s*,\s*(\d+)\s*\)\s*;?')
SIDE = re.compile(r'SetChaSideID\s*\(\s*(\w+)\s*,\s*\d+\s*\)\s*;?')


def lua_lines(path):
    text = path.read_bytes().decode('gb18030', errors='replace').lstrip('\ufeff')
    text = re.sub(r'--\[(=*)\[.*?\]\1\]', '\n', text, flags=re.S)
    return [code for line in text.splitlines() if (code := line.split('--', 1)[0].strip())]


def startup_spawns(resource, maps):
    directory = resource/'script'/'monster'
    index = directory/'mlist.lua'
    rows = set()
    if not index.is_file():
        return rows
    scripts = {path.stem.casefold(): path for path in sorted(directory.glob('*.lua')) if path.is_file()}
    for match in MAP_BLOCK.finditer('\n'.join(lua_lines(index))):
        name, body = match.groups()
        if name not in maps:
            continue
        statements = [line for line in body.splitlines() if line and not line.startswith('LG(')]
        includes = [INCLUDE.fullmatch(line) for line in statements]
        if not all(includes):
            continue
        for include in includes:
            path = scripts.get(include[1].casefold())
            if path is None:
                continue
            parsed = []
            last_local = None
            for line in lua_lines(path):
                spawn, side = SPAWN.fullmatch(line), SIDE.fullmatch(line)
                if spawn:
                    last_local = spawn[1]
                    model, x, y, respawn = map(int, spawn.groups()[1:])
                    if 0 <= x < 409600 and 0 <= y < 409600:
                        parsed.append((name, model, x, y, x, y, 1, respawn))
                elif not side or side[1] != last_local:
                    break
            else:
                rows.update(parsed)
    return rows


def table_spawns(resource, maps):
    def numbers(field):
        return [int(x) for x in field.split(',') if x.strip().lstrip('-').isdigit()]

    rows = set()
    for name in maps:
        table = resource/name/(name+'ChaSpn.txt')
        if not table.is_file():
            continue
        for line in table.read_bytes().decode('gb18030', errors='replace').splitlines():
            fields = line.split('\t')
            if len(fields) < 8 or not fields[0].isdigit():
                continue
            low, high = numbers(fields[1]), numbers(fields[2])
            if len(low) != 2 or len(high) != 2 or not all(0 <= a <= b < 409600 for a, b in zip(low, high)):
                continue
            counts, delays = numbers(fields[5]), numbers(fields[7])
            for i, model in enumerate(numbers(fields[4])):
                if model > 0:
                    rows.add((name, model, *low, *high, counts[min(i, len(counts)-1)] if counts else 0,
                              delays[min(i, len(delays)-1)] if delays else 0))
    return rows


def compile_spawns(resource, assets, include_tables=True):
    maps = json.loads((assets/'world-navigation.json').read_text(encoding='utf-8'))['maps']
    monsters = json.loads((assets/'world-mobs.json').read_text(encoding='utf-8'))['monsters']
    startup = startup_spawns(resource, maps)
    tables = table_spawns(resource, maps) if include_tables else set()
    result = defaultdict(list)
    for kind, rows in (('startup', startup), ('table', tables)):
        for name, model, *coordinates in sorted(rows):
            if str(model) in monsters:
                result[name].append([model, *coordinates, kind])
    return {'version': 1, 'maps': dict(result)}


def refresh_local_spawns(assets, data, resource=None):
    if resource is None:
        for filename in ('server-spawn-source.json','server-source.json'):
            try:
                location = json.loads((data/filename).read_text(encoding='utf-8')).get('resource')
                if isinstance(location, str) and location and Path(location).is_dir():
                    resource = Path(location)
                    break
            except (OSError, ValueError, AttributeError):
                continue
    if resource is None:
        return {'mode': 'bundled'}
    try:
        resource=Path(resource)
        if (resource/'resource'/'script').is_dir() and not (resource/'script').is_dir():
            resource=resource/'resource'
        compiled = compile_spawns(resource, assets)
        if compiled['maps'] and write_snapshot(data/'server-spawns.json', compiled):
            return {'mode': 'server', 'maps': len(compiled['maps']),
                    'placements': sum(map(len, compiled['maps'].values()))}
    except (OSError, ValueError, TypeError):
        pass
    return {'mode': 'last_saved_or_bundled'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('resource', type=Path)
    parser.add_argument('output', type=Path, nargs='?')
    parser.add_argument('--startup-only', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output is None:
        data = root/'data'
        data.mkdir(exist_ok=True)
        result = refresh_local_spawns(root/'assets', data, args.resource)
        if result['mode'] != 'server':
            parser.error('No readable supported sources, or could not save the index')
        write_snapshot(data/'server-spawn-source.json', {'resource': str(args.resource.resolve())})
        print(f"Maps: {result['maps']}. Placements: {result['placements']}. Restart bots.")
        raise SystemExit(0)
    compiled = compile_spawns(args.resource, root/'assets', not args.startup_only)
    if not compiled['maps']:
        parser.error('No supported spawn sources found')
    if not write_snapshot(args.output, compiled):
        parser.error('Could not write the spawn index')
