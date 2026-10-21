// Validate new content independently; retain every pre-replacement hero/economy field.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),heroes=require('../map/heroes.json'),balance=require('../map/balance.json'),pets=require('../map/simple-pets.json');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const old=new MapFile();old.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.17.1-alpha.w3x'))),true);
require('./historical-wave-settings.cjs')(old);
const bytes=(n,prior=false)=>prior?Buffer.from(old.get(n).bytes()):fs.readFileSync(path.join(root,'build/map',n));
function parse(P,n,prior=false){const p=new P();p.load(new Uint8Array(bytes(n,prior)));return p;}
const units=parse(U,'war3map.w3u'),abilities=parse(A,'war3map.w3a'),items=parse(U,'war3map.w3t');
const index=p=>new Map(p.customTable.objects.map(o=>[o.newId,o])),u=index(units),a=index(abilities),i=index(items);
const get=(o,id,rank=0)=>o.modifications.find(m=>m.id===id&&(m.levelOrVariation||0)===rank)?.value;
assert.equal(heroes.length,50);assert.equal(heroes.filter(h=>h.simple).length,4);
const removed=new Set(['Fy00','Fy01','Fy02',...Array.from({length:12},(_,k)=>'Y'+String(k).padStart(3,'0')),'fp46','fp47','fp48']);
for(const id of ['Fy00','Fy01','Fy02'])assert(!u.has(id)&&!heroes.some(h=>h.id===id));
for(let k=0;k<12;k++)assert(!a.has('Y'+String(k).padStart(3,'0')));
let skillRanks=0,petRanks=0;
for(const h of heroes.filter(h=>h.simple)){
 assert.equal(get(u.get(h.id),'upra'),['STR','AGI','INT'][h.primary]);assert.equal(get(u.get(h.id),'umdl'),h.model);
 assert.equal(get(u.get(h.id),'uhab'),[...h.skills,'Fatr'].join(','));assert.equal(get(u.get(h.id),'usnd'),h.soundset);
 for(const [slot,s]of h.simple.entries()){
  const raw=h.skills[slot],ability=a.get(raw),cap=slot===3?50:200;
  assert.equal(ability.oldId,s.base);assert.equal(get(ability,'alev'),cap);assert.equal(get(ability,'ahky'),'QWER'[slot]);assert.equal(get(ability,'abpx'),slot);
  assert.equal(get(ability,'arlv'),slot===3?6:1);assert.equal(get(ability,'alsk'),slot===3?10:1);
  for(let rank=1;rank<=cap;rank++){assert(get(ability,'aub1',rank).includes(s.description));assert.equal(get(ability,'amcs',rank),s.mana);assert.equal(get(ability,'acdn',rank),s.cooldown);skillRanks++;}
 }
}
for(let family=0;family<3;family++)for(let rank=1;rank<=(family===2?50:200);rank++){
 const id='k'+family+(rank-1).toString(16).padStart(2,'0'),unit=u.get(id),row=pets[family];assert(unit);
 const extra=(rank-1)*299/199;
 const round=x=>{const n=Math.floor(x);return x-n===.5?n+n%2:Math.round(x);};
 assert.equal(get(unit,'uhpm'),Math.max(1,round(round(row.hp*(1+.15*extra))*balance.summon_hp_multiplier)));
 assert.equal(get(unit,'ua1b'),round(round(row.damage*(1+.12*extra)+extra)*balance.summon_damage_multiplier));
 assert.equal(get(unit,'udef'),round(row.armor+.2*extra));
 assert(Math.abs(get(unit,'usca')-row.scale*balance.summon_model_scale*(1+.0005*extra))<1e-6);assert.equal(get(unit,'umvt'),'foot');assert.equal(get(unit,'ua1r'),row.range);assert.equal(get(unit,'upgr'),'');assert.equal(get(unit,'ubba'),0);assert.equal(get(unit,'ubdi'),0);petRanks++;
}
assert.equal(skillRanks,2600);assert.equal(petRanks,450);
assert.equal(a.get('Clif').oldId,'AIva');
for(let rank=1;rank<=200;rank++){assert(Math.abs(get(a.get('Clif'),'Ivam',rank)-.002*rank)<1e-7);assert(!/organic|melee/.test(get(a.get('Clif'),'atar',rank)));}
assert.equal(get(a.get('V008'),'Uav1',1),0,'No melee-only native aura on top of distributed lifesteal');
assert.equal(get(a.get('V005'),'atar',200),'self');assert(Math.abs(get(a.get('V005'),'Oae2',200)-.65)<1e-6);
assert(Math.abs(get(a.get('V012'),'nca1',200)-.75)<1e-6);assert(Math.abs(get(a.get('V014'),'Eev1',200)-.45)<1e-6);
assert.equal(get(u.get('Fz01'),'ustr'),14);assert.equal(get(u.get('Fz01'),'uhpm'),180);assert.equal(get(u.get('Fz03'),'ua1c'),.75);
assert.equal(i.get('fvlm').oldId,'vamp');assert.equal(get(i.get('fvlm'),'igol'),3200);assert.equal(get(i.get('fvlm'),'iabi'),'Cvam');
assert.equal(i.get('ftot').oldId,'wswd');assert.equal(get(i.get('ftot'),'igol'),480);assert.equal(get(i.get('ftot'),'iabi'),'Cdet');
assert.equal(a.get('Cdet').oldId,'AIsw');assert.equal(get(a.get('Cdet'),'adur',1),180);assert.equal(get(a.get('Cdet'),'amcs',1),0);
assert.equal(get(u.get('futl'),'usei'),'fdgr,fsdm,fsar,fshl,fvlm,ftot,fpH0,fpM0');
for(const [P,name]of [[U,'war3map.w3u'],[A,'war3map.w3a'],[U,'war3map.w3h'],[U,'war3map.w3t']]){
 const current=parse(P,name),previous=parse(P,name,true);
 for(const table of ['originalTable','customTable'])previous[table].objects=previous[table].objects.filter(o=>!removed.has(o.newId));
 require('./simple-comparison.cjs').objects(current,previous);assert.deepEqual(current,previous,'Every retained '+name+' field is identical to 0.17.1');
}
for(const name of ['war3map.w3q','war3map.w3e','war3map.wpm','war3mapMisc.txt','war3map.w3b','war3map.doo','war3mapUnits.doo','war3map.imp'])assert.deepEqual(bytes(name),bytes(name,true),name+' unchanged');
const canonical=s=>s.split('\n').map(l=>l.trim()).filter(Boolean).join('\n');
const stripped=s=>require('./creative-comparison.cjs').runtime(s,bytes('war3map.j',true).toString());
assert.equal(canonical(stripped(bytes('war3map.j').toString()).replaceAll(balance.version,'0.17.1-alpha')),canonical(stripped(bytes('war3map.j',true).toString())),'Existing runtime unchanged outside replacement, bounded aura state and pet bounty');
assert.equal(balance.spawn_seconds,18);assert.equal(balance.army_cap,85);assert.equal(balance.attack_per_rank,4);assert.equal(balance.armor_per_rank,1.5);assert.equal(balance.health_percent,.10);
fs.writeFileSync(path.join(root,'build/verification-018.json'),JSON.stringify({version:balance.version,heroes:50,removedHeroes:3,replacementHeroes:4,pages:8,skillRanks,petRanks,newShopItems:2,lifestealNative:'AIva for ranged/melee actual attacks',ordinaryPetGold:12,ultimatePetGold:60,previous46HeroesPreserved:true,allArmyPricesAndEffectsPreserved:true,waveSeconds:18,armyCap:85,enginePlaytest:false},null,2)+'\n');
console.log('PASS: four straightforward kits, 2600 skill ranks, 450 ground-pet ranks, ranged/melee lifesteal, two native shop items and pet bounties; all other 0.17.1 data retained.');
