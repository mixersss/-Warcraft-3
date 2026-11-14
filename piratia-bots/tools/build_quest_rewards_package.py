"""Package only the public patcher; never include the owner's server Lua."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'releases'/'piratia'/'quest-rewards-9-5'
NAME='Piratia-Quest-Rewards-x9-Gold-x5'
README='''# Награды за квесты: опыт ×9, золото ×5

1. Останови GameServer и распакуй этот архив в отдельную папку.
2. Запусти Configure-Quest-Rewards.cmd.
3. Вставь полный путь к папке сервера, в которой находится GameServer.exe,
   либо к его resource. Путь можно скопировать из адресной строки Проводника.
   Допускается также перетащить сам GameServer.exe в окно ввода пути.
4. Утилита покажет найденный Lua-файл и резервную копию. После сообщения
   «Обычный опыт за квесты: x9; золото за квесты: x5» перезапусти GameServer.

Имя MissionSdk.lua искать вручную не нужно: проверяется содержимое Lua-файлов.
Если найдены несколько копий сервера, программа перечислит их и ничего
не изменит — повтори запуск, указав папку конкретного GameServer.

Повторный запуск оставляет ×9/×5, без накопления множителей. Резервная копия
создаётся рядом с изменяемым файлом и имеет окончание .bak. Для отмены останови
GameServer и восстанови этот Lua-файл из резервной копии, затем запусти сервер.

Меняется обычный опыт и золото от AddExp/AddMoney в обработчике заданий.
Существующие бонусы GetExpState сохраняются; опыт мирных навыков AddExpAndType,
дроп, опыт с мобов, деньги в базе и персонажи этой утилитой не меняются.
Числа в уже загруженных заданиях не перемножаются при каждой сдаче.

Нужен Python3.9+ (как для ботов). Утилита работает локально и сохраняет
кодировку остальных частей Lua-файла. Архив содержит только нашу утилиту,
без исходных Lua-файлов сервера, данных аккаунтов или паролей.
Проверены11автоматических тестов, включая выполнение повторных наград в Lua5.4;
это не живая проверка на Windows GameServer.
'''

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    files={'Configure-Quest-Rewards.cmd':(ROOT/'Configure-Quest-Rewards.cmd').read_bytes(),
           'src/configure_quest_rewards.py':(ROOT/'src/configure_quest_rewards.py').read_bytes(),
           'README.md':README.encode('utf-8')}
    artifact=OUT/(NAME+'.zip')
    with zipfile.ZipFile(artifact,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,data in files.items():
            if name.endswith('.cmd'):data=data.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
            entry=zipfile.ZipInfo(NAME+'/'+name,date_time=(2026,11,14,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(entry,data)
    manifest={'artifact':artifact.name,'sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),
              'quest_xp_multiplier':9,'quest_gold_multiplier':5,'repeated_run_compounds':False,
              'owner_server_scripts_included':False,'automatic_tests_passed':11,'live_windows_server_tested':False}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'README.md').write_text(README)
    print(artifact);print(manifest['sha256'])

if __name__=='__main__':main()
