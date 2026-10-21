const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),b=require('../map/balance.json'),heroes=require('../map/heroes.json');
const M=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const old=new M();old.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.20.0-alpha.w3x'))),true);
const now=n=>fs.readFileSync(path.join(root,'build/map',n)),before=n=>Buffer.from(old.get(n).bytes());
const parse=(P,n,prior=false)=>{const p=new P();p.load(new Uint8Array(prior?before(n):now(n)));return p;};
const get=(o,id,r=0)=>o.modifications.find(m=>m.id===id&&(m.levelOrVariation||0)===r)?.value;
const a=parse(A,'war3map.w3a'),u=parse(U,'war3map.w3u'),original=a.originalTable.objects.find(o=>o.oldId==='AEfn'),summon=a.customTable.objects.find(o=>o.newId==='Fent');
assert.equal(summon.oldId,'AHwe','Native immediate summon does not target trees');assert.equal(get(summon,'alev'),200);assert.equal(get(summon,'aher'),1);assert.equal(get(summon,'ahky'),'E');assert.equal(get(summon,'arhk'),'E');assert.equal(get(summon,'abpx'),2);assert.equal(get(summon,'abpy'),2);assert.equal(get(summon,'arlv'),1);assert.equal(get(summon,'alsk'),1);
const units=new Map(u.customTable.objects.map(o=>[o.newId,o]));
for(let rank=1;rank<=200;rank++){
 assert.equal(get(summon,'Hwe1',rank),get(original,'Efnu',rank));assert.equal(get(summon,'Hwe2',rank),get(original,'Efn1',rank));
 assert.equal(units.get(get(summon,'Hwe1',rank)).oldId,'efon');assert.equal(get(summon,'atar',rank),undefined);
 for(const f of ['acdn','amcs','adur','ahdu','acas','aare','aran','abuf'])assert.equal(get(summon,f,rank),get(original,f,rank),f+' retains original curve');
 assert(get(summon,'aub1',rank).includes('без деревьев'));
}
const keeper=heroes.find(h=>h.id==='Ekee');assert.equal(keeper.skills[2],'Fent');assert.deepEqual(keeper.spells[2],['Fent','waterelemental',0]);
assert.equal(get(u.originalTable.objects.find(o=>o.oldId==='Ekee'),'uhab'),'AEer,AEah,Fent,AEtq,Fatr');
for(const[P,n]of[[U,'war3map.w3u'],[A,'war3map.w3a']]){const current=parse(P,n),previous=parse(P,n,true);require('./army-orders-comparison.cjs').objects(current);require('./treant-comparison.cjs').objects(current);assert.deepEqual(current,previous,n+' exact0.20 except one skill and Keeper learnable list');}
for(const n of ['war3map.w3q','war3map.w3t','war3map.w3h','war3map.w3b','war3map.wpm','war3map.w3e','war3mapMisc.txt','war3map.doo','war3mapUnits.doo','war3map.imp','war3mapMap.tga','war3mapPreview.tga'])assert.deepEqual(now(n),before(n),n+' unchanged');
assert.equal(require('./treant-comparison.cjs').runtime(require('./army-orders-comparison.cjs').runtime(now('war3map.j').toString(),before('war3map.j').toString())).replaceAll(b.version,'0.20.0-alpha'),before('war3map.j').toString(),'Only native skill/AI bindings change at runtime');
fs.writeFileSync(path.join(root,'build/verification-0201.json'),JSON.stringify({version:b.version,keeperSkill:'Fent',nativeBase:'AHwe',requiresTrees:false,hotkey:'E',ranks:200,allOriginalTreantUnitsCountsDurationsManaCooldownsPreserved:true,botOrder:'waterelemental',allOther020ContentUnchanged:true,enginePlaytest:false},null,2)+'\n');
console.log('PASS:200 native tree-free Keeper summon ranks, exact old treant/count/lifetime/cost curves, human E and bot immediate order; every other0.20 field/runtime preserved.');
