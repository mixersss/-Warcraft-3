"""Patch only verified owner scripts; keep private originals out of this package."""
import hashlib
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = {'MisScript/CharBornScript.lua':'661d043ba2ed9a1ee967811b1cc2f92573803fc573dfca63237f61ee62890bd1',
        'calculate/functions.lua':'cc0c0e0657fa88807a6f49d37f84c3877d5dd2894b08306e248902a50bd99516'}
MARKER = '-- StarterBirthAliasesFix01'
RECOVERY = '''
-- StarterBirthAliasesFix01: repair only an untouched novice welcome state.
function StarterBirthAliasesRecover01(role)
    if IsPlayer(role) ~= 1 or PfEqual(role, 0) ~= LUA_TRUE then return end
    for id = 1, 3 do
        if NoRecord(role, id) ~= LUA_TRUE or NoMission(role, id) ~= LUA_TRUE then return end
    end
    -- A started class referral is preserved, not mixed with a new welcome.
    for id = 58, 61 do
        if NoRecord(role, id) ~= LUA_TRUE or NoMission(role, id) ~= LUA_TRUE then return end
    end
    if GetChaFreeBagGridNum(role) < 1 then return end
    local boxes = {436, 985, 986, 987, 988}
    for i = 1, 5 do
        if NoItem(role, boxes[i], 1) ~= LUA_TRUE then return end
        if BankNoItem(role, boxes[i], 1) ~= LUA_TRUE then return end
        if EquipNoItem(role, boxes[i], 1) ~= LUA_TRUE then return end
    end
    local names = {"Argent City", "Shaitan City", "Icicle Castle", "Аргент", "Шайтан", "Ледынь"}
    local missions = {1, 2, 3, 1, 2, 3}
    for i = 1, 6 do
        if IsSpawnPos(role, names[i]) == LUA_TRUE then
            ObligeAcceptMission(role, missions[i])
            SaveMissionData(role)
            return
        end
    end
end
'''


def patched(relative, raw):
    text=raw.decode('cp1251')
    nl='\r\n' if '\r\n' in text else '\n'
    if relative=='MisScript/CharBornScript.lua':
        needle='\tlocal triggerlist = GetMultiTrigger()'
        assert text.count(needle)==1
        extra=('\t'+MARKER+'\n\tTriggerCondition( 4, IsSpawnPos, "Аргент" )\n'
               '\tTriggerAction( 4, ObligeAcceptMission, 1 )\n'
               '\tTriggerCondition( 5, IsSpawnPos, "Шайтан" )\n'
               '\tTriggerAction( 5, ObligeAcceptMission, 2 )\n'
               '\tTriggerCondition( 6, IsSpawnPos, "Ледынь" )\n'
               '\tTriggerAction( 6, ObligeAcceptMission, 3 )\n').replace('\n',nl)
        text=text.replace(needle,extra+needle)
        needle='TriggerAction( 1, MultiTrigger, triggerlist, 3 )'
        assert text.count(needle)==1
        text=text.replace(needle,'TriggerAction( 1, MultiTrigger, triggerlist, 6 )')
        text+=RECOVERY.replace('\n',nl)
    else:
        needle='\tSetChaParam(role, 1, now_tick + freq * time)'
        assert text.count(needle)==1
        extra=('\n\t'+MARKER+'\n'
               '\tif math.mod(now_tick, 30) == 0 and StarterBirthAliasesRecover01 ~= nil then\n'
               '\t\tStarterBirthAliasesRecover01(role)\n\tend').replace('\n',nl)
        text=text.replace(needle,needle+extra)
    return text.encode('cp1251')


def locate(selected):
    selected=Path(selected)
    for p in (selected,selected/'script',selected/'resource/script',selected.parent/'resource/script'):
        if (p/'MisScript/CharBornScript.lua').is_file() and (p/'calculate/functions.lua').is_file():return p
    raise RuntimeError('Не найдена resource/script. Укажи путь к resource или script.')


def install(selected):
    root=locate(selected)
    marker=root/'starter-birth-fix-01.sha256'
    if marker.exists():
        rows=marker.read_text().splitlines()
        if all(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for digest,name in (row.split(' ',1) for row in rows)):
            return 'Исправление уже установлено; файлы не изменены.'
        raise RuntimeError('После установки файлы изменились. Автоматическая перезапись остановлена.')
    originals={};outputs={}
    for relative,expected in BASE.items():
        raw=(root/relative).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected:
            raise RuntimeError('Другая версия '+relative+'. Ничего не изменено; нужна проверка этой версии.')
        originals[relative]=raw;outputs[relative]=patched(relative,raw)
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backups=[]
    for relative,raw in originals.items():
        p=root/relative;backup=p.with_name(p.name+'.before-starter-fix-'+stamp)
        with backup.open('xb') as f:f.write(raw)
        assert backup.read_bytes()==raw
        backups.append(backup)
    changed=[]
    try:
        for relative,raw in outputs.items():
            p=root/relative;temp=p.with_name(p.name+'.starter-fix.tmp')
            with temp.open('xb') as f:f.write(raw)
            os.replace(temp,p);changed.append(relative)
        marker.write_text(''.join(hashlib.sha256(raw).hexdigest()+' '+name+'\n' for name,raw in outputs.items()))
    except BaseException:
        for relative in changed:(root/relative).write_bytes(originals[relative])
        raise
    return 'ГОТОВО. Изменены только CharBornScript.lua и calculate/functions.lua.\nРезервные копии:\n'+'\n'.join(map(str,backups))


def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    if os.name=='nt':
        running=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq GameServer.exe','/FO','CSV','/NH'],capture_output=True,check=True)
        if b'gameserver.exe' in running.stdout.lower():raise RuntimeError('Сначала штатно останови все GameServer. База и персонажи не изменены.')
    selected=sys.argv[1] if len(sys.argv)>1 else input('Полный путь к папке resource: ').strip().strip('"')
    print(install(selected))

if __name__=='__main__':
    try:main()
    except Exception as exc:print('ОШИБКА: '+str(exc));sys.exit(1)
