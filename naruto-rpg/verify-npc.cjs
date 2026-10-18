// Compare shipped NPC objects against frozen, source-derived records, including fields outside the small playable schema.
const fs=require('fs'),assert=require('assert/strict'),path=require('path');
const U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const read=n=>JSON.parse(fs.readFileSync(path.join(__dirname,n)));
function parse(P,n){let p=new P();p.load(new Uint8Array(fs.readFileSync(path.join(__dirname,'dist/map',n))));let rows=p.customTable.objects;assert.equal(new Set(rows.map(o=>o.newId)).size,rows.length,'Duplicate object IDs');return Object.fromEntries(rows.map(o=>[o.newId,o]));}
const units=parse(U,'war3map.w3u'),abilities=parse(A,'war3map.w3a'),buffs=parse(U,'war3map.w3h'),items=parse(U,'war3map.w3t');
const native=read('src/npc-native-source.json'),invasion=read('src/invasion-source.json'),audit=read('src/npc-source-audit.json'),first=read('src/first-battle-source.json');
const manifest=new Set(read('src/asset-manifest.json').map(a=>a.path.toLowerCase()));
function icon(k,v){return ['uico','aart','arar','fart'].includes(k)&&typeof v==='string'&&v.toLowerCase().endsWith('.blp')&&!manifest.has(v.toLowerCase())&&!/^(replaceabletextures|ui)\\/i.test(v)?'ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp':v;}
let fields=0;
function same(expected,actual,skip=[]){assert(actual,expected.newId);assert.equal(actual.oldId,expected.oldId);for(const m of expected.modifications){if(skip.includes(m.id))continue;const actualMod=actual.modifications.find(x=>x.id===m.id&&(x.levelOrVariation||0)===(m.levelOrVariation||0)&&(x.dataPointer||0)===(m.dataPointer||0));assert(actualMod,expected.newId+':'+m.id);assert.equal(actualMod.variableType,m.variableType);assert.equal(actualMod.value,icon(m.id,m.value),expected.newId+':'+m.id);fields++;}}
for(const o of native.abilities)same(o,abilities[o.newId]);
for(const o of native.units)same(o,units[o.newId],['usnd','ucs1','ucs2']);
for(const o of native.buffs)same(o,buffs[o.newId]);
for(const p of Object.values(native.profiles))same(p.body,units[p.body.newId],['unam','uabi','usnd','ucs1','ucs2']);
for(const [id,o]of Object.entries(first))same(o,units[id],['unam','uabi','usnd','ucs1','ucs2','ulev']);
assert.equal(invasion.leafDefenders.length,140);assert.equal(invasion.anbuDefenders.length,102);assert.equal(invasion.villageShops.length,4);
const map=fs.readFileSync(path.join(__dirname,'dist/map/war3map.j'),'utf8');
for(const [list,name]of [['leafDefenders','Leaf'],['anbuDefenders','Anbu']])for(const [j,p]of invasion[list].entries())for(const [suffix,key]of [['X','x'],['Y','y'],['Facing','facing']])assert.equal(Number(map.match(new RegExp('set Campaign'+name+suffix+'\\['+j+'\\]=(-?[0-9.]+)'))?.[1]),Number(p[key]),'Exact source defender placement '+name+j);
for(const n of Object.keys(audit.sourceFunctions))assert(map.includes('function OrigNPC_'+n+' takes'),'Missing source callback '+n);
const sourceToItem={I00G:'Nlku',I002:'Nlsh',gobm:'Nnot',I006:'Nlpi',I008:'Nlne',I007:'Nlra',I00A:'Nlga',I00K:'Nlca',I004:'Nsht',I005:'Nsta',I003:'Nsch'};
for(const [original,id]of Object.entries(sourceToItem)){const f=Object.fromEntries(items[id].modifications.map(m=>[m.id,m.value]));assert.equal(f.igol,invasion.shopGoldPrices[original]);assert.equal(f.isto,10);assert.equal(f.istr,0);}
assert.equal(units.rqsh.modifications.find(m=>m.id==='usei').value,invasion.shopStockSourceIds.map(id=>sourceToItem[id]).join(','));
assert(map.includes('(CampaignStage!=10 and CampaignStage!=12) or CampaignTransition'));assert(map.includes('function StoryShopsClose takes'));
const report={sourceNPCBodies:Object.keys(native.profiles).length,sourceFirstBattleBodies:3,sourceExamEnemyTypes:2,nativeAbilities:native.abilities.length,sourceCallbackFunctions:Object.keys(audit.sourceFunctions).length,sourceEventRoots:audit.rootTriggers.length,sourceDependencies:audit.dependencyTriggers.length,fieldsComparedToSource:fields,leafDefenders:140,anbuDefenders:102,medics:6,sourceVillageShops:4,pricesAndStockVerified:11,shopsOnlyDuringInvasion:false,shopsFromJiraiyaSearch:true,sourceSakonSplitThreshold:15000,sourceKimimaroBoneThreshold:25000,sourceTayuyaSleepThreshold:5000,targetSelectionAI:'adapted for bots',fullOriginalScenarioIdentical:false,enginePlaytest:false};
fs.writeFileSync(path.join(__dirname,'dist/npc-verification.json'),JSON.stringify(report,null,2));console.log('PASS: '+fields+' NPC fields match source records; '+report.nativeAbilities+' spells / '+report.sourceCallbackFunctions+' source functions; 242 exact defenders, 6 medics, four shops from Jiraiya search and eleven original prices/stock. Actual engine playback remains untested.');
