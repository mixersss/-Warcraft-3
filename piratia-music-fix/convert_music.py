"""Reversible classic Piratia music workaround: Vorbis payloads at unchanged paths."""
import argparse
import contextlib
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

FFMPEG_URL = 'https://github.com/GyanD/codexffmpeg/releases/download/7.1.1/ffmpeg-7.1.1-full_build.zip'
FFMPEG_SHA256 = 'd760e1b3574402ed18b4865851f87d87e73965a982e6453212df8621fed1c508'
BACKUP = 'music-backup-before-ogg'
KIT = Path(__file__).resolve().parent


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def atomic_bytes(path, data):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.piratia-',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)


def save_manifest(root, manifest):
    atomic_bytes(root/'manifest.json',(json.dumps(manifest,indent=2)+'\n').encode('utf-8'))


def contained(root, relative):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0]!='music':
        raise ValueError('Неверный путь в списке резервных копий.')
    result = (root/relative).resolve()
    result.relative_to(root.resolve())
    return result


def validate_client(client):
    client = Path(client).resolve()
    if not (client/'system/Game.exe').is_file() or not (client/'scripts/kop.cfg').is_file() or not (client/'music').is_dir():
        raise ValueError('Нужна папка клиента с music, scripts и system/Game.exe, а не папка сервера.')
    if (client/'music').is_symlink() or (client/BACKUP).is_symlink():
        raise ValueError('Используй обычную папку клиента без ссылок на другие каталоги.')
    return client


def ensure_game_closed():
    if os.name != 'nt':return
    result = subprocess.run(['tasklist','/FI','IMAGENAME eq Game.exe','/FO','CSV','/NH'],
                            capture_output=True,encoding='utf-8',errors='replace',check=True)
    if any(row and row[0].lower()=='game.exe' for row in csv.reader(io.StringIO(result.stdout))):
        raise RuntimeError('Полностью закрой игру Game.exe и повтори запуск. Сервер можно оставить работающим.')


@contextlib.contextmanager
def client_lock(root):
    root.mkdir(exist_ok=True)
    with (root/'operation.lock').open('a+b') as f:
        f.seek(0)
        if not f.read(1):f.write(b'0');f.flush()
        f.seek(0)
        if os.name=='nt':
            import msvcrt
            try:msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
            except OSError:raise RuntimeError('Другая операция с музыкой уже работает.') from None
        else:
            import fcntl
            fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def read_manifest(root):
    p = root/'manifest.json'
    if not p.exists():return {'version':1,'files':{}}
    data = json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or data.get('version')!=1 or not isinstance(data.get('files'),dict):
        raise ValueError('Неизвестный формат списка резервных копий.')
    for relative,record in data['files'].items():
        contained(root/'originals',relative)
        if not isinstance(record,dict) or set(record)!={'original','converted'}:
            raise ValueError('Повреждён список резервных копий.')
        for value in record.values():
            if value is not None and (not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value)):
                raise ValueError('Повреждена контрольная сумма.')
    return data


def tools(ffmpeg=None,ffprobe=None):
    if ffmpeg or ffprobe:
        if not (ffmpeg and ffprobe):raise ValueError('Укажи и ffmpeg, и ffprobe.')
        return str(ffmpeg),str(ffprobe)
    installed = shutil.which('ffmpeg'),shutil.which('ffprobe')
    if all(installed):return installed
    folder = KIT/'tools/ffmpeg-7.1.1'
    if all((folder/n).is_file() for n in ('ffmpeg.exe','ffprobe.exe')):
        return str(folder/'ffmpeg.exe'),str(folder/'ffprobe.exe')
    if os.name!='nt':raise RuntimeError('На этой ОС укажи установленные ffmpeg и ffprobe.')
    folder.mkdir(parents=True,exist_ok=True)
    archive = folder/'ffmpeg.zip'
    print('Загружаю FFmpeg 7.1.1 с GitHub GyanD. Это разовая загрузка большого ZIP.',flush=True)
    print(FFMPEG_URL,flush=True)
    if not archive.exists() or digest(archive)!=FFMPEG_SHA256:
        temporary = archive.with_suffix('.download')
        try:
            with urllib.request.urlopen(urllib.request.Request(FFMPEG_URL,headers={'User-Agent':'PiratiaMusicFix/1'}),timeout=60) as response,temporary.open('wb') as out:
                total,shown=0,0
                while True:
                    block=response.read(1024*1024)
                    if not block:break
                    total+=len(block)
                    if total>500*1024*1024:raise RuntimeError('Превышен ожидаемый размер архива FFmpeg.')
                    out.write(block)
                    if total-shown>=20*1024*1024:
                        print(f'Загружено {total//(1024*1024)} МБ…',flush=True);shown=total
            if digest(temporary)!=FFMPEG_SHA256:raise RuntimeError('Контрольная сумма FFmpeg не совпала. Запуск отменён.')
            os.replace(temporary,archive)
        finally:
            if temporary.exists():temporary.unlink()
    with zipfile.ZipFile(archive) as z:
        for name in ('ffmpeg.exe','ffprobe.exe'):
            entries=[n for n in z.namelist() if n.endswith('/bin/'+name)]
            if len(entries)!=1:raise RuntimeError('Неожиданное содержимое архива FFmpeg.')
            with z.open(entries[0]) as src,(folder/name).open('wb') as dst:shutil.copyfileobj(src,dst)
    return str(folder/'ffmpeg.exe'),str(folder/'ffprobe.exe')


def probe(path, ffprobe):
    completed=subprocess.run([ffprobe,'-v','error','-select_streams','a:0','-show_entries',
                              'stream=codec_name,sample_rate,channels:format=duration','-of','json',str(path)],
                             capture_output=True,check=True,encoding='utf-8',timeout=60)
    result=json.loads(completed.stdout)
    stream=result['streams'][0]
    return stream,float(result['format']['duration'])


def convert_one(source,output,ffmpeg,ffprobe):
    before,duration=probe(source,ffprobe)
    if before['codec_name']!='mp3':raise ValueError('Оригинал не является MP3: '+source.name)
    subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-nostdin','-y','-i',str(source),
                    '-map','0:a:0','-vn','-map_metadata','-1','-ar','44100','-ac','2',
                    '-c:a','libvorbis','-q:a','6','-f','ogg',str(output)],
                   check=True,capture_output=True,timeout=1800)
    after,new_duration=probe(output,ffprobe)
    with output.open('rb') as f:magic=f.read(4)
    if (magic!=b'OggS' or after['codec_name']!='vorbis'
            or after.get('sample_rate')!='44100' or after.get('channels')!=2
            or abs(duration-new_duration)>.15):
        raise ValueError('Проверка преобразованной композиции не пройдена: '+source.name)
    # Decode the complete output, rather than trusting a valid header alone.
    subprocess.run([ffmpeg,'-v','error','-nostdin','-i',str(output),'-map','0:a:0','-f','null','-'],
                   check=True,capture_output=True,timeout=1800)


def apply(client,ffmpeg,ffprobe,tell=print):
    client=validate_client(client)
    ensure_game_closed()
    root=client/BACKUP
    with client_lock(root):
        manifest=read_manifest(root)
        tracks=sorted(p for p in (client/'music').rglob('*') if p.is_file() and p.suffix.lower()=='.mp3')
        if not tracks:raise ValueError('В папке music не найдены MP3-композиции.')
        changed=0
        for index,path in enumerate(tracks,1):
            relative=path.relative_to(client).as_posix()
            contained(client,relative)
            tell(f'Музыка {index}/{len(tracks)}: {path.name}')
            current=digest(path)
            record=manifest['files'].get(relative)
            backup=contained(root/'originals',relative)
            if record:
                if not backup.is_file() or digest(backup)!=record['original']:
                    raise ValueError('Повреждён или отсутствует оригинал: '+path.name)
                if current==record['converted']:
                    tell('Уже преобразована, пропускаю.');continue
                if current!=record['original']:
                    raise ValueError('Файл изменён после резервного копирования: '+path.name)
            else:
                with path.open('rb') as f:magic=f.read(4)
                if magic==b'OggS':
                    tell('Уже OGG, файл оставлен без изменений.');continue
                # Do not overwrite an orphaned original after an interrupted first save.
                if backup.exists() and digest(backup)!=current:
                    raise ValueError('В резервной папке другой оригинал: '+path.name)
                backup.parent.mkdir(parents=True,exist_ok=True)
                if not backup.exists():shutil.copy2(path,backup)
                if digest(backup)!=current:raise ValueError('Ошибка проверки резервной копии.')
                record={'original':current,'converted':None}
                manifest['files'][relative]=record
                save_manifest(root,manifest)
            fd,name=tempfile.mkstemp(prefix='.piratia-ogg-',suffix='.tmp',dir=path.parent)
            os.close(fd);temporary=Path(name)
            try:
                convert_one(backup,temporary,ffmpeg,ffprobe)
                record['converted']=digest(temporary)
                save_manifest(root,manifest)  # Crash before replacement remains resumable.
                if digest(path)!=record['original']:raise ValueError('Исходный файл изменился во время операции.')
                os.replace(temporary,path)
                changed+=1
            finally:
                if temporary.exists():temporary.unlink()
        return changed,len(tracks)


def restore(client,tell=print):
    client=validate_client(client)
    ensure_game_closed()
    root=client/BACKUP
    if not (root/'manifest.json').is_file():raise ValueError('Не найден список резервных копий этой программы.')
    with client_lock(root):
        manifest=read_manifest(root)
        # Validate the entire restore before changing even its first file.
        files=[]
        for relative,record in manifest['files'].items():
            target=contained(client,relative);backup=contained(root/'originals',relative)
            if not backup.is_file() or digest(backup)!=record['original']:
                raise ValueError('Оригинальная копия повреждена: '+Path(relative).name)
            current=digest(target)
            if current not in (record['original'],record['converted']):
                raise ValueError('Файл изменён вручную; восстановление отменено: '+target.name)
            if current!=record['original']:files.append((target,backup))
        for target,backup in files:
            atomic_bytes(target,backup.read_bytes())
            tell('Восстановлена: '+target.name)
        return len(files)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client',type=Path)
    parser.add_argument('--restore',action='store_true')
    parser.add_argument('--ffmpeg',type=Path)
    parser.add_argument('--ffprobe',type=Path)
    args=parser.parse_args()
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8',errors='replace')
    try:
        client=args.client
        if client is None:
            import tkinter as tk
            from tkinter import filedialog
            ui=tk.Tk();ui.withdraw()
            selected=filedialog.askdirectory(title='Выбери папку клиента Пиратии: music, scripts, system')
            ui.destroy()
            if not selected:
                print('Выбор отменён.');return 0
            client=Path(selected)
        client=validate_client(client)
        ensure_game_closed()
        if args.restore:
            count=restore(client)
            print(f'Готово. Восстановлено оригиналов: {count}.')
        else:
            ffmpeg,ffprobe=tools(args.ffmpeg,args.ffprobe)
            changed,total=apply(client,ffmpeg,ffprobe)
            print(f'Готово. Проверено музыкальных файлов: {total}, преобразовано сейчас: {changed}.')
            print('Музыка сохранена. Запусти игру и проверь несколько входов/выходов из города.')
            print('Резервные копии находятся в папке клиента: '+BACKUP)
        return 0
    except KeyboardInterrupt:
        print('\nОстановлено. Повторный запуск продолжит обработку; оригиналы сохранены.');return 1
    except PermissionError:
        print('Нет доступа к файлам. Закрой игру и запусти CMD программы правой кнопкой → от имени администратора.');return 1
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError,KeyError,IndexError,zipfile.BadZipFile) as exc:
        print('Операция остановлена: '+str(exc))
        print('Оригиналы сохранены. Можно повторить запуск или использовать Restore-Music.cmd.');return 1


if __name__=='__main__':sys.exit(main())
