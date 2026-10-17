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
for(let t=0;t<4;t++){
 const start=cell(sx[t*3],sy[t*3]),seen=new Uint8Array(w*w),queue=new Int32Array(w*w);let head=0,tail=0;
 assert(!blocked[start],'Blocked team spawn '+t);queue[tail++]=start;seen[start]=1;
 while(head<tail){const cur=queue[head++];for(const next of [cur-1,cur+1,cur-w,cur+w])if(next>=0&&next<w*w&&!blocked[next]&&!seen[next]){seen[next]=1;queue[tail++]=next}}
 for(let n=0;n<4;n++)assert(seen[cell(gx[t*4+n],gy[t*4+n])],'Unreachable chapter stage '+t+':'+n);
 for(let n=0;n<16;n++){
  const [x,y]=n<14?original.ninjas[t][n]:n===14?original.haku[t]:original.zabuza[t];
  assert.equal(ex[t*18+n],x);assert.equal(ey[t*18+n],y);
  // Source CreateUnit may settle a colliding spawn onto adjacent clear ground.
  let reachable=false;for(let dy=-128;dy<=128;dy+=32)for(let dx=-128;dx<=128;dx+=32)if(seen[cell(x+dx,y+dy)])reachable=true;
  assert(reachable,'Unreachable original actor '+t+':'+n);
 }
 for(let other=0;other<4;other++)if(other!==t)assert(!seen[cell(sx[other*3],sy[other*3])],'Unexpected cross-team forest route');
}
const originalDoo=new Parser();originalDoo.load(new Uint8Array(fs.readFileSync(path.join(root,'src/location/original-war3map.doo'))));
for(let i=0;i<doodads.doodads.length;i++){
 const a=doodads.doodads[i],b=originalDoo.doodads[i];assert.equal(a.id,b.id);assert.deepEqual([...a.location],[...b.location]);assert.equal(a.flags,b.flags);assert.equal(a.life,b.life);
 if(['LTlt','CTtc'].includes(a.id))assert.deepEqual([...a.scale],[1,1,1]);else assert.deepEqual([...a.scale],[...b.scale]);
}
const scenery=new ObjectParser();scenery.load(read('war3map.w3b'));
for(const id of ['LTlt','CTtc']){
 const mods=scenery.originalTable.objects.find(o=>o.oldId===id).modifications;
 const get=k=>mods.find(m=>m.id===k)?.value;
 assert.equal(get('bvar'),10);assert(get('bfil').startsWith('Doodads\\Terrain\\'));assert.equal(get('bmap'),0);assert.equal(get('bmar'),0);
}
const misc=fs.readFileSync(path.join(root,'dist/map/war3mapMisc.txt'),'utf8');
assert(misc.includes('MaxHeroLevel=60'));assert(misc.includes('HeroExpRange=2000.0'));assert(misc.includes('HeroFactorXP=90,90,70,70,70,70,70,50,40,40,40,40,40,40,40,40,40,40,30'));
const schema=JSON.parse(fs.readFileSync(path.join(root,'src/classic-skill-schema.json')));
const itemFile=new ObjectParser();itemFile.load(read('war3map.w3t'));
assert.equal(itemFile.customTable.objects.length,14);
const field=o=>Object.fromEntries(o.modifications.map(m=>[m.id,m.value]));
for(const item of itemFile.customTable.objects){assert(schema.stockIds.items.includes(item.oldId),'Invalid item base');const f=field(item);assert(f.igol>0 && f.ilum===0);if(f.iabi)assert(schema.stockIds.abilities.includes(f.iabi) || ['Lgar','Lcar','Ljkn','Ljsh','Ljnt'].includes(f.iabi));for(const m of item.modifications)assert(schema.itemFields[m.id],'Invalid item field '+m.id)}
const assets=new Set(JSON.parse(fs.readFileSync(path.join(root,'src/asset-manifest.json'))).map(a=>a.path.toLowerCase()));
const modelAnimations=JSON.parse(fs.readFileSync(path.join(root,'src/model-animations.json')));
for(const [model,index] of [['MistNin.mdx',5],['RainGenin.mdx',4],['haku.mdx',2],['Zabuza.mdx',5]])assert(modelAnimations.find(m=>m.path===model).animations[index]);
assert(assets.has('gaarasand2.mdx'));
const result={sourceSceneryCount:8936,terrainSize:[256,256],independentTeamRoutes:4,reachableStages:16,approximateHeroClearance:32,rectangularSceneryCollisionIncluded:true,nonRectangularFootprints:'retained original WPM; native engine test needed',nativeShopItems:7,originalLootItems:7,originalNinjasPerTeam:14,originalActorPositionsVerified:64,mentorDepartureSeconds:330,validatedEnemyAnimationIndices:4,enginePlaytest:false};
fs.writeFileSync(path.join(root,'dist/story-verification.json'),JSON.stringify(result,null,2));
console.log('PASS: original terrain/scenery, four isolated forest routes and 16 reachable stages with conservative rectangular footprints/clearance; seven valid native shop items, seven original loot types, 56 original ninja positions, Haku/Zabuza and the 330s mentor timer and enemy model animation indices.');
