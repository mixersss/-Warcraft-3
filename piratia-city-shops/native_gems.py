"""Remove Alpha90's additional gem roll and verify stock client gem records."""
import hashlib
import json
import re
import struct

from personal_forge import SCRIPT, MARKER, START as FORGE_START, END as FORGE_END, forge_script

GEMS = (860, 861, 862, 863, 864, 865, 866, 1012)
ROLL = re.compile(
    rb"(?m)^    if math\.random\(1,100\)>3 then return end\r?\n"
    rb"    Owner56GemStats\.rolls=Owner56GemStats\.rolls\+1\r?\n"
    rb"    Owner57GroundDrop\(dead,(?:Owner56GemIDs\[math\.random\(1,8\)\],1"
    rb"|ground_stones\[math\.random\(1,8\)\],1|(?:6399|5608)\+math\.random\(1,8\),99)\)\r?\n"
)
VANILLA = b"    -- OWNER_NATIVE_GEM_DROPS"


def restore_script(raw):
    nl = b"\r\n" if b"\r\n" in raw else b"\n"
    known = len(re.findall(rb"(?m)^function Owner56GroundGem\(", raw))
    if not known or known>2 or b"function Owner57GroundDrop(" not in raw:
        raise ValueError("Не найден знакомый серверный обработчик добычи Alpha90.")
    raw = ROLL.sub(lambda _: VANILLA+nl, raw)
    if raw.count(VANILLA)!=known or b"Owner56GemStats.rolls=Owner56GemStats.rolls+1" in raw:
        raise ValueError("Логика выпадения гемов отличается от известных версий Alpha90.")
    lines = {
        b"    for _,id in ipairs(Owner56GemIDs) do allowed[id]=true end",
        b"for _,id in ipairs(ground_stones) do replaced[id]=true end",
    }
    return b"".join(line for line in raw.splitlines(keepends=True)
                    if line.rstrip(b"\r\n") not in lines)


def native_text(raw):
    seen=set()
    result=[]
    for line in raw.splitlines(keepends=True):
        fields=line.split(b"\t")
        if fields[0].strip().isdigit() and int(fields[0]) in GEMS:
            identity=int(fields[0])
            if identity in seen or len(fields)<=22 or fields[1].endswith(b" (Lv1)"):
                raise ValueError(f"Не удалось подтвердить исходную запись гема {identity} в ItemInfo.txt.")
            seen.add(identity)
            if int(fields[10])!=49:
                fields[10]=b"49"
            if int(fields[20])!=1:
                fields[20]=b"1"
            line=b"\t".join(fields)
        result.append(line)
    if seen!=set(GEMS):
        raise ValueError("В ItemInfo.txt отсутствуют штатные гемы.")
    return b"".join(result)


def native_binary(raw):
    if not raw.startswith(struct.pack("<I",868)) or (len(raw)-4)%868:
        raise ValueError("Неизвестный формат ItemInfo.bin.")
    result=bytearray(raw)
    seen=set()
    for pos in range(4,len(raw),868):
        identity,=struct.unpack_from("<I",raw,pos+4)
        if identity not in GEMS:
            continue
        if (identity in seen or struct.unpack_from("<I",raw,pos+108)[0]!=identity
                or raw[pos+112:pos+192].split(b"\0",1)[0].endswith(b" (Lv1)")):
            raise ValueError(f"Не удалось подтвердить штатную запись гема {identity} в ItemInfo.bin.")
        seen.add(identity)
        struct.pack_into("<h",result,pos+308,49)
        struct.pack_into("<i",result,pos+352,1)
    if seen!=set(GEMS):
        raise ValueError("В ItemInfo.bin отсутствуют штатные гемы.")
    return bytes(result)


def check_client_stones(client):
    stones=next((p for p in client.parent.iterdir() if p.name.casefold()=="stoneinfo.bin"),None)
    if stones is None:
        raise ValueError("Рядом с клиентским ItemInfo.bin не найден StoneInfo.bin. Укажи папку запущенного игрового клиента.")
    raw=stones.read_bytes()
    stride=192
    if not raw.startswith(struct.pack("<I",stride)) or (len(raw)-4)%stride:
        raise ValueError("Формат клиентского StoneInfo.bin не подтверждён.")
    found={struct.unpack_from("<I",raw,pos+108)[0] for pos in range(4,len(raw),stride)
           if raw[pos+128:pos+192].split(b"\0",1)[0]}
    if set(GEMS)-found:
        raise ValueError("В клиентском StoneInfo.bin отсутствуют штатные эффекты гемов.")


def plan(resource, client):
    check_client_stones(client)
    script=resource/SCRIPT
    text=resource/"ItemInfo.txt"
    binary=resource/"ItemInfo.bin"
    old={p:p.read_bytes() for p in (script,text,binary,client)}
    updated={script:restore_script(old[script]),text:native_text(old[text]),
             binary:native_binary(old[binary]),client:native_binary(old[client])}
    # On older installations update the existing personal forge in place so
    # old acquired stacks can be exchanged without touching NPC placement.
    if FORGE_START in updated[script]:
        if updated[script].count(FORGE_START)!=1 or updated[script].count(FORGE_END)!=1:
            raise ValueError("Блок личной кузницы неполный или повторяется.")
        nl=b"\r\n" if b"\r\n" in updated[script] else b"\n"
        patch=forge_script().encode("cp1251").replace(b"\n",nl)
        updated[script]=re.sub(re.escape(FORGE_START)+rb"[\s\S]*?"+re.escape(FORGE_END),
                               lambda _:patch,updated[script])
    changes={p:raw for p,raw in updated.items() if raw!=old[p]}
    receipt=resource/MARKER
    if receipt.is_file():
        ledger=json.loads(receipt.read_text(encoding="utf-8"))
        for path in (script,text,binary):
            if path in changes:
                name=path.relative_to(resource).as_posix()
                if name in ledger.get("installed_sha256",{}):
                    ledger["installed_sha256"][name]=hashlib.sha256(changes[path]).hexdigest()
        if any(path in changes for path in (script,text,binary)):
            changes[receipt]=(json.dumps(ledger,ensure_ascii=False,indent=2)+"\n").encode()
    return changes
