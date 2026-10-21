// Independent check of army branches, ground replacements, collision and exact release scope.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),balance=require('../map/balance.json'),races=require('../map/races.json');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const old=new MapFile();old.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.18.1-alpha.w3x'))),true);
const now=n=>fs.readFileSync(path.join(root,'build/map',n)),before=n=>Buffer.from(old.get(n).bytes());
const parse=(P,n,prior=false)=>{const p=new P();p.load(new Uint8Array(prior?before(n):now(n)));if(!prior)require('./army-traits-comparison.cjs').objects(p);return p;};
const get=(o,id,rank=0)=>o.modifications.find(m=>m.id===id&&(m.levelOrVariation||0)===rank)?.value;
const u=parse(U,'war3map.w3u'),a=parse(A,'war3map.w3a'),q=parse(A,'war3map.w3q'),by=p=>new Map(p.customTable.objects.map(o=>[o.newId,o]));
const units=by(u),skills=by(a),research=by(q);
const expected=[['hfoo','hrif','hspt','hkni','hsor'],['hfoo','ogru','orai','okod','otau'],['hfoo','ugho','ucry','uabo','nrvi'],['hfoo','earc','esen','edry','emtg']];
assert.deepEqual(races.map(r=>r.units),expected);assert.equal(balance.spawn_units,6);assert.equal(balance.army_collision,8);assert.equal(balance.army_cap,85);assert.equal(balance.spawn_seconds,18);
for(let race=0;race<4;race++)for(let tier=0;tier<5;tier++){
 const unit=units.get('fm'+race+tier);assert.equal(unit.oldId,expected[race][tier]);assert.equal(get(unit,'ucol'),8);assert.equal(get(unit,'uhpm'),balance.tiers[tier].hp);assert.equal(get(unit,'ua1b'),balance.tiers[tier].damage);
 assert.equal(get(unit,'upgr'),'Rfat,Rfar,Rfhp,Rfa2,Rfr2,Rfh2');assert.equal(get(unit,'ua1t'),races[race].attack_types[tier]);assert.equal(get(unit,'ua1r'),races[race].ranged_tiers.includes(tier)?550:100);
}
assert.equal(get(units.get('fbax'),'uabi'),'Fbr0,Fbr1,Fbr2,Fbr3');
for(let race=0;race<4;race++){
 const skill=skills.get('Fbr'+race);assert.equal(skill.oldId,'ANcl');assert.equal(get(skill,'aher'),0);assert.deepEqual([get(skill,'abpx'),get(skill,'abpy')],[[1,1],[2,1],[0,2],[1,2]][race]);assert(![[3,1],[3,2],[0,1]].some(([x,y])=>get(skill,'abpx')===x&&get(skill,'abpy')===y),'Do not overlap rally, cancel or wave research');assert.equal(get(skill,'amcs',1),0);assert.equal(get(skill,'Ncl3',1),1);assert.equal(get(skill,'Ncl5',1),0);
 for(const name of races[race].tier_names.slice(1))assert(get(skill,'aub1',1).includes(name));
}
for(let rank=1;rank<=20;rank++)assert(get(research.get('Rfwn'),'gub1',rank).includes('Следующая волна: '+(6+rank)+' бойцов.'));
for(const [P,name]of [[U,'war3map.w3u'],[A,'war3map.w3a'],[A,'war3map.w3q']]){
 const current=parse(P,name),previous=parse(P,name,true);
 for(const table of ['originalTable','customTable']){
  const refs=new Map(previous[table].objects.map(o=>[o.newId==='\0\0\0\0'?o.oldId:o.newId,o]));
  current[table].objects=current[table].objects.filter(o=>!(name==='war3map.w3a'&&/^Fbr[0-3]$/.test(o.newId)));
  for(const o of current[table].objects){
   const ref=refs.get(o.newId==='\0\0\0\0'?o.oldId:o.newId);assert(ref);
   const troop=name==='war3map.w3u'&&/^fm[0-3][0-4]$/.test(o.newId);
   if(troop){o.oldId=ref.oldId;const race=Number(o.newId[2]),tier=Number(o.newId[3]),projectile=races[race].tier_projectiles?.[tier];if(projectile){assert.equal(get(o,'ua1w'),'missile');assert.equal(get(o,'ua1m'),projectile);assert.equal(get(o,'ua1z'),900);o.modifications=o.modifications.filter(m=>!['ua1w','ua1m','ua1z'].includes(m.id));}}
   for(const m of o.modifications){
    const allowed=troop&&['unam','ua1r','ua1t','ua1g','ucol'].includes(m.id)||name==='war3map.w3u'&&o.newId==='fbax'&&['uabi','utub'].includes(m.id)||name==='war3map.w3q'&&o.newId==='Rfwn'&&m.id==='gub1';
    if(allowed){const prior=ref.modifications.find(n=>n.id===m.id&&n.levelOrVariation===m.levelOrVariation&&n.dataPointer===m.dataPointer);assert(prior);m.value=prior.value;}
   }
  }
 }
 assert.deepEqual(current,previous,'Every unrelated field preserved: '+name);
}
for(const n of ['war3map.w3t','war3map.w3h','war3map.w3b','war3map.wpm','war3map.w3e','war3mapMisc.txt','war3map.doo','war3mapUnits.doo','war3map.imp','war3mapMap.tga','war3mapPreview.tga'])assert.deepEqual(now(n),before(n),n+' unchanged');
const source=now('war3map.j').toString(),prior=before('war3map.j').toString(),canonical=s=>s.split('\n').map(l=>l.trim()).filter(Boolean).join('\n');
const normalize=s=>require('./army-branch-comparison.cjs').runtime(s,prior).replaceAll(balance.version,'0.18.1-alpha').replace('// Native branch cards are separate from paid development research.','');
assert.equal(canonical(normalize(source)),canonical(normalize(prior)),'Unrelated runtime preserved');assert(!source.includes('SetUnitPathing('),'Collision reduced without disabling terrain collision');
fs.writeFileSync(path.join(root,'build/verification-019.json'),JSON.stringify({version:balance.version,sharedStart:'hfoo',troopBranches:expected,collisionRadius:8,previousCollisionRadius:16,historicalStartingWaveSize:4,currentStartingWaveSize:6,historicalMaxWaveSize:24,currentMaxWaveSize:26,armyCap:85,waveSeconds:18,baseBranchCards:4,permanentChoice:true,otherHeroesPetsItemsPricesTerrainPreserved:true,enginePlaytest:false},null,2)+'\n');
console.log('PASS: four permanent barracks branch cards, shared footman start, 16 requested ground troops, collision8; current6..26 waves and troop traits audited separately by verify-020.');
