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
const nav={};for(const st of doc.stages){let target=near(...st.target),spawn=near(...st.spawn);const seen=flood(target);let portal=false;if(!seen[cell(...spawn)]){portal=true;spawn=near(target[0]-256,target[1]);if(!seen[cell(...spawn)])spawn=target;}nav[st.id]={spawn,target,bounds:[Math.min(st.bounds[0],spawn[0]-512,target[0]-512),Math.min(st.bounds[1],spawn[1]-512,target[1]-512),Math.max(st.bounds[2],spawn[0]+512,target[0]+512),Math.max(st.bounds[3],spawn[1]+512,target[1]+512)],incomingScenePortal:portal,sourceSpawn:st.spawn,sourceTarget:st.target};}
// Jiraiya: 20 source-style barrels on connected clear village tiles.
nav.barrels=[];const center=nav['10'].spawn,seen=flood(center);for(let y=-13000;y<-4000 && nav.barrels.length<20;y+=800)for(let x=0;x<12000 && nav.barrels.length<20;x+=1200){const p=near(x,y,512);if(seen[cell(...p)]&&!nav.barrels.some(q=>Math.hypot(q[0]-p[0],q[1]-p[1])<400))nav.barrels.push(p)}assert.equal(nav.barrels.length,20);
nav.routes=doc.invasionRoutePoints.map(p=>near(...p));nav.five=doc.soundFivePositions.map(p=>near(p[2],p[3]));
fs.writeFileSync(path.join(root,'src/campaign-navigation.json'),JSON.stringify(nav,null,2));console.log('Generated source-room navigation for '+doc.stages.length+' phases and 20 connected barrels');
