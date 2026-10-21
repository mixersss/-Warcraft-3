// Independent 0.20 release-scope and native troop-role checks, using real 0.19 bytes.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),b=require('../map/balance.json'),traits=require('../map/army-traits.json');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const old=new MapFile();old.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.19.0-alpha.w3x'))),true);
const now=n=>fs.readFileSync(path.join(root,'build/map',n)),before=n=>Buffer.from(old.get(n).bytes());
const parse=(P,n,prior=false)=>{const p=new P();p.load(new Uint8Array(prior?before(n):now(n)));return p;};
const get=(o,id,rank=0)=>o.modifications.find(m=>m.id===id&&(m.levelOrVariation||0)===rank)?.value;
const u=parse(U,'war3map.w3u'),a=parse(A,'war3map.w3a'),q=parse(A,'war3map.w3q'),units=new Map(u.customTable.objects.map(o=>[o.newId,o])),skills=new Map(a.customTable.objects.map(o=>[o.newId,o]));
const native=['Jtev','Jtcr','Jtfb','Jtss','Jtba','Jtne','Jtdr','Jtdv','Jtdg','Jtpv','Jtpo','Jtab','Jtsk','Jtta','Jtwe','Jtpl','Jtfr','Jtfz'];
assert.deepEqual(traits.abilities.map(r=>r.id),native);assert.equal(b.spawn_units,6);assert.equal(b.army_cap,85);assert.equal(b.spawn_seconds,18);
const stats={fm01:[400,20,4,1.5,600],fm02:[650,23,5,1.5,550],fm03:[1020,30,8,1.5,100],fm04:[935,46,7,1.8,600],fm11:[650,20,2,1.9,100],fm12:[650,23,3,1.5,100],fm13:[935,24,4,2,550],fm14:[1320,44,5,1.5,100],fm21:[350,18,2,.9,100],fm22:[715,23,3,1.3,550],fm23:[1020,30,4,1.3,100],fm24:[1100,44,5,1.8,600],fm31:[325,18,2,1.25,700],fm32:[552,23,3,1.5,450],fm33:[722,30,4,1.5,650],fm34:[1760,28,8,2,100]};
for(const[id,values]of Object.entries(stats))for(const[field,index]of [['uhpm',0],['ua1b',1],['udef',2],['ua1c',3],['ua1r',4]])assert(Math.abs(get(units.get(id),field)-values[index])<1e-6,id+':'+field);
for(let race=0;race<4;race++){const p=units.get('fm'+race+'0');assert.equal(p.oldId,'hfoo');assert.equal(get(p,'uhpm'),380);assert.equal(get(p,'uabi'),'');}
for(const row of traits.abilities){const actual=skills.get(row.id);assert(actual);assert.equal(actual.oldId,row.base);assert.equal(get(actual,'aher'),0);assert.equal(get(actual,'alev'),1);assert.equal(get(actual,'areq'),'');
 const keys=actual.modifications.map(m=>[m.id,m.levelOrVariation,m.dataPointer].join(':'));assert.equal(new Set(keys).size,keys.length,'No duplicated native fields');
}
const check=(id,field,value)=>assert(Math.abs(get(skills.get(id),field,1)-value)<1e-6,id+':'+field);
check('Jtev','Eev1',.12);check('Jtcr','Ocr1',15);check('Jtcr','Ocr2',1.6);check('Jtfb','fbk1',12);check('Jtfb','fbk3',4);check('Jtba','ahdu',.4);check('Jtba','adur',.8);
check('Jtne','ahdu',1);check('Jtdr','Akb1',.15);check('Jtdg','Car1',1);check('Jtdg','Dev2',25);check('Jtpv','War1',20);check('Jtpv','War2',40);check('Jtpl','Apl1',4);check('Jtpl','Apl2',4);check('Jtpl','Apl3',4);
assert.equal(get(units.get('fm32'),'ua1w'),'mbounce');assert.equal(get(units.get('fm32'),'utc1'),3);assert.equal(get(units.get('fm04'),'ua1w'),'msplash');assert.equal(get(units.get('fm04'),'ua1p'),'ground,enemy,neutral');assert(get(units.get('fm33'),'uabi').includes('Amim'));assert(get(units.get('fm02'),'uabi').includes('Amim'));
for(let rank=1;rank<=20;rank++)assert(get(q.customTable.objects.find(o=>o.newId==='Rfwn'),'gub1',rank).includes('Следующая волна: '+(6+rank)+' бойцов.'));
// Every other field remains exact, including all 50 heroes, summons, prices and upgrades.
for(const[P,name]of[[U,'war3map.w3u'],[A,'war3map.w3a'],[A,'war3map.w3q']]){
 const current=parse(P,name),previous=parse(P,name,true);
 for(const table of ['originalTable','customTable']){
  const refs=new Map(previous[table].objects.map(o=>[o.oldId+':'+o.newId,o]));
  current[table].objects=current[table].objects.filter(o=>!native.includes(o.newId));
  for(const o of current[table].objects){const ref=refs.get(o.oldId+':'+o.newId);assert(ref);
   const troop=traits.troops[o.newId],allowed=new Set(troop?['uhpm','ua1b','udef','umvs','ua1c','ua1r','uabi','utub','utip',...Object.keys(troop.fields)]:[]);
   o.modifications=o.modifications.filter(m=>{if(allowed.has(m.id)||name==='war3map.w3a'&&/^Fbr[0-3]$/.test(o.newId)&&m.id==='aub1'||name==='war3map.w3q'&&o.newId==='Rfwn'&&m.id==='gub1'){
    const oldMod=ref.modifications.find(n=>n.id===m.id&&n.levelOrVariation===m.levelOrVariation&&n.dataPointer===m.dataPointer);if(!oldMod)return false;m.value=oldMod.value;
   }return true;});
  }
 }
 for(const p of [current,previous])for(const t of ['originalTable','customTable'])for(const o of p[t].objects)o.modifications.sort((a,b)=>a.id.localeCompare(b.id)||a.levelOrVariation-b.levelOrVariation||a.dataPointer-b.dataPointer);
 assert.deepEqual(current,previous,name+' unrelated fields unchanged');
}
for(const n of ['war3map.w3t','war3map.w3h','war3map.w3b','war3map.wpm','war3map.w3e','war3mapMisc.txt','war3map.doo','war3mapUnits.doo','war3map.imp','war3mapMap.tga','war3mapPreview.tga'])assert.deepEqual(now(n),before(n),n+' unchanged');
const functions=['AssignBotChoices','SelectArmyRace','OnChat','ShowModes','ShowRaces','SetAllRandom','SpawnWave','CommandArmy','OnLeave','InitSlot'];
let source=now('war3map.j').toString(),prior=before('war3map.j').toString();
for(const name of functions){const re=new RegExp('function '+name+' takes[\\s\\S]*?endfunction');source=source.replace(re,()=>prior.match(re)[0]);}
for(const name of ['RandomBotArmyBranch','ArmyTraitCast'])source=source.replace(new RegExp('function '+name+' takes[\\s\\S]*?endfunction\\s*'),'');
source=source.replaceAll(b.version,'0.19.0-alpha').replace('constant integer SPAWN_UNITS = 6','constant integer SPAWN_UNITS = 4').replaceAll('Waves: six plus','Waves: four plus').replaceAll('Six plus wave-size research troops per wave','Four plus wave-size research troops per wave');
const canonical=s=>s.split('\n').map(l=>l.trim()).filter(Boolean).join('\n');assert.equal(canonical(source),canonical(prior),'Only requested runtime functions change');
fs.writeFileSync(path.join(root,'build/verification-020.json'),JSON.stringify({version:b.version,startingWave:6,maxWave:26,armyCap:85,waveSeconds:18,heroModes:['manual','randomHeroesOnly'],botRaces:'team-unique, least represented globally, synchronized random tie break',troopProfiles:16,isolatedNativeAbilities:18,ghoulHP:350,ghoulAttackInterval:.9,otherDataPreserved:true,enginePlaytest:false},null,2)+'\n');
console.log('PASS: 16 troop roles,18 isolated native abilities,6..26 waves,hero-only modes; exact0.19 delta preserves every other gameplay field.');
