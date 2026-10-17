// Small Classic MDX ground strip. No external textures: standard replaceable team-color
// texture, tinted near black at runtime, non-additive material. Original imports stay untouched.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const base='mdx-m3-viewer/dist/cjs/parsers/mdlx/';
const C=n=>require(base+n).default;
const m=new (C('model'))();m.version=800;m.name='Shinobi Shadow Strip';
const extent=e=>{e.min.set([-25,-12,0]);e.max.set([25,12,1]);e.boundsRadius=28;return e;};extent(m.extent);
const s=new (C('sequence'))();s.name='Stand';s.interval.set([0,1000]);s.nonLooping=0;extent(s.extent);m.sequences.push(s);
const t=new (C('texture'))();t.replaceableId=1;m.textures.push(t);
const layer=new (C('layer'))();layer.filterMode=2;layer.flags=1|16;layer.textureId=0;layer.alpha=.9;
const mat=new (C('material'))();mat.layers.push(layer);m.materials.push(mat);
const g=new (C('geoset'))();g.vertices=new Float32Array([-25,-12,0,25,-12,0,25,12,0,-25,12,0]);g.normals=new Float32Array([0,0,1,0,0,1,0,0,1,0,0,1]);g.faceTypeGroups=new Uint32Array([4]);g.faceGroups=new Uint32Array([6]);g.faces=new Uint16Array([0,1,2,0,2,3]);g.vertexGroups=new Uint8Array(4);g.matrixGroups=new Uint32Array([1]);g.matrixIndices=new Uint32Array([0]);g.uvSets.push(new Float32Array([0,0,1,0,1,1,0,1]));extent(g.extent);const E=require(base+'extent').default;g.sequenceExtents.push(extent(new E()));m.geosets.push(g);
const b=new (C('bone'))();b.name='GroundStrip';b.objectId=0;b.geosetId=0;m.bones.push(b);m.pivotPoints.push(new Float32Array(3));
const bytes=Buffer.from(m.saveMdx());const parsed=new (C('model'))();parsed.load(new Uint8Array(bytes));assert.equal(parsed.version,800);assert.equal(parsed.geosets[0].vertices.length,12);assert.equal(parsed.materials[0].layers[0].filterMode,2);assert.equal(parsed.textures[0].replaceableId,1);
const file=path.join(__dirname,'src/generated-shadow-strip.mdx');fs.writeFileSync(file,bytes);
fs.writeFileSync(path.join(__dirname,'src/generated-assets.json'),JSON.stringify([{path:'ShinobiShadowStrip.mdx',file:'src/generated-shadow-strip.mdx',bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),purpose:'Visible non-additive ground shadow, 50 by 24 units, native team-color texture tinted near black'}],null,2)+'\n');
console.log('Generated and parsed Classic 800 shadow strip with opaque-color geometry and no external textures.');
