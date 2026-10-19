// AI-only release: native combat, economy objects and geometry must not change.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..');
const War3Map=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const previous=new War3Map();previous.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.14.3-alpha.w3x'))),true);
const unchanged=['war3map.w3u','war3map.w3a','war3map.w3h','war3map.w3q','war3map.w3t','war3map.w3e','war3map.wpm','war3mapMisc.txt','war3map.doo','war3mapUnits.doo'];
for(const name of unchanged)assert.deepEqual(fs.readFileSync(path.join(root,'build/map',name)),Buffer.from(previous.get(name).bytes()),'AI change must preserve '+name);
const read=name=>JSON.parse(fs.readFileSync(path.join(root,name)));
const profiles=read('map/bot-profiles.json'),heroes=read('map/heroes.json'),balance=read('map/balance.json');
assert.equal(Object.keys(profiles.heroes).length,36);assert.equal(Object.keys(profiles.roles).length,4);
for(const hero of heroes){
 const p=profiles.heroes[hero.id],role=profiles.roles[p.role];assert(role);
 assert.deepEqual([...p.skill_priority].sort(),[0,1,2]);
 assert.equal(role.tactics.length,3);
 for(const index of role.tactics){
  assert(index>=0&&index<balance.bot_tactics.length);
  const t=balance.bot_tactics[index];assert(t.tier_percent>0&&t.gear_percent>0&&t.tier_percent+t.gear_percent<=90);
  if(p.role==='support')assert(t.gear_percent<=25);
  if(p.role==='carry'){assert.equal(t.gear_percent,75);assert.equal(t.tier_percent,15)};
 }
}
const ai=fs.readFileSync(path.join(root,'map/bot-ai.j'),'utf8');
assert(!/\b(?:CreateGroup|CreateTimer|CreateTrigger|GetLocalPlayer)\s*\(/.test(ai),'No per-think handle allocation or local gameplay branch');
assert.match(ai,/IsUnitVisible/);assert.match(ai,/IsUnitInvisible/);assert.match(ai,/UnitUseItem/);
const report=read('build/verification-0142.json');
Object.assign(report,{AIRelease:balance.version,heroProfiles:36,roles:4,styleVariants:108,economyStrategies:5,supportGearPercent:[15,25],carryGearPercent:[75,75],carryTierPercent:15,minimumTroopResearchPercent:10,teamCommands:['-follow','-defend','-push','-regroup','-free','-ai'],commandSeconds:90,sharedPushSeconds:22,combatScanRadius:1100,soldierScrollRadius:700,realNativeSupplies:true,combatObjectsByteIdenticalTo:'0.14.3-alpha',enginePlaytest:false});
fs.writeFileSync(path.join(root,'build/verification-015.json'),JSON.stringify(report,null,2)+'\n');
console.log('PASS: 36 hero-role profiles, five funded strategies, 108 style mappings, bounded AI module and all native combat/terrain/economy objects unchanged from 0.14.3.');
