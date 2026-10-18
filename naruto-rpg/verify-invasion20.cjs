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
 if(d.id==='YTpb'||(d.id==='LTe1'&&Math.abs(d.location[0]-5248)<1&&Math.abs(d.location[1]+3456)<1)||(d.id==='LTe3'&&Math.abs(d.location[0]+1664)<1&&Math.abs(d.location[1]+11904)<1))continue;
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

const connected=flood(nav.routes[11]);
const wave=JSON.parse(fs.readFileSync(path.join(root,'src/invasion-waves-source.json')));
for(const [i,p]of nav.routes.entries())assert(!blocked[cell(...p)]&&connected[cell(...p)],'Source invasion waypoint is unreachable: '+i);
assert(connected[cell(...near(...wave.attackerHeroCenter))],'Sand hero FM camp disconnected');

const layout=JSON.parse(fs.readFileSync(path.join(root,'src/invasion20-layout.json')));
for(const [positions,xname,yname]of [[layout.defenders,'CampaignDefenderX','CampaignDefenderY'],[layout.waveSpawns,'CampaignWaveSpawnX','CampaignWaveSpawnY']]){
 for(const [i,p]of positions.entries()){
  assert.equal(values(xname)[i],p[0]);assert.equal(values(yname)[i],p[1]);
  assert(!blocked[cell(...p)]&&connected[cell(...p)],'Unreachable new placement '+xname+i);
  for(let k=0;k<i;k++)assert((p[0]-positions[k][0])**2+(p[1]-positions[k][1])**2>=96**2,'Crowded placement');
 }
}
for(const p of layout.defenders)assert((p[0]-16128)**2+(p[1]+15744)**2<800**2,'Defender too far from corner fountain');
for(const row of layout.reserves){assert.equal(values('CampaignReserveX')[row.kind],row.position[0]);assert.equal(values('CampaignReserveY')[row.kind],row.position[1]);assert(!blocked[cell(...row.position)]&&connected[cell(...row.position)]);}
assert.equal(layout.defenders.length,9);assert.equal(layout.reserves.length,5);assert.equal(layout.waveSpawns.length,24);
for(const p of layout.defenders)assert(Math.abs(p[0]-16128)>=288||Math.abs(p[1]+15744)>=288,'Keep heroes outside fountain footprint');
const recovery=script.match(/function CampaignWaveRecover takes[\s\S]*?endfunction/)[0];
assert(!/SetUnit(?:Position|X|Y)|CreateTimer|CreateGroup/.test(recovery),'Recovery must not teleport or allocate per-unit handles');
assert(recovery.includes('IsTerrainPathable')&&recovery.includes('exitwhen k>=8'));
assert(script.includes('not CampaignReserveOnly(CampaignActorType[j])'));
const report={defenderFountain:layout.defenderFountain,defenderSpawns:layout.defenders,reservePlacements:layout.reserves,waveSpawnPositions:layout.waveSpawns.length,minSpawnSpacing:96,allPlacementsStaticallyConnected:true,waveRecoveryProbeSeconds:8,recoveryDoesNotTeleport:true,recoveryUsesExistingSharedHeartbeat:true,sourceWaveCountsAndSchedulesUnchanged:true,enginePlaytest:false};
fs.writeFileSync(path.join(root,'dist/invasion20-verification.json'),JSON.stringify(report,null,2));console.log('PASS: nine corner-fountain spawns, five rear reserve positions, 24 separated wave spawns on statically connected clear ground; dynamic unit collision still needs an engine test.');
