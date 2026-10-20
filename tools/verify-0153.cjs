// Compare every emitted ability/research field with the published 0.15.2 map.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),balance=require('../map/balance.json');
const Map=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const Parser=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const old=new Map();old.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.15.2-alpha.w3x'))),true);
function parse(name,previous=false){const p=new Parser();p.load(new Uint8Array(previous?old.get(name).bytes():fs.readFileSync(path.join(root,'build/map',name))));return p;}
const key=m=>m.id+':'+m.levelOrVariation+':'+m.dataPointer;
let changed=0,mortar=0;
for(const name of ['war3map.w3a','war3map.w3q']){
 const current=parse(name),previous=parse(name,true);require('./roster-comparison.cjs')(current,previous);
 for(const table of ['originalTable','customTable']){
  const before=new globalThis.Map(previous[table].objects.map(o=>[o.oldId+':'+o.newId,o]));
  for(const o of current[table].objects){
   const ref=before.get(o.oldId+':'+o.newId);assert(ref);
   const mods=new globalThis.Map(ref.modifications.map(m=>[key(m),m]));
   for(const m of o.modifications){
    const prior=mods.get(key(m));assert(prior);
    if(name.endsWith('w3a') && balance.spell_damage_overrides[o.oldId] && balance.spell_damage_fields[o.oldId].includes(m.id)){
     assert(Math.abs(m.value-prior.value*.7)<=Math.max(.00011,Math.abs(prior.value)*1e-6),o.newId+':'+m.id);changed++;if(o.newId==='Fc20')mortar++;
     m.value=prior.value;
    }else if(name.endsWith('w3a') && balance.spell_damage_overrides[o.oldId] && m.id==='aub1')m.value=prior.value;

   }
  }
 }
 if(name.endsWith('w3q'))require('./summon-comparison.cjs').research(current,previous);
 assert.deepEqual(current,previous,'All unrelated '+name+' fields must remain identical');
}
assert(changed>1000 && mortar===400,'Mortar custom wave: damage/hit cap at all 200 ranks');
for(const name of ['war3map.w3t','war3map.w3h','war3map.w3e','war3map.wpm','war3mapMisc.txt','war3map.doo'])assert.deepEqual(fs.readFileSync(path.join(root,'build/map',name)),Buffer.from(old.get(name).bytes()),name+' unchanged');
fs.writeFileSync(path.join(root,'build/verification-0153.json'),JSON.stringify({version:balance.version,additionalBurstDamageFactor:.7,abilities:Object.keys(balance.spell_damage_overrides),mortarRanks:200,damageFields:changed,troopPricesValidatedSeparately:'verify-0161',buildingWavePricesUnchanged:true,summonsUnitsItemsTerrainUnchanged:true,enginePlaytest:false},null,2)+'\n');
console.log('PASS: Mortar and related burst spells -30% against published 0.15.2; troop prices checked separately by verify-0161; all unrelated spell/research/unit/item/terrain data preserved.');
