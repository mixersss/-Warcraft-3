const fs=require('fs'),assert=require('node:assert/strict'),crypto=require('crypto');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const root=__dirname,old=new MapFile(),now=new MapFile(),file=fs.readFileSync(root+'/dist/Shinobi_Story_Alpha_52.w3x');
old.load(new Uint8Array(fs.readFileSync(root+'/../releases/shinobi-new/Shinobi_Story_Alpha_51.w3x')),true);now.load(new Uint8Array(file),true);
const bytes=(map,n)=>Buffer.from(map.get(n).bytes());assert.deepEqual(now.getFileNames().sort(),old.getFileNames().sort());
for(const n of now.getFileNames())if(!['war3map.w3u','war3map.w3i','war3map.j'].includes(n))assert.deepEqual(bytes(now,n),bytes(old,n),n+' unchanged');
for(const n of ['war3map.j','war3map.w3i'])assert.deepEqual(bytes(now,n),Buffer.from(bytes(old,n).toString('latin1').replaceAll('ALPHA 51','ALPHA 52'),'latin1'),n+' version only');
const parse=d=>{const p=new U();p.load(new Uint8Array(d));return p.customTable.objects;};
const a=parse(bytes(old,'war3map.w3u')),b=parse(bytes(now,'war3map.w3u')),ids=JSON.parse(fs.readFileSync(root+'/src/heroes.json')).map(h=>h.id).concat(['Rnfm','Rsfm','Rkfm','Rgfm']);
assert.equal(ids.length,16);assert.deepEqual(a.map(o=>o.newId),b.map(o=>o.newId));let changed=0;
for(let i=0;i<a.length;i++){const p=a[i],q=b[i];if(!ids.includes(p.newId)){assert.deepEqual(q,p,p.newId+' unchanged');continue;}assert.equal(q.oldId,p.oldId);assert.equal(p.modifications.find(m=>m.id==='ucol').value,24);assert.equal(q.modifications.find(m=>m.id==='ucol').value,16);assert.deepEqual(q.modifications.filter(m=>m.id!=='ucol'),p.modifications.filter(m=>m.id!=='ucol'));changed++;}
assert.equal(changed,16);const report={filename:'Shinobi_Story_Alpha_52.w3x',bytes:file.length,sha256:crypto.createHash('sha256').update(file).digest('hex'),heroCollisionRadius:{before:24,after:16},heroObjects:ids,terrainPathingPreserved:true,allOtherFieldsAssetsAndGameplayUnchanged:true,enginePlaytest:false};fs.writeFileSync(root+'/dist/collision52-verification.json',JSON.stringify(report,null,2)+'\n');console.log('PASS: all12 heroes and4 alternate forms collision24->16; all other fields/files/JASS exact51 except version.');
