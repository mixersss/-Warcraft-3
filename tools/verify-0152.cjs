// Inspect the emitted objects against the last published map, not the Python generator.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
const W3Map=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default,U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const historical=new W3Map();historical.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.15.1-alpha.w3x'))),true);require('./historical-wave-settings.cjs')(historical);
const read=(name,old=false)=>new Uint8Array(old?historical.get(name).bytes():fs.readFileSync(path.join(root,'build/map',name)));
function parse(P,name,old=false){const p=new P();p.load(read(name,old));return p;}
const abilities=parse(A,'war3map.w3a'),previousAbilities=parse(A,'war3map.w3a',true);
const units=parse(U,'war3map.w3u'),previousUnits=parse(U,'war3map.w3u',true);
const index=p=>new Map([...p.originalTable.objects.map(o=>[o.oldId,o]),...p.customTable.objects.map(o=>[o.newId,o])]);
const a=index(abilities),oldA=index(previousAbilities),u=index(units),oldU=index(previousUnits);
const get=(o,id,rank=0)=>o.modifications.find(m=>m.id===id&&(m.levelOrVariation||0)===rank)?.value;
const balance=require('../map/balance.json');
let lastHP=0,lastDamage=0;const samples=[];
for(let rank=1;rank<=200;rank++){
 const raw=get(a.get('AHwe'),'Hwe1',rank),oldRaw=get(oldA.get('AHwe'),'Hwe1',rank);assert.equal(raw,oldRaw);
 const now=u.get(raw),old=oldU.get(raw),hp=get(now,'uhpm'),damage=get(now,'ua1b');
 assert(hp>lastHP&&damage>=lastDamage,'No reversal or sharp drop at a rank transition');
 assert(hp<=get(old,'uhpm')&&damage<=get(old,'ua1b'),'Never buff water summons above their former curve');
 if(rank>1&&rank<200)assert(hp<get(old,'uhpm')&&damage<get(old,'ua1b'));
 if(rank===1||rank===200){assert(Math.abs(hp-get(old,'uhpm')*.85)<=.5);assert(Math.abs(damage-get(old,'ua1b')*.85)<=.5);}
 assert.equal(get(now,'udef'),get(old,'udef'));assert.equal(get(now,'upgr'),'');
 assert.equal(get(a.get('AHwe'),'Hwe2',rank),1+Math.floor(rank/10));
 assert.equal(get(a.get('AHwe'),'adur',rank),60);
 for(const id of ['AHwe','F090']){
  assert.equal(get(a.get(id),'Hwe1',rank),raw,'Human/bot/custom hero share the same rank-specific unit');
  const tooltip=get(a.get(id),'aub1',rank);assert(tooltip.includes(hp+' HP')&&tooltip.includes('урон '+damage+';'),'Tooltips show the emitted summon stats');
 }
 if([1,3,10,13,50,100,200].includes(rank))samples.push({rank,hp,baseDamage:damage,armor:get(now,'udef'),count:get(a.get('AHwe'),'Hwe2',rank)});
 if(rank===13){assert.equal(hp,1376);assert.equal(damage,59);assert.equal(get(a.get('AHwe'),'Hwe2',rank),2);assert(hp/get(old,'uhpm')<.5&&damage/get(old,'ua1b')<.5);}
 lastHP=hp;lastDamage=damage;
}
// Every real generated summon, including secondary spirits and phoenix eggs, gets the same reduction.
let summonUnitsChecked=0;const bases=new Set();
for(const now of units.customTable.objects){
 if(!require('./summon-comparison.cjs').isSummon(now))continue;
 const old=oldU.get(now.newId);assert(old);bases.add(now.oldId);summonUnitsChecked++;
 for(const field of ['uhpm','ua1b']){
  const actual=get(now,field),before=get(old,field);
  assert(actual<=before,'No summoned unit may gain HP/damage');
  if(!['hwat','hwt2','hwt3'].includes(now.oldId))assert(Math.abs(actual-before*.85)<=.50001,now.newId+':'+field+' exact global reduction with integer rounding');
 }
}
assert(summonUnitsChecked>1000&&bases.has('hpxe')&&bases.has('even')&&bases.has('ninf')&&bases.has('nfac'),'Nested summons and ultimates must not bypass the global multiplier');
const refs=new Set('Hwe1 Osf1 Efnu Esvu Nbau Ndou Nef1 Nsy2 Nsyu Rai3 Uin4 Ntou Ulsu'.split(' '));
for(const skill of a.values())for(const m of skill.modifications){
 if(!refs.has(m.id))continue;
 const pet=u.get(m.value.split(',')[0]),tip=get(skill,'aub1',m.levelOrVariation);
 if(pet&&tip&&tip.includes('Призыв:'))assert(tip.includes(get(pet,'uhpm')+' HP')&&tip.includes('урон '+get(pet,'ua1b')+';'),'Every summon tooltip reflects the new combat data');
}
// All offensive magnitudes are 70%; utility fields must not enter the whitelist.
const seeds=require('../map/ability-seeds.json');let damageFieldsChecked=0;
for(const [id,fields]of Object.entries(balance.spell_damage_fields))for(const field of fields){
 const meta=seeds[id].fields.find(f=>f.id===field);assert(meta,'Known native field');
 assert(!/delay|radius|factor|reduction|targets|speed|duration|count/i.test(meta.label),'Never treat utility as damage');
 assert(!/interval/i.test(meta.label)||meta.label==='Damage per Interval');
}
for(const skill of a.values()){
 const before=oldA.get(skill.newId==='\0\0\0\0'?skill.oldId:skill.newId);if(!before)continue;
 for(const m of skill.modifications)if(balance.spell_damage_fields[skill.oldId]?.includes(m.id)||(/^Ft[0-9]{2}$/.test(skill.newId)&&['Tdg1','Tdg3'].includes(m.id))){
  const expected=get(before,m.id,m.levelOrVariation)*(balance.spell_damage_overrides?.[skill.oldId]??.7);
  assert(Math.abs(m.value-expected)<=Math.max(.0001,Math.abs(expected)*1e-6),skill.oldId+':'+m.id+' damage -30%');damageFieldsChecked++;
 }
}
const runtime=Buffer.from(read('war3map.j')).toString();
const hybridPowers=new Map([...runtime.matchAll(/set HybridPower\[(\d+)\] = ([\d.]+)/g)].map(m=>[+m[1],+m[2]]));
for(const [kind,id,field]of [[0,'AHhb','Hhb1'],[1,'AUdc','Udc1'],[2,'AEmb','Emb1']])for(let rank=1;rank<=200;rank++){
 assert.equal(get(a.get(id),field,rank),0,'No second native damage/heal application');
 assert.equal(Math.fround(hybridPowers.get(kind*200+rank-1)),get(oldA.get(id),field,rank),'Preserve original heal and mana burn magnitudes independently');
}
const q=parse(A,'war3map.w3q'),oldQ=parse(A,'war3map.w3q',true),qi=index(q),oldQi=index(oldQ);
for(const [base,advanced,cost,step,oldCost,oldStep]of [['Rfat','Rfa2',84,63,224,168],['Rfar','Rfr2',84,63,224,168],['Rfhp','Rfh2',151,101,403,269]])for(let total=0;total<200;total++){
 const id=total<10?base:advanced,offset=total<10?0:10,factor=1;
 const actual=get(qi.get(id),'gglb')+(total-offset)*get(qi.get(id),'gglm'),expected=(cost+total*step)*factor;
 assert.equal(actual,expected);assert(Math.abs(actual/((oldCost+total*oldStep)*factor)-.375)<.0011,'All ranks retain the cumulative price cuts; no advanced surcharge');
 const tip=get(qi.get(id),'gub1',total-offset+1);assert(tip.includes('Цена: '+actual+' золота.'),'Command-card tooltip and native price agree');assert.equal(tip,get(oldQi.get(id),'gub1',total-offset+1).replace(/Цена: \d+ золота\./,'Цена: '+actual+' золота.').replace(' Продвинутое исследование: цена ×4 после 10-го уровня.','').replace('+3 к атаке','+4 к атаке').replace('+1 к броне','+1.5 к броне').replace('+6.66667% базового','+10% базового'),'Only the authorized price and effect portions of the research tooltip may change');
}
assert.deepEqual(require('./summon-comparison.cjs').research(q,oldQ),oldQ,'Building/wave research, effects and unlocks stay exactly unchanged');
// Restore only the authorized fields, then require complete object equality.
const restore=require('./summon-comparison.cjs');
assert.deepEqual(restore(units,previousUnits,true),previousUnits,'Every unrelated unit/stat/reference remains identical');
assert.deepEqual(restore(abilities,previousAbilities),previousAbilities,'All non-damage utility spell fields remain identical');
for(const name of ['war3map.w3h','war3map.w3t','war3map.w3b','war3map.w3e','war3map.wpm','war3mapMisc.txt','war3map.doo','war3mapUnits.doo','war3map.w3r','war3map.w3c','war3map.w3s','war3map.imp','war3map.shd','war3mapMap.tga','war3mapPreview.tga'])assert.deepEqual(Buffer.from(read(name)),Buffer.from(read(name,true)),name+' must remain byte-identical');
// Only new hybrid handler, its registration/data, six cost constants and quest/version text may differ.
const canonical=s=>s.split('\n').map(l=>l.trim()).filter(Boolean).join('\n');
const stripped=require('./roster-comparison.cjs').runtime(runtime,Buffer.from(read('war3map.j',true)).toString()).replace(/function HybridSpellKind[\s\S]*?(?=function OnTransmute)/,'')
 .replace(/^\s*(?:constant real SPELL_DAMAGE_MULTIPLIER|real array HybridPower|set HybridPower\[).*$/gm,'')
 .replace(/^.*TriggerAddAction\(TransmuteTrigger, function OnHybridSpell\).*$/gm,'');
let expectedRuntime=Buffer.from(read('war3map.j',true)).toString().replaceAll('0.15.1-alpha',balance.version)
 .replace('return TroopResearchCost(HEALTH_COST,HEALTH_COST_STEP,Vitality[p])','return HEALTH_COST+Vitality[p]*HEALTH_COST_STEP')
 .replace('From rank 11 the normal next-rank price is multiplied by four.','Attack, armor and troop HP keep their normal linear prices at all ranks; no rank-11 surcharge.')
 .replace('prices are 20% lower than 0.13.2','attack/armor/HP prices are 50% lower than 0.16.0');
for(const [name,before,after]of [['ATTACK_COST',224,84],['ATTACK_COST_STEP',168,63],['ARMOR_COST',224,84],['ARMOR_COST_STEP',168,63],['HEALTH_COST',403,151],['HEALTH_COST_STEP',269,101],['ADVANCED_RESEARCH_COST_MULTIPLIER',4,1]])expectedRuntime=expectedRuntime.replace('constant integer '+name+' = '+before,'constant integer '+name+' = '+after);
assert.equal(canonical(require('./research-effects-comparison.cjs')(stripped)),canonical(expectedRuntime),'Existing AI/economy/gameplay logic preserved');
const file=`FourFrontsFrenzy-${balance.version}.w3x`;
fs.writeFileSync(path.join(root,'build/verification-0152.json'),JSON.stringify({filename:file,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'build',file))).digest('hex'),waterRanksChecked:200,spellDamageMultiplier:.7,damageFieldsChecked,hybridRanksPreserveHealingAndManaBurn:600,troopLinearPriceFactorVs0151Approx:.375,troopResearchRanksChecked:600,buildingAndWaveCostsUnchanged:true,summonHPMultiplier:.85,summonDamageMultiplier:.85,summonUnitsChecked,summonBaseTypes:bases.size,waterFirstAndFinalRanksOnlyGlobalReduction:true,unrelatedUnitsAndSpellsPreserved:true,customCopy:'F090',summonCountsLifetimeCooldownArmorScaleUnchanged:true,botAndHumanSameUnits:true,unchangedRuntimeFrom:'0.15.1-alpha',samples,enginePlaytest:false},null,2)+'\n');
console.log('PASS: all real summoned unit HP/damage -15%, 200 deferred water ranks, preserved every count/lifetime/cooldown/armor/scale; custom copy synchronized, spell damage -30% with intact utility, 600 reduced research ranks, unchanged buildings/waves and existing gameplay logic.');
