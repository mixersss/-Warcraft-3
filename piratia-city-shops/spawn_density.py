"""Raise verified ordinary monster populations by fifty percent."""
import re

MARKER = b"WORLD_EXPANSION_DENSITY_V1"
CREATE = re.compile(rb"CreateCha\s*\(\s*(\d+)\s*,\s*\d+\s*,\s*\d+\s*,\s*-?\d+\s*,\s*(\d+)\s*\)\s*;?")
MAP = re.compile(rb"(?m)^\s*(?:local +)?m\s*=\s*SetCurMap\([\'\"\w]+\)\s*\r?\nif\s+m\s*==\s*1\s+then\s*\r?\n([\s\S]*?)^end\s*$")
INCLUDE = re.compile(rb"PM\s*\(\s*[\"\']([\w-]+)[\"\']\s*\)\s*;?")


def monster_ids(raw):
    return {int(row[0]) for line in raw.splitlines() for row in (line.split(b"\t"),)
            if len(row)>4 and row[0].isdigit() and row[4].strip()==b"5"}


def newline(raw):
    return b"\r\n" if b"\r\n" in raw else b"\n"


def half(count, model, odd):
    # Carry odd halves across placements of the same species.
    change, odd[model] = divmod(count + odd.get(model, 0), 2)
    return change


def table(raw, monsters):
    if MARKER in raw:
        return raw, 0
    out = []
    odd = {}
    extra = 0
    for original in raw.splitlines(keepends=True):
        fields = original.split(b"\t")
        if len(fields) >= 8 and fields[0].isdigit():
            models = fields[4].split(b",")
            counts = fields[5].split(b",")
            if len(models) == len(counts) and all(v.strip().isdigit() for v in models+counts):
                for index, (model, count) in enumerate(zip(map(int, models), map(int, counts))):
                    if model in monsters and count:
                        added = half(count, model, odd)
                        if added:
                            counts[index] = str(count+added).encode()
                            extra += added
                fields[5] = b",".join(counts)
                original = b"\t".join(fields)
        out.append(original)
    if not extra:
        return raw, 0
    nl = newline(raw)
    return b"".join(out).rstrip(b"\r\n")+nl+b"// "+MARKER+nl, extra


def startup(raw, monsters):
    if MARKER in raw:
        return raw, 0
    parsed = []
    for line in raw.splitlines(keepends=True):
        code = line.split(b"--", 1)[0].strip()
        candidate = CREATE.fullmatch(code) if code else None
        if code and not candidate:
            return raw, 0
        parsed.append((line, candidate))
    odd = {}
    extra = 0
    output = []
    nl = newline(raw)
    for line, candidate in parsed:
        output.append(line)
        if candidate:
            model, delay = map(int, candidate.groups())
            if model in monsters and 0 < delay <= 600 and half(1, model, odd):
                if not line.endswith((b"\r", b"\n")):
                    output.append(nl)
                output.append(candidate[0]+nl)
                extra += 1
    if not extra:
        return raw, 0
    return b"".join(output).rstrip(b"\r\n")+nl+b"-- "+MARKER+nl, extra


def plan(resource):
    monsters = monster_ids((resource/"CharacterInfo.txt").read_bytes())
    changes = {}
    skipped = []
    added = 0
    for path in sorted(resource.glob("*/*ChaSpn.txt")):
        if any(p.suffix.lower()==".bin" and p.stem.lower()==path.stem.lower()
               for p in path.parent.iterdir()):
            skipped.append(path.relative_to(resource).as_posix())
            continue
        raw = path.read_bytes()
        result, count = table(raw, monsters)
        if count:
            changes[path] = result
            added += count
    directory = resource/"script/monster"
    listing = directory/"mlist.lua"
    if listing.is_file():
        scripts = {p.stem.lower(): p for p in directory.glob("*.lua")}
        used = set()
        index_source = b"\n".join(line.split(b"--", 1)[0] for line in listing.read_bytes().splitlines())
        for block in MAP.findall(index_source):
            parts = [c for line in block.splitlines() if (c := line.split(b"--", 1)[0].strip())
                     and not c.startswith(b"LG(")]
            calls = [INCLUDE.fullmatch(c) for c in parts]
            if not calls or not all(calls):
                continue
            for match in calls:
                path = scripts.get(match[1].decode("ascii").lower())
                if path and path not in used:
                    used.add(path)
                    result, count = startup(path.read_bytes(), monsters)
                    if count:
                        changes[path] = result
                        added += count
    return changes, added, skipped
