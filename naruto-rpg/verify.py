from pathlib import Path
import json,hashlib,ctypes as c,subprocess,sys,io,struct,zlib
ROOT=Path(__file__).parent
report=json.loads((ROOT/'dist/build-report.json').read_text());target=ROOT/'dist'/report['filename']
r=subprocess.run(['/tmp/warcraft-pjass/pjass','/tmp/warcraft-common-legacy.j','/tmp/warcraft-w3x2lni/data/zhCN-1.24.4/mpq/Scripts/Blizzard.j','+shadow','+checkglobalsinit','+checkstringlength','+nomodulooperator',str(ROOT/'dist/map/war3map.j')],capture_output=True,text=True,check=True)
(ROOT/'dist/jass-check.log').write_text(r.stdout+r.stderr)
exec(Path('/workspace/naruto-bots/storm-check.py').read_text().split('files=')[0])
# The declaration snippet is self-contained and does not alter ROOT.
a=c.c_void_p();assert S.SFileOpenArchive(str(target).encode(),0,0x100,c.byref(a))
def read(name):
 f=c.c_void_p();assert S.SFileOpenFileEx(a,name.encode('ascii'),0,c.byref(f)),name
 size=S.SFileGetFileSize(f,None);buf=c.create_string_buffer(size);got=c.c_uint32();assert S.SFileReadFile(f,buf,size,c.byref(got),None) and got.value==size,name
 S.SFileCloseFile(f);return buf.raw
manifest=json.loads((ROOT/'src/asset-manifest.json').read_text())
for row in manifest:
 data=read(row['path']);assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],row['path']
metadata={p.name:p.read_bytes() for p in (ROOT/'dist/map').iterdir() if p.is_file()}
for name,data in metadata.items():assert read(name)==data,name
S.SFileCloseArchive(a)
sys.path.insert(0,'/tmp/warcraft-validation/python');import mpyq
full=target.read_bytes();mpq=mpyq.MPQArchive(io.BytesIO(full[512:]),listfile=False)
assert mpq.header['header_size']==32 and mpq.header['sector_size_shift']==3
assert mpq.header['archive_size']==len(full)-512
for row in manifest:
 entry=mpq.get_hash_table_entry(row['path']);assert entry is not None
 b=mpq.block_table[entry.block_table_index];raw=full[512+b.offset:512+b.offset+b.archived_size]
 assert b.flags==0x80000200 and b.size==row['bytes']
 count=(b.size+4095)//4096;off=struct.unpack_from('<'+'I'*(count+1),raw)
 assert off[0]==4*(count+1) and off[-1]==len(raw)
 plain=[]
 for k in range(count):
  sector=raw[off[k]:off[k+1]];size=min(4096,b.size-k*4096)
  if len(sector)<size:assert sector[0]==2;sector=zlib.decompress(sector[1:])
  assert len(sector)==size;plain.append(sector)
 assert hashlib.sha256(b''.join(plain)).hexdigest()==row['sha256']
assert len(full)<8*1024*1024 and hashlib.sha256(full).hexdigest()==report['sha256']
# File tables, scenario and imported data are newly authored; no original JASS.
assert b'function QDV takes' not in metadata['war3map.j']
result={'strictLegacyJASS':True,'nativeStormLibImportedAssetsVerified':len(manifest),'independentPythonAssetsVerified':len(manifest),'nativeStormLibMetadataVerified':len(metadata),'allImportedBytesOriginal':True,'ordinary4096ByteSectors':True,'below8MiBLimit':True,'enginePlaytest':False,'skillsMechanicsRecreated':0}
(ROOT/'dist/verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
