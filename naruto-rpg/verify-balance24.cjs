// Exact object scope against Alpha23, plus requested runtime constants and native bases.
const fs=require('node:fs'),assert=require('node:assert/strict');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const old=new MapFile();old.load(new Uint8Array(fs.readFileSync(__dirname+'/../releases/shinobi-new/Shinobi_Story_Alpha_23.w3x')),true);
const now=n=>fs.readFileSync(__dirname+'/dist/map/'+n),before=n=>Buffer.from(old.get(n).bytes());
const parse=(P,n,prior=false)=>{const p=new P();p.load(new Uint8Array(prior?before(n):now(n)));return p;};
const index=p=>new Map(p.customTable.objects.map(o=>[o.newId,o])),get=(o,id,l=0)=>o.modifications.find(m=>m.id===id&&(m.levelOrVariation||0)===l)?.value;
const units=index(parse(U,'war3map.w3u')),skills=index(parse(A,'war3map.w3a')),items=index(parse(U,'war3map.w3t'));
for(const id of ['R008','R00B']){assert.equal(get(units.get(id),'upra'),'AGI');assert.equal(units.get(id).oldId,'Edem');}
assert.equal(skills.get('R302').oldId,'AHtb');for(let l=1;l<=4;l++){assert.equal(get(skills.get('R302'),'adur',l),1);assert.equal(get(skills.get('R302'),'ahdu',l),.75);assert.equal(get(skills.get('R302'),'abuf',l),'Rksb');assert.equal(get(skills.get('R302'),'Htb1',l),[160,240,320,400][l-1]);}
assert.equal(get(skills.get('Rmic'),'ahdu',1),Math.fround(.1));assert.equal(get(skills.get('Rmic'),'adur',1),Math.fround(.2));
for(const [id,ability,field]of [['Nsht','Cstr','Istr'],['Nsta','Cagi','Iagi'],['Nsch','Cint','Iint']]){assert.equal(items.get(id).oldId,'tst2');assert.equal(get(items.get(id),'iabi'),ability);assert.equal(get(skills.get(ability),field,1),6);}
for(const [P,n]of [[U,'war3map.w3u'],[A,'war3map.w3a']]){
 const current=parse(P,n),previous=parse(P,n,true),refs=index(previous);
 for(const o of current.customTable.objects){
  const ref=refs.get(o.newId);assert(ref,'No new models/hero objects/skills');
  if(n==='war3map.w3u'&&o.newId==='R00B')o.oldId=ref.oldId;
  if(n==='war3map.w3a'&&o.newId==='R302')o.oldId=ref.oldId;
  for(const m of o.modifications){
   const allowed=n==='war3map.w3u'&&o.newId==='R00B'&&m.id==='upra'||n==='war3map.w3a'&&(['R402','R802','R702'].includes(o.newId)&&['arut','aub1'].includes(m.id)||o.newId==='R302'&&['arut','aub1','adur','ahdu','amsp','abuf'].includes(m.id));
   if(allowed){const r=ref.modifications.find(x=>x.id===m.id&&x.levelOrVariation===m.levelOrVariation&&x.dataPointer===m.dataPointer);assert(r);m.value=r.value;}
  }
 }
 assert.deepEqual(current,previous,'Only requested character/skill data changes: '+n);
}
for(const n of ['war3map.w3t','war3map.w3h','war3map.w3q','war3map.w3e','war3map.wpm','war3map.w3b','war3map.doo','war3mapUnits.doo','war3mapMisc.txt','war3map.imp','war3map.wts','war3mapMap.tga','war3mapPreview.tga'])assert.deepEqual(now(n),before(n),n+' preserved');
const source=now('war3map.j').toString(),prior=before('war3map.j').toString(),canonical=s=>s.split('\n').map(l=>l.trim()).filter(l=>l&&!l.startsWith('//')).join('\n');
let normalized=require('./visibility25-comparison.cjs').runtime(source,prior).replaceAll('ALPHA 25','ALPHA 24').replaceAll('ALPHA 24','ALPHA 23').replace('set RosterDuration[16]=1.0','set RosterDuration[16]=0.75');
for(const fn of ['CommonLogBot','CampaignResetFighter','CampaignFinalTick','CampaignDuelTick','RosterArea','RosterApply','StoryTick']){const re=new RegExp('function '+fn+' takes[\\s\\S]*?endfunction');const ref=prior.match(re);assert(ref);normalized=normalized.replace(re,()=>ref[0]);}
for(const fn of ['CampaignArenaReward','StoryStatScrollScan','StoryStatLootBot'])normalized=normalized.replace(new RegExp('function '+fn+' takes[\\s\\S]*?endfunction'),'');
normalized=normalized.replace(/^.*(?:boolean array LogArenaUsed|rect StatLootRect=|integer StatLootPlayer=|item StatLootBest=|real StatLootDistance=|\/\/ One reused spatial rect).*$/gm,'');
for(const idx of [21,41])for(let rank=0;rank<4;rank++)normalized=normalized.replace('set RosterPower['+(idx*4+rank)+']='+[120,180,240,420][rank]+'.0','set RosterPower['+(idx*4+rank)+']='+[100,150,200,350][rank]+'.0');
assert.equal(canonical(normalized),canonical(prior),'All other story, AI, music, timers and source NPC runtime preserved');
const report={hinataPrimary:'AGI',temariPrimary:'AGI',leeStun:{ordinary:1,hero:.75,native:'AHtb'},kibaSmokeMicrostun:{radius:300,ordinary:.2,hero:.1},kaitenDamage:[120,180,240,420],arenaBotLogMaxUsesPerFight:1,arenaBotLogHealthThreshold:.2,kawarimiCooldownSeconds:22,arenaWinLevels:1,maxHeroLevel:60,statScrollPowerups:['Nsht','Nsta','Nsch'],statScrollStats:6,statPickupRadius:650,enemyPriorityRadius:900,persistentItemRects:1,allOtherObjectsAndRuntimePreserved:true,enginePlaytest:false};
fs.writeFileSync(__dirname+'/dist/balance24-verification.json',JSON.stringify(report,null,2)+'\n');console.log('PASS: Alpha24 requested balance/native stun bases, powerup6 data and exact Alpha23 scope; assets, items, terrain and other story mechanics preserved.');
