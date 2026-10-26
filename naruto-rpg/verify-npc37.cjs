// Autonomous NPC ownership only; all combat/object/music data must stay exact.
const fs=require('fs'),assert=require('node:assert/strict'),crypto=require('crypto'),MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const root=__dirname,old=new MapFile(),now=new MapFile(),file=fs.readFileSync(root+'/dist/Shinobi_Story_Alpha_37.w3x');
old.load(new Uint8Array(fs.readFileSync(root+'/../releases/shinobi-new/Shinobi_Story_Alpha_36.w3x')),true);now.load(new Uint8Array(file),true);
const a=n=>Buffer.from(old.get(n).bytes()),b=n=>Buffer.from(now.get(n).bytes());
assert.deepEqual(now.getFileNames().sort(),old.getFileNames().sort());for(const n of now.getFileNames())if(!['war3map.j','war3map.w3i'].includes(n))assert.deepEqual(b(n),a(n),n+' unchanged');
assert.deepEqual(b('war3map.w3i'),Buffer.from(a('war3map.w3i').toString('latin1').replaceAll('SHINOBI STORY ALPHA 36','SHINOBI STORY ALPHA 37'),'latin1'));
let expected=a('war3map.j').toString().replaceAll('SHINOBI STORY ALPHA 36','SHINOBI STORY ALPHA 37');
const replace=(before,after)=>{assert(expected.includes(before),before);expected=expected.replace(before,after);};
replace('        set owner=CampaignLeader\n        if HeroRole[owner]>=9 then\n            set owner=PLAYER_NEUTRAL_AGGRESSIVE\n        endif\n        set CampaignDefenseOwner=owner','        set owner=13\n        set CampaignDefenseOwner=owner');
for(const kind of [37,38,28])replace(`CampaignAdd(${kind},CampaignLeader,`,`CampaignAdd(${kind},13,`);
const leaf=`        set allied=mode!=2 or HeroRole[p]<9
        call SetPlayerAllianceStateAllyBJ(Player(13),Player(p),allied)
        call SetPlayerAllianceStateAllyBJ(Player(p),Player(13),allied)
        call SetPlayerAllianceStateVisionBJ(Player(13),Player(p),allied)
        call SetPlayerAllianceStateVisionBJ(Player(p),Player(13),allied)
        call SetPlayerAlliance(Player(13),Player(p),ALLIANCE_SHARED_CONTROL,false)
        call SetPlayerAlliance(Player(13),Player(p),ALLIANCE_SHARED_ADVANCED_CONTROL,false)
`;
replace('        call SetPlayerAllianceStateAllyBJ(Player(14),Player(p),true)',leaf+'        call SetPlayerAllianceStateAllyBJ(Player(14),Player(p),true)');
const rogue=`    call SetPlayerAllianceStateAllyBJ(Player(13),Player(CampaignSasukePlayer),false)
    call SetPlayerAllianceStateAllyBJ(Player(CampaignSasukePlayer),Player(13),false)
    call SetPlayerAllianceStateVisionBJ(Player(13),Player(CampaignSasukePlayer),false)
    call SetPlayerAllianceStateVisionBJ(Player(CampaignSasukePlayer),Player(13),false)
`;
const marker='    loop\n        exitwhen p>=12\n        if p!=CampaignSasukePlayer then';replace(marker,rogue+marker);
assert.equal(b('war3map.j').toString(),expected,'All remaining runtime exact Alpha36');
const report={stage:37,filename:'Shinobi_Story_Alpha_37.w3x',sha256:crypto.createHash('sha256').update(file).digest('hex'),bytes:file.length,autonomousLeafNPCOwner:13,noPlayerSharedControl:true,defenderSandHostilityPreserved:true,rogueSasukeHostilityPreserved:true,combatObjectsWorldMusicUnchanged:true,alpha36TestLevelsAndDeathRecoveryUnchanged:true,enginePlaytest:false};
fs.writeFileSync(root+'/dist/npc37-verification.json',JSON.stringify(report,null,2)+'\n');console.log('PASS: exact Alpha36 except autonomous Leaf campaign ownership/alliances/version; all objects, world, music, recovery and level45 test unchanged.');
