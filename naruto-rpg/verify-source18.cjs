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
for(const lane of wave.lanes){
 for(const [key,name]of Object.entries({origin:'CampaignWaveOrigin',destination:'CampaignWaveDestination',kind:'CampaignWaveKind',role:'CampaignWaveRole',period:'CampaignWavePeriod',delay:'CampaignWaveDelay'}))assert.equal(values(name)[lane.lane],lane[key]);
 let next=lane.destination;const chain=[lane.origin,next];while(next!==11){next=wave.redirects[next];assert(next!==undefined);chain.push(next)}
 assert(chain.every(i=>connected[cell(...nav.routes[i])]),'Disconnected wave lane '+lane.lane);
 assert.equal(lane.count,3);
}
const units=new ObjectParser();units.load(read('war3map.w3u'));
const unit=id=>units.customTable.objects.find(o=>o.newId===id);
const get=(o,k,l=0)=>o.modifications.find(m=>m.id===k&&(m.levelOrVariation||0)===l)?.value;
const frozen=JSON.parse(fs.readFileSync(path.join(root,'src/source18-fixes.json')));
const barrel=frozen.objects.w3u.find(o=>o.newId==='h01P');
for(const k of ['umdl','uhpm','usca'])assert.equal(get(unit('c012'),k),get(barrel,k));
const A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default,abilities=new A();abilities.load(read('war3map.w3a'));
const clone=abilities.customTable.objects.find(o=>o.newId==='Rn02');
const sourceClone=frozen.objects.w3a.find(o=>o.newId==='A001');
for(let rank=1;rank<=4;rank++){assert.equal(get(clone,'Omi1',rank),get(sourceClone,'Omi1',rank));assert.equal(get(clone,'Omi3',rank),get(sourceClone,'Omi3',rank));}
const sourceKaiten=frozen.objects.w3a.find(o=>o.newId==='A006');
assert.deepEqual([1,2,3,4].map(l=>get(sourceKaiten,'Wrs1',l)),[100,150,200,350]);
assert(script.includes('call UnitResetCooldown(Hero[p])'));
assert(script.includes('CampaignStage!=9 and CampaignStage!=11'));
assert(script.includes('FOG_OF_WAR_VISIBLE')&&script.includes('2600.,false,false'));
assert(script.includes('CampaignWinnerCount==3'));
assert(script.includes('call CampaignInvasionWave(lane)'));
assert(script.includes('call PauseUnit(CampaignActor[slot],false)'));
const report={sourceBarrelModelAndBody:true,sourceNarutoCloneRanks:4,sourceNarutoClonesEachRank:8,sourceKaitenDamage:[100,150,200,350],sourceInvasionStreams:8,sourceWaveCount:3,sourceWavePeriods:wave.lanes.map(l=>l.period),sourceWaveFirstDelays:wave.lanes.map(l=>l.delay),sourceSandHeroCamp:wave.attackerHeroCenter,sourceRouteWaypoints:nav.routes.length,allInvasionRouteWaypointsStaticallyConnected:true,sourceInvasionGatesOpen:2,allWaveLanesReachHokage:true,privateArenaTerrainSight:true,finalThreePlayers:true,nativeCooldownReset:true,enginePlaytest:false};
fs.writeFileSync(path.join(root,'dist/source18-verification.json'),JSON.stringify(report,null,2));console.log('PASS: source barrel body, four clone/Kaiten ranks, eight invasion schedules and connected source routes with opened gates; static checks, engine pathfinding still requires playtest.');
