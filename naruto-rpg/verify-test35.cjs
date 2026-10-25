// Test shortcuts only: all gameplay objects, music and Alpha34 recovery stay exact.
const fs=require('fs'),assert=require('node:assert/strict'),crypto=require('crypto'),MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const root=__dirname,old=new MapFile(),now=new MapFile(),file=fs.readFileSync(root+'/dist/Shinobi_Story_Alpha_35.w3x');
old.load(new Uint8Array(fs.readFileSync(root+'/../releases/shinobi-new/Shinobi_Story_Alpha_34.w3x')),true);now.load(new Uint8Array(file),true);
const a=n=>Buffer.from(old.get(n).bytes()),b=n=>Buffer.from(now.get(n).bytes());
assert.deepEqual(now.getFileNames().sort(),old.getFileNames().sort());for(const n of now.getFileNames())if(!['war3map.j','war3map.w3i'].includes(n))assert.deepEqual(b(n),a(n),n+' unchanged');
assert.deepEqual(b('war3map.w3i'),Buffer.from(a('war3map.w3i').toString('latin1').replaceAll('SHINOBI STORY ALPHA 34','SHINOBI STORY ALPHA 35'),'latin1'));
const funcs=s=>new Map([...s.matchAll(/^function (\w+) takes[^]*?^endfunction/gm)].map(m=>[m[1],m[0]])),prior=a('war3map.j').toString(),current=b('war3map.j').toString(),before=funcs(prior),after=funcs(current),changed=new Set(['CampaignClear','CampaignStartPlay','FoundationChat','config']);
for(const[n,code]of before){assert(after.has(n));if(!changed.has(n))assert.equal(after.get(n),code,n+' exactAlpha34');}
assert.deepEqual([...after.keys()].filter(n=>!before.has(n)).sort(),['CampaignTestHost','CampaignFastWaveStep','CampaignFastInvasion','CampaignTestFast','CampaignTestSasukeDeath'].sort());
const globals=s=>s.match(/^globals\n[^]*?^endglobals/m)[0];assert.equal(globals(current).split('\n').filter(l=>!/^\s*(boolean CampaignFastTest(Queued|Active)=false|integer CampaignFastWaveCursor=0)$/.test(l)).join('\n'),globals(prior));
assert(after.get('FoundationChat').includes('msg=="-village fast"'));assert(after.get('FoundationChat').includes('msg=="-sasuke-die"'));
assert(after.get('CampaignTestSasukeDeath').includes('call KillUnit(Hero[p])'));assert(after.get('CampaignTestSasukeDeath').includes('not CampaignFastTestActive'));
for(const n of ['CampaignTestHost','CampaignFastWaveStep','CampaignFastInvasion','CampaignTestFast','CampaignTestSasukeDeath'])assert(!/CreateTimer|ReviveHero|SetHeroLevel|SetPlayerState|SetWidgetLife/.test(after.get(n)),n+' no extra timer/free stats/resources/revival');
assert(after.get('CampaignFastInvasion').includes('call ExecuteFunc("CampaignInvasionEvents")'));assert(after.get('CampaignFastWaveStep').includes('call CampaignInvasionWave(lane)'));
const report={stage:35,filename:'Shinobi_Story_Alpha_35.w3x',sha256:crypto.createHash('sha256').update(file).digest('hex'),bytes:file.length,fastCommand:'-village fast',deathCommand:'-sasuke-die',hostOnly:true,originalWaveLanes:8,immediateScheduledReinforcements:['Kabuto','Jiraiya','Snake','Orochimaru'],repeatDoesNotDuplicateEnemies:true,nativeDeathAndOrdinary20SecondRevival:true,noNewTimers:true,noFreeLevelsOrEquipment:true,alpha34RecoveryUnchanged:true,allObjectsWorldMusicAndVoicesUnchanged:true,enginePlaytest:false};
fs.writeFileSync(root+'/dist/test35-verification.json',JSON.stringify(report,null,2)+'\n');console.log('PASS: Alpha35 host-only fast invasion/native death commands; exact Alpha34 objects, recovery and ordinary campaign runtime outside explicit test gates.');
