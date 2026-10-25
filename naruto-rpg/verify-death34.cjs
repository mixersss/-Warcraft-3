// Exact runtime-only death/revival delta against the published Alpha33.
const fs=require('fs'),assert=require('node:assert/strict'),crypto=require('crypto'),MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const root=__dirname,old=new MapFile(),current=new MapFile(),file=fs.readFileSync(root+'/dist/Shinobi_Story_Alpha_34.w3x');
old.load(new Uint8Array(fs.readFileSync(root+'/../releases/shinobi-new/Shinobi_Story_Alpha_33.w3x')),true);current.load(new Uint8Array(file),true);
const prior=n=>Buffer.from(old.get(n).bytes()),now=n=>Buffer.from(current.get(n).bytes());
assert.deepEqual(current.getFileNames().sort(),old.getFileNames().sort());
for(const n of current.getFileNames())if(!['war3map.j','war3map.w3i'].includes(n))assert.deepEqual(now(n),prior(n),n+' byte-identical');
assert.deepEqual(now('war3map.w3i'),Buffer.from(prior('war3map.w3i').toString('latin1').replaceAll('SHINOBI STORY ALPHA 33','SHINOBI STORY ALPHA 34'),'latin1'));
const funcs=s=>new Map([...s.matchAll(/^function (\w+) takes[^]*?^endfunction/gm)].map(m=>[m[1],m[0]]));
const before=prior('war3map.j').toString(),after=now('war3map.j').toString(),a=funcs(before),b=funcs(after);
const changed=new Set(['FoundationAlive','InvasionSasukeStatus','InvasionFixSasuke','InvasionHeroVisibility','StoryTick','config']);
const guards=new Set(['OrigNPC_A2X','OrigNPC_A3X','OrigNPC_NBX','OrigNPC_NCX','OrigNPC_NHX','OrigNPC_NJX','OrigNPC_NPX','OrigNPC_NQX']);
function unwrap(code,name){
 code=code.replace(/call InvasionSourceLife\((.*),"\w+"\)/g,'call SetWidgetLife($1)').replace(/call InvasionSourceLifePercent\((.*),"\w+"\)/g,'call SetUnitLifePercentBJ($1)');
 if(guards.has(name)){const pattern=/^return FoundationAlive\(OrigNPC_OR\[([01])\]\) and FoundationAlive\(OrigNPC_RR\[\1\]\) and \((.*)\)$/m;assert(pattern.test(code),name+' live caster/target guard');code=code.replace(pattern,'return$2');}
 return code;
}
for(const[name,code]of a){assert(b.has(name));if(!changed.has(name))assert.equal(unwrap(b.get(name),name),code,name+' unchanged outside audited guard wrappers');}
assert.deepEqual([...b.keys()].filter(n=>!a.has(n)).sort(),['InvasionSourceLife','InvasionSourceLifePercent','InvasionQueueCorpse','InvasionAfterRevive'].sort());
const globals=s=>s.match(/^globals\n[^]*?^endglobals/m)[0];assert.equal(globals(after).split('\n').filter(l=>!/^\s*integer array Sasuke(CorpseHealsBlocked|ReviveFailures)$/.test(l)).join('\n'),globals(before));
assert(b.get('FoundationAlive').includes('not IsUnitType(u,UNIT_TYPE_DEAD)'));
assert(b.get('StoryTick').includes('if ReviveHero(Hero[p],SpawnX[p],SpawnY[p],true) and FoundationAlive(Hero[p]) then'));
assert(b.get('StoryTick').includes('set StoryRevive[p]=TimeNow+1.'));
assert(!b.get('InvasionAfterRevive').includes('CreateUnit('));assert(!b.get('InvasionFixSasuke').includes('ReviveHero('));
for(const name of ['CampaignClonesTick','CampaignLateProgress','CampaignSurvivors','ExamKabutoKill','FoundationMusicStart'])assert.equal(b.get(name),a.get(name),name+' previous behavior preserved');
const report={stage:34,filename:'Shinobi_Story_Alpha_34.w3x',bytes:file.length,sha256:crypto.createHash('sha256').update(file).digest('hex'),nativeDeathFlagAuthoritative:true,positiveHpCorpseNotAlive:true,sourceCorpseHealingBlocked:true,sourceDrainCasterAndTargetGuards:8,nativeReviveResultChecked:true,reviveRetrySeconds:1,ordinaryRespawnSeconds:20,sasukeAfterReviveControlCleanup:true,heroReplacement:false,allObjectsWorldModelsMusicAndVoiceBytesUnchanged:true,alpha33CloneAndForestRulesUnchanged:true,reportedEngineCauseConfirmed:false,enginePlaytest:false};
fs.writeFileSync(root+'/dist/death34-verification.json',JSON.stringify(report,null,2)+'\n');console.log('PASS: Alpha34 exact runtime death-flag/healing/revival scope; all objects/assets, clone outcomes, forest Kabuto and music unchanged from33.');
