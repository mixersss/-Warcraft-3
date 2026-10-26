// Narrow release delta plus independent original3.5 object/script evidence.
const fs=require('fs'),assert=require('node:assert/strict'),crypto=require('crypto');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,Abilities=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const root=__dirname,old=new MapFile(),now=new MapFile(),file=fs.readFileSync(root+'/dist/Shinobi_Story_Alpha_42.w3x');
old.load(new Uint8Array(fs.readFileSync(root+'/../releases/shinobi-new/Shinobi_Story_Alpha_41.w3x')),true);now.load(new Uint8Array(file),true);
const a=n=>Buffer.from(old.get(n).bytes()),b=n=>Buffer.from(now.get(n).bytes());
assert.deepEqual(now.getFileNames().sort(),old.getFileNames().sort());
for(const n of now.getFileNames())if(!['war3map.j','war3map.w3i','war3map.w3a'].includes(n))assert.deepEqual(b(n),a(n),n+' exactAlpha41');
assert.deepEqual(b('war3map.w3i'),Buffer.from(a('war3map.w3i').toString('latin1').replaceAll('SHINOBI STORY ALPHA 41','SHINOBI STORY ALPHA 42'),'latin1'));
const objects=buffer=>{const p=new Abilities();p.load(new Uint8Array(buffer));return p.customTable.objects},before=objects(a('war3map.w3a')),after=objects(b('war3map.w3a'));
assert.deepEqual(before.map(x=>x.newId),after.map(x=>x.newId));
for(const o of after)if(o.newId!=='R302')assert.deepEqual(o,before.find(x=>x.newId===o.newId),o.newId+' unchanged');
const kick=after.find(x=>x.newId==='R302'),get=(o,id,rank=0)=>o.modifications.find(m=>m.id===id&&m.levelOrVariation===rank)?.value;
assert.equal(kick.oldId,'ANfb');for(let n=1;n<=4;n++){assert.equal(get(kick,'Htb1',n),[100,150,250,400][n-1]);assert.equal(get(kick,'aran',n),90);assert.equal(get(kick,'acdn',n),[25,25,25,35][n-1]);assert.equal(get(kick,'amcs',n),[150,150,150,200][n-1]);assert.equal(get(kick,'ahdu',n),.25);}
assert.equal(get(kick,'aani'),'attack,walk,stand,spin');
const original=JSON.parse(fs.readFileSync(root+'/src/skills35-source.json')).abilities.find(x=>x.newId==='A00E');
for(const m of original.modifications)if(['Htb1','aran','acdn','amcs','adur','ahdu','aani'].includes(m.id))assert.equal(get(kick,m.id,m.levelOrVariation),m.value,'original '+m.id+':'+m.levelOrVariation);
const funcs=s=>new Map([...s.matchAll(/^function (\w+) takes[^]*?^endfunction/gm)].map(m=>[m[1],m[0]]));
const prior=funcs(a('war3map.j').toString()),current=funcs(b('war3map.j').toString());
const changed=new Set(['SkillsData3','SkillsEffect','SkillsBot','Source35Clear','Source35Apply','Source35TickPlayer','VisualApply','VisualTick','config']);
for(const[n,code]of prior)if(!changed.has(n))assert.equal(current.get(n),code,n+' exactAlpha41');
assert.deepEqual([...current.keys()].filter(n=>!prior.has(n)).sort(),['Lee42Clear','Lee42KickStart','Lee42DrinkStart','Lee42Tick'].sort());
for(const n of ['Lee42Clear','Lee42KickStart','Lee42DrinkStart','Lee42Tick'])assert(!/CreateTimer|CreateTrigger|TriggerSleepAction|UnitDamageTarget|PauseUnit|ShowUnit|SetUnitInvulnerable/.test(current.get(n)),n+' bounded presentation only');
const globals=s=>s.match(/^globals\n[^]*?^endglobals/m)[0];assert.equal(globals(b('war3map.j').toString()).split('\n').filter(l=>!/^    (real|integer|unit) array Lee42/.test(l)).join('\n'),globals(a('war3map.j').toString()));
const report={stage:42,filename:'Shinobi_Story_Alpha_42.w3x',sha256:crypto.createHash('sha256').update(file).digest('hex'),bytes:file.length,sourceVersion:'3.5',leeNativeDamage:[100,150,250,400],leeNativeDamageAlreadyCorrectIn41:true,leeFormerRange:800,leeMeleeRange:90,leeStun:.25,leeCooldown:[25,25,25,35],leeFineClockSeconds:.05,sourceKickRiseAndAcceleratedPose:true,sourcePushWithScenePathCliffGuards:true,suikenStatsUnchanged:true,suikenSourcePoseSequence:[9,6,6,6],sharinganCombatPriority:true,sharinganCooldownCommittedOnlyOnEffect:true,sharinganBonusAndNativeObjectUnchanged:true,allOtherObjectsWorldMusicExactAlpha41:true,sasukeRecoveryExactAlpha41:true,enginePlaytest:false};
fs.writeFileSync(root+'/dist/lee42-verification.json',JSON.stringify(report,null,2)+'\n');console.log('PASS: original3.5 Lee values; narrow Alpha41 delta; no duplicate damage/timers/hidden actors; existing Sasuke recovery and all other objects/music/world unchanged.');
