// Exact regression against the published map, without historical normalization.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),balance=require('../map/balance.json');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default,Q=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const previous=new MapFile();previous.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.17.0-alpha.w3x'))),true);
const before=n=>Buffer.from(previous.get(n).bytes()),now=n=>fs.readFileSync(path.join(root,'build/map',n));
assert.equal(balance.spawn_seconds,18);assert.equal(balance.spawn_min_seconds,18);assert.equal(balance.army_cap,85);
let tooltips=0;
for(const [Parser,name,id,field]of [[U,'war3map.w3u','fbax','utub'],[Q,'war3map.w3q','Rfwn','gub1']]){
 const current=new Parser(),old=new Parser();current.load(new Uint8Array(now(name)));old.load(new Uint8Array(before(name)));
 const ref=old.customTable.objects.find(o=>o.newId===id);
 for(const m of current.customTable.objects.find(o=>o.newId===id).modifications)if(m.id===field){
  const prior=ref.modifications.find(n=>n.id===m.id&&n.levelOrVariation===m.levelOrVariation);
  assert.equal(m.value,prior.value.replace('Спавн раз в 21 секунд','Спавн раз в 18 секунд').replace('Предел живой армии 60 сохранён.','Предел живой армии 85 сохранён.'));
  m.value=prior.value;tooltips++;
 }
 assert.deepEqual(current,old,'All other unit/research fields stay identical');
}
assert.equal(tooltips,21);
for(const name of ['war3map.w3a','war3map.w3t','war3map.w3h','war3map.w3b','war3map.wpm','war3map.w3e','war3mapMisc.txt','war3map.doo','war3mapUnits.doo','war3map.imp','war3mapMap.tga','war3mapPreview.tga'])assert.deepEqual(now(name),before(name),name+' unchanged');
const expected=before('war3map.j').toString().replaceAll('0.17.0-alpha',balance.version).replace('constant integer SPAWN_SECONDS = 21','constant integer SPAWN_SECONDS = 18').replace('constant integer SPAWN_MIN_SECONDS = 21','constant integer SPAWN_MIN_SECONDS = 18').replace('constant integer ARMY_CAP = 60','constant integer ARMY_CAP = 85').replaceAll('every 21 seconds','every 18 seconds').replaceAll('army cap 60','army cap 85');
assert.equal(now('war3map.j').toString(),expected,'Only wave constants, version and explanatory text changed');
fs.writeFileSync(path.join(root,'build/verification-0171.json'),JSON.stringify({version:balance.version,waveSeconds:18,previousWaveSeconds:21,armyCapPerPlayer:85,teamArmyCap:255,allTwelvePlayersArmyCap:1020,startingWave:3,otherUnitResearchSpellItemFieldsUnchanged:true,otherRuntimeUnchanged:true,enginePlaytest:false},null,2)+'\n');
console.log('PASS: 18-second waves, cap 85 per player / 255 per team; every other 0.17.0 object and runtime field preserved.');
