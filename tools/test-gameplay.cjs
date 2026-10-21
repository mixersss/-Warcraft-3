// Execute the shipped JASS economy/spawn/death functions after translation to Lua.
// Native mocks validate trigger decisions, not Warcraft combat/pathfinding/networking.
const fs = require('node:fs');
const path = require('node:path');
const { lua, lauxlib, lualib, to_luastring, to_jsstring } = require('fengari');
const jass2lua = require('mdx-m3-viewer/dist/cjs/utils/jass2/jass2lua').default;
const source = fs.readFileSync(path.join(__dirname, '../build/map/war3map.j'), 'utf8');
const L = lauxlib.luaL_newstate();
lualib.luaL_openlibs(L);
function run(code) {
  const status = lauxlib.luaL_dostring(L, to_luastring(code));
  if (status !== lua.LUA_OK) throw new Error(to_jsstring(lua.lua_tostring(L, -1)));
}
// This translator drops the separating space after "not" inside return/exitwhen
// expressions. Restore that token boundary (all map identifiers use capitals).
const translated = jass2lua(source).replace(/\bnot(?=[A-Z(])/g, 'not ');
run(translated);
const defaults = [];
for (const match of source.matchAll(/^\s*(integer|real|boolean) array (\w+)\s*$/gm)) {
  defaults.push(`setmetatable(${match[2]}, {__index=function() return ${match[1] === 'boolean' ? 'false' : '0'} end})`);
}
run(defaults.join('\n'));
// Read prices and skill requirements from the emitted object data, independently
// of UpgradeCost()/LearnHero(), so disagreements with native command-card data fail.
const ObjectParser = require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const parseObjects = file => {
  const p = new ObjectParser();p.load(new Uint8Array(fs.readFileSync(path.join(__dirname,'../build/map',file))));return p;
};
const get = (o,id) => o.modifications.find(m=>m.id===id && m.levelOrVariation===0)?.value;
const raw = id => [...id].reduce((v,c)=>v*256+c.charCodeAt(0),0);
const researches = parseObjects('war3map.w3q').customTable.objects;
run('EngineResearch={'+researches.map(o=>{
 const req=o.modifications.find(m=>m.id==='greq' && m.levelOrVariation===1)?.value;
 const count=o.modifications.find(m=>m.id==='grqc' && m.levelOrVariation===1)?.value;
 return `[${raw(o.newId)}]={base=${get(o,'gglb')},step=${get(o,'gglm')},cap=${get(o,'glvl')},column=${get(o,'gbpx')},row=${get(o,'gbpy')}${req ? `,requires=${raw(req)},required=${Number(count)}` : ''}}`;
}).join(',')+'}');
const ItemParser=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const itemData=new ItemParser();itemData.load(new Uint8Array(fs.readFileSync(path.join(__dirname,'../build/map/war3map.w3t'))));
run('EngineItems={'+itemData.customTable.objects.map(o=>`[${raw(o.newId)}]={cost=${get(o,'igol')}}`).join(',')+'}');
// Classic native power-up bases, independent of the requested book descriptions.
const bookBases={tst2:'str',tdx2:'agi',tin2:'int',tkno:'level'};
run('EngineBooks={'+itemData.customTable.objects.filter(o=>bookBases[o.oldId]).map(o=>`[${raw(o.newId)}]="${bookBases[o.oldId]}"`).join(',')+'}');
const unitsData=new ItemParser();unitsData.load(new Uint8Array(fs.readFileSync(path.join(__dirname,'../build/map/war3map.w3u'))));
run('EngineShops={'+unitsData.customTable.objects.filter(o=>/^fs[0-4]p$/.test(o.newId) || o.newId==='fsup' || o.newId==='fpot' || o.newId==='fbks' || o.newId==='futl').map(o=>`[${raw(o.newId)}]={${get(o,'usei').split(',').map(id=>`[${raw(id)}]=true`).join(',')}}`).join(',')+'}');
run('EngineTroopTraits={'+unitsData.customTable.objects.filter(o=>/^fm[0-3][0-4]$/.test(o.newId)).map(o=>`[${raw(o.newId)}]={${(get(o,'uabi')||'').split(',').filter(Boolean).map(id=>raw(id)).join(',')}}`).join(',')+'}');
const abilityData=parseObjects('war3map.w3a');
const abilities=[...abilityData.originalTable.objects,...abilityData.customTable.objects.filter(o=>get(o,'aher')===1)];
run('SkillCaps={'+abilities.map(o=>`[${raw(o.newId==='\0\0\0\0' ? o.oldId : o.newId)}]={cap=${get(o,'alev')},req=${get(o,'arlv')},skip=${get(o,'alsk')}}`).join(',')+'}');
const profiles=require('../map/bot-profiles.json'),roster=require('../map/heroes.json');
run('EngineBotProfiles={'+roster.map((h,i)=>{const role=profiles.roles[profiles.heroes[h.id].role];return `[${i}]={role=${role.id},tactics={${role.tactics.join(',')}}}`;}).join(',')+'}');
run(fs.readFileSync(path.join(__dirname, 'gameplay-harness.lua'), 'utf8'));
run(fs.readFileSync(path.join(__dirname, 'patch14-harness.lua'), 'utf8'));
run(fs.readFileSync(path.join(__dirname, 'patch141-harness.lua'), 'utf8'));
run(fs.readFileSync(path.join(__dirname, 'patch15-harness.lua'), 'utf8'));
const OldMap=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,oldMap=new OldMap();oldMap.load(new Uint8Array(fs.readFileSync(path.join(__dirname,'../releases/FourFrontsFrenzy-0.15.1-alpha.w3x'))),true);
const hybridOld=new ObjectParser();hybridOld.load(new Uint8Array(oldMap.get('war3map.w3a').bytes()));
const hybridValues=[],hybridCases=[];
for(const [kind,id,field]of [[0,'AHhb','Hhb1'],[1,'AUdc','Udc1'],[2,'AEmb','Emb1']]){
 const object=hybridOld.originalTable.objects.find(o=>o.oldId===id);
 for(let rank=1;rank<=200;rank++)hybridValues.push(`[${kind*200+rank-1}]=${object.modifications.find(m=>m.id===field&&m.levelOrVariation===rank).value}`);
 const ids=[id,...roster.flatMap(h=>(h.skill_sources||[]).flatMap((base,n)=>base===id?[h.skills[n]]:[]))];
 for(const code of ids)hybridCases.push(`{kind=${kind},raw=${raw(code)}}`);
}
run('EngineHybridExpected={'+hybridValues.join(',')+'};EngineHybridCases={'+hybridCases.join(',')+'}');
run(fs.readFileSync(path.join(__dirname, 'patch152-harness.lua'), 'utf8'));
run(fs.readFileSync(path.join(__dirname, 'patch16-harness.lua'), 'utf8'));
run(fs.readFileSync(path.join(__dirname, 'patch18-harness.lua'), 'utf8'));
run(fs.readFileSync(path.join(__dirname, 'patch19-harness.lua'), 'utf8'));
run(fs.readFileSync(path.join(__dirname, 'patch20-harness.lua'), 'utf8'));
run(fs.readFileSync(path.join(__dirname, 'patch201-harness.lua'), 'utf8'));
run(fs.readFileSync(path.join(__dirname, 'patch21-harness.lua'), 'utf8'));

console.log('PASS: JASS: mixed open/computer/human startup, hero-only random mode, portrait selection, base defense, shared native research queue/prices, 200-rank caps and bot progression, 18s waves, 4 races, 50 heroes with 200/50 skills, channels, summons, charm, elimination and revival (mock natives).');
