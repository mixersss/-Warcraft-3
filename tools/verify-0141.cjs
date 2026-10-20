// Compare actual binary objects with the published previous release.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..'),read=n=>JSON.parse(fs.readFileSync(path.join(root,n)));
const U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const previous=new MapFile();previous.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.14.0-alpha.w3x'))),true);require('./historical-wave-settings.cjs')(previous);
function parse(P,name,old=false){const p=new P();p.load(new Uint8Array(old?previous.get(name).bytes():fs.readFileSync(path.join(root,'build/map',name))));return p;}
function index(p){return new Map([...p.originalTable.objects.map(o=>[o.oldId,o]),...p.customTable.objects.map(o=>[o.newId,o])]);}
const a=index(parse(A,'war3map.w3a')),oldA=index(parse(A,'war3map.w3a',true));
const u=index(parse(U,'war3map.w3u')),oldU=index(parse(U,'war3map.w3u',true));
const buffs=index(parse(U,'war3map.w3h'));
const get=(o,k,l=0)=>o.modifications.find(m=>m.id===k&&(m.levelOrVariation||0)===l)?.value;
const close=(actual,expected,label)=>assert(Math.abs(actual-expected)<Math.max(.00001,Math.abs(expected)*.000001),label);
const heroes=read('map/heroes.json'),b=read('map/balance.json');
assert.deepEqual(heroes.find(h=>h.id==='Hpal').skills,['Fhas','AHad','AHds','AHre']);
assert.deepEqual(heroes.find(h=>h.id==='Emoo').skills,['AHfa','AEar','Fmrg','AEsf']);
assert(!heroes.find(h=>h.id==='Hpal').spells.some(s=>s[0]==='AHhb'));
for(const [id,base,buff,oldBuff,field,start,cap]of [['Fhas','AOae','Bhas','BOae','Oae2',.12,.55],['Fmrg','ACnr','Bmrg','Boar','Oar1',3,45]]){
 const skill=a.get(id);assert.equal(skill.oldId,base);assert.equal(get(skill,'aher'),1);
 assert.equal(buffs.get(buff).oldId,oldBuff);assert.equal(get(buffs.get(buff),'fefl'),'');
 let last=-1;
 for(let rank=1;rank<=200;rank++){
  const value=get(skill,field,rank);assert(value>last&&value<=cap+.000001);last=value;
  assert.equal(get(skill,'abuf',rank),buff);assert.equal(get(skill,'aare',rank),900);
  assert(!/organic|enemy|neutral/.test(get(skill,'atar',rank)));
  assert.equal(get(skill,id==='Fhas'?'Oae1':'Oar2',rank),0);
 }
 close(get(skill,field,1),start);close(last,cap);
}
assert(get(a.get('Fmrg'),'atar',1).includes('nonhero'));
assert.notEqual(get(a.get('Fhas'),'abuf',1),get(a.get('AOae'),'abuf',1),'Independent auras');
for(let rank=1;rank<=50;rank++){
 for(const [id,field]of [['AHre','Hre1'],['AUan','Uan1']])assert.equal(get(a.get(id),field,rank),6+rank-1);
 close(get(a.get('AEme'),'Eme5',rank),get(oldA.get('AEme'),'Eme5',rank)*1.2);
 assert.equal(get(a.get('ANtm'),'Ntm1',rank),0);assert.equal(get(a.get('ANtm'),'Ntm4',rank),0);
 for(const id of ['ANrg','ANg1','ANg2','ANg3']){
  if(rank>1)assert(get(a.get(id),'Nrg5',rank)>=get(a.get(id),'Nrg5',rank-1));
  assert(get(a.get(id),'Nrg5',rank)>=get(oldA.get(id),'Nrg5',rank));
  assert(get(a.get(id),'Nrg6',rank)>=get(oldA.get(id),'Nrg6',rank));
 }
 const pad=String(rank).padStart(2,'0');
 close(get(a.get('Fk'+pad),'Eim1',1),get(oldA.get('Fk'+pad),'Eim1',1)*1.25);
 for(const field of ['Tdg1','Tdg3'])close(get(a.get('Ft'+pad),field,1),get(oldA.get('Ft'+pad),field,1)*1.5*b.spell_damage_multiplier);
 assert.equal(get(a.get('Ft'+pad),'Tdg2',1),undefined,'Radius is not damage');
}
for(let rank=1;rank<=200;rank++){
 close(get(a.get('AOmi'),'Omi2',rank),.25+.55*(rank-1)/199);
 close(get(a.get('AOmi'),'Omi3',rank),1.8-.8*(rank-1)/199);
 assert.equal(get(a.get('AOmi'),'Omi1',rank),get(oldA.get('AOmi'),'Omi1',rank));
}
const boosted=new Set(['npn1','npn2','npn3','ncgb','ncg1','ncg2','nfac','nfa1','nfa2']);
for(const [id,old]of oldU){
 const now=u.get(id);assert(now);
 if(boosted.has(old.oldId)){
  const multiplier=old.oldId.startsWith('npn')?1.25:1.15;
  for(const field of ['uhpm','ua1b'])assert(Math.abs(get(now,field)-get(old,field)*multiplier*b[field==='uhpm'?'summon_hp_multiplier':'summon_damage_multiplier'])<=1.00001);
  for(const mod of old.modifications)if(!['uhpm','ua1b'].includes(mod.id))assert.equal(get(now,mod.id),mod.value,'Preserve other summon mechanics');
 }else{
  for(const mod of old.modifications)if(!(id==='futl'&&mod.id==='usei') && !(require('./summon-comparison.cjs').isSummon(old)&&['uhpm','ua1b'].includes(mod.id)) && !(['Hpal','Emoo'].includes(id)&&mod.id==='uhab') && !(/^fp\d{2}$/.test(id)&&['ubpx','ubpy','utub'].includes(mod.id)) && !(/^fpk\d$/.test(id)&&['utra','unam'].includes(mod.id)))assert.equal(get(now,mod.id),mod.value,'Unrequested unit changes: '+id+':'+mod.id);
 }
}
for(const filename of ['war3map.w3q','war3map.w3t','war3map.wpm','war3map.w3e']){
 if(filename==='war3map.w3q'){
  const historical=parse(A,filename,true);
  for(const o of historical.customTable.objects)for(const m of o.modifications)if(m.id==='gub1')m.value=m.value.replace('Предел живой армии 48 сохранён.','Предел живой армии 60 сохранён.');
  const current=parse(A,filename);require('./summon-comparison.cjs').research(current,historical);
  assert.deepEqual(current,historical,'Only requested army prices and army-cap tooltip may change');
 }else if(filename==='war3map.w3t')require('./simple-comparison.cjs').same(fs.readFileSync(path.join(root,'build/map',filename)),previous.get(filename).bytes(),filename);else assert.deepEqual(fs.readFileSync(path.join(root,'build/map',filename)),Buffer.from(previous.get(filename).bytes()),'Preserve research/economy/terrain');
}
assert.equal(b.transmute_gold_base,100);assert.equal(b.transmute_gold_step,30);
const report=read('build/verification-014.json');Object.assign(report,{heroBalancePatch:'0.14.1',armyPassives:2,resurrectionCount:[6,55],mirrorDamage:[.25,.8],mirrorDamageTaken:[1.8,1],metamorphHPFactor:1.2,pandaPowerFactor:1.25,tornadoDamageFactor:1.5,factoryPowerFactor:1.15,roboMinimumCurveStep:2,transmuteGold:[100,1570],nativeTransmuteBounty:false,enginePlaytest:false});
fs.writeFileSync(path.join(root,'build/verification-0141.json'),JSON.stringify(report,null,2)+'\n');
console.log('PASS: 0.14.1 two isolated army auras, 50 corpse-count ranks, 200 useful clone ranks, upgraded forms/factory/spirits/tornado, fixed Transmute data and preserved army/economy/terrain.');
