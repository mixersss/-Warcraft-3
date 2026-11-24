"""Add one level trophy to the engine's ordinary monster loot records."""
import struct

ROW_SIZE = 968
DROP_OFFSET = 428
DROP_LIMIT = 10
DUNGEON_AND_TROPHIES = {4915, 938, 2374, 2843, 2844, 3141, *range(2461, 2488)}


def positives(ids, rates):
    return [(int(i), int(rate)) for i, rate in zip(ids.split(b","), rates.split(b","))
            if int(i)>0 and int(rate)>0]


def patch(text, binary, kinds, trophies):
    output = []
    edits = {}
    managed = 0
    fallback = 0
    for line in text.splitlines(keepends=True):
        body = line.rstrip(b"\r\n")
        fields = body.split(b"\t")
        if len(fields)>60 and fields[0].strip().isdigit() and fields[4].strip()==b"5":
            level = int(fields[60])
            trophy = 5618 + level//10 - 1
            if trophy in trophies:
                model = int(fields[0])
                before = positives(fields[46], fields[47])
                stock = before.copy()
                native = next((i for i,(identity,_) in enumerate(stock) if identity==trophy),None)
                if native is not None:
                    managed += 1
                    output.append(line)
                    continue
                if len(stock)<DROP_LIMIT:
                    stock.append((trophy,100))
                elif len(stock)==DROP_LIMIT:
                    expendable = next((i for i,(identity,_) in enumerate(stock)
                                      if kinds.get(identity)==41 and identity not in DUNGEON_AND_TROPHIES
                                      and identity not in trophies and not 6410<=identity<=6439),None)
                    if expendable is not None:
                        stock[expendable]=(trophy,100)
                if stock==before:
                    fallback += 1
                else:
                    managed += 1
                    fields[46] = b",".join(str(i).encode() for i,_ in stock)
                    fields[47] = b",".join(str(rate).encode() for _,rate in stock)
                    line = b"\t".join(fields)+line[len(body):]
                    edits[model]=(before,stock)
        output.append(line)
    if binary is not None and edits:
        if not binary.startswith(struct.pack("<I",ROW_SIZE)) or (len(binary)-4)%ROW_SIZE:
            raise ValueError("Неизвестный формат CharacterInfo.bin для уровня трофеев.")
        buf = bytearray(binary)
        remaining = set(edits)
        for pos in range(4,len(binary),ROW_SIZE):
            identity, = struct.unpack_from("<I",binary,pos+4)
            if identity not in edits:
                continue
            before,after = edits[identity]
            offset=pos+DROP_OFFSET
            stock=[struct.unpack_from("<ii",binary,offset+i*8) for i in range(DROP_LIMIT)]
            if identity not in remaining or stock[:len(before)]!=before or any(
                    item>0 and rate>0 for item,rate in stock[len(before):]):
                raise ValueError(f"Обычная добыча TXT и BIN расходится у моба {identity}.")
            remaining.remove(identity)
            for index,(item,rate) in enumerate(after):
                struct.pack_into("<ii",buf,offset+index*8,item,rate)
        if remaining:
            raise ValueError(f"В CharacterInfo.bin отсутствует модель {min(remaining)}.")
        binary=bytes(buf)
    return b"".join(output),binary,managed,fallback
