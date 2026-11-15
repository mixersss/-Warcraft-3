"""Install an exact, backed-up entry hook in the classic SDK, loaded on restart."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

ROOT=Path(__file__).resolve().parent
SDK=Path('script/MisSdk/NpcSdk.lua')
MARKER='owner-buba-fix04-install.json'
BEGIN=b'-- BUBA_GIFT_FIX04_BEGIN'
END=b'-- BUBA_GIFT_FIX04_END'
BOOT=b'-- BUBA_GIFT_FIX04_BOOT\nprint("BUBA04 SDK HOOK LOADED: buba can talk to an NPC for the owner swords")\n'
HOOK=b'''    -- BUBA_GIFT_FIX04_BEGIN
    if character ~= nil and npc ~= nil then
        local buba_name = GetChaDefaultName(character)
        if type(buba_name)=="string" and string.lower(buba_name)=="buba" and not BubaGift04Attempted then
            BubaGift04Attempted=true
            SystemNotice(character,"BUBA04 START: checking the two owner swords")
            local buba_ok,buba_error=pcall(function()
                BubaLoadOnly=true
                dofile(GetResPath("script/BubaSwords.lua"))
                BubaLoadOnly=nil
                BubaGiveSwords(character)
            end)
            BubaLoadOnly=nil
            if not buba_ok then
                SystemNotice(character,"BUBA04 ERROR: "..string.sub(tostring(buba_error),1,160))
                print("BUBA04 ERROR: "..tostring(buba_error))
            end
        end
    end
    -- BUBA_GIFT_FIX04_END
'''


def digest(raw):return hashlib.sha256(raw).hexdigest()


def locate(selected):
    p=Path(str(selected).strip().strip('"'))
    for base in (p,*p.parents):
        for r in (base/'resource',base):
            if (r/SDK).is_file() and (r/'script/MisScript/NpcScript01.lua').is_file():return r
    raise ValueError('Не найдена серверная resource с NpcSdk.lua и NpcScript01.lua.')


def patch_sdk(raw):
    normalized=raw.replace(b'\r\n',b'\n')
    if BEGIN in normalized or END in normalized:
        if normalized.count(HOOK)==1 and normalized.count(BOOT)==1:return raw
        raise ValueError('В SDK уже есть изменённый/неполный BUBA04 блок; нужна проверка.')
    matches=list(re.finditer(rb'(?m)^function[ \t]+MsgProc[ \t]*\([ \t]*character[ \t]*,[ \t]*npc[ \t]*,[ \t]*rpk[ \t]*,[ \t]*page[ \t]*,[ \t]*trade[ \t]*,[ \t]*missionlist[ \t]*,[ \t]*exchangeData[ \t]*\)[ \t]*\r?\n',raw))
    if len(matches)!=1:raise ValueError('Не найден единственный ожидаемый MsgProc. SDK не изменён.')
    nl=b'\r\n' if b'\r\n' in raw else b'\n';at=matches[0].end()
    return raw[:at]+HOOK.replace(b'\n',nl)+raw[at:]+nl+BOOT.replace(b'\n',nl)


def atomic(path,raw):
    fd,name=tempfile.mkstemp(dir=path.parent,prefix=path.name+'.buba-',suffix='.tmp')
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw)
        os.replace(name,path)
    finally:Path(name).unlink(missing_ok=True)


def install(selected):
    resource=locate(selected);marker=resource/MARKER;sdk=resource/SDK
    before=sdk.read_bytes();after=patch_sdk(before);gift=(ROOT/'BubaSwords.lua').read_bytes()
    target=resource/'script/BubaSwords.lua'
    known=json.loads((ROOT/'previous-script-sha256.json').read_text())
    if target.exists() and target.read_bytes()!=gift and digest(target.read_bytes()) not in known.get('BubaSwords.lua',[]):
        raise ValueError('BubaSwords.lua изменён неизвестным образом; перезапись остановлена.')
    changes={sdk:after,target:gift}
    # Keep a known shop installation's SDK checksum consistent with this explicit hook.
    shopmarker=resource/'owner-city-shops-v2.json'
    if shopmarker.exists():
        shop=json.loads(shopmarker.read_text())
        if shop.get('installed_sha256',{}).get(SDK.as_posix())==digest(before):
            shop['installed_sha256'][SDK.as_posix()]=digest(after)
            changes[shopmarker]=(json.dumps(shop,ensure_ascii=False,indent=2)+'\n').encode()
    changes={p:b for p,b in changes.items() if not p.exists() or p.read_bytes()!=b}
    if not changes:return {'already_installed':True,'restart_all_gameservers_required':True}
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f');backup=resource/'owner-buba-backups'/stamp
    backup.mkdir(parents=True,exist_ok=False)
    original={p:p.read_bytes() if p.exists() else None for p in changes}
    saved=[]
    for i,(p,raw) in enumerate(original.items()):
        name=str(i)+'-'+p.name
        if raw is not None:
            (backup/name).write_bytes(raw)
            if (backup/name).read_bytes()!=raw:raise OSError('Не подтверждена резервная копия.')
        saved.append({'relative':p.relative_to(resource).as_posix(),'backup':name if raw is not None else None,'installed_sha256':digest(changes[p])})
    written=[]
    try:
        for p,raw in changes.items():atomic(p,raw);written.append(p)
        report={'version':4,'target_character':'buba','backup':str(backup),'sdk_before':digest(before),'sdk_after':digest(after),'changes':saved,'restart_all_gameservers_required':True,'grant_ledger_preserved':True}
        atomic(marker,(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode())
    except BaseException:
        for p in reversed(written):
            if original[p] is None:p.unlink(missing_ok=True)
            else:atomic(p,original[p])
        raise
    return report


if __name__=='__main__':
    print('Сначала останови ботов и ВСЕ GameServer. Аккаунты, уровень и профессия сохраняются.')
    try:
        report=install(input('Папка GameServer или resource: '))
        print(json.dumps(report,ensure_ascii=False,indent=2))
        print('Запусти сервер заново, зайди за buba и поговори с НПС. Ожидается BUBA04 START.')
        print('Вводить &lua больше не нужно. Файл owner-buba-swords-01.state не удаляй.')
    except (OSError,ValueError) as error:
        print('Ошибка:',str(error));raise SystemExit(1)
