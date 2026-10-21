// Validate new content separately, then compare all retained data to published 0.15.3.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..'),heroes=require('../map/heroes.json'),balance=require('../map/balance.json'),profiles=require('../map/bot-profiles.json');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default,U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const previous=new MapFile();previous.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.15.3-alpha.w3x'))),true);require('./historical-wave-settings.cjs')(previous);
function parse(P,name,old=false){const p=new P();p.load(new Uint8Array(old?previous.get(name).bytes():fs.readFileSync(path.join(root,'build/map',name))));return p;}
const unitFile=parse(U,'war3map.w3u'),abilityFile=parse(A,'war3map.w3a');
const index=p=>new Map(p.customTable.objects.map(o=>[o.newId,o]));const units=index(unitFile),abilities=index(abilityFile);
const get=(o,id,rank=0)=>o.modifications.find(m=>m.id===id&&(m.levelOrVariation||0)===rank)?.value;
const extra=heroes.filter(h=>h.signature);assert.equal(heroes.length,50);assert.equal(extra.length,10);
assert.deepEqual(extra.map(h=>h.signature.kind),[0,1,2,3,4,5,6,7,8,9]);
assert.equal(new Set(heroes.filter(h=>h.base).map(h=>h.model.toLowerCase())).size,26);
for(const h of extra){
 const u=units.get(h.id);assert(u);assert.equal(get(u,'upra'),['STR','AGI','INT'][h.primary]);assert.equal(get(u,'umdl'),h.model);assert.equal(get(u,'usnd'),h.soundset);assert.equal(get(u,'usca'),Math.fround(h.scale));
 if(h.attack_visual){assert.equal(get(u,'ua1m'),h.attack_visual.projectile);assert.equal(get(u,'ua1r'),h.attack_visual.range);assert.equal(get(u,'ua1w'),'missile');}
 assert(!h.model.includes('\\\\')&&!h.icon.includes('\\\\'),'New stock asset paths use canonical separators');
 assert.equal(get(u,'uhab'),[...h.skills,'Fatr'].join(','));assert.equal(h.skills.length,4);assert(profiles.heroes[h.id]);assert.equal(h.gear_families.length,6);
 assert.equal(h.spells.length,h.skill_sources.filter(s=>!['AHad','AHab','AUav','AEar','AUts','AEev','AOae','AUau','AOre'].includes(s)).length,'Every active ability has an AI order');
 for(const [slot,id] of h.skills.entries()){
  const a=abilities.get(id);assert(a);assert.equal(get(a,'anam'),h.ability_names[slot]);assert.equal(a.oldId,h.skill_sources[slot]);assert.equal(get(a,'alev'),slot===3?50:200);assert.equal(get(a,'ahky'),'QWER'[slot]);assert.equal(get(a,'auhk'),'QWER'[slot]);assert.equal(get(a,'abpx'),slot);assert.equal(get(a,'aani'),'attack');
  if(slot===h.signature.slot||(slot===0&&h.signature.slot===-1))for(let rank=1;rank<=(slot===3?50:200);rank++)assert(get(a,'aub1',rank).includes(h.signature.description));
 }
}
const aura=abilities.get('Fxwr');assert.equal(aura.oldId,'AOae');assert.equal(get(aura,'aher'),0);assert.equal(get(aura,'aite'),1);
for(let rank=1;rank<=50;rank++){assert.equal(get(aura,'Oae1',rank),0);assert(Math.abs(get(aura,'Oae2',rank)-(.15+.006*rank))<1e-6);assert.equal(get(aura,'aare',rank),650);assert(get(aura,'atar',rank).includes('nonhero'));}
for(const [P,name]of [[U,'war3map.w3u'],[A,'war3map.w3a']]){
 const current=parse(P,name),old=parse(P,name,true);const original=current.customTable.objects.length;
 require('./roster-comparison.cjs')(current,old);assert.equal(original-current.customTable.objects.length,name.endsWith('w3u')?480:87);
 assert.deepEqual(current,old,'Every retained '+name+' field is unchanged');
}
for(const name of ['war3map.w3t','war3map.w3h','war3map.w3e','war3map.wpm','war3mapMisc.txt','war3map.doo','war3mapUnits.doo']){if(['war3map.w3h','war3map.w3t'].includes(name))require('./simple-comparison.cjs').same(fs.readFileSync(path.join(root,'build/map',name)),previous.get(name).bytes(),name);else assert.deepEqual(fs.readFileSync(path.join(root,'build/map',name)),Buffer.from(previous.get(name).bytes()),name+' unchanged');}
const research=parse(A,'war3map.w3q'),oldResearch=parse(A,'war3map.w3q',true);
assert.deepEqual(require('./summon-comparison.cjs').research(research,oldResearch),oldResearch,'Only six troop research price records may differ');
const moduleSource=fs.readFileSync(path.join(root,'map/expansion-heroes.j'),'utf8');
assert(!/\b(?:CreateTimer|CreateUnit|Location|GetLocalPlayer|TriggerSleepAction)\s*\(/.test(moduleSource));
assert(moduleSource.includes('function ExpansionOnDeath'));assert(moduleSource.includes('function ExpansionPlayerTick'));assert(moduleSource.includes('call TriggerExecute(ExpansionThinkTrigger[p])'));
const report={version:balance.version,heroes:50,newCustomHeroes:10,customTotal:26,skillSlots:200,pickerPages:8,uniqueModels:26,newSkills:40,nativeTimedAuraRanks:50,allActiveSkillsHaveBotOrders:true,oldHeroesSpellsTerrainUnchanged:true,troopPriceChangeValidatedBy:"verify-0161",boundedPlayerState:12,perCastTimers:0,enginePlaytest:false};
fs.writeFileSync(path.join(root,'build/verification-016.json'),JSON.stringify(report,null,2)+'\n');console.log('PASS: 50 heroes / 26 unique creature models; 10 new mechanics, 40 isolated QWER skills, capped temporary troop aura, complete AI orders and retained 0.15.3 mechanics unchanged; troop price differences isolated.');
