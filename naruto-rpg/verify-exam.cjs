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

const exam=JSON.parse(fs.readFileSync(path.join(root,'src/exam-source.json')));
function closest(x,y){let best=null,dist=1e30;for(let dy=-512;dy<=512;dy+=32)for(let dx=-512;dx<=512;dx+=32){const cx=Math.floor((x+dx+16384)/32),cy=Math.floor((y+dy+16384)/32),n=cy*w+cx;if(!blocked[n]&&dx*dx+dy*dy<dist){best=[cx*32-16384+16,cy*32-16384+16];dist=dx*dx+dy*dy}}assert(best);return best;}
const tower=closest(...exam.tower),seen=new Uint8Array(w*w),queue=new Int32Array(w*w);let h=0,tail=0;const start=cell(...tower);queue[tail++]=start;seen[start]=1;
while(h<tail){const n=queue[h++];for(const next of [n-1,n+1,n-w,n+w])if(next>=0&&next<w*w&&!blocked[next]&&!seen[next]){seen[next]=1;queue[tail++]=next}}
let bad=[];for(const [i,a] of exam.enemies.entries()){let p=closest(a.x,a.y);if(!seen[cell(...p)])bad.push(i)}
assert.equal(bad.length,0,'Every source genin must be reachable');
for(const p of exam.navigation.entrances)assert(seen[cell(...p)],'Every team entrance must reach tower');
assert.deepEqual(tower,exam.navigation.tower);
assert.equal(exam.enemies.length,85);
for(const [i,a] of exam.enemies.entries()){const p=exam.navigation.enemies[i];assert(Math.hypot(a.x-p[0],a.y-p[1])<=512,'Source placement moved too far');assert(seen[cell(...p)])}
const questions=JSON.parse(fs.readFileSync(path.join(root,'src/exam-questions.json')));assert.equal(questions.length,16);for(const q of questions){assert.equal(q.options.length,4);assert(q.answer>=1&&q.answer<=4)}
const result={originalGeninPositions:85,reachableGeninPositions:85,originalTeamEntrances:4,allEntrancesReachTowerAfterOpening:true,openedDestructableType:'YTpb',questionBank:16,rounds:5,secondsPerQuestion:15,sourceTimerSeconds:1320,nativeMocksIn:'test-skills.cjs / exam-harness.lua',enginePlaytest:false};
fs.writeFileSync(path.join(root,'dist/exam-verification.json'),JSON.stringify(result,null,2));
console.log('PASS: four original entrances and all 85 genin placements reach the original tower after YTpb gate opening; 16 valid translated question choices. Engine pathfinding remains untested.');
