from pathlib import Path
import sys,json,re,hashlib,subprocess
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'naruto-rpg'))
from mpq_tools import StormArchive
from classic_formats import archive
src=ROOT/'source/XHeroSiege-4.80-original.w3x';a=StormArchive(src)
files={n:a.read(n) for n in a.read('(listfile)').decode().splitlines()};a.close()
original=files['war3map.j'].decode('utf-8-sig').replace('\r\n','\n')
objects=json.loads((ROOT/'source/objects.json').read_text())
units={o['oldId']:o for o in objects['w3u']['original']};units.update({o['newId']:o for o in objects['w3u']['custom']})
abilities={o['oldId']:o for o in objects['w3a']['original']};abilities.update({o['newId']:o for o in objects['w3a']['custom']})
def field(o,k,d=None):return next((m['value'] for m in o['modifications'] if m['id']==k),d)
# Explicit order semantics, inherited only from the actual native ability base.
orders={
'AOhw':('healingwave',4),'ANht':('howlofterror',1),'AEfk':('fanofknives',1),'ACbf':('breathoffrost',3),'ACcb':('thunderbolt',2),'ANmo':('monsoon',3),'AHhb':('holybolt',4),'AHds':('divineshield',5),'AHre':('resurrection',1),'AHtb':('thunderbolt',2),'AHtc':('thunderclap',1),'AHav':('avatar',6),
'AHbz':('blizzard',3),'AHwe':('waterelemental',6),'AEsf':('starfall',1),'AEim':('immolation',1),'AEme':('metamorphosis',6),
'AOwk':('windwalk',5),'AOmi':('mirrorimage',6),'AOww':('whirlwind',1),'AOsh':('shockwave',3),'AOws':('stomp',1),
'AOcl':('chainlightning',2),'AOsf':('spiritwolf',6),'AOeq':('earthquake',3),'AUfn':('frostnova',2),'AUfu':('frostarmor',4),'AUdd':('deathanddecay',3),
'AUcs':('carrionswarm',3),'AUsl':('sleep',2),'AUin':('inferno',3),'ANrf':('rainoffire',3),'ANdo':('doom',2),'AOw2':('howlofterror',1),
'ANwm':('wateryminion',6),'ANfl':('forkedlightning',2),'ANsg':('summongrizzly',6),'ANsw':('summonwareagle',6),'ANsq':('summonquillbeast',6),'ANst':('stampede',3),
'ANbf':('breathoffire',3),'ANcf':('breathoffire',3),'AHfs':('flamestrike',3),'AHpx':('phoenix',3),'ANic':('incineratearrow',2)}
profiles={};skillids=set()
for raw,o in units.items():
 skills=field(o,'uhab','').split(',')
 if skills!=['']:
  profiles[raw]=skills[:5];skillids.update(skills[:5])
func=['function XHSkill takes integer raw, integer slot returns integer']
for raw,skills in profiles.items():
 func.append(f"    if raw=='{raw}' then")
 for k,id in enumerate(skills):func.extend([f'        if slot=={k} then',f"            return '{id}'",'        endif'])
 func.append('    endif')
func.extend(['    return 0','endfunction'])
spellrows={}
for id in sorted(skillids):
 base=abilities[id]['oldId'] if id in abilities and abilities[id]['newId']!= '\0'*4 else id
 order,mode=orders.get(base,('',0));spellrows[id]={'base':base,'order':order,'mode':mode}
for name,ret,key,default in [('XHOrder','string','order','""'),('XHMode','integer','mode','0')]:
 func.append(f'function {name} takes integer id returns {ret}')
 for id,v in spellrows.items():
  if v['mode']:
   val=json.dumps(v[key]) if ret=='string'else str(v[key]);func.extend([f"    if id=='{id}' then",f'        return {val}','    endif'])
 func.extend([f'    return {default}','endfunction'])
pool=['Hpal','Obla','Otch','Ulic','Hamg','Hmkg','Nplh','Emoo']
assert all(raw in re.findall(r"set udg_integers12\[\d+\]='(....)'",original) for raw in pool)
module=(ROOT/'src/bots.j').read_text().replace('// PROFILE_FUNCTIONS','\n'.join(func)).replace('// PROFILE_DATA','\n'.join(f"    set XHPool[{i}]='{raw}'" for i,raw in enumerate(pool)))
globals='''    boolean XHReady=false
    real XHTime=0.
    integer XHCursor=0
    group XHScratch=null
    integer array XHPool
    boolean array XHCreated
    integer array XHPurchases
    real array XHBusy
    real array XHCastAt
    real array XHBuyAt
    real array XHHealAt
'''
s=original.replace('endglobals',globals+'endglobals',1)
# Resolve existing definite-initialization errors without changing InitGlobals values.
s,n=re.subn(r'(    string\s+udg_string\d+)(\s*\n)',r'\1 = ""\2',s);assert n==13,n
# Helper must precede original call sites; rest of AI comes after original declarations.
helper=re.search(r'function XHParticipant takes[^]*?endfunction',module) if False else re.search(r'function XHParticipant takes[\s\S]*?endfunction',module)
s=s.replace('function InitGlobals takes',helper[0]+'\n\nfunction InitGlobals takes',1);module=module.replace(helper[0],'')
# Only change existing human-only participant gates; never change player controllers globally.
changed=[]
pattern=re.compile(r'GetPlayerController\((GetTriggerPlayer\(\)|GetFilterPlayer\(\)|GetOwningPlayer\(GetTriggerUnit\(\)\)|GetOwningPlayer\(GetKillingUnit\(\)\)|GetOwningPlayer\(GetAttacker\(\)\)|Player\(-1\+\(bj_forLoopAIndex\)\))\)==MAP_CONTROL_USER')
for m in re.finditer(r'function (\w+) takes[\s\S]*?endfunction',s):
 if pattern.search(m[0]):changed.append(m[1])
s=pattern.sub(r'XHParticipant(\1)',s)
# This entrance opens a human choice dialog; bots must not open an unanswered dialog.
name='Trig_SpecialXDialog_Conditions'
origfn=re.search(r'function '+name+r' takes[\s\S]*?endfunction',original)[0]
s=re.sub(r'function '+name+r' takes[\s\S]*?endfunction',lambda m:origfn,s)
changed.remove(name)
for name in ['Trig_ModeNormal_Actions','Trig_ModeRandom_Actions']:
 pattern2=re.compile(r'(function '+name+r' takes[\s\S]*?)(endfunction)');s=pattern2.sub(r'\1    set XHReady=true\n\2',s)
s=s.replace('function main takes',module+'\nfunction main takes',1).replace('    call InitCustomTriggers(  )','    call InitCustomTriggers(  )\n    call XHInit()',1)
files['war3map.j']=s.encode()
files['war3map.wts']=re.sub(rb'(STRING 1\s*\{\s*)X Hero Siege 4.80',rb'\1X Hero Siege 4.80 - Bots Alpha01',files['war3map.wts'],count=1)
# Keep object data, imported models, landscape and map metadata byte-for-byte.
out=ROOT/'dist';out.mkdir(exist_ok=True);(out/'map').mkdir(exist_ok=True)
for name in ['war3map.j','war3map.w3i']:(out/'map'/name).write_bytes(files[name])
target=out/'XHeroSiege-4.80-Bots-Alpha01.w3x';target.write_bytes(archive(files,'X Hero Siege 4.80 - Bots Alpha01'))
report={'filename':target.name,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'originalSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'changedArchiveFiles':['war3map.j','war3map.wts'],'preservedFiles':{n:hashlib.sha256(d).hexdigest() for n,d in files.items()if n not in ['war3map.j','war3map.wts']},'adaptedParticipantFunctions':changed,'initializedMusicStrings':13,'botPool':pool,'profiles':profiles,'spells':spellrows,'enginePlaytest':False}
(out/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(target,report['bytes'])
