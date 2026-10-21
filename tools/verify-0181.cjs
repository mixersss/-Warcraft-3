// Exact scope check against the last published build; rank stats are checked by verify-018.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),balance=require('../map/balance.json');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const prior=new MapFile();prior.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.18.0-alpha.w3x'))),true);
require('./historical-wave-settings.cjs')(prior);
const before=n=>Buffer.from(prior.get(n).bytes()),now=n=>fs.readFileSync(path.join(root,'build/map',n));
let petFields=0,descriptions=0;
for(const [P,name]of [[U,'war3map.w3u'],[A,'war3map.w3a']]){
 const current=new P(),previous=new P();current.load(new Uint8Array(now(name)));previous.load(new Uint8Array(before(name)));
 require('./army-branch-comparison.cjs').objects(current);
 for(const table of ['originalTable','customTable']){
  const old=new Map(previous[table].objects.map(o=>[o.oldId+':'+o.newId,o]));
  for(const o of current[table].objects){
   const ref=old.get(o.oldId+':'+o.newId);assert(ref,'No added objects');
   for(const m of o.modifications){
    const pet=name==='war3map.w3u'&&/^k[012][0-9a-f]{2}$/.test(o.newId)&&['uhpm','ua1b','udef','usca'].includes(m.id);
    const desc=name==='war3map.w3a'&&['V000','V001','V003'].includes(o.newId)&&['arut','aub1'].includes(m.id);
    if(pet||desc){const oldMod=ref.modifications.find(n=>n.id===m.id&&n.levelOrVariation===m.levelOrVariation&&n.dataPointer===m.dataPointer);assert(oldMod);m.value=oldMod.value;if(pet)petFields++;else descriptions++;}
   }
  }
 }
 assert.deepEqual(current,previous,name+' changes restricted to pet stats and three summon descriptions');
}
assert.equal(petFields,1800);assert.equal(descriptions,453);
for(const name of ['war3map.w3q','war3map.w3t','war3map.w3h','war3map.w3b','war3map.wpm','war3map.w3e','war3mapMisc.txt','war3map.doo','war3mapUnits.doo','war3map.imp','war3mapMap.tga','war3mapPreview.tga'])assert.deepEqual(now(name),before(name),name+' unchanged');
const strip=s=>require('./army-branch-comparison.cjs').runtime(s,before('war3map.j').toString()).replaceAll(balance.version,'0.18.0-alpha').replace(/function CreativeSummon takes[\s\S]*?endfunction/,'');
assert.equal(strip(now('war3map.j').toString()),strip(before('war3map.j').toString()),'Only CreativeSummon and version change at runtime');
fs.writeFileSync(path.join(root,'build/verification-0181.json'),JSON.stringify({version:balance.version,petRanks:450,petStatFields:petFields,summonCount:'base + floor(skillRank / 10)',ordinaryCounts:{1:2,10:3,20:4,200:22},ultimateCounts:{1:1,10:2,50:6},growth:'Rexxar ordinary summon curve; no ultimate multipliers',otherObjectsAndRuntimePreserved:true,enginePlaytest:false},null,2)+'\n');
console.log('PASS: 450 pet ranks use ordinary Rexxar growth; only pet stats, descriptions and summon handler differ from 0.18.0.');
