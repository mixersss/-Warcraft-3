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
run('EngineResearch={'+researches.map(o=>`[${raw(o.newId)}]={base=${get(o,'gglb')},step=${get(o,'gglm')},cap=${get(o,'glvl')}}`).join(',')+'}');
const ItemParser=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const itemData=new ItemParser();itemData.load(new Uint8Array(fs.readFileSync(path.join(__dirname,'../build/map/war3map.w3t'))));
run('EngineItems={'+itemData.customTable.objects.map(o=>`[${raw(o.newId)}]={cost=${get(o,'igol')}}`).join(',')+'}');
const unitsData=new ItemParser();unitsData.load(new Uint8Array(fs.readFileSync(path.join(__dirname,'../build/map/war3map.w3u'))));
run('EngineShops={'+unitsData.customTable.objects.filter(o=>/^fs[0-2]p$/.test(o.newId)).map(o=>`[${raw(o.newId)}]={${get(o,'usei').split(',').map(id=>`[${raw(id)}]=true`).join(',')}}`).join(',')+'}');
const abilities = parseObjects('war3map.w3a').originalTable.objects;
run('SkillCaps={'+abilities.map(o=>`[${raw(o.oldId)}]={cap=${get(o,'alev')},req=${get(o,'arlv')},skip=${get(o,'alsk')}}`).join(',')+'}');
run(fs.readFileSync(path.join(__dirname, 'gameplay-harness.lua'), 'utf8'));
console.log('PASS: JASS: shared native research queue/prices, 200-rank caps and bot progression, 16s waves, 4 races, 24 heroes with 300/50 skills, channels, summons, charm, elimination and revival (mock natives).');
