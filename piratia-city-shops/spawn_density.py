"""Read and reverse the verified Alpha90 spawn multipliers."""
import re
import struct

OLD_MARKER = b"WORLD_EXPANSION_DENSITY_V1"
MARKER = b"WORLD_EXPANSION_DENSITY_V2"
CREATE = re.compile(rb"CreateCha\s*\(\s*(\d+)\s*,\s*\d+\s*,\s*\d+\s*,\s*-?\d+\s*,\s*(\d+)\s*\)\s*;?")


def monster_ids(raw):
    return {int(row[0]) for line in raw.splitlines() for row in (line.split(b"\t"),)
            if len(row)>4 and row[0].strip().isdigit() and row[4].strip()==b"5"}


def newline(raw):
    return b"\r\n" if b"\r\n" in raw else b"\n"


def original_count(count, parity):
    approximate = count * 2 // 3
    for candidate in range(max(1, approximate-1), approximate+3):
        if candidate + (candidate+parity)//2 == count:
            return candidate
    raise ValueError("Количество не соответствует установленному множителю спавна.")


def density_version(raw, prefix):
    for version, marker in ((2, MARKER), (1, OLD_MARKER)):
        if prefix+marker in raw.splitlines():
            return version
    return 0


def table_plan(raw, monsters, *, restore=False):
    version = density_version(raw, b"// ")
    if (restore and not version) or (not restore and version==2):
        return raw, 0, {}
    columns = {}
    output = []
    previous = {}
    extra = 0
    for line in raw.splitlines(keepends=True):
        if line.rstrip(b"\r\n") in (b"// "+OLD_MARKER, b"// "+MARKER):
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
                    base = original_count(count, parity if version==1 else 1) if version else count
                    previous[model] = (base+parity)%2
                    target = base if restore else base+(base+1)//2
                    original[index] = (model, base, odds, delay)
                    changed[index] = (model, target, odds, delay)
                    if target!=count:
                        values[1][index] = str(target).encode()
                    extra += count-target if restore else target-count
                identity = int(fields[0])
                if identity in columns:
                    raise ValueError("Повтор строки в таблице спавна.")
                columns[identity] = (seen, original, changed)
                fields[5] = b",".join(values[1])
                line = b"\t".join(fields)
        output.append(line)
    if restore:
        if not extra:
            raise ValueError("В отмеченном файле нет увеличенных групп.")
        return b"".join(output), extra, columns
    if not extra and not version:
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


def startup(raw, monsters, *, restore=False):
    version = density_version(raw, b"-- ")
    if (restore and not version) or (not restore and version==2) or b"--[[" in raw:
        return raw, 0
    lines = [line for line in raw.splitlines(keepends=True)
             if line.rstrip(b"\r\n") not in (b"-- "+OLD_MARKER,b"-- "+MARKER)]
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
        duplicated = version==2 or (version==1 and delay<=600 and seen[model]%2==0)
        if duplicated:
            if index>=len(parsed) or parsed[index][0].strip()!=candidate[0]:
                return raw,0  # locally edited marked script
            index+=1
        if restore:
            extra+=int(duplicated)
        else:
            extra+=int(not duplicated)
            output.append(candidate[0]+nl)
    if not extra:
        return raw,0
    if restore:
        return b"".join(output),extra
    return b"".join(output).rstrip(b"\r\n")+nl+b"-- "+MARKER+nl,extra


def restore_plan(resource):
    monsters=monster_ids((resource/"CharacterInfo.txt").read_bytes())
    changes={}
    skipped=[]
    removed=0
    for folder in sorted(p for p in resource.iterdir() if p.is_dir()):
        name=(folder.name+"ChaSpn").casefold()
        variants={p.suffix.lower():p for p in folder.iterdir() if p.stem.casefold()==name}
        path,binary=variants.get(".txt"),variants.get(".bin")
        if not path:
            continue
        raw=path.read_bytes()
        if not density_version(raw,b"// "):
            continue
        try:
            result,count,columns=table_plan(raw,monsters,restore=True)
            if binary:
                original=binary.read_bytes()
                restored=update_binary(original,columns)
                if restored!=original:
                    changes[binary]=restored
        except ValueError as error:
            skipped.append(path.relative_to(resource).as_posix()+f" ({error})")
            continue
        changes[path]=result
        removed+=count
    for path in sorted((resource/"script/monster").glob("*.lua")):
        raw=path.read_bytes()
        if not density_version(raw,b"-- "):
            continue
        result,count=startup(raw,monsters,restore=True)
        if count:
            changes[path]=result
            removed+=count
        else:
            skipped.append(path.relative_to(resource).as_posix()+" (строки спавна отличаются)")
    return changes,removed,skipped
