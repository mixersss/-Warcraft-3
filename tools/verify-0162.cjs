// Verify the emitted native effect curves against the published 0.16.1 release.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const canonical=s=>s.split('\n').map(l=>l.trim()).filter(Boolean).join('\n');
const root=path.resolve(__dirname,'..'),balance=require('../map/balance.json');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const Parser=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const old=new MapFile();old.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.16.1-alpha.w3x'))),true);
const bytes=(name,prior=false)=>prior?Buffer.from(old.get(name).bytes()):fs.readFileSync(path.join(root,'build/map',name));
function parse(prior=false){const p=new Parser();p.load(new Uint8Array(bytes('war3map.w3q',prior)));return p;}
const current=parse(),previous=parse(true),index=p=>new Map(p.customTable.objects.map(o=>[o.newId,o]));
const now=index(current),before=index(previous),get=(o,id)=>o.modifications.find(m=>m.id===id&&m.levelOrVariation===0)?.value;
const key=m=>m.id+':'+m.levelOrVariation+':'+m.dataPointer;
let ranks=0,effectFields=0,tooltips=0;
for(const [base,advanced,effect,amount,oldText,newText]of [
 ['Rfat','Rfa2','ratx',4,'+3 к атаке','+4 к атаке'],
 ['Rfar','Rfr2','rarm',1.5,'+1 к броне','+1.5 к броне'],
 ['Rfhp','Rfh2','rhpo',.1,'+6.66667% базового','+10% базового']]){
 for(let rank=1;rank<=200;rank++){
  let total=0,prior=0;
  for(const [id,n] of [[base,Math.min(rank,10)],[advanced,Math.max(0,rank-10)]])if(n){
   const o=now.get(id),oldO=before.get(id);assert.equal(get(o,'gef1'),effect);
   total+=get(o,'gba1')+get(o,'gmo1')*(n-1);
   prior+=get(oldO,'gba1')+get(oldO,'gmo1')*(n-1);
  }
  assert(Math.abs(total-amount*rank)<1e-5,'Exact intended cumulative effect at every rank');
  assert(Math.abs(total-prior*(amount/(base==='Rfat'?3:base==='Rfar'?1:.06666666666666667)))<1e-5,'Requested effect relative to previous combined native stages');ranks++;
 }
 for(const id of [base,advanced]){
  const o=now.get(id),ref=before.get(id),mods=new Map(ref.modifications.map(m=>[key(m),m]));
  for(const m of o.modifications){const prior=mods.get(key(m));assert(prior);
   if(['gba1','gmo1'].includes(m.id)){
    assert(Math.abs(m.value-prior.value*(amount/(base==='Rfat'?3:base==='Rfar'?1:.06666666666666667)))<1e-7);assert(Math.abs(m.value-amount)<1e-7);m.value=prior.value;effectFields++;
   }else if(m.id==='gub1'){
    assert(prior.value.includes(oldText));assert.equal(m.value,prior.value.replace(oldText,newText));m.value=prior.value;tooltips++;
   }
  }
 }
}
assert.equal(ranks,600);assert.equal(effectFields,12);assert.equal(tooltips,600);
assert.deepEqual(current,previous,'All prices, native prerequisites, research timing, building and wave effects remain identical');
for(const name of ['war3map.w3a','war3map.w3u','war3map.w3t','war3map.w3h','war3map.w3e','war3map.wpm','war3mapMisc.txt','war3map.doo','war3mapUnits.doo','war3map.w3b','war3map.imp','war3mapMap.tga','war3mapPreview.tga']){if(['war3map.w3a','war3map.w3u'].includes(name))require('./creative-comparison.cjs').sameObjects(bytes(name),bytes(name,true),name);else assert.deepEqual(bytes(name),bytes(name,true),name+' byte-identical');}
const runtime=bytes('war3map.j').toString();
for(const text of ['Атака армии +4','Броня армии +1,5','Здоровье армии +10%','Attack research adds 4 damage and armor adds 1.5 per rank. HP research adds 10% of base HP per rank.'])assert(runtime.includes(text));
assert.equal(canonical(require('./research-effects-comparison.cjs')(require('./creative-comparison.cjs').runtime(runtime,bytes('war3map.j',true).toString())).replaceAll(balance.version,'0.16.1-alpha')),canonical(bytes('war3map.j',true).toString()),'Runtime unchanged except version and four explanatory strings');
fs.writeFileSync(path.join(root,'build/verification-0162.json'),JSON.stringify({version:balance.version,checkedRanks:ranks,attackPerRank:4,armorPerRank:1.5,baseHPFractionPerRank:.1,changedEffectFields:effectFields,updatedTooltips:tooltips,allPricesUnchanged:true,allOtherObjectFieldsUnchanged:true,runtimeUnchangedExceptVersionAndText:true,enginePlaytest:false},null,2)+'\n');
console.log('PASS: all 600 native troop-effect ranks +4 damage/+1.5 armor/+10% base HP; 600 tooltips agree, prices and every unrelated field/runtime remain unchanged from 0.16.1.');
