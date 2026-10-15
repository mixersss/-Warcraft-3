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
run(fs.readFileSync(path.join(__dirname, 'gameplay-harness.lua'), 'utf8'));
console.log('PASS: shipped JASS trigger logic: purchases, upgrade caps, bot economy, wave caps, bounties, team elimination and hero revival (mock natives).');
