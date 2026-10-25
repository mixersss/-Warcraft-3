// Full current balance validation; numeric assertions for older balance releases are archived.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),b=require('../map/balance.json'),profiles=require('../map/balance-profiles.json'),heroes=require('../map/heroes.json'),seeds=require('../map/ability-seeds.json'),meta=require('../map/classic-balance-metadata.json');
const M=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const old=new M();old.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.22.0-alpha.w3x'))),true);
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
for(const[cat,p]of [['unit',uf],['ability',af],['unit',tf]])for(const o of all(p)){
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
assert.equal(heroes.find(h=>h.id==='Nfir').skills[2],'Finc');assert.equal(get(a.get('Clif'),'alev'),480);for(let r=1;r<=480;r++)near(get(a.get('Clif'),'Ivam',r),r*.001,'Precise native lifesteal');
// Every untouched technical spell flag/interval remains exact. Scoped magnitude/control overrides are explicit.
const technical=new Set(['Eim2','Eim3','Ucb5','Omi4','Esf2','Esf3','Etq2','Etq3','Hav4','Hbh2','Hbh4','Hds1','Hmt3','Ncs2','Ncs3','Ncs5','Ncs6','Nlm2','Nlm3','Nlm4','Nlm5','Nlm6','Nms2','Nst1','Nst2','Nst4','Nst5','Nsy1','Nsy3','Nsy4','Nsy5','Uim1','Uim2','Uim4','Uin2','Uin3','Uls1','Uls2','Uls3','Udp3','Udp4','Udp5','Hre2','Uan3','Ocr5','Hca4','Ofs1','Nsi1','Eme1','Eme2','Eme3','Neg3','Neg4','Neg5','Neg6']);
const sourceByRaw=new Map(heroes.flatMap(h=>(h.skill_sources||[]).map((s,k)=>[h.skills[k],s])));
for(const[raw,prev]of oldA){const current=a.get(raw),source=sourceByRaw.get(raw)||raw;
 for(const m of prev.modifications)if(technical.has(m.id)&&!profiles.curves[source]?.[m.id])assert.equal(get(current,m.id,m.levelOrVariation),m.value,'Technical field '+raw+':'+fieldKey(m));
}
// All object identity, world geometry, cosmetics, prices and rank caps are retained.
// The separate music-only verifier checks the full import table and exact0.23 runtime.
for(const n of ['war3map.w3q','war3map.w3h','war3map.w3b','war3map.wpm','war3map.w3e','war3map.doo','war3mapUnits.doo','war3mapMap.tga','war3mapPreview.tga'])assert.deepEqual(now(n),before(n),n+' exact0.21');
for(const[raw,prev]of oldU){const current=u.get(raw);assert(current);assert.equal(current.oldId,prev.oldId);for(const m of prev.modifications)if(['umdl','uico','uclr','uclg','uclb','usca','ucol','ureq','ufoo','ubba','ubdi','ubsi','ugol','ulum','upgr'].includes(m.id))assert.equal(get(current,m.id,m.levelOrVariation),m.value,'Preserved cosmetics/count/economy '+raw+':'+m.id);}
for(const[raw,prev]of oldU)if(raw!=='ftow')assert.deepEqual(u.get(raw),prev,'Unchanged prior unit '+raw);
const tower=u.get('ftow');assert.equal(get(tower,'uhpm'),40000);assert.equal(get(tower,'ua1b')+get(tower,'ua1d')*get(tower,'ua1s'),250);assert.equal(get(tower,'ua1s'),1);near(get(tower,'ua1c'),.5,'Fast front tower');assert(get(tower,'udp1')+get(tower,'ubs1')<.5);assert.equal(get(tower,'ua1r'),700);
const priorItems=index(parse(U,'war3map.w3t',true));for(const[raw,prev]of priorItems){assert(items.has(raw));for(const m of prev.modifications)if(m.id!=='ides'&&m.id!=='utip'&&m.id!=='utub')assert.equal(get(items.get(raw),m.id,m.levelOrVariation),m.value,'Item identity/price/stock '+raw+':'+m.id);}
const misc=now('war3mapMisc.txt').toString();for(const[k,v]of Object.entries(profiles.misc))assert(misc.includes(k+'='+v+'\n'));assert(!misc.includes('AgiAttackBonus='));
assert.equal(b.spawn_units,6);assert.equal(b.spawn_seconds,18);assert.equal(b.army_cap,85);assert.equal(b.hero_respawn_seconds,35);assert.equal(b.autosave_seconds,120);
for(const h of heroes){const object=u.get(h.id);assert.equal(get(object,'uhab'),[...h.skills,'Fatr'].join(','));if(h.stats){for(const[k,f]of [['hp','uhpm'],['strength','ustr'],['agility','uagi'],['intelligence','uint'],['damage','ua1b'],['armor','udef']])assert.equal(get(object,f),h.stats[k]);assert(h.stats.hp<=100);}}
// Explicit runtime delta against published0.22: changed functions are covered by real handler mocks.
const source=now('war3map.j').toString(),priorSource=before('war3map.j').toString();
const changed=['AddGold','RegularGearCost','BotShop','BotResearch','BotHero','BotUseSupplies','OnChat','main','Tick','CreativeCache'];
const added=['BotArenaShop','ArenaItemIndex'];
const functionRE=name=>new RegExp(String.raw`^function ${name} takes[\s\S]*?^endfunction`,'m');
let normalized=require('./verify-music-0231.cjs').stripMusic(source).replaceAll(b.version,'0.22.0-alpha').replace('constant integer TOWER_HP = 40000','constant integer TOWER_HP = 7800');
for(const name of changed){const prev=priorSource.match(functionRE(name));const current=normalized.match(functionRE(name));assert(prev&&current,'Audited function '+name);normalized=normalized.replace(functionRE(name),()=>prev[0]);}
for(const name of added){assert(normalized.match(functionRE(name)));normalized=normalized.replace(functionRE(name),'');}
const newGlobals=['ArenaStore','ArenaItemId','ArenaItemCost','ArenaRelicBought','ArenaShopAt','ArmySavings','ArmyFraction'];
normalized=normalized.split('\n').filter(line=>!newGlobals.some(k=>new RegExp(String.raw`^\s*(unit|integer|boolean) array ${k}$`).test(line)||new RegExp(String.raw`^\s*set ${k}\[`).test(line))).join('\n');
for(const[k,oldValue]of [['BotGearBudget',75],['BotTierBudget',15]])normalized=normalized.replace(new RegExp(String.raw`set ${k}\[3\] = \d+`), 'set '+k+'[3] = '+oldValue);
for(let k=0;k<2;k++){const line='    call SetUnitInvulnerable(ArenaStore['+k+'],true)';assert(normalized.includes(line));normalized=normalized.replace(line,'');assert(source.includes("'frs"+k+"',"+(k===0?-720:720)+",320,270)"));}
normalized=normalized.replace('// Shared native stores: one role item and situational supplies, paid from equipment income.','');
const canonical=s=>s.split('\n').map(l=>l.trim()).filter(Boolean).join('\n');if(canonical(normalized)!==canonical(priorSource)){fs.writeFileSync('/tmp/fff023-normalized.j',canonical(normalized));fs.writeFileSync('/tmp/fff023-before.j',canonical(priorSource));}assert(canonical(normalized)===canonical(priorSource),'Runtime unchanged outside central market,carry accounting and aura cache');
// All aura ranks, including diminishing early progression and exact finite caps.
let auraValues=0;
for(const[raw,defs]of Object.entries(b.aura_balance))for(const[field,spec]of Object.entries(defs))for(let rank=1;rank<=200;rank++){
 const t=((rank-1)/(rank-1+20))/(199/219);near(get(a.get(raw),field,rank),spec.start+(spec.cap-spec.start)*t,'Aura progression '+raw+':'+field+':'+rank);auraValues++;
}
for(const spec of require('../map/hero-passives.json'))for(let rank=1;rank<=200;rank++){const t=((rank-1)/(rank-1+20))/(199/219);near(get(a.get(spec.id),spec.field,rank),spec.start+(spec.cap-spec.start)*t,'Custom army aura');auraValues++;}
const market=require('../map/arena-items.json');assert.equal(market.length,8);
for(const row of market){const obj=items.get(row.id);assert(obj);assert.equal(get(obj,'igol'),row.cost);assert.equal(obj.oldId,row.base);assert.equal(get(u.get('frs'+row.shop),'usei').split(',').includes(row.id),true);if(row.ability)assert.equal(get(obj,'icid'),row.ability);}
const effects={attack:'Iatt',attack_speed:'Isx1',lifesteal:'Ivam',intelligence:'Iint',mana:'Iman',health:'Ilif',armor:'Idef',fire_dps:'Icfd'};
for(const row of market.filter(r=>r.stats)){
 const ids=get(items.get(row.id),'iabi').split(',');for(const[stat,expected]of Object.entries(row.stats)){const field=effects[stat];assert(field);assert(ids.some(raw=>Math.abs((get(a.get(raw),field,1)??NaN)-expected)<.00001),'Actual relic effect '+row.id+':'+stat);}
 if(row.extra_ability)assert(ids.includes(row.extra_ability));
}
assert.equal(get(a.get('Frsp'),'atar',1),'ground,air,friend,nonhero,nonstructure,vuln,invu');near(get(a.get('Frsp'),'Oae2',1),.15,'Relic army haste');
const changedAbilities=new Set([...Object.keys(b.aura_balance),'Fhas','Fmrg','Clif']);
for(const h of heroes)for(const[slot,raw]of h.skills.entries())if(changedAbilities.has((h.skill_sources||h.skills)[slot])||['army_vamp','army_speed','army_armor','banner'].includes(h.simple?.[slot]?.kind))changedAbilities.add(raw);
for(const[raw,prev]of oldA)if(!changedAbilities.has(raw))assert.deepEqual(a.get(raw),prev,'Unchanged prior ability '+raw);
for(const[raw,defs]of Object.entries(b.aura_balance))for(const[field,spec]of Object.entries(defs))for(const rank of[1,5,10,25,50,200])assert(get(a.get(raw),field,rank)>get(oldA.get(raw),field,rank),'Stronger aura already at reachable ranks '+raw+':'+rank);
assert.equal(a.get('Frss').oldId,'ANss');assert.equal(get(a.get('Frss'),'acdn',1),25);
for(const raw of['Frsp','Frat','Frdf','Frrs'])assert(get(a.get(raw),'atar',1).includes('nonstructure'),'Never buff/heal towers or barracks via '+raw);
assert.equal(get(a.get('Frrs'),'Ihps',1),4000);assert.equal(get(a.get('Frrs'),'Imps',1),1800);assert(!get(a.get('Frrs'),'atar',1).includes('organic'));
assert.equal(get(a.get('Friv'),'adur',1),3);assert.equal(get(a.get('Friv'),'acdn',1),75);
assert.equal(get(a.get('Frat'),'adur',1),15);near(get(a.get('Frat'),'Roa1',1),.6,'Assault boost');assert.equal(get(a.get('Frdf'),'Idef',1),16);
assert.equal(b.bot_tactics[3].gear_percent,55);assert.equal(b.bot_tactics[3].tier_percent,20);
fs.writeFileSync(path.join(root,'build/verification-023.json'),JSON.stringify({version:b.version,heroSlots:200,heroes:50,validatedNativeFields:fields,validatedProfileRankValues:curves,allSummonCountsPreserved:true,allResearchAndItemPricesPreserved:true,allScenarioAndRoutingPreserved:true,centralShops:2,newItems:8,auraValuesChecked:auraValues,carryGearPercent:55,carryArmyPercent:45,frontTowers:{hp:40000,damage:250,cooldown:.5},classicMetadataChecked:true,enginePlaytest:false},null,2)+'\n');
console.log('PASS:current0.23 balance profiles,all200 skills,Classic types,aura progression,two native stores,eight items,55/45 budgets and preserved world/economy/counts.');
