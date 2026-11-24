"""Increase each ordinary persistent spawn by half, rounded up."""
import re
import struct

OLD_MARKER = b"WORLD_EXPANSION_DENSITY_V1"
MARKER = b"WORLD_EXPANSION_DENSITY_V2"
CREATE = re.compile(rb"CreateCha\s*\(\s*(\d+)\s*,\s*\d+\s*,\s*\d+\s*,\s*-?\d+\s*,\s*(\d+)\s*\)\s*;?")
MAP = re.compile(rb"(?m)^\s*(?:local +)?m\s*=\s*SetCurMap\([\'\"\w]+\)\s*\r?\nif\s+m\s*==\s*1\s+then\s*\r?\n([\s\S]*?)^end\s*$")
INCLUDE = re.compile(rb"PM\s*\(\s*[\"\']([\w-]+)[\"\']\s*\)\s*;?")


def monster_ids(raw):
    return {int(row[0]) for line in raw.splitlines() for row in (line.split(b"\t"),)
            if len(row)>4 and row[0].strip().isdigit() and row[4].strip()==b"5"}


def newline(raw):
    return b"\r\n" if b"\r\n" in raw else b"\n"


def old_base(count, parity):
    approximate = count * 2 // 3
    for candidate in range(max(1, approximate-1), approximate+3):
        if candidate + (candidate+parity)//2 == count:
            return candidate
    raise ValueError("Количество в таблице V1 не совпадает с известной схемой.")


def table_plan(raw, monsters):
    if MARKER in raw:
        return raw, 0, {}
    columns = {}
    output = []
    previous = {}
    extra = 0
    legacy = OLD_MARKER in raw
    for line in raw.splitlines(keepends=True):
        if OLD_MARKER in line:
            continue
        fields = line.split(b"\t")
        if len(fields)>=8 and fields[0].strip().isdigit():
            values = [field.split(b",") for field in fields[4:8]]
            try:
                models, counts, odds, delays = [list(map(int, group)) for group in values]
            except ValueError:
                output.append(line)
                continue
            seen = list(zip(models, counts, odds, delays))
            if len(seen)==len(models)==len(counts):
                original = list(seen)
                changed = list(seen)
                for index, (model, count, odds, delay) in enumerate(seen):
                    if model not in monsters or count<1:
                        continue
                    parity = previous.get(model, 0)
                    base = old_base(count, parity) if legacy else count
                    previous[model] = (base+parity)%2
                    target = base + (base+1)//2
                    original[index] = (model, base, odds, delay)
                    changed[index] = (model, target, odds, delay)
                    if target!=count:
                        values[1][index] = str(target).encode()
                    extra += target-count
                identity = int(fields[0])
                if identity in columns:
                    raise ValueError("Повтор строки в таблице спавна.")
                columns[identity] = (seen, original, changed)
                fields[5] = b",".join(values[1])
                line = b"\t".join(fields)
        output.append(line)
    if not extra and not legacy:
        return raw, 0, {}
    nl = newline(raw)
    return b"".join(output).rstrip(b"\r\n")+nl+b"// "+MARKER+nl, extra, columns


def table(raw, monsters):
    out, extra, _ = table_plan(raw, monsters)
    return out, extra


def update_binary(raw, columns):
    """Certify record layout against all matched text rows before changing counts."""
    if not columns or len(raw)<4:
        raise ValueError("нет строк для сверки")
    size, = struct.unpack_from("<I", raw)
    if not 125<=size<=4096 or (len(raw)-4)%size:
        raise ValueError("неизвестный размер записи")
    records = {}
    for pos in range(4,len(raw),size):
        identity, = struct.unpack_from("<I",raw,pos+4)
        if identity not in columns or identity in records:
            raise ValueError("ID в TXT и BIN расходятся")
        records[identity]=pos
    if set(records)!=set(columns):
        raise ValueError("TXT и BIN содержат разные строки")

    def match(pos, offset, rows):
        return any(all(struct.unpack_from("<4i",raw,pos+offset+16*i)==item
                       for i,item in enumerate(items)) for items in rows[:2])

    pos = next(iter(records.values()))
    sizes = [len(rows[0]) for rows in columns.values()]
    offsets = [offset for offset in range(8,size-16*max(sizes)+1,4)
               if match(pos,offset,columns[next(iter(records))])
               and all(match(at,offset,columns[i]) for i,at in records.items())]
    if len(offsets)!=1:
        raise ValueError("формат записей BIN не подтверждён")
    out = bytearray(raw)
    for identity, pos in records.items():
        for i, (_,target,_,_) in enumerate(columns[identity][2]):
            struct.pack_into("<i",out,pos+offsets[0]+16*i+4,target)
    return bytes(out)


def startup(raw, monsters):
    if MARKER in raw or b"--[[" in raw:
        return raw, 0
    lines = [line for line in raw.splitlines(keepends=True) if OLD_MARKER not in line]
    parsed = []
    for line in lines:
        code = line.split(b"--",1)[0].strip()
        candidate = CREATE.fullmatch(code) if code else None
        if code and not candidate:
            return raw, 0
        parsed.append((line,candidate))
    output = []
    seen = {}
    extra = 0
    nl = newline(raw)
    index = 0
    while index<len(parsed):
        line,candidate=parsed[index]
        index+=1
        output.append(line.rstrip(b"\r\n")+nl)
        if not candidate:
            continue
        model,delay=map(int,candidate.groups())
        if model not in monsters or delay<=0:
            continue
        if delay<=600:
            seen[model]=seen.get(model,0)+1
        if OLD_MARKER in raw and delay<=600 and seen[model]%2==0:
            if index>=len(parsed) or parsed[index][0].strip()!=candidate[0]:
                return raw,0  # locally edited V1 script
            index+=1
        else:
            extra+=1
        output.append(candidate[0]+nl)
    if not extra:
        return raw,0
    return b"".join(output).rstrip(b"\r\n")+nl+b"-- "+MARKER+nl,extra


def plan(resource):
    monsters=monster_ids((resource/"CharacterInfo.txt").read_bytes())
    changes={}
    skipped=[]
    added=0
    for folder in sorted(p for p in resource.iterdir() if p.is_dir()):
        name=(folder.name+"ChaSpn").casefold()
        variants={p.suffix.lower():p for p in folder.iterdir() if p.stem.casefold()==name}
        path,binary=variants.get(".txt"),variants.get(".bin")
        if not path:
            if binary:
                skipped.append(binary.relative_to(resource).as_posix()+" (нет TXT)")
            continue
        raw=path.read_bytes()
        result,count,columns=table_plan(raw,monsters)
        if result==raw:
            continue
        if binary:
            try:
                data=binary.read_bytes()
                patched=update_binary(data,columns)
            except ValueError as error:
                skipped.append(binary.relative_to(resource).as_posix()+f" ({error})")
                continue
            if patched!=data:
                changes[binary]=patched
        changes[path]=result
        added+=count
    directory=resource/"script/monster"
    listing=directory/"mlist.lua"
    if listing.is_file():
        scripts={p.stem.casefold():p for p in directory.glob("*.lua")}
        used=set()
        source=b"\n".join(line.split(b"--",1)[0] for line in listing.read_bytes().splitlines())
        for block in MAP.findall(source):
            parts=[line.strip() for line in block.splitlines()
                   if line.strip() and not line.strip().startswith(b"LG(")]
            calls=[INCLUDE.fullmatch(part) for part in parts]
            if not calls or not all(calls):
                continue
            for call in calls:
                path=scripts.get(call[1].decode("ascii").casefold())
                if path and path not in used:
                    used.add(path)
                    raw=path.read_bytes()
                    result,count=startup(raw,monsters)
                    if count:
                        changes[path]=result
                        added+=count
                    elif MARKER not in raw and any(
                            CREATE.fullmatch(line.split(b"--",1)[0].strip())
                            for line in raw.splitlines()):
                        skipped.append(path.relative_to(resource).as_posix()+" (сложный сценарий или нет подходящих мобов)")
    return changes,added,skipped
