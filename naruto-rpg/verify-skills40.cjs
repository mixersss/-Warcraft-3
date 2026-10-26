// Exact release boundary and independent native-object/source provenance checks.
const fs=require('fs'),assert=require('node:assert/strict'),crypto=require('crypto'),MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default,U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const root=__dirname,old=new MapFile(),now=new MapFile(),file=fs.readFileSync(root+'/dist/Shinobi_Story_Alpha_40.w3x');
old.load(new Uint8Array(fs.readFileSync(root+'/../releases/shinobi-new/Shinobi_Story_Alpha_39.w3x')),true);now.load(new Uint8Array(file),true);
const a=n=>Buffer.from(old.get(n).bytes()),b=n=>Buffer.from(now.get(n).bytes());
assert.deepEqual(now.getFileNames().sort(),old.getFileNames().sort());for(const n of now.getFileNames())if(!['war3map.j','war3map.w3i','war3map.w3a','war3map.w3u'].includes(n))assert.deepEqual(b(n),a(n),n+' exactAlpha39');
assert.deepEqual(b('war3map.w3i'),Buffer.from(a('war3map.w3i').toString('latin1').replaceAll('SHINOBI STORY ALPHA 39','SHINOBI STORY ALPHA 40'),'latin1'));
const objects=(C,buf)=>{const p=new C();p.load(new Uint8Array(buf));return p;},prior=objects(A,a('war3map.w3a')),next=objects(A,b('war3map.w3a'));
assert.deepEqual(next.originalTable,prior.originalTable);const spells=new Map(next.customTable.objects.map(o=>[o.newId,o]));
const altered=new Set(['Rs02','Rsag','R505','R702','R703','R803','RA04','RA05','RB05']);
for(const o of prior.customTable.objects)if(!altered.has(o.newId))assert.deepEqual(spells.get(o.newId),o,o.newId+' unchanged');
assert.deepEqual([...spells.keys()].filter(n=>!prior.customTable.objects.some(o=>o.newId===n)).sort(),['R40a','R40c','R40d','R40p','R40q','R40t','R40w'].sort());
const get=(id,f,l=0)=>spells.get(id).modifications.find(m=>m.id===f&&m.levelOrVariation===l)?.value;
const source=JSON.parse(fs.readFileSync(root+'/src/skills40-source.json'));
const sourceValue=(v,id,f,l)=>source[v].abilities[id].modifications.find(m=>m.id===f&&m.levelOrVariation===l)?.value;
const same=(id,v,original,fields,ranks)=>{for(let l=1;l<=ranks;l++)for(const f of fields)assert.equal(get(id,f,l),sourceValue(v,original,f,l),id+':'+f+'/'+l+' native source value');};
assert.equal(spells.get('R505').oldId,'ANcl');assert.equal(get('R505','amcs',1),600);assert.equal(get('R505','acdn',1),150);assert.equal(get('R505','Ncl1',1),8.25);
assert.equal(spells.get('R703').oldId,'AEme');same('R703','35','A01Q',['Eme5','ahdu','amcs','acdn'],3);
for(let l=1;l<=3;l++){assert.equal(get('R703','Eme1',l),'R007');assert.equal(get('R703','Emeu',l),'Rkfm');assert.equal(get('R40a','Iagi',l),[20,40,80][l-1]);assert.equal(get('Rsag','Iagi',l),[50,100,200][l-1]);}
assert.equal(spells.get('R803').oldId,'ANsi');same('R803','35','A01E',['amcs','acdn','aran'],3);for(let l=1;l<=3;l++)assert.equal(get('R803','aare',l),[200,275,350][l-1]);
assert.equal(spells.get('RA04').oldId,'AUin');same('RA04','35','A013',['amcs','acdn','Uin1','Uin2'],3);for(let l=1;l<=3;l++){assert.equal(get('RA04','Uin4',l),'rs0'+l);assert.equal(get('RA04','adur',l),0);assert.equal(get('RA04','ahdu',l),0);}
assert.equal(get('RA05','amcs',1),600);assert.equal(get('RA05','acdn',1),150);
assert.equal(spells.get('RB05').oldId,'AOsh');same('RB05','35','A027',['Osh1','Osh2','Osh3','aare','amcs','acdn','aran'],1);
assert.equal(spells.get('Rs02').oldId,'AOw2');same('Rs02','35','A01A',['amcs','acdn','Wrs1','aare'],3);
assert.equal(spells.get('R702').oldId,'ANc3');same('R702','35','A016',['Ncs1','Ncs2','Ncs3','Ncs4','Ncs6','amcs','acdn','aare'],4);
for(let l=1;l<=4;l++){assert.equal(get('R40c','Wrs1',l),[50,100,150,200][l-1]);assert.equal(get('R40c','aare',l),[200,400,600,800][l-1]);assert.equal(get('R40c','ahdu',l),Math.fround(.1));assert.equal(get('R40c','adur',l),Math.fround(.2));}
same('R40d','35','A02C',['Ndr1','Ndr2','Ndr3','adur','ahdu','aran'],1);
same('R40p','42','A02P',['Dda1','Dda2','Dda4','atar'],1);same('R40q','42','A02Q',['Min1','Min2','aran','atar'],1);
same('R40w','35','A025',['Nst1','Nst2','Nst3','Nst4','adur','ahdu','amat'],1);same('R40t','35','A00V',['Nst1','Nst2','Nst3','Nst4','adur','ahdu','amat'],1);
const pu=objects(U,a('war3map.w3u')),nu=objects(U,b('war3map.w3u'));assert.deepEqual(nu.originalTable,pu.originalTable);const units=new Map(nu.customTable.objects.map(o=>[o.newId,o]));for(const o of pu.customTable.objects)if(o.newId!=='Rkfm')assert.deepEqual(units.get(o.newId),o,o.newId+' unchanged');
assert.deepEqual([...units.keys()].filter(n=>!pu.customTable.objects.some(o=>o.newId===n)).sort(),['r40b','r40c','r40d','r40s','r40w'].sort());
const ug=(id,f)=>units.get(id).modifications.find(m=>m.id===f)?.value;assert.equal(ug('Rkfm','umdl'),'kiba.mdl');assert.equal(ug('Rkfm','uani'),'alternate');assert(ug('Rkfm','uhab').includes('R703'));assert.equal(ug('r40s','usca'),12);assert.equal(ug('r40s','umvh'),200);assert.equal(ug('r40s','uabi'),'Avul');assert.equal(ug('r40s','uaen'),0);assert.equal(ug('r40b','uabi'),'R40p,R40q,Aloc');
const funcs=s=>new Map([...s.matchAll(/^function (\w+) takes[^]*?^endfunction/gm)].map(m=>[m[1],m[0]])),pr=a('war3map.j').toString(),cur=b('war3map.j').toString(),pf=funcs(pr),nf=funcs(cur),changed=new Set(['VisualApply','VisualTick','RosterResetEffects','RosterApply','SkillsEffect','SkillsEndcast','SkillsSummoned','SkillsBot','SkillsData1','SkillsData5','SkillsData7','SkillsData8','SkillsData10','SkillsData11','SkillsInit','StoryTick','config']);
for(const[n,body]of pf){assert(nf.has(n));if(!changed.has(n))assert.equal(nf.get(n),body,n+' exactAlpha39');}
const extra=[...nf.keys()].filter(n=>!pf.has(n));assert(extra.every(n=>n.startsWith('Source40')||n==='VisualSource40Smoke'));
for(const n of extra)assert(!/CreateTimer|TimerStart|TriggerSleepAction|PauseUnit\(|ShowUnit\(|ReviveHero\(|SetUnitInvulnerable\(|SetPlayerState/.test(nf.get(n)),n+' no hidden/paused units, new timers or free resources/revival');
const globals=s=>s.match(/^globals\n[^]*?^endglobals/m)[0];assert.equal(globals(cur).split('\n').filter(l=>!/^    (group|hashtable|rect|real|integer|unit|boolean) (array )?Source40\w+/.test(l)).join('\n'),globals(pr));
assert(nf.get('StoryTick').includes('if TimeNow<VisualChannelUntil[p] then'));assert(nf.get('SkillsSummoned').includes('call Source40Adopt(p,summoned)'));assert(nf.get('Source40Tick').includes('ExecuteFunc("Source40PlayerTick")'));assert(nf.get('Source40PlayerTick').includes('Source40BallBudget[p]-.03'));
const report={stage:40,filename:'Shinobi_Story_Alpha_40.w3x',sha256:crypto.createHash('sha256').update(file).digest('hex'),bytes:file.length,sourceNativeSkillReplacement:true,controlledBallSeconds:7.5,tentenChargeSeconds:.75,hinataHelpersPerEnemy:[1,2,3],kibaMorphBonusHP:[50,100,200],kibaAgility:[20,40,80],kibaSmokeNativeDamage:[50,100,150,200],kibaSmokeMicrostunHeroes:.1,permanentSanshoNativeLandingDamage:[200,300,400],nativeBombsPerPuppet:6,sharinganAgility:[50,100,200],sharinganDurations:[8.5,10.5,12.5],temariNativeShockwaveDamage:2000,temariDistance:1800,temariStampedeAndAllOtherAbilitiesUnchanged:true,sourceSchedulingOnExistingVisualClock:true,noNewTimers:true,worldMusicVoicesArmyOwnershipWavesRecoveryExactAlpha39:true,enginePlaytest:false};
fs.writeFileSync(root+'/dist/skills40-verification.json',JSON.stringify(report,null,2)+'\n');console.log('PASS: exact Alpha39 archive outside eight roster replacements, hidden agility, native helpers/Kiba form/scoped runtime; independent original numeric data verified.');
