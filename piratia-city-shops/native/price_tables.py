"""Byte-preserving price edits for this verified classic868-byte item format."""
import struct

def patch_binary(raw,items):
 if len(raw)<4 or struct.unpack_from('<I',raw)[0]!=868 or (len(raw)-4)%868:raise ValueError('Неизвестный формат ItemInfo.bin')
 output=bytearray(raw);seen=set()
 for pos in range(4,len(raw),868):
  identity=struct.unpack_from('<I',raw,pos+4)[0]
  if identity!=struct.unpack_from('<I',raw,pos+108)[0] or identity in seen:raise ValueError('Неверные ID в ItemInfo.bin')
  seen.add(identity)
  if identity in items:
   item=items[identity]
   if struct.unpack_from('<h',raw,pos+308)[0]!=item['kind']:raise ValueError('Не совпадает тип предмета ID'+str(identity))
   struct.pack_into('<i',output,pos+320,item['price'])
 missing=set(items)-seen
 if missing:raise ValueError('В ItemInfo.bin нет нужных ID: '+','.join(map(str,sorted(missing)[:8])))
 return bytes(output)

def patch_text(raw,items):
 output=[];seen=set()
 for line in raw.splitlines(keepends=True):
  fields=line.split(b'\t')
  if len(fields)>22 and fields[0].strip().isdigit():
   identity=int(fields[0]);
   if identity in seen and identity in items:raise ValueError('Повтор продаваемого ID в ItemInfo.txt')
   seen.add(identity)
   if identity in items:
    item=items[identity]
    if int(fields[10])!=item['kind']:raise ValueError('Не совпадает тип предмета ID'+str(identity))
    old=fields[22];prefix=old[:len(old)-len(old.lstrip())];suffix=old[len(old.rstrip()):]
    fields[22]=prefix+str(item['price']).encode()+suffix;line=b'\t'.join(fields)
  output.append(line)
 if set(items)-seen:raise ValueError('В ItemInfo.txt отсутствуют предметы магазина')
 return b''.join(output)
