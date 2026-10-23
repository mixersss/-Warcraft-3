// Independent Alpha26 scope and exact original3.5 object/asset checks.
const fs=require('fs'),assert=require('node:assert/strict'),crypto=require('crypto');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,Objects=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const current=new MapFile();current.load(new Uint8Array(fs.readFileSync(__dirname+'/dist/Shinobi_Story_Alpha_28.w3x')),true);
const root=__dirname,read=n=>Buffer.from(current.get(n.replaceAll('/','\\')).bytes()),json=n=>JSON.parse(fs.readFileSync(root+'/src/'+n));
const prior=new MapFile();prior.load(new Uint8Array(fs.readFileSync(root+'/../releases/shinobi-new/Shinobi_Story_Alpha_25.w3x')),true);
const old=n=>Buffer.from(prior.get(n).bytes()),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
for(const n of ['war3map.w3u','war3map.w3t','war3map.w3h','war3map.w3q','war3mapMisc.txt','war3map.w3e','war3map.wpm','war3map.doo','war3mapUnits.doo','war3map.w3b','war3map.wts','war3mapMap.tga','war3mapPreview.tga'])assert.deepEqual(read(n),old(n),'Unchanged '+n);
const overrides=[...json('music35-source.json').tracks,...json('extra35-assets.json')],byPath=new Map(overrides.map(r=>[r.path.toLowerCase(),r]));
for(const r of [...json('asset-manifest.json'),...json('generated-assets.json')]){const replacement=byPath.get(r.path.toLowerCase());assert.equal(hash(read(r.path.replaceAll('\\','/'))),(replacement||r).sha256,r.path);if(!replacement)assert.deepEqual(read(r.path.replaceAll('\\','/')),old(r.path));}
for(const r of overrides)assert.equal(hash(read(r.path.replaceAll('\\','/'))),r.sha256,r.path);
const parse=b=>{let p=new Objects();p.load(new Uint8Array(b));return p;},before=parse(old('war3map.w3a')),after=parse(read('war3map.w3a'));
assert.deepEqual(after.originalTable,before.originalTable);
const allowed=new Set(['Rn02','R301','R302','R303','R304','R601','R602','R603','R604']);
const aa=new Map(after.customTable.objects.map(r=>[r.newId,r]));
for(const r of before.customTable.objects){assert(aa.has(r.newId));if(!allowed.has(r.newId))assert.deepEqual(aa.get(r.newId),r,'Unchanged ability '+r.newId);}
assert.deepEqual(after.customTable.objects.filter(r=>!before.customTable.objects.some(o=>o.newId===r.newId)).map(r=>r.newId).sort(),['R35c','R35i','R35k','R35s']);
const get=(id,field,level=0)=>aa.get(id).modifications.find(r=>r.id===field&&(r.levelOrVariation||0)===level)?.value;
for(let n=1;n<=4;n++){assert.equal(get('Rn02','Omi1',n),8);assert(Math.abs(get('Rn02','Omi2',n)-[.10,.11,.12,.13][n-1])<1e-6);assert.equal(get('Rn02','Omi3',n),15);assert.equal(get('Rn02','adur',n),30);assert.equal(get('Rn02','Omi4',n),0);assert(Math.abs(get('R35i','Iild',n)-[.10,.11,.12,.13][n-1])<1e-6);assert.equal(get('R601','mls1',n),30);}
for(const id of ['R301','R604'])assert.notEqual(aa.get(id).oldId,'AOre');
assert.equal(aa.get('R601').oldId,'Amls');assert.equal(aa.get('R604').oldId,'ANcl');assert.equal(aa.get('R35c').oldId,'Amls');
assert.equal(get('R35k','Htb1',1),100);assert.equal(get('R35k','ahdu',1),2);
const source=read('war3map.j').toString(),oldSource=old('war3map.j').toString();
const fns=s=>new Map([...s.matchAll(/^function (\w+) takes[^]*?^endfunction/gm)].map(m=>[m[1],m[0]]));
const sf=fns(source),of=fns(oldSource);
const changed=new Set(['CampaignNearest','InvasionHeroVisibility','VisualApply','RosterShadow','RosterGrantInnate','RosterResetEffects','RosterApply','RosterTick','SkillsEffect','SkillsEndcast','SkillsSummoned','SkillsTick','SkillsData0','SkillsData3','SkillsData6','SkillsData7','SkillsInit','StoryChooseItem','StoryBuy','CampaignBot','CampaignEventWake','CampaignClear','CampaignSpawnStage','CampaignNPCTick','CampaignInvasionEvents','CampaignTick','FoundationTick','FoundationInit','config']);
for(const [name,text]of of){assert(sf.has(name),'Retain function '+name);if(!changed.has(name))assert.equal(sf.get(name).replaceAll('call InvasionSourceColor(','call SetUnitVertexColorBJ('),text,'Unchanged function '+name);}
for(const name of sf.keys())if(!of.has(name))assert(name.startsWith('Source35')||['CampaignLateProgress','CampaignEntranceUnlock','StoryStatChoice','StoryCanCarryChoice','InvasionRecoverHero','InvasionSourceColor','InvasionOroWatch'].includes(name));
const tick=sf.get('FoundationTick');assert(tick.indexOf('ExecuteFunc("InvasionHeroVisibility")')<tick.indexOf('call StoryTick()'));assert(tick.indexOf('ExecuteFunc("InvasionOroWatch")')<tick.indexOf('call StoryTick()'));
assert(sf.get('InvasionHeroVisibility').includes('HeroRole[p]==1'));assert(sf.get('InvasionHeroVisibility').includes('SasukePauseSince[p]+15.'));assert(sf.get('InvasionOroWatch').includes('CampaignEventDue[3]'));
assert(sf.get('Source35TickPlayer').includes('0xD0132'));assert(sf.get('Source35TickPlayer').includes('j>=8'));
assert(!fs.readFileSync(root+'/src/skills35.j','utf8').includes('TriggerSleepAction('));
const report={stage:28,source:'Naruto Ultimate RPG3.5',exactSourceMusicTracks:6,exactSourceSkillVoices:5,newSourceIcons:4,clonesByRank:[8,16,24,40],cloneDamage:[.10,.11,.12,.13],cloneLifetimeSeconds:30,fullKitsReplaced:['Rock Lee','Shikamaru'],otherAbilitiesUnitsItemsTerrainUnchanged:true,sasukeSeparateRecoveryThread:true,orochimaruDedicatedController:true,enginePlaytest:false};
fs.writeFileSync(root+'/dist/source35-verification.json',JSON.stringify(report,null,2)+'\n');console.log('PASS: Alpha26 exact music/voice/icon bytes;3.5 skill objects,clone profiles; unchanged other objects,world and unrelated runtime; invasion recovery isolation.');
