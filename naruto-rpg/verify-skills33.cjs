// Independently compare the shipped archive and source/native fields with Alpha32.
const fs=require('fs'),assert=require('node:assert/strict'),crypto=require('crypto');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default,U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const root=__dirname,prior=new MapFile(),current=new MapFile(),file=fs.readFileSync(root+'/dist/Shinobi_Story_Alpha_33.w3x');
prior.load(new Uint8Array(fs.readFileSync(root+'/../releases/shinobi-new/Shinobi_Story_Alpha_32.w3x')),true);current.load(new Uint8Array(file),true);
const old=n=>Buffer.from(prior.get(n).bytes()),now=n=>Buffer.from(current.get(n).bytes()),read=n=>JSON.parse(fs.readFileSync(root+'/src/'+n));
assert.deepEqual(current.getFileNames().sort(),prior.getFileNames().sort());
for(const n of current.getFileNames())if(!['war3map.j','war3map.w3i','war3map.w3a','war3map.w3u'].includes(n))assert.deepEqual(now(n),old(n),n+' unchanged, including all music/models/voices');
assert.deepEqual(now('war3map.w3i'),Buffer.from(old('war3map.w3i').toString('latin1').replaceAll('SHINOBI STORY ALPHA 32','SHINOBI STORY ALPHA 33'),'latin1'));
function parse(C,b){const o=new C();o.load(new Uint8Array(b));return o;}
const before=parse(A,old('war3map.w3a')),after=parse(A,now('war3map.w3a')),map=new Map(after.customTable.objects.map(o=>[o.newId,o])),skills=read('playable-skills.json');
assert.deepEqual(before.originalTable,after.originalTable);assert.equal(after.customTable.objects.length,before.customTable.objects.length+1);
for(const a of before.customTable.objects){const b=map.get(a.newId);assert(b);if(a.newId==='RB04')continue;
 if(skills.some(r=>r.id===a.newId)){const omit=m=>!['ahky','arhk','atp1'].includes(m.id);assert.deepEqual(b.modifications.filter(omit),a.modifications.filter(omit),a.newId+' balance unchanged');}
 else if(a.newId==='Rlog'){assert.deepEqual(JSON.parse(JSON.stringify(b.modifications)),a.modifications.map(m=>({...m,value:m.id==='ahky'?'D':m.id==='atp1'?m.value.replace('[R]','[D]'):m.value})));}
 else assert.deepEqual(b,a,a.newId+' untouched');
}
for(const r of skills){const a=map.get(r.id);for(const key of ['ahky','arhk'])assert.equal(a.modifications.find(m=>m.id===key).value,'QWERF'[r.slot]);for(const m of a.modifications.filter(m=>m.id==='atp1'))assert(m.value.includes('['+r.key+']'));}
const source=read('forest33-source.json'),wind=source.abilities.find(a=>a.newId==='A00V'),actual=map.get('RB04');assert.equal(actual.oldId,'ANst');
const get=(a,id,rank=0)=>a.modifications.find(m=>m.id===id&&m.levelOrVariation===rank)?.value;
for(const id of ['Nst1','Nst2','Nst3','Nst4','amat','amsp','aare','adur','ahdu','amcs','acdn','aran','atar'])for(let rank=1;rank<=3;rank++){
 const global=['amat','amsp'].includes(id),n=global?0:rank,original=wind.modifications.find(m=>m.id===id&&m.levelOrVariation===n);
 if(original)assert.equal(get(actual,id,n),original.value,'Original wind field '+id+'/'+n);
}
const bu=parse(U,old('war3map.w3u')),au=parse(U,now('war3map.w3u'));assert.deepEqual(bu.originalTable,au.originalTable);assert.equal(au.customTable.objects.length,bu.customTable.objects.length+1);
for(const a of bu.customTable.objects)assert.deepEqual(au.customTable.objects.find(b=>b.newId===a.newId),a,a.newId+' stats/models unchanged');assert(au.customTable.objects.some(a=>a.newId==='vchi'));
const funcs=s=>new Map([...s.matchAll(/^function (\w+) takes[^]*?^endfunction/gm)].map(m=>[m[1],m[0]])),a=funcs(old('war3map.j').toString()),b=funcs(now('war3map.j').toString());
const changed=new Set(['VisualClearHero','VisualPulse','VisualApply','VisualTick','SkillsEffect','SkillsTick','SkillsData11','ExamStartForest','ExamNearest','ExamForestTick','CampaignClear','CampaignClonesTick','CampaignSpawnStage','CampaignLateProgress','CampaignTick','config']);
for(const[n,code]of a){assert(b.has(n));if(n==='FoundationInit'){const withoutNames=s=>s.split('\n').filter(l=>!l.includes('set SkillName[')).join('\n');assert.equal(withoutNames(b.get(n)),withoutNames(code));}else if(!changed.has(n))assert.equal(b.get(n),code,n+' unchanged');}
assert.deepEqual([...b.keys()].filter(k=>!a.has(k)).sort(),['VisualLineFan','VisualApproachTick','ExamKabutoClear','ExamKabutoTick','CampaignSurvivors','ExamKabutoDropScrolls','ExamKabutoKill','ExamKabutoSetup'].sort());
assert(b.get('ExamStartForest').includes('ExamKabutoAt=TimeNow+540.'));assert(b.get('ExamKabutoTick').includes('ExamKabutoAt=0.'));assert(!b.get('CampaignLateProgress').includes('CampaignNarutoPlayer>=0'));assert(!b.get('CampaignTick').includes('CampaignNarutoPlayer>=0 and not FoundationAlive'));
assert(b.get('CampaignLateProgress').includes('call CampaignQueueStage(26)'));assert(b.get('CampaignLateProgress').includes('call CampaignQueueStage(CampaignStage+1)'));assert(!b.has('CampaignKabutoRescue'));assert(b.get('CampaignClonesTick').includes('CampaignX[17],CampaignY[17]'));assert(b.get('CampaignLateProgress').includes('CampaignAliveEnemies()==0 and not pending'));
const report={stage:33,filename:'Shinobi_Story_Alpha_33.w3x',bytes:file.length,sha256:crypto.createHash('sha256').update(file).digest('hex'),heroKeys:'QWERF',substitutionKey:'D',kabutoSourceSpawnSeconds:540,nativeTemariStampedeSourceFields:true,gaaraDamageAndShieldUnchanged:true,allOtherAbilityBalanceAndHeroUnitStatsUnchanged:true,sourceMusicAndVoiceBytesUnchanged:true,lateCampaignContinuesWithAnySurvivor:true,forestKabutoStealsActualScrolls:true,forestHeroesRespawnAfter20Seconds:true,cloneWinnersReturnToCaveEntrance:true,noStageJumpWhileCloneDuelsPending:true,existingCaveProgressionPreserved:true,cloneLosersNeverRevive:true,enginePlaytest:false};
fs.writeFileSync(root+'/dist/skills33-verification.json',JSON.stringify(report,null,2)+'\n');console.log('PASS: Alpha33 exact archive scope, QWERF/D, source wind fields and Kabuto timing, unchanged Gaara damage/all other skill balance/units/world/audio; late survivor gate.');
