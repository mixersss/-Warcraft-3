// Independent release comparison: prices only, all 600 ranks and untouched mechanics.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),balance=require('../map/balance.json');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const Parser=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const old=new MapFile();old.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.16.0-alpha.w3x'))),true);
const bytes=(name,prior=false)=>prior?Buffer.from(old.get(name).bytes()):fs.readFileSync(path.join(root,'build/map',name));
function parse(prior=false){const p=new Parser();p.load(new Uint8Array(bytes('war3map.w3q',prior)));return p;}
const current=parse(),previous=parse(true),get=(o,id,rank=0)=>o.modifications.find(m=>m.id===id&&m.levelOrVariation===rank)?.value;
const byId=p=>new Map(p.customTable.objects.map(o=>[o.newId,o]));const now=byId(current),before=byId(previous);
const samples=[];
for(const [base,advanced,cost,step] of [['Rfat','Rfa2',84,63],['Rfar','Rfr2',84,63],['Rfhp','Rfh2',151,101]]){
 let last=0;
 for(let total=0;total<200;total++){
  const id=total<10?base:advanced,local=total<10?total:total-10;
  const actual=get(now.get(id),'gglb')+local*get(now.get(id),'gglm');
  const oldPrice=get(before.get(id),'gglb')+local*get(before.get(id),'gglm');
  assert.equal(actual,cost+total*step);
  assert.equal(actual,oldPrice/(total>=10&&base!=='Rfhp'?8:2),'Half price, plus removal of former attack/armor x4 surcharge');
  if(total)assert.equal(actual-last,step,'No price cliff at rank 11 or elsewhere');
  const tip=get(now.get(id),'gub1',local+1);assert(tip.includes('Цена: '+actual+' золота.'));assert(!tip.includes('×4'));
  if([0,9,10,199].includes(total))samples.push({research:base,rank:total+1,price:actual});
  last=actual;
 }
}
assert.deepEqual(require('./summon-comparison.cjs').research(current,previous),previous,'Prerequisites, building/wave prices and unrelated research data preserved; effect values checked separately by verify-0162');
for(const name of ['war3map.w3a','war3map.w3u','war3map.w3t','war3map.w3h','war3map.w3e','war3map.wpm','war3mapMisc.txt','war3map.doo','war3mapUnits.doo','war3map.imp'])assert.deepEqual(bytes(name),bytes(name,true),name+' byte-identical to 0.16.0');
let runtime=require('./research-effects-comparison.cjs')(bytes('war3map.j').toString()).replaceAll(balance.version,'0.16.0-alpha');
for(const [key,after,prior]of [['ATTACK_COST',84,168],['ATTACK_COST_STEP',63,126],['ARMOR_COST',84,168],['ARMOR_COST_STEP',63,126],['HEALTH_COST',151,302],['HEALTH_COST_STEP',101,202],['ADVANCED_RESEARCH_COST_MULTIPLIER',1,4]])runtime=runtime.replace('constant integer '+key+' = '+after+'\n','constant integer '+key+' = '+prior+'\n');
runtime=runtime.replace('attack/armor/HP prices are 50% lower than 0.16.0','attack/armor/HP prices are a further 25% lower than 0.15.1').replace('Attack, armor and troop HP keep their normal linear prices at all ranks; no rank-11 surcharge.','From rank 11 attack and armor prices are multiplied by four; troop HP keeps its normal linear price.');
assert.equal(runtime,bytes('war3map.j',true).toString(),'Every other runtime function, bot budget, income and wave setting remains unchanged');
fs.writeFileSync(path.join(root,'build/verification-0161.json'),JSON.stringify({version:balance.version,checkedResearchRanks:600,allAdvancedSurchargesRemoved:true,ordinaryPriceMultiplier:.5,buildingWavePricesUnchanged:true,heroesSpellsTroopsItemsTerrainByteIdentical:true,runtimeIdenticalExceptResearchText:true,samples,enginePlaytest:false},null,2)+'\n');
console.log('PASS: all 600 attack/armor/HP ranks half price, no advanced surcharge, uniform increments; 0.16.0 content preserved outside research prices/effects and explanatory text.');
