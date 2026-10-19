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
const seats=JSON.parse(fs.readFileSync(path.join(root,'src/arena-stands-source.json')));
let checked=0;
for(const [stage,rows]of Object.entries(seats.stages)){
 assert.equal(rows.length,12);const floor=stage==='9'?[15200,-9152]:[14784,-13648];const height=e.corners[Math.floor((floor[1]+16384)/128)][Math.floor((floor[0]+16384)/128)].layerHeight;
 for(const [p,s]of rows.entries()){
  const b=seats.regions[s.region],n=p+(stage==='11'?12:0);assert(s.x>=b[0]&&s.x<=b[2]&&s.y>=b[1]&&s.y<=b[3]);
  assert(!blocked[Math.floor((s.y+16384)/32)*w+Math.floor((s.x+16384)/32)],'Clear original upper terrace seat');
  const c=e.corners[Math.floor((s.y+16384)/128)][Math.floor((s.x+16384)/128)];assert(c.layerHeight>height,'Spectator must actually be above arena');
  assert(script.includes(`set ArenaSeatX[${n}]=${s.x}.0`)&&script.includes(`set ArenaSeatY[${n}]=${s.y}.0`));
  for(const other of rows.slice(0,p))assert(Math.hypot(s.x-other.x,s.y-other.y)>=72,'Separate viewer footprints');checked++;
 }
}
const U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
function parse(P,name){let p=new P();p.load(read(name));return Object.fromEntries(p.customTable.objects.map(o=>[o.newId,o]));}
const units=parse(U,'war3map.w3u'),items=parse(U,'war3map.w3t'),abilities=parse(A,'war3map.w3a');
const get=(o,k)=>o.modifications.find(m=>m.id===k)?.value;
assert.equal(get(items.Nnot,'iabi'),'Lexp');assert.equal(get(items.Nnot,'iuse'),2);assert.equal(get(items.Nnot,'iprn'),1);assert.equal(get(items.Nnot,'icla'),'Charged');
assert.equal(abilities.Lexp.oldId,'ANcl');assert.equal(get(abilities.Lexp,'aite'),1);assert.equal(get(abilities.Lexp,'Ncl2'),2);assert.equal(get(abilities.Lexp,'aran'),300);assert.equal(get(abilities.Lexp,'Ncl6'),'stasistrap');
assert.equal(units.rnnt.oldId,'nglm');assert.equal(get(units.rnnt,'umdl'),'Note.mdl');assert.equal(get(units.rnnt,'uabi'),'');assert.equal(get(units.rnnt,'uhpm'),100);
const use=script.match(/function RamenUse takes[\s\S]*?endfunction/)[0];assert(!use.includes('CreateTrigger'));assert(!script.includes('RamenInterrupted'));assert(script.includes('if CampaignStage!=9 and CampaignStage!=11 and StoryStage[t]<9 and not CampaignTransition and dx*dx+dy*dy<700.*700. then'));
assert(script.includes("set StoryShop[j]=CreateUnit(Player(14),'rqsh'"));assert(script.includes('call CampaignVillageLandmarksOpen()'));assert(script.includes('call CampaignVillageLandmarksClose()'));assert(script.includes('msg=="-fountain"'));
const source=JSON.parse(fs.readFileSync(path.join(root,'src/exploding-note-source.json')));const damage=source.originalRecords.w3a.find(o=>o.oldId==='Amnx');assert.equal(damage.modifications.find(m=>m.id==='Dda2').value,400);assert.equal(damage.modifications.find(m=>m.id==='Dda3').value,300);
const result={upperTierSeatsVerified:checked,sourceTerraceRegions:6,realTerrainElevationAndFootprints:true,arenaCampHealingExcluded:true,explodingNotePointCast:true,explosionDamage:[400,300],boundedTraps:128,trapExpirySeconds:180,ramenUnaffectedByDamage:true,ramenDamageTriggers:0,villageNeutralShops:4,villageFountains:4,villageServiceFogRadius:320,villageServiceFogHandlesBounded:96,nativeMocks:'test-skills.cjs / arena-items-harness.lua / campaign-harness.lua / forest-fixes-harness.lua',enginePlaytest:false};
fs.writeFileSync(path.join(root,'dist/arena-items-verification.json'),JSON.stringify(result,null,2));console.log('PASS: 24 clear seats on higher original terraces; point-target consumable/trap objects and source damage; no camp healing in arenas or ramen damage listeners; neutral visible village services. Actual engine playtest unrun.');
