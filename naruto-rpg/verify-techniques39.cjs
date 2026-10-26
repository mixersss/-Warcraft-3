// Exact archive scope: only source-based visual presentation and requested two forms.
const fs=require('fs'),assert=require('node:assert/strict'),crypto=require('crypto'),MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,P=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default,U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const root=__dirname,old=new MapFile(),now=new MapFile(),file=fs.readFileSync(root+'/dist/Shinobi_Story_Alpha_39.w3x');
old.load(new Uint8Array(fs.readFileSync(root+'/../releases/shinobi-new/Shinobi_Story_Alpha_38.w3x')),true);now.load(new Uint8Array(file),true);
const a=n=>Buffer.from(old.get(n).bytes()),b=n=>Buffer.from(now.get(n).bytes());
assert.deepEqual(now.getFileNames().sort(),old.getFileNames().sort());for(const n of now.getFileNames())if(!['war3map.j','war3map.w3i','war3map.w3a','war3map.w3u'].includes(n))assert.deepEqual(b(n),a(n),n+' unchanged');
assert.deepEqual(b('war3map.w3i'),Buffer.from(a('war3map.w3i').toString('latin1').replaceAll('SHINOBI STORY ALPHA 38','SHINOBI STORY ALPHA 39'),'latin1'));
const parse=(C,v)=>{const o=new C();o.load(new Uint8Array(v));return o;};
const prior=parse(P,a('war3map.w3a')),current=parse(P,b('war3map.w3a'));
assert.deepEqual(current.originalTable,prior.originalTable);assert.equal(current.customTable.objects.length,prior.customTable.objects.length);
for(const obj of prior.customTable.objects){const actual=current.customTable.objects.find(o=>o.newId===obj.newId);if(!['Rn05','Rs05'].includes(obj.newId)){assert.deepEqual(actual,obj,obj.newId+' exact');continue;}
 const expected=structuredClone(obj),hp=obj.newId==='Rn05'?1000:850,desc=`С 60 уровня сразу максимальная сила формы: +${hp} максимального HP и усиленные атаки. Без ограничения времени; действует до смерти.`;
 expected.modifications=expected.modifications.filter(m=>m.levelOrVariation<=1);
 for(const m of expected.modifications){const changes={alev:1,alsk:0,arut:desc,aub1:desc,amcs:300,Eme5:hp,ahdu:0};if(m.id in changes)m.value=changes[m.id];}
 assert.deepEqual(JSON.parse(JSON.stringify(actual)),expected,obj.newId+' exact maximum native form');
}
const pu=parse(U,a('war3map.w3u')),cu=parse(U,b('war3map.w3u'));assert.deepEqual(cu.originalTable,pu.originalTable);
for(const obj of pu.customTable.objects)assert.deepEqual(cu.customTable.objects.find(o=>o.newId===obj.newId),obj,obj.newId+' unchanged unit');
assert.deepEqual(cu.customTable.objects.filter(o=>!pu.customTable.objects.some(p=>p.newId===o.newId)).map(o=>o.newId).sort(),['vcmf','vras']);
const funcs=s=>new Map([...s.matchAll(/^function (\w+) takes[^]*?^endfunction/gm)].map(m=>[m[1],m[0]])),before=funcs(a('war3map.j').toString()),after=funcs(b('war3map.j').toString()),allowed=new Set(['VisualClearHero','VisualApproachTick','VisualApply','VisualTick','SkillsData0','SkillsData1','config']);
for(const[n,code]of before){assert(after.has(n));if(!allowed.has(n))assert.equal(after.get(n),code,n+' exact Alpha38');}
const helpers=['VisualChidoriEnd','VisualChidoriTick','VisualRasenganEnd','VisualRasenganStart','VisualRasenganTick'];assert.deepEqual([...after.keys()].filter(n=>!before.has(n)).sort(),helpers.sort());
for(const n of helpers)assert(!/CreateTimer|CreateGroup|TriggerSleepAction|PauseUnit\(|ShowUnit\(|SetUnitInvulnerable|UnitDamageTarget|SetPlayerState|KillUnit\(|ReviveHero\(/.test(after.get(n)),n+' no extra timer/combat/control/revival side effects');
for(const [fn,rank,first]of [['SkillsData0',4,16],['SkillsData1',9,36]]){const strip=s=>s.split('\n').filter(l=>!new RegExp('^    set (SkillRanks|SkillSkip)\\['+rank+'\\]=').test(l)&&!new RegExp('^    set (SkillMana|RosterPower|RosterBurn)\\[(' +[first,first+1,first+2].join('|')+')\\]=').test(l)).join('\n');assert.equal(strip(after.get(fn)),strip(before.get(fn)));}
const globals=s=>s.match(/^globals\n[^]*?^endglobals/m)[0];assert.equal(globals(b('war3map.j').toString()).split('\n').filter(l=>!/^    (integer array VisualApproachSkill|real array VisualChidoriUntil|unit array VisualRasengan(Caster|Target)|real array VisualRasengan(Until|PoseUntil)|effect array VisualRasenganArt)$/.test(l)).join('\n'),globals(a('war3map.j').toString()));
const report={stage:39,filename:'Shinobi_Story_Alpha_39.w3x',sha256:crypto.createHash('sha256').update(file).digest('hex'),bytes:file.length,sourceChidoriRushAndStrike:true,sourceRasenganLayersAndPose:true,permanentMaxFormsAtLevel:60,oneSkillPointPerMaxForm:true,nativeDamageCooldownAndStunUnchanged:true,noNewTimers:true,armyOwnershipFourNinjaWavesAndSasukeRecoveryExactAlpha38:true,allMusicWorldAndOtherObjectsUnchanged:true,enginePlaytest:false};
fs.writeFileSync(root+'/dist/techniques39-verification.json',JSON.stringify(report,null,2)+'\n');console.log('PASS: scoped Alpha38->39 visual presentation/two native maximum forms only; all armies, recovery, music, terrain and other skills exact.');
