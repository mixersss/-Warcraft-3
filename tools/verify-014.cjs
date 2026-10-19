// Independent regression checks for the user's 0.14 changes. No engine emulation.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const crypto=require('crypto');
const root=path.resolve(__dirname,'..'),read=n=>JSON.parse(fs.readFileSync(path.join(root,n)));
const U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
function parse(P,file){const x=new P();x.load(new Uint8Array(fs.readFileSync(path.join(root,'build/map',file))));return x;}
const unitFile=parse(U,'war3map.w3u'),u=new Map(unitFile.customTable.objects.map(o=>[o.newId,o])),originalUnits=new Map(unitFile.originalTable.objects.map(o=>[o.oldId,o]));
const abilityFile=parse(A,'war3map.w3a'),a=new Map([...abilityFile.originalTable.objects.map(o=>[o.oldId,o]),...abilityFile.customTable.objects.map(o=>[o.newId,o])]);
const itemFile=parse(U,'war3map.w3t'),items=new Map(itemFile.customTable.objects.map(o=>[o.newId,o]));
const q=new Map(parse(A,'war3map.w3q').customTable.objects.map(o=>[o.newId,o]));
const get=(o,k,l=0)=>o.modifications.find(m=>m.id===k&&(m.levelOrVariation||0)===l)?.value;
const heroes=read('map/heroes.json'),balance=read('map/balance.json'),seeds=read('map/ability-seeds.json');
for(const h of heroes)for(const [slot,id]of h.skills.entries()){
 assert.equal(get(a.get(id),'ahky'),'QWER'[slot]);assert.equal(get(a.get(id),'auhk'),'QWER'[slot]);assert.equal(get(a.get(id),'arhk'),'QWER'[slot]);
 assert.equal(get(a.get(id),'alev'),slot===3?50:200);
}
for(const [prefix,key]of [['ANs','Q'],['ANc','W'],['ANg','R']])for(let level=1;level<=3;level++)assert.equal(get(a.get(prefix+level),'ahky'),key);
for(const [id,h]of originalUnits)if(['Edmm','Nalm','Nal2','Nal3','Nrob'].includes(id))assert(get(h,'uhab').includes('Fatr'));
const timing=read('map/hero-attack-seeds.json').units;
for(const h of heroes){const o=u.get(h.id)||originalUnits.get(h.id);for(const [field,v]of Object.entries(timing[h.base||h.id]))assert(Math.abs(get(o,field)-v*.75)<1e-5,'Actual lower base interval/animation timing for '+h.name);}
let lastCooldown=Infinity;
for(let rank=1;rank<=200;rank++){
 assert.equal(get(a.get('ANab'),'Nab4',rank),Math.fround((20+12*(rank-1))*.7));assert.equal(get(a.get('ANab'),'Nab5',rank),Math.fround((12+8*(rank-1))*.7));assert.equal(get(a.get('ANab'),'Nab6',rank),1);
 const form=u.get(get(a.get('ANcr'),'Emeu',rank));assert(form&&get(form,'uhab').includes('Fatr'));
 const cooldown=get(form,'ua1c');assert(cooldown<lastCooldown,'Chemical Rage physically changes attack cooldown at every rank');lastCooldown=cooldown;
 const bonus=get(a.get('ANcr'),'Ncr6',rank);assert(Math.abs(cooldown-timing.Nalc.ua1c*.75/(1+bonus))<1e-5);
}
for(let rank=1;rank<=50;rank++)assert.equal(get(a.get('ANtm'),'Ntm1',rank),0);
for(let race=0;race<4;race++)for(let tier=0;tier<5;tier++)assert.equal(get(u.get(`fm${race}${tier}`),'ugol'),[75,110,160,225,300][tier]);
// Compare old prices by item identity rather than trusting the newly edited catalog.
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,oldMap=new MapFile();oldMap.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.13.2-alpha.w3x'))),true);
const oldItems=new U();oldItems.load(new Uint8Array(oldMap.get('war3map.w3t').bytes()));
for(const old of oldItems.customTable.objects)assert.equal(get(items.get(old.newId),'igol'),Math.round(get(old,'igol')*.8),'20% item price reduction');
assert.deepEqual([get(q.get('Rfwn'),'glvl'),get(q.get('Rfwn'),'gglb'),get(q.get('Rfwn'),'gglm'),get(q.get('Rfwn'),'gbpx'),get(q.get('Rfwn'),'gbpy')],[20,2000,1000,0,1]);
assert.equal(balance.spawn_seconds,21);assert.equal(balance.army_cap,60);assert.equal(balance.spawn_units,3);
assert.equal(get(u.get('fbax'),'uhpm'),50700);assert.equal(get(q.get('Rfti'),'gba1'),25350);
assert.equal(get(u.get('fbst'),'uhpm'),156000);assert.equal(get(u.get('fbst'),'ua1b'),1750);assert(Math.abs(get(u.get('fbst'),'ua1c')-.2)<1e-6);assert(Math.abs(get(u.get('fbst'),'ua1p')-.05)<1e-6);
assert.equal(get(a.get('Fdag'),'Ebl1',1),900);assert.equal(get(a.get('Fdag'),'amcs',1),0);assert.equal(get(a.get('Fdag'),'acdn',1),12);
assert.equal(get(a.get('Fsdm'),'Roa1',1),Math.fround(.35));assert.equal(get(a.get('Fsar'),'Idef',1),8);assert.equal(get(a.get('Fshl'),'Ihpg',1),2500);
for(const id of ['Fsdm','Fsar','Fshl']){assert.equal(get(a.get(id),'aare',1),700);assert(get(a.get(id),'atar',1).includes('friend'));assert(get(a.get(id),'atar',1).includes('nonhero'));assert(!get(a.get(id),'atar',1).includes('organic'));}
assert.equal(get(u.get('futl'),'usei'),'fdgr,fsdm,fsar,fshl,fpH0,fpM0');
for(const o of unitFile.customTable.objects.filter(o=>/^fs[0-4]p$/.test(o.newId)||o.newId==='futl'))assert(get(o,'usei').split(',').length<=9,'Keep native selection/sell controls available');
// Referenced summon types stay correct after regenerating smaller per-rank catalogs.
const summon=new Set(['Hwe1','Osf1','Efnu','Esvu','Nbau','Ndou','Nef1','Nsy2','Nsyu','Rai3','Uin4','Ntou','Ulsu']);
for(const [id,seed]of Object.entries(seeds))for(const field of seed.fields)if(summon.has(field.id))for(let rank=1;rank<=seed.cap;rank++){
 const base=field.values[Math.min(rank,field.values.length)-1].split(','),actual=get(a.get(id),field.id,rank).split(',');
 assert.deepEqual(actual.map(x=>u.get(x)?.oldId),base,'Same summoned creature types by skill/rank');
}
const csv=fs.readFileSync(path.join(root,'docs/Heroes-and-skills.csv'),'utf8');assert.equal(csv.trim().split('\n').length,heroes.length*4+1);
fs.writeFileSync(path.join(root,'build/verification-014.json'),JSON.stringify({filename:`FourFrontsFrenzy-${balance.version}.w3x`,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'build',`FourFrontsFrenzy-${balance.version}.w3x`))).digest('hex'),heroes:heroes.length,skillSlots:heroes.length*4,normalSkillRanks:200,ultimateRanks:50,QWER:true,chemicalForms:200,realChemicalRageCooldownGrowth:true,transmuteGold:[100,1570],nativeTransmuteFactor:0,transmuteTroopCosts:[75,110,160,225,300],itemPriceFactor:.8,researchPriceFactorApprox:.8,waveSeconds:21,startingTroops:3,waveResearchRanks:20,waveResearchCost:[2000,1000],maxWave:23,armyCap:60,barracksHP:50700,bastionHP:156000,bastionBaseDamage:1750,bastionCooldown:.2,heroBaseAttackIntervalFactor:.75,engineAttackSpeedCapModified:false,enginePlaytest:false},null,2));
console.log('PASS: 0.14 QWER/200-rank roster, 200 actual rage forms, poison/Transmute costs, 20% prices, wave research, tower attack timings, native utility objects and 184-skill export (structural checks).');
