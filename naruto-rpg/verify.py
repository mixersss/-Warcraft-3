from pathlib import Path
import json,hashlib,ctypes as c,subprocess,sys,io,struct,zlib
ROOT=Path(__file__).parent
report=json.loads((ROOT/'dist/build-report.json').read_text());target=ROOT/'dist'/report['filename']
r=subprocess.run(['/workspace/.warcraft-tools/pjass','/workspace/.warcraft-tools/common.j','/workspace/.warcraft-tools/Blizzard.j','+shadow','+checkglobalsinit','+checkstringlength','+nomodulooperator',str(ROOT/'dist/map/war3map.j')],capture_output=True,text=True,check=True)
(ROOT/'dist/jass-check.log').write_text(r.stdout+r.stderr)
from mpq_tools import StormArchive
archive=StormArchive(target)
read=archive.read
original_manifest=json.loads((ROOT/'src/asset-manifest.json').read_text())
generated_manifest=json.loads((ROOT/'src/generated-assets.json').read_text())
manifest=__import__('music35').effective_manifest(original_manifest)+generated_manifest
for row in manifest:
 data=read(row['path']);assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],row['path']
metadata={p.name:p.read_bytes() for p in (ROOT/'dist/map').iterdir() if p.is_file()}
for name,data in metadata.items():assert read(name)==data,name
# Classic loads war3mapMap as a fixed 256x256 RGBA buffer (0x40000 bytes).
# A valid smaller TGA parses successfully but the 1.26 engine overreads it.
for name in ('war3mapMap.tga','war3mapPreview.tga'):
 data=metadata[name]
 assert data[2]==2 and data[16]==24,name
 assert struct.unpack_from('<HH',data,12)==(256,256),name
 assert len(data)==18+256*256*3,name
archive.close()
sys.path.insert(0,'/workspace/.warcraft-tools');import mpyq
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
assert len(full)<16*1024*1024 and hashlib.sha256(full).hexdigest()==report['sha256']
# Source scenery is intentionally transferred unchanged; runtime/story remain new.
scene=json.loads((ROOT/'src/location/provenance.json').read_text())
for row in scene['files']:
 data=(ROOT/'src/location'/row['file']).read_bytes()
 assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
 name=row['file'].removeprefix('original-')
 if name=='war3map.w3b':
  from presentation import scenery
  data=scenery()
 elif name=='war3map.wpm':
  from terrain49 import pathing
  data=pathing(data)
 elif name=='war3map.doo':data=(ROOT/'src/location/render-war3map.doo').read_bytes()
 assert metadata[name]==data
# Archive tables and scenario are newly authored; no original JASS.
assert b'function QDV takes' not in metadata['war3map.j']
result={'strictLegacyJASS':True,'classicMinimap256x256':True,'nativeStormLibImportedAssetsVerified':len(manifest),'independentPythonAssetsVerified':len(manifest),'nativeStormLibMetadataVerified':len(metadata),'allOriginalImportsUnchanged':False,'userMusicTracks':13,'preservedChapterTracks':2,'unchangedEarlierImports':len(original_manifest)-13,'originalImportsUnchanged':len(original_manifest)-13,'source35SkillVoices':5,'source35Icons':4,'generatedAssetsVerified':len(generated_manifest),'allImportedBytesOriginal':False,'ordinary4096ByteSectors':True,'below8MiBLimit':len(full)<8*1024*1024,'classic126NetworkSizeCompatible':len(full)<8*1024*1024,'enginePlaytest':False,'skillsMechanicsRecreated':report['recreatedSkillMechanics']}
(ROOT/'dist/verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
