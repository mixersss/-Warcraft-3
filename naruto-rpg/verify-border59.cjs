// Independent old/new archive comparison; no test calls to the padding builder.
const fs=require('fs'),assert=require('node:assert/strict'),crypto=require('crypto');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const W3e=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3e/file').default;
const W3i=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3i/file').default;
const root=__dirname,old=new MapFile(),now=new MapFile();
const file=fs.readFileSync(root+'/dist/Shinobi_Story_Alpha_59.w3x');
old.load(new Uint8Array(fs.readFileSync(root+'/../releases/shinobi-new/Shinobi_Story_Alpha_58.w3x')),true);now.load(new Uint8Array(file),true);
const bytes=(m,n)=>Buffer.from(m.get(n).bytes());
assert.deepEqual(now.getFileNames().sort(),old.getFileNames().sort());
const changed=new Set(['war3map.j','war3map.w3i','war3map.w3e','war3map.wpm','war3map.shd','war3mapMap.tga','war3mapPreview.tga']);
for(const n of old.getFileNames())if(!changed.has(n))assert.deepEqual(bytes(now,n),bytes(old,n),n+' exact Alpha58, including complete JASS, all objects, models, voices and music');
assert.equal(bytes(now,'war3map.j').toString().replaceAll('SHINOBI STORY ALPHA 59','SHINOBI STORY ALPHA 58'),bytes(old,'war3map.j').toString(),'Entire JASS unchanged except map title');
const a=new W3i(),b=new W3i();a.load(bytes(old,'war3map.w3i'));b.load(bytes(now,'war3map.w3i'));
assert.deepEqual([...a.cameraBoundsComplements],[0,0,0,0]);assert.deepEqual([...b.cameraBoundsComplements],[16,16,16,16]);
assert.deepEqual([...b.playableSize],[256,256]);assert.deepEqual(b.cameraBounds,a.cameraBounds);
b.name=b.name.replace('ALPHA 59','ALPHA 58');b.loadingScreenTitle=b.loadingScreenTitle.replace('ALPHA 59','ALPHA 58');b.cameraBoundsComplements=a.cameraBoundsComplements;assert.deepEqual(b,a,'All slots, allies, lobby and playable bounds unchanged');
const ea=new W3e(),eb=new W3e();ea.load(bytes(old,'war3map.w3e'));eb.load(bytes(now,'war3map.w3e'));
assert.deepEqual([...ea.mapSize],[257,257]);assert.deepEqual([...eb.mapSize],[289,289]);
assert.deepEqual([...eb.centerOffset],[-18432,-18432]);
for(let y=0;y<289;y++)for(let x=0;x<289;x++)assert.deepEqual(eb.corners[y][x],ea.corners[Math.max(0,Math.min(256,y-16))][Math.max(0,Math.min(256,x-16))],`Source vertex / edge apron ${x},${y}`);
function raster(name,header){
 const a=bytes(old,name),b=bytes(now,name),oldWidth=1024,w=1152,pad=64;
 if(header){assert.deepEqual(b.subarray(0,8),a.subarray(0,8));assert.equal(b.readUInt32LE(8),w);assert.equal(b.readUInt32LE(12),w);}
 assert.equal(b.length,header+w*w);
 for(let y=0;y<w;y++){
  const row=b.subarray(header+y*w,header+(y+1)*w);
  if(y<pad||y>=pad+oldWidth)assert(row.every(v=>v===255),'Whole outer row blocked/shadowed');
  else{assert(row.subarray(0,pad).every(v=>v===255));assert(row.subarray(pad+oldWidth).every(v=>v===255));assert.deepEqual(row.subarray(pad,pad+oldWidth),a.subarray(header+(y-pad)*oldWidth,header+(y-pad+1)*oldWidth),'Original interior raster exact');}
 }
}
raster('war3map.wpm',16);raster('war3map.shd',0);
for(const n of ['war3mapPreview.tga','war3mapMap.tga']){const p=bytes(now,n);assert.equal(p.length,18+256*256*3);assert.equal(p[2],2);assert.equal(p[16],24);assert.equal(p.readUInt16LE(12),256);assert.equal(p.readUInt16LE(14),256);}
assert.deepEqual(bytes(now,'war3mapPreview.tga'),bytes(now,'war3mapMap.tga'));
const result={filename:'Shinobi_Story_Alpha_59.w3x',bytes:file.length,sha256:crypto.createHash('sha256').update(file).digest('hex'),previousVersion:58,physicalTerrainTiles:288,playableTiles:256,apronUnits:2048,allOriginalWorldCoordinatesPreserved:true,allOriginalTerrainVerticesExact:true,allOriginalPathingAndShadowCellsExact:true,apronFullyBlocked:true,cameraBoundsAnd12SlotsExact:true,completeJASSExactExceptTitle:true,allGameplayObjectsAndImportedAssetsExact:true,minimap256Reframed:true,crashRootCauseConfirmed:false,enginePlaytest:false};
fs.writeFileSync(root+'/dist/border59-verification.json',JSON.stringify(result,null,2)+'\n');
console.log('PASS: full Alpha58 archive/JASS scope; byte-preserved interior terrain/pathing/shadows, consistent 288-tile physical world and blocked 2048-unit apron, unchanged 256-tile playable bounds/12 slots/assets. Native crash mitigation unconfirmed.');
