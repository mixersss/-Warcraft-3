"""Read-only quest/start-item resource inventory. Never read account state or SQL."""
import hashlib
import json
import re
import sys
from pathlib import Path


def audit(selected):
    selected=Path(selected)
    if selected.is_file():selected=selected.parent
    candidates=(selected/'resource',selected,selected.parent/'resource')
    resource=next((p for p in candidates if (p/'script').is_dir()),None)
    if resource is None:return 'Не найдена папка resource/script. Укажи папку GameServer или её resource.'
    lines=['Проверка файлов сервера: '+str(resource),
           'Это проверка наличия файлов; фактическую загрузку Lua нужно сверять с журналом запуска GameServer.']
    known=json.loads((Path(__file__).resolve().parents[1]/'knowledge/sources-local.json').read_text()) if (Path(__file__).resolve().parents[1]/'knowledge/sources-local.json').exists() else {'sources':[]}
    hashes={row['path']:row['sha256'] for row in known['sources']}
    for relative in ('script/MisScript/MissionScript01.lua','script/MisScript/NpcScript01.lua',
                     'script/MisSdk/MissionSdk.lua','script/MisSdk/NpcSdk.lua','ItemInfo.txt'):
        path=resource/relative
        if not path.is_file():lines.append(relative+': НЕ НАЙДЕН');continue
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        status='совпадает с прежним ресурсом владельца' if hashes.get(relative)==digest else 'версия требует сверки'
        lines.append(relative+': найден; SHA256='+digest+'; '+status)
    files=sorted((resource/'script').rglob('*.lua'))
    if len(files)>2000:lines.append('Слишком много Lua-файлов: проверены только первые 2000.')
    for path in files[:2000]:
        try:body=path.read_bytes().decode('cp1251',errors='replace')
        except OSError:lines.append(str(path.relative_to(resource))+': нет доступа');continue
        for number,line in enumerate(body.splitlines(),1):
            if re.search(r'GiveItem\s*[,\(][^\r\n]*\b(?:436|985|986|987|988)\b',line):
                lines.append(str(path.relative_to(resource))+':'+str(number)+' — ссылка выдачи известного сундука')
            if re.search(r'\b(?:dofile|require|LoadScript)\b',line,re.I) and re.search(r'MissionScript|NpcScript|MissionSdk|NpcSdk',line,re.I):
                lines.append(str(path.relative_to(resource))+':'+str(number)+' — ссылка загрузки скриптов заданий/NPC')
        if path.name.lower()=='missionscript01.lua':
            count=len(re.findall(r'\bDefineMission\s*\(',body))
            lines.append('Объявлений DefineMission в MissionScript01.lua: '+str(count))
            for title in ('Swordsman Promotion','Hunter Promotion','Herbalist Promotion','Explorer Promotion'):
                lines.append(title+': '+('название найдено' if title in body else 'название не найдено'))
    return '\n'.join(lines)


def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    selected=sys.argv[1] if len(sys.argv)>1 else input('Вставь полный путь к папке GameServer: ').strip().strip('"')
    result=audit(selected)
    print(result)
    output=Path(__file__).resolve().parents[1]/'server-quest-check.log'
    output.write_text(result,encoding='utf-8')
    print('\nРезультат: '+str(output))


if __name__=='__main__':main()
