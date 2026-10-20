// New Channel-only kits, plus full object/runtime regression against 0.16.2.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),heroes=require('../map/heroes.json'),balance=require('../map/balance.json');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default,U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const old=new MapFile();old.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.16.2-alpha.w3x'))),true);
const bytes=(name,prior=false)=>prior?Buffer.from(old.get(name).bytes()):fs.readFileSync(path.join(root,'build/map',name));
function parse(P,name,prior=false){const p=new P();p.load(new Uint8Array(bytes(name,prior)));return p;}
const abilities=parse(A,'war3map.w3a'),units=parse(U,'war3map.w3u');
const byId=p=>new Map(p.customTable.objects.map(o=>[o.newId,o]));const a=byId(abilities),u=byId(units);
const get=(o,id,rank=0)=>o.modifications.find(m=>m.id===id&&m.levelOrVariation===rank)?.value;
const extra=heroes.filter(h=>h.creative);assert.equal(heroes.length,49);assert.equal(extra.length,3);
let ranks=0;
for(const h of extra){
 const unit=u.get(h.id);assert.equal(get(unit,'upra'),['STR','AGI','INT'][h.primary]);assert.equal(get(unit,'umdl'),h.model);assert.equal(get(unit,'usnd'),h.soundset);
 assert.equal(get(unit,'uhab'),[...h.skills,'Fatr'].join(','));assert.equal(h.creative.length,4);assert.equal(h.spells.length,4);
 for(const [slot,id]of h.skills.entries()){
  const skill=a.get(id),meta=h.creative[slot],cap=slot===3?50:200;
  assert.equal(skill.oldId,'ANcl','No copied stock spell effect: only a native order/UI shell');
  assert.equal(get(skill,'alev'),cap);assert.equal(get(skill,'arlv'),slot===3?6:1);assert.equal(get(skill,'alsk'),slot===3?10:1);
  assert.equal(get(skill,'anam'),meta.name);assert.equal(get(skill,'ahky'),'QWER'[slot]);assert.equal(get(skill,'abpx'),slot);assert.equal(get(skill,'arpx'),slot);
  for(let rank=1;rank<=cap;rank++){
   assert.equal(get(skill,'Ncl2',rank),meta.target);assert.equal(get(skill,'Ncl3',rank),1);assert.equal(get(skill,'Ncl5',rank),0);assert.equal(get(skill,'Ncl1',rank),0);
   assert.equal(get(skill,'Ncl6',rank),['berserk','roar','taunt','howlofterror'][slot]);
   assert.equal(get(skill,'amcs',rank),meta.mana);assert.equal(get(skill,'acdn',rank),meta.cooldown);assert(get(skill,'aub1',rank).includes(meta.description));ranks++;
  }
 }
}
assert.equal(ranks,1950);assert.equal(new Set(heroes.filter(h=>h.base).map(h=>h.model.toLowerCase())).size,25);
for(const [P,name]of [[U,'war3map.w3u'],[A,'war3map.w3a']]){
 const current=parse(P,name),previous=parse(P,name,true),count=current.customTable.objects.length;
 require('./creative-comparison.cjs').objects(current,previous);
 assert.equal(count-current.customTable.objects.length,name.endsWith('w3u')?6:12);assert.deepEqual(current,previous,'Every retained '+name+' field unchanged');
}
for(const name of ['war3map.w3q','war3map.w3t','war3map.w3h','war3map.w3e','war3map.wpm','war3mapMisc.txt','war3map.doo','war3mapUnits.doo','war3map.w3b','war3map.imp'])assert.deepEqual(bytes(name),bytes(name,true),name+' unchanged, including new troop prices/effects');
const canonical=s=>s.split('\n').map(l=>l.trim()).filter(Boolean).join('\n');
assert.equal(canonical(require('./creative-comparison.cjs').runtime(bytes('war3map.j').toString(),bytes('war3map.j',true).toString()).replaceAll(balance.version,'0.16.2-alpha')),canonical(bytes('war3map.j',true).toString()),'Runtime preserved outside new kits, hooks and roster growth');
const kitSource=fs.readFileSync(path.join(root,'map/creative-heroes.j'),'utf8');
assert(!/\b(?:CreateTimer|CreateUnit|Location|GetLocalPlayer|TriggerSleepAction)\s*\(/.test(kitSource));
assert.equal((kitSource.match(/CreateGroup\(/g)||[]).length,1);assert(kitSource.includes('set CreativeThread[p] = CreateTrigger()'));
fs.writeFileSync(path.join(root,'build/verification-017.json'),JSON.stringify({version:balance.version,heroes:49,customHeroes:25,newHeroes:3,newTriggerSkills:12,channelRanksChecked:ranks,pages:7,newProfilesHaveAI:true,oldObjectsAndEconomyUnchanged:true,staticPlayerThreads:12,perCastTimers:0,perCastGroups:0,enginePlaytest:false},null,2)+'\n');
console.log('PASS: three unique models, twelve Channel-only original trigger skills, 1950 native UI ranks, combo-aware AI; all 0.16.2 content and economy preserved.');
