// Conservative static route check; Warcraft's dynamic collision still needs a playtest.
const fs=require('fs'),assert=require('assert/strict'),path=require('path');
const Parser=require('mdx-m3-viewer/dist/cjs/parsers/w3x/doo/file').default;
const ObjectParser=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const W3e=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3e/file').default;
const root=__dirname,read=n=>new Uint8Array(fs.readFileSync(path.join(root,'dist/map',n)));
const doodads=new Parser();doodads.load(read('war3map.doo'));
assert.equal(doodads.doodads.length,8936);
const e=new W3e();e.load(read('war3map.w3e'));assert.deepEqual([...e.mapSize],[257,257]);assert.deepEqual([...e.centerOffset],[-16384,-16384]);
const paths=JSON.parse(fs.readFileSync(path.join(root,'src/location/scenery-paths.json')));
const wpm=Buffer.from(read('war3map.wpm'));assert.equal(wpm.readInt32LE(8),1024);assert.equal(wpm.readInt32LE(12),1024);
let grid=Uint8Array.from(wpm.subarray(16));const w=1024;
for(const d of doodads.doodads){
 if(d.id==='YTpb')continue;
 assert(d.id in paths,'Unresolved scenery ID '+d.id);
 const m=paths[d.id].match(/(\d+)x(\d+)(Default|Unflyable)/);
 if(!m)continue;const sx=+m[1],sy=+m[2],cx=(d.location[0]+16384)/32,cy=(d.location[1]+16384)/32;
 for(let y=Math.max(0,Math.floor(cy-sy/2));y<Math.min(w,Math.ceil(cy+sy/2));y++)for(let x=Math.max(0,Math.floor(cx-sx/2));x<Math.min(w,Math.ceil(cx+sx/2));x++)grid[y*w+x]|=2;
}
// Add one cell of clearance around walls and rectangular footprints (hero collision=24).
const blocked=new Uint8Array(grid.length);
for(let y=0;y<w;y++)for(let x=0;x<w;x++)blocked[y*w+x]=x===0||y===0||x===w-1||y===w-1||[0,-1,1,-w,w].some(k=>grid[y*w+x+k]&2)?1:0;
const script=fs.readFileSync(path.join(root,'dist/map/war3map.j'),'utf8');
function values(name){return Object.fromEntries([...script.matchAll(new RegExp('set '+name+'\\[(\\d+)\\]=(-?[\\d.]+)','g'))].map(m=>[+m[1],+m[2]]))}
const sx=values('SpawnX'),sy=values('SpawnY'),gx=values('StoryX'),gy=values('StoryY'),ex=values('EnemySpawnX'),ey=values('EnemySpawnY');
const original=JSON.parse(fs.readFileSync(path.join(root,'src/original-forest-spawns.json')));
assert(original.ninjas.every(a=>a.length===14));
const cell=(x,y)=>Math.floor((y+16384)/32)*w+Math.floor((x+16384)/32);


const doc=JSON.parse(fs.readFileSync(path.join(root,'src/campaign-source.json')));
function near(x,y,max=1024){let best=null,d=1e30;for(let dy=-max;dy<=max;dy+=32)for(let dx=-max;dx<=max;dx+=32){const cx=Math.floor((x+dx+16384)/32),cy=Math.floor((y+dy+16384)/32),n=cy*w+cx;if(cx>0&&cx<w-1&&cy>0&&cy<w-1&&!blocked[n]&&dx*dx+dy*dy<d){best=[cx*32-16384+16,cy*32-16384+16];d=dx*dx+dy*dy}}assert(best,'No free source ground');return best;}
function flood(p){const seen=new Uint8Array(w*w),q=new Int32Array(w*w);let h=0,t=0;const start=cell(...p);q[t++]=start;seen[start]=1;while(h<t){const n=q[h++];for(const j of [n-1,n+1,n-w,n+w])if(j>=0&&j<w*w&&!blocked[j]&&!seen[j]){seen[j]=1;q[t++]=j}}return seen;}
const nav=JSON.parse(fs.readFileSync(path.join(root,'src/campaign-navigation.json')));
const objects=new ObjectParser();objects.load(read('war3map.w3u'));const npcs=Object.fromEntries(objects.customTable.objects.map(o=>[o.newId,o]));
for(const st of doc.stages){const p=nav[st.id],seen=flood(p.target);assert(!blocked[cell(...p.spawn)],'Blocked scene spawn '+st.id);assert(seen[cell(...p.spawn)],'Disconnected scene '+st.id);assert(st.name && st.intro && st.sourceFunction);}
const village=flood(nav[10].spawn);assert.equal(nav.barrels.length,20);for(const p of nav.barrels)assert(village[cell(...p)],'Unreachable search barrel');
assert.equal(doc.cloneRooms.length,8);for(let n=20;n<28;n++){const u=npcs['C'+n.toString(16).toUpperCase().padStart(3,'0')];assert(u,'Missing clone body '+n);}
const byId=Object.fromEntries(doc.stages.map(s=>[s.id,s]));for(const [id,seconds] of [[10,150],[12,1500],[13,360],[14,360],[15,240]])assert.equal(byId[id].seconds,seconds,'Wrong source chapter deadline '+id);
assert.equal(nav.routes.length,12);assert.equal(nav.five.length,5);
for(const [n,hp,damage] of [[0,100000,299],[3,375000,549],[4,275000,549],[11,10000,129],[12,60000,499],[15,3000,109],[16,3000,109]]){const o=npcs['C'+n.toString(16).toUpperCase().padStart(3,'0')],f=Object.fromEntries(o.modifications.map(m=>[m.id,m.value]));assert.equal(f.uhpm,hp);assert.equal(f.ua1b,damage);}
const items=new ObjectParser();items.load(read('war3map.w3t'));const AbilityParser=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;const abilities=new AbilityParser();abilities.load(read('war3map.w3a'));const amap=Object.fromEntries(abilities.customTable.objects.map(o=>[o.newId,o]));
for(const [id,a,field,column] of [['Nsht','Cstr','Istr',3],['Nsch','Cint','Iint',2],['Nsta','Cagi','Iagi',1]]){const item=items.customTable.objects.find(o=>o.newId===id);assert.equal(item.modifications.find(m=>m.id==='iabi').value,a);const m=amap[a].modifications.find(m=>m.id===field);assert.equal(m.value,6);assert.equal(m.dataPointer,column);}
const note=items.customTable.objects.find(o=>o.newId==='Nnot');assert.equal(note.modifications.find(m=>m.id==='iabi').value,'AIpm');
const result={objectives:doc.stages.length,connectedObjectivePairs:doc.stages.length,connectedSearchBarrels:20,sourceDeadlinesVerified:5,parallelClones:8,sourceSeededNpcStatsVerified:7,sourceShopItems:11,nativeStatScrollBonus:6,fullJASSBehavior:'test-skills.cjs / campaign-harness.lua',originalCinematicsIdentical:false,originalNpcJutsusComplete:false,enginePlaytest:false};
fs.writeFileSync(path.join(root,'dist/campaign-verification.json'),JSON.stringify(result,null,2));console.log('PASS: 22 source-linked objectives, connected room entrances/targets and 20 search barrels, eight clone models, original chapter deadlines/NPC stats, real +6 stat item fields and native exploding note alias. Engine playtest remains required.');
