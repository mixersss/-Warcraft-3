// Full current balance validation; numeric assertions for older balance releases are archived.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),b=require('../map/balance.json'),profiles=require('../map/balance-profiles.json'),heroes=require('../map/heroes.json'),seeds=require('../map/ability-seeds.json'),meta=require('../map/classic-balance-metadata.json');
const M=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const old=new M();old.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.21.0-alpha.w3x'))),true);
const now=n=>fs.readFileSync(path.join(root,'build/map',n)),before=n=>Buffer.from(old.get(n).bytes());
const parse=(P,n,prior=false)=>{const p=new P();p.load(new Uint8Array(prior?before(n):now(n)));return p;};
const all=p=>[...p.originalTable.objects,...p.customTable.objects],id=o=>o.newId==='\0\0\0\0'?o.oldId:o.newId;
const get=(o,f,r=0)=>o?.modifications.find(m=>m.id===f&&(m.levelOrVariation||0)===r)?.value;
const index=p=>new Map(all(p).map(o=>[id(o),o]));
const af=parse(A,'war3map.w3a'),uf=parse(U,'war3map.w3u'),qf=parse(A,'war3map.w3q'),tf=parse(U,'war3map.w3t'),a=index(af),u=index(uf),q=index(qf),items=index(tf),oldA=index(parse(A,'war3map.w3a',true)),oldU=index(parse(U,'war3map.w3u',true));
const near=(x,y,msg)=>assert(Math.abs(x-y)<=Math.max(.00002,Math.abs(y)*1e-6),msg+': '+x+' != '+y);
const pyround=x=>{const n=Math.floor(x);return x-n===.5?n+n%2:Math.round(x);};
const fieldKey=m=>[m.id,m.levelOrVariation||0,m.dataPointer||0].join(':');
let fields=0,curves=0;
for(const[cat,p]of [['unit',uf],['ability',af]])for(const o of all(p)){
 const seen=new Set();for(const m of o.modifications){assert(!seen.has(fieldKey(m)),'No duplicate modification '+id(o)+':'+fieldKey(m));seen.add(fieldKey(m));const spec=meta[cat][m.id];assert(spec,'Known Classic field '+m.id);
  if([1,2].includes(spec.kind))assert([1,2].includes(m.variableType),'Floating native field '+id(o)+':'+m.id);else assert.equal(m.variableType,spec.kind,'Native field type '+id(o)+':'+m.id);
  if(m.variableType!==3)assert(Number.isFinite(m.value),'Finite native value');fields++;
 }
}
for(const[raw,defs]of Object.entries(profiles.curves)){
 const object=a.get(raw);assert(object);const cap=get(object,'alev');
 for(const[f,s]of Object.entries(defs)){
  if(!seeds[raw].fields.some(field=>field.id===f))continue;
  let prior=null;
  for(let rank=1;rank<=cap;rank++){
   const t=s.shape?((rank-1)/(rank-1+s.shape))/((cap-1)/(cap-1+s.shape)):(rank-1)/(cap-1);
   let expected=s.start+(s.cap-s.start)*t;
   const kind=seeds[raw].fields.find(field=>field.id===f).kind;if(kind===0)expected=pyround(Math.round(expected*1e6)/1e6);
   near(get(object,f,rank),expected,raw+':'+f+':'+rank);if(prior!==null&&s.start!==s.cap)assert((get(object,f,rank)-prior)*(s.cap-s.start)>=-1e-5,'Monotone profile');prior=get(object,f,rank);curves++;
  }
 }
}
// All 200 player-facing ability slots preserve native requirements/QWER and actual ranks.
for(const h of heroes)for(const[slot,raw]of h.skills.entries()){
 const s=a.get(raw);assert(s);assert.equal(get(s,'alev'),slot===3?50:200);assert.equal(get(s,'ahky'),'QWER'[slot]);assert.equal(get(s,'arlv'),slot===3?6:1);assert.equal(get(s,'alsk'),slot===3?10:1);
 for(let r=1;r<=(slot===3?50:200);r++)assert(get(s,'aub1',r),'Every rank has a tooltip');
}
assert.equal(heroes.length,50);assert.equal(get(a.get('Fatr'),'alev'),500);for(let r=1;r<=500;r++)for(const f of ['Iagi','Iint','Istr'])assert.equal(get(a.get('Fatr'),f,r),2*r);
// Actual summon/illusion counts are preserved against the released archive at every rank.
const countFields=new Set(['Hwe2','Osf2','Efn1','Esv1','Nba2','Ndo2','Rai1','Rai2','Ucb5','Omi1','Uls1','Uls3','Nst1','Hre1','Uan1']);
for(const[oRaw,prev]of oldA){const current=a.get(oRaw);assert(current);for(const m of prev.modifications)if(countFields.has(m.id))assert.equal(get(current,m.id,m.levelOrVariation),m.value,'Preserve counts '+oRaw+':'+fieldKey(m));}
// The maximum chance and uptime never make a single native control/defense permanent.
for(const o of all(af))for(const m of o.modifications)if(['Eev1','Ocr4'].includes(m.id))assert(m.value>=0&&m.value<=.500001);
for(let r=1;r<=200;r++){
 for(const[raw,field]of [['AHtb','ahdu'],['AEer','ahdu'],['AOhx','ahdu'],['AOws','ahdu'],['AUim','ahdu']])assert(get(a.get(raw),field,r)/get(a.get(raw),'acdn',r)<=.31);
 assert(get(a.get('AHds'),'adur',r)/get(a.get('AHds'),'acdn',r)<=.37);
 const n=get(a.get('AOmi'),'Omi1',r),total=get(a.get('AOmi'),'Omi2',r)*n;near(total,.35+(2.2-.35)*((r-1)/(r-1+60))/(199/259),'Finite illusion group budget');
 near(get(a.get('ANms'),'Nms1',r),1+2*((r-1)/(r-1+60))/(199/259),'Mana shield finite efficiency');
 assert.equal(get(a.get('Fent'),'Hwe1',r),get(a.get('AEfn'),'Efnu',r));assert.equal(get(a.get('Fent'),'Hwe2',r),get(a.get('AEfn'),'Efn1',r));
 const rage=u.get(get(a.get('ANcr'),'Emeu',r));near(get(rage,'ua1c'),require('../map/hero-attack-seeds.json').units.Nalc.ua1c*b.hero_attack_interval_multiplier/(1+get(a.get('ANcr'),'Ncr6',r)),'Real rage form interval');
}
assert.equal(a.get('Finc').oldId,'ANic');for(let r=2;r<=200;r++)for(const f of ['Nic1','Nic2','Nic4'])assert(get(a.get('Finc'),f,r)>get(a.get('Finc'),f,r-1));
assert.equal(heroes.find(h=>h.id==='Nfir').skills[2],'Finc');assert.equal(get(a.get('Clif'),'alev'),420);for(let r=1;r<=420;r++)near(get(a.get('Clif'),'Ivam',r),r*.001,'Precise native lifesteal');
// Every untouched technical spell flag/interval remains exact. Scoped magnitude/control overrides are explicit.
const technical=new Set(['Eim2','Eim3','Ucb5','Omi4','Esf2','Esf3','Etq2','Etq3','Hav4','Hbh2','Hbh4','Hds1','Hmt3','Ncs2','Ncs3','Ncs5','Ncs6','Nlm2','Nlm3','Nlm4','Nlm5','Nlm6','Nms2','Nst1','Nst2','Nst4','Nst5','Nsy1','Nsy3','Nsy4','Nsy5','Uim1','Uim2','Uim4','Uin2','Uin3','Uls1','Uls2','Uls3','Udp3','Udp4','Udp5','Hre2','Uan3','Ocr5','Hca4','Ofs1','Nsi1','Eme1','Eme2','Eme3','Neg3','Neg4','Neg5','Neg6']);
const sourceByRaw=new Map(heroes.flatMap(h=>(h.skill_sources||[]).map((s,k)=>[h.skills[k],s])));
for(const[raw,prev]of oldA){const current=a.get(raw),source=sourceByRaw.get(raw)||raw;
 for(const m of prev.modifications)if(technical.has(m.id)&&!profiles.curves[source]?.[m.id])assert.equal(get(current,m.id,m.levelOrVariation),m.value,'Technical field '+raw+':'+fieldKey(m));
}
// All object identity, world geometry, cosmetics, prices and rank caps are retained.
for(const n of ['war3map.w3q','war3map.w3h','war3map.w3b','war3map.wpm','war3map.w3e','war3map.doo','war3mapUnits.doo','war3map.imp','war3mapMap.tga','war3mapPreview.tga'])assert.deepEqual(now(n),before(n),n+' exact0.21');
for(const[raw,prev]of oldU){const current=u.get(raw);assert(current);assert.equal(current.oldId,prev.oldId);for(const m of prev.modifications)if(['umdl','uico','uclr','uclg','uclb','usca','ucol','ureq','ufoo','ubba','ubdi','ubsi','ugol','ulum','upgr'].includes(m.id))assert.equal(get(current,m.id,m.levelOrVariation),m.value,'Preserved cosmetics/count/economy '+raw+':'+m.id);}
const priorItems=index(parse(U,'war3map.w3t',true));for(const[raw,prev]of priorItems){assert(items.has(raw));for(const m of prev.modifications)if(m.id!=='ides'&&m.id!=='utip'&&m.id!=='utub')assert.equal(get(items.get(raw),m.id,m.levelOrVariation),m.value,'Item identity/price/stock '+raw+':'+m.id);}
const misc=now('war3mapMisc.txt').toString();for(const[k,v]of Object.entries(profiles.misc))assert(misc.includes(k+'='+v+'\n'));assert(!misc.includes('AgiAttackBonus='));
assert.equal(b.spawn_units,6);assert.equal(b.spawn_seconds,18);assert.equal(b.army_cap,85);assert.equal(b.hero_respawn_seconds,35);assert.equal(b.autosave_seconds,120);
for(const h of heroes){const object=u.get(h.id);assert.equal(get(object,'uhab'),[...h.skills,'Fatr'].join(','));if(h.stats){for(const[k,f]of [['hp','uhpm'],['strength','ustr'],['agility','uagi'],['intelligence','uint'],['damage','ua1b'],['armor','udef']])assert.equal(get(object,f),h.stats[k]);assert(h.stats.hp<=100);}}
const source=now('war3map.j').toString(),priorSource=before('war3map.j').toString();
// Only profile values and the native finer-grained lifesteal lookup change, never scenario, AI, routing or timers.
let normalized=source.replaceAll(b.version,'0.21.0-alpha').replace('Shared fountain: native auras restore 0.35% health and 0.4% mana per second','Shared fountain: native health/mana auras restore 1.5% per second').replace('700 damage, 24 armor, attacks every 0.5s','1750 damage, 24 armor, attacks every 0.2s').replace('six-second defense window, range 1000','six-second defense window, range 1400').replace('.12+.20*I2R(rank-1)/199.','.12+.18*I2R(rank-1)/199.').replace('IMinBJ(420,R2I(percent*1000.+.5))','IMinBJ(200,R2I(percent*500.+.5))');
for(const array of ['HeroSkill','SpellAbility','AutoSkill','AutoOrder']){
 const oldLines=new Map([...priorSource.matchAll(new RegExp('^\\s*set '+array+'\\[(\\d+)\\] = .*$', 'gm'))].map(m=>[m[1],m[0].trim()]));
 normalized=normalized.replace(new RegExp('^\\s*set '+array+'\\[(\\d+)\\] = .*$', 'gm'),(line,k)=>'    '+(oldLines.get(k)||line.trim()));
}
for(const key of ['FOUNTAIN_HP_PERCENT','FOUNTAIN_MANA_PERCENT']){const re=new RegExp('constant real '+key+' = [0-9.]+');normalized=normalized.replace(re,priorSource.match(re)[0]);}
const oldHybrid=new Map([...priorSource.matchAll(/^\s*set HybridPower\[(\d+)\] = .*$/gm)].map(m=>[m[1],m[0].trim()]));normalized=normalized.replace(/^\s*set HybridPower\[(\d+)\] = .*$/gm,(line,k)=>'    '+oldHybrid.get(k));
const canonical=s=>s.split('\n').map(l=>l.trim()).filter(Boolean).join('\n');assert.equal(canonical(normalized),canonical(priorSource),'Game logic unchanged outside explicit profile bindings and aura precision');
fs.writeFileSync(path.join(root,'build/verification-022.json'),JSON.stringify({version:b.version,heroSlots:200,heroes:50,validatedNativeFields:fields,validatedProfileRankValues:curves,allSummonCountsPreserved:true,allResearchAndItemPricesPreserved:true,allScenarioAIAndRoutingPreserved:true,classicMetadataChecked:true,enginePlaytest:false},null,2)+'\n');
console.log('PASS:current0.22 balance profiles,all200 skills,Classic field types,controls/defenses/caps,counts and every untouched scenario/economy/world field.');
