"""Install five owner-priced shops while preserving existing resources byte-for-byte."""
import argparse,base64,hashlib,json,os,re,struct,sys,zlib
from pathlib import Path
from datetime import datetime
from render import render,ROOT
MARK=b'OWNER_CITY_SHOPS_V1_BEGIN'
DEFAULT_POINTS=((2247,2777),(2247,2779),(2247,2781),(2247,2783),(2247,2784))
DEFAULT_CENTER=DEFAULT_POINTS[0]
ANCHOR=b'elseif item.func == TradeGoods then'
HOOK=b'elseif item.func == OwnerMarketBuy then\n\t\t\treturn OwnerMarketBuy(character, npc, item.p1, item.p2)\n\t\t'


def locate(selected):
    p=Path(selected).expanduser()
    for root in (p/'resource',p,p.parent/'resource'):
        if (root/'script/MisScript/NpcScript01.lua').is_file():return root
    raise ValueError('Не найдена серверная resource/script/MisScript/NpcScript01.lua')


def binary_rows(raw):
    if len(raw)<4 or struct.unpack_from('<I',raw)[0]!=428 or (len(raw)-4)%428:
        raise ValueError('Неизвестный формат garnerNPC.bin; файлы не изменены')
    return [raw[i:i+428] for i in range(4,len(raw),428)]


def npc_rows(raw):
    result={}
    for line in raw.splitlines():
        parts=line.split(b'\t')
        if len(parts)>=13 and parts[0].strip().isdigit():
            identity=int(parts[0]);
            if identity in result:raise ValueError('Повтор ID в garnernpc.txt')
            result[identity]=parts
    return result


def validate_npcs(text,raw):
    rows=npc_rows(text);records=binary_rows(raw)
    if len(rows)!=len(records):raise ValueError('garnernpc.txt и garnerNPC.bin содержат разное число НПС')
    for index,record in enumerate(records):
        identity=struct.unpack_from('<I',record,4)[0];row=rows.get(identity)
        if row is None:raise ValueError('ID НПС не совпадают между txt/bin')
        checks=[record[108:236].split(b'\0')[0]==row[1].strip(),
                record[394:410].split(b'\0')[0]==row[11].strip(),
                struct.unpack_from('<H',record,238)[0]==int(row[3]),
                list(struct.unpack_from('<ii',record,244))==list(map(int,row[5].split(b','))),
                list(struct.unpack_from('<ii',record,252))==list(map(int,row[6].split(b','))),
                struct.unpack_from('<I',record,100)[0]==identity]
        if not all(checks):raise ValueError('Не совпадает структура НПС ID'+str(identity))
    return rows,records


def placement(center,avoid=()):
    data=json.loads((ROOT/'city-safety.json').read_text());mask=zlib.decompress(base64.b64decode(data['safe_zlib']))
    ox,oy=data['origin'];w,h=data['width'],data['height'];x,y=center
    candidates=[]
    for dy in range(-10,11):
        for dx in range(-10,11):
            px,py=x+dx,y+dy;cx,cy=px-ox,py-oy
            if (0<=cx<w and 0<=cy<h and mask[cy*w+cx]
                    and all((px+.5-a)**2+(py+.5-b)**2>=9 for a,b in avoid)):
                candidates.append((dx*dx+dy*dy,px,py))
    result=[]
    for _,px,py in sorted(candidates):
        if all((px-a)**2+(py-b)**2>=9 for a,b in result):result.append((px,py))
        if len(result)==5:return result
    raise ValueError('Рядом с указанной точкой нет пяти проверенных сухих мест в безопасной зоне Аргента')


def plan(root,center,catalog=None):
    catalog=catalog or json.loads((ROOT/'catalog.json').read_text())
    expected={i['id']:i for shop in catalog['shops'] for i in shop['items']}
    found={}
    for line in (root/'ItemInfo.txt').read_bytes().splitlines():
        columns=line.split(b'\t')
        if len(columns)>10 and columns[0].strip().isdigit():
            identity=int(columns[0]);found[identity]=(columns[1].strip(),int(columns[10]))
    for identity,item in expected.items():
        if found.get(identity)!=(item['name'].encode('ascii').strip(),item['kind']):
            raise ValueError('Другая версия предмета ID'+str(identity)+'; нужна сверка каталога')
    script=Path('script/MisScript/NpcScript01.lua');sdk=Path('script/MisSdk/NpcSdk.lua')
    table=Path('garner/garnernpc.txt');binary=Path('garner/garnerNPC.bin')
    originals={p:(root/p).read_bytes() for p in (script,sdk,table,binary)}
    if MARK in originals[script] or b'item.func == OwnerMarketBuy' in originals[sdk]:
        raise ValueError('Маркеры установки уже есть, но контрольная запись не подтверждена')
    if originals[sdk].count(ANCHOR)!=1:raise ValueError('Другая версия NpcSdk.lua; нужна проверка точки подключения')
    textrows,records=validate_npcs(originals[table],originals[binary])
    existing=[tuple(int(v)/100 for v in row[5].split(b',')) for row in textrows.values()]
    if tuple(center)==DEFAULT_CENTER:
        data=json.loads((ROOT/'city-safety.json').read_text());mask=zlib.decompress(base64.b64decode(data['safe_zlib']))
        ox,oy=data['origin'];width,height=data['width'],data['height'];points=list(DEFAULT_POINTS)
        for x,y in points:
            cx,cy=x-ox,y-oy
            if not (0<=cx<width and 0<=cy<height and mask[cy*width+cx]):
                raise ValueError('Указанная владельцем точка не подтверждена как сухая безопасная')
            if any((x+.5-a)**2+(y+.5-b)**2<1 for a,b in existing):
                raise ValueError('Указанная владельцем точка занята существующим НПС')
    else:points=placement(center,existing)
    nls={p:b'\r\n' if b'\r\n' in raw else b'\n' for p,raw in originals.items()}
    outputs={script:originals[script]+nls[script]+render(catalog).replace(b'\n',nls[script]),
             sdk:originals[sdk].replace(ANCHOR,HOOK.replace(b'\n',nls[sdk])+ANCHOR)}
    newrecords=[];newlines=[];ids=[];maximum=max(textrows)
    for index,shop in enumerate(catalog['shops']):
        identity=maximum+index+1;ids.append(identity);x,y=points[index]
        # Clone an ordinary merchant, preserving unknown compiled record fields.
        template_index=next(i for i,r in enumerate(records) if struct.unpack_from('<I',r,4)[0]==18)
        template=list(textrows[18]);record=bytearray(records[template_index]);name=shop['name'].encode('ascii');function=shop['function'].encode('ascii')
        if len(name)>=40 or len(function)>=16:raise ValueError('Имя или функция НПС слишком длинные')
        struct.pack_into('<I',record,4,identity);struct.pack_into('<I',record,100,identity)
        record[8:48]=name.ljust(40,b'\0');record[108:236]=name.ljust(128,b'\0')
        record[394:410]=function.ljust(16,b'\0');record[410:426]=b'0'.ljust(16,b'\0')
        struct.pack_into('<iiiiI',record,244,x*100+50,y*100+50,x*100+50,y*100+50,180)
        template[0]=str(identity).encode();template[1]=name;template[5]=template[6]=f'{x*100+50},{y*100+50}'.encode()
        template[7]=b'180';template[11]=function;template[12]=b'0'
        newlines.append(b'\t'.join(template));newrecords.append(bytes(record))
    outputs[table]=originals[table]+nls[table]+nls[table].join(newlines)+nls[table]
    outputs[binary]=originals[binary]+b''.join(newrecords)
    validate_npcs(outputs[table],outputs[binary])
    return originals,outputs,{'center_m':list(center),'positions_m':points,'npc_ids':ids,
       'shops':[{k:s[k] for k in ('key','name','function')} for s in catalog['shops']],
       'catalog_sha256':hashlib.sha256((ROOT/'catalog.json').read_bytes()).hexdigest()}


def install(selected,center,apply=False):
    root=locate(selected);marker=root/'owner-city-shops-v1.json'
    if marker.exists():
        previous=json.loads(marker.read_text())
        if previous.get('catalog_sha256')!=hashlib.sha256((ROOT/'catalog.json').read_bytes()).hexdigest():
            raise ValueError('Каталог после установки изменился; нужна проверка обновления магазинов')
        if all(hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in previous['installed_sha256'].items()):
            if list(center)!=previous['center_m']:raise ValueError('НПС уже установлены в другой точке; автоматическое перемещение остановлено')
            return {'already_installed':True,**previous}
        raise ValueError('После установки файлы изменены; автоматическая перезапись остановлена')
    originals,outputs,report=plan(root,center)
    report['applied']=False
    if not apply:return report
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f');backup=root/'owner-city-shops-backups'/stamp
    backup.mkdir(parents=True,exist_ok=False)
    for relative,raw in originals.items():
        target=backup/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        if target.read_bytes()!=raw:raise OSError('Ошибка проверки резервной копии')
    changed=[]
    try:
        for relative,raw in outputs.items():
            target=root/relative;temp=target.with_name(target.name+'.owner-shops.tmp')
            with temp.open('xb') as stream:stream.write(raw)
            os.replace(temp,target);changed.append(relative)
        report.update(applied=True,backup=str(backup),installed_sha256={p.as_posix():hashlib.sha256(b).hexdigest() for p,b in outputs.items()})
        marker.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    except BaseException:
        for relative in changed:
            target=root/relative;temp=target.with_name(target.name+'.owner-shops-restore.tmp');temp.write_bytes(originals[relative]);os.replace(temp,target)
        for relative in outputs:(root/relative).with_name(relative.name+'.owner-shops.tmp').unlink(missing_ok=True)
        marker.unlink(missing_ok=True);raise
    return report


def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',nargs='?');p.add_argument('--x',type=int,default=DEFAULT_CENTER[0]);p.add_argument('--y',type=int,default=DEFAULT_CENTER[1]);p.add_argument('--apply',action='store_true');a=p.parse_args()
    try:
        selected=a.path or input('Папка GameServer или resource: ').strip().strip('"')
        x,y=a.x,a.y
        if a.apply and sys.platform=='win32':
            import subprocess
            listing=subprocess.check_output(['tasklist','/FI','IMAGENAME eq GameServer.exe','/FO','CSV','/NH'],text=True,errors='replace')
            if 'gameserver.exe' in listing.casefold():raise ValueError('Сначала останови GameServer.exe, затем запусти установщик снова')
        report=install(selected,(x,y),a.apply)
        print(json.dumps(report,ensure_ascii=False,indent=2));print('Готово. Перезапусти сервер.' if a.apply else 'Предпросмотр: файлы не изменены. Для установки запусти Install-City-Shops.cmd.')
    except (OSError,ValueError,KeyError,struct.error) as error:print('Ошибка: '+str(error));return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
