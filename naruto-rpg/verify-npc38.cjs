// Autonomous NPC ownership only; all combat/object/music data must stay exact.
const fs=require('fs'),assert=require('node:assert/strict'),crypto=require('crypto'),MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const root=__dirname,old=new MapFile(),now=new MapFile(),file=fs.readFileSync(root+'/dist/Shinobi_Story_Alpha_38.w3x');
old.load(new Uint8Array(fs.readFileSync(root+'/../releases/shinobi-new/Shinobi_Story_Alpha_37.w3x')),true);now.load(new Uint8Array(file),true);
const a=n=>Buffer.from(old.get(n).bytes()),b=n=>Buffer.from(now.get(n).bytes());
assert.deepEqual(now.getFileNames().sort(),old.getFileNames().sort());for(const n of now.getFileNames())if(!['war3map.j','war3map.w3i'].includes(n))assert.deepEqual(b(n),a(n),n+' unchanged');
assert.deepEqual(b('war3map.w3i'),Buffer.from(a('war3map.w3i').toString('latin1').replaceAll('SHINOBI STORY ALPHA 37','SHINOBI STORY ALPHA 38'),'latin1'));
let expected=a('war3map.j').toString().replaceAll('SHINOBI STORY ALPHA 37','SHINOBI STORY ALPHA 38');
const replace=(before,after)=>{assert(expected.includes(before),before);expected=expected.replace(before,after);};
replace('local integer owner=CampaignAttackerOwner[CampaignWaveRole[lane]]','local integer owner=PLAYER_NEUTRAL_PASSIVE');
replace('CampaignAdd(11,CampaignAttackerOwner[1],','CampaignAdd(11,PLAYER_NEUTRAL_PASSIVE,');
replace('CampaignAdd(36,CampaignAttackerOwner[2],','CampaignAdd(36,PLAYER_NEUTRAL_PASSIVE,');
replace('CampaignAdd(13,CampaignAttackOwner,','CampaignAdd(13,PLAYER_NEUTRAL_PASSIVE,');
replace('call SetUnitOwner(u,Player(CampaignAttackOwner),true)','call SetUnitOwner(u,Player(PLAYER_NEUTRAL_PASSIVE),true)');
const flags=`        call SetPlayerAlliance(Player(PLAYER_NEUTRAL_PASSIVE),Player(p),ALLIANCE_SHARED_CONTROL,false)
        call SetPlayerAlliance(Player(PLAYER_NEUTRAL_PASSIVE),Player(p),ALLIANCE_SHARED_ADVANCED_CONTROL,false)
`;
replace('        set allied=mode!=2 or HeroRole[p]<9',flags+'        set allied=mode!=2 or HeroRole[p]<9');
const cross=`    call SetPlayerAllianceStateAllyBJ(Player(13),Player(PLAYER_NEUTRAL_PASSIVE),mode!=2)
    call SetPlayerAllianceStateAllyBJ(Player(PLAYER_NEUTRAL_PASSIVE),Player(13),mode!=2)
    call SetPlayerAllianceStateVisionBJ(Player(13),Player(PLAYER_NEUTRAL_PASSIVE),false)
    call SetPlayerAllianceStateVisionBJ(Player(PLAYER_NEUTRAL_PASSIVE),Player(13),false)
`;
replace('    endloop\nendfunction\nfunction CampaignBindRoles','    endloop\n'+cross+'endfunction\nfunction CampaignBindRoles');
const oldSpawn=n=>[...a('war3map.j').toString().matchAll(new RegExp('^    set CampaignWaveSpawn'+n+'\\[(\\d+)\\]=(-?[0-9.]+)$','gm'))].map(m=>+m[2]);
const newSpawn=n=>[...b('war3map.j').toString().matchAll(new RegExp('^    set CampaignWaveSpawn'+n+'\\[(\\d+)\\]=(-?[0-9.]+)$','gm'))].map(m=>+m[2]);
for(const n of ['X','Y']){const src=oldSpawn(n),wanted=[];assert.equal(src.length,24);for(let lane=0;lane<8;lane++)wanted.push(...src.slice(lane*3,lane*3+3),src[lane*3+2]+(n==='X'?128:0));assert.deepEqual(newSpawn(n),wanted);}
const wave=expected.match(/^function CampaignInvasionWave takes[^]*?^endfunction/m)[0];replace(wave,wave.replace('exitwhen n>=3','exitwhen n>=4').replaceAll('lane*3+n','lane*4+n'));
const strip=s=>s.replace(/^    set CampaignWaveSpawn[XY]\[\d+\]=-?[0-9.]+\n/gm,'');
assert.equal(strip(b('war3map.j').toString()),strip(expected),'All other runtime exact Alpha37');
const report={stage:38,filename:'Shinobi_Story_Alpha_38.w3x',sha256:crypto.createHash('sha256').update(file).digest('hex'),bytes:file.length,autonomousLeafNPCOwner:13,autonomousSandNPCOwner:15,noPlayerSharedControl:true,reciprocalNPCArmyHostility:true,unitsPerWave:4,waveSchedulesUnchanged:true,allOtherRuntimeObjectsWorldMusicUnchanged:true,enginePlaytest:false};
fs.writeFileSync(root+'/dist/npc38-verification.json',JSON.stringify(report,null,2)+'\n');console.log('PASS: exact Alpha37 except autonomous attacker ownership and NPC army alliances, four-unit waves and spaced spawns/version.');
