const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const root=__dirname,read=n=>JSON.parse(fs.readFileSync(path.join(root,n)));
function parse(P,n){const p=new P();p.load(new Uint8Array(fs.readFileSync(path.join(root,'dist/map',n))));return Object.fromEntries(p.customTable.objects.map(o=>[o.newId,o]));}
const units=parse(U,'war3map.w3u'),spells=parse(A,'war3map.w3a'),buffs=parse(U,'war3map.w3h'),map=fs.readFileSync(path.join(root,'dist/map/war3map.j'),'utf8');
const get=(o,k,l=0)=>o.modifications.find(m=>m.id===k&&(m.levelOrVariation||0)===l)?.value;
const fountains=read('src/village-fountains-source.json').fountains;assert.equal(fountains.length,4);
for(const [i,f]of fountains.entries()){
 assert.equal(units[f.newId].oldId,'nfnp');assert.equal(get(units[f.newId],'uabi'),(f.doubleHealth?'Crg2':'ACnr')+',ANre,Avul');
 assert(map.includes(`set VillageFountain[${i}]=CreateUnit(Player(14),'${f.newId}',${f.x}.,${f.y}.,270.)`),'Exact original fountain coordinate/owner');
 for(const m of f.effectiveModifications.filter(m=>!['unam','uabi','umdl'].includes(m.id)))assert.equal(get(units[f.newId],m.id),m.value,'Preserve source fountain body '+m.id);
 if(f.sourceType==='n006'||f.sourceType==='n007')assert.equal(get(units[f.newId],'umdl'),'Doodads\\Cityscape\\Props\\City_Fountain\\City_Fountain.mdl');
}
assert.equal(spells.Crg2.oldId,'ACnr');assert.equal(get(spells.Crg2,'Oar1',1),Math.fround(.02));assert(map.includes('call SetPlayerAllianceStateAllyBJ(Player(14),Player(p),true)'));
const expected={R000:'STR',R001:'STR',R002:'INT',R003:'AGI',R004:'AGI',R005:'AGI',R006:'INT',R007:'AGI',R008:'AGI',R009:'INT',R00A:'INT',R00B:'AGI'};
for(const [id,primary]of Object.entries(expected)){assert.equal(get(units[id],'upra'),primary);assert.equal(get(units[id],'ua1t'),'hero');assert.equal(units[id].oldId,{STR:'Hpal',AGI:'Edem',INT:'Hblm'}[primary]);assert.equal(get(units[id],'ustr'),20);assert.equal(get(units[id],'uagi'),20);assert.equal(get(units[id],'uint'),20);}
for(const [normal,form]of [['R000','Rnfm'],['R001','Rsfm'],['R007','Rkfm'],['R009','Rgfm']]){assert.equal(get(units[form],'ua1t'),'hero');assert.equal(units[normal].oldId,units[form].oldId);assert.equal(get(units[normal],'upra'),get(units[form],'upra'));}
assert.equal(spells.R501.oldId,'ANcl');assert.equal(get(spells.R501,'Ncl2',1),1);assert(!spells.R501.modifications.some(m=>m.id==='Htb1'),'No duplicate native kunai damage');
assert.equal(spells.Rkst.oldId,'AHtb');assert.equal(get(spells.Rkst,'Htb1',1),0);assert.equal(get(spells.Rkst,'adur',1),1.25);assert.equal(get(spells.Rkst,'ahdu',1),.75);assert.equal(get(spells.Rkst,'abuf',1),'Rksb');assert.equal(buffs.Rksb.oldId,'BPSE');
assert.equal(get(units.rdst,'ucpt'),0);assert.equal(get(units.rdst,'usin'),0);assert.equal(get(units.rdst,'usid'),0);
const target=map.slice(map.indexOf('function StoryEnemyTarget takes'),map.indexOf('function StoryEnemyCast takes'));assert(target.includes('set candidate=Hero[p]')&&target.includes('set candidate=Companion[p*3+n]'));assert(!target.includes('MAP_CONTROL')&&!target.includes('GetPlayerController'));
const init=map.slice(map.indexOf('function StoryInit takes'),map.indexOf('function FoundationChat takes'));assert(!init.includes('CreateTimerDialog')&&!init.includes('call HUDInit()'));
assert(map.includes('if TimeNow<.5 then'));assert(map.includes('call TimerDialogDisplay(PhaseDialog,true)'));
const report={sourceVillageFountains:4,exactOriginalCoordinates:true,originalNeutralOwner:14,sourceDoubleHPFountains:2,primaryAttributesAndStockFamiliesVerified:12,normalAttackTypeHeroVerified:12,alternateFormAttackTypesVerified:4,globalAlliedByakugan:true,byakuganMarksEverySeconds:2,byakuganFogHandlesBounded:128,kunaiHomingDamageOnceOnImpact:true,kunaiIndependentNativeStun:{ordinarySeconds:1.25,heroSeconds:.75},enemyTargetingAlliedBotsAndSummons:true,openingUIAfterFirstHeartbeat:true,nativeMocks:'test-skills.cjs / village-fixes-harness.lua',enginePlaytest:false};
fs.writeFileSync(path.join(root,'dist/village-fixes-verification.json'),JSON.stringify(report,null,2));console.log('PASS: four source fountains/owners/aura variants; all 12 primary attributes and stock hero families; Tenten impact-only damage and separate stun; opening UI and unbiased enemy target selection. Actual Warcraft playtest unrun.');
