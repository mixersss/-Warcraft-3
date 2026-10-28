from pathlib import Path
import sys,json,hashlib,subprocess,io,struct,zlib,re
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT.parent/'naruto-rpg'))
from mpq_tools import StormArchive
report=json.loads((ROOT/'dist/build-report.json').read_text());target=ROOT/'dist'/report['filename']
run=subprocess.run(['/workspace/.warcraft-tools/pjass','/workspace/.warcraft-tools/common.j','/workspace/.warcraft-tools/Blizzard.j','+shadow','+checkglobalsinit','+checkstringlength','+nomodulooperator',str(ROOT/'dist/map/war3map.j')],capture_output=True,text=True,check=True)
(ROOT/'dist/pjass.log').write_text(run.stdout+run.stderr)
old=StormArchive(ROOT/'source/XHeroSiege-4.80-original.w3x');now=StormArchive(target)
files=old.read('(listfile)').decode().splitlines();allbytes={n:now.read(n)for n in files}
for n in files:
 if n not in report['changedArchiveFiles']:assert allbytes[n]==old.read(n),n
assert allbytes['war3map.w3i']==old.read('war3map.w3i')
# Exact allowed title change, preserving the rest of the 297KB strings file.
assert allbytes['war3map.wts']==re.sub(rb'(STRING 1\s*\{\s*)X Hero Siege 4.80',rb'\1X Hero Siege 4.80 - Bots Alpha01',old.read('war3map.wts'),count=1)
original=old.read('war3map.j').decode('utf-8-sig').replace('\r\n','\n');s=allbytes['war3map.j'].decode();originalfunctions=dict(re.findall(r'^function (\w+) takes([^]*?)',original))if False else {m[1]:m[0]for m in re.finditer(r'^function (\w+) takes[\s\S]*?^endfunction',original,re.M)}
newfunctions={m[1]:m[0]for m in re.finditer(r'^function (\w+) takes[\s\S]*?^endfunction',s,re.M)}
allowed=set(report['adaptedParticipantFunctions']+['main','Trig_ModeNormal_Actions','Trig_ModeRandom_Actions'])
for n,code in originalfunctions.items():
 if n not in allowed:assert newfunctions[n]==code,n
assert newfunctions['Trig_HeroDead_Actions']==originalfunctions['Trig_HeroDead_Actions'],'Preserve actual native120sec source revival and penalty'
for p in range(8):assert f'call SetPlayerController( Player({p}), MAP_CONTROL_USER )'in s
assert s.count('call XHInit()')==1
assert not re.search(r'\b(?:Blz|Dz|EX)[A-Z]\w*\(',s)
old.close();now.close()
sys.path.insert(0,'/workspace/.warcraft-tools');import mpyq
full=target.read_bytes();mpq=mpyq.MPQArchive(io.BytesIO(full[512:]),listfile=False)
assert mpq.header['header_size']==32 and mpq.header['sector_size_shift']==3
for n,d in allbytes.items():
 entry=mpq.get_hash_table_entry(n);b=mpq.block_table[entry.block_table_index]
 assert not b.flags&0x01000000,'No compressed SINGLE_UNIT files'
 raw=full[512+b.offset:512+b.offset+b.archived_size]
 if not d:assert b.size==0;continue
 count=(b.size+4095)//4096;offsets=struct.unpack_from('<'+'I'*(count+1),raw);assert offsets[0]==4*(count+1) and offsets[-1]==len(raw)
 chunks=[]
 for k in range(count):
  sector=raw[offsets[k]:offsets[k+1]];size=min(4096,b.size-k*4096)
  if len(sector)<size:assert sector[0]==2;sector=zlib.decompress(sector[1:])
  assert len(sector)==size;chunks.append(sector)
 assert b''.join(chunks)==d,n
assert len(full)<8*1024*1024
r={'filename':target.name,'sha256':hashlib.sha256(full).hexdigest(),'strictClassicJASS':True,'nativeStormAndIndependentMPQFiles':len(files),'allModelsTexturesTerrainObjectsAndSlotsPreserved':True,'sourceRevivalAndPenaltyPreserved':True,'sourceWaveAndBossFunctionsPreserved':True,'onlyChangedFiles':report['changedArchiveFiles'],'ordinary4096ByteSectors':True,'below8MiB':True,'enginePlaytest':False}
(ROOT/'dist/verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
