const fs=require('fs'),{lua,lauxlib,lualib,to_luastring,to_jsstring}=require('fengari');
const L=lauxlib.luaL_newstate();lualib.luaL_openlibs(L);
let b=Buffer.concat([fs.readFileSync(__dirname+'/before.lua'),fs.readFileSync(process.argv[2]+'/MisScript/CharBornScript.lua'),fs.readFileSync(__dirname+'/after.lua')]);
let s=lauxlib.luaL_loadbuffer(L,b,b.length,to_luastring('starter-regression'));if(s===lua.LUA_OK)s=lua.lua_pcall(L,0,1,0);if(s!==lua.LUA_OK)throw Error(to_jsstring(lua.lua_tostring(L,-1)));
console.log('PASS:',lua.lua_tointeger(L,-1),'Lua assertions');
for(let p of ['MisScript/CharBornScript.lua','calculate/functions.lua']){let a=fs.readFileSync(process.argv[2]+'/'+p);let state=lauxlib.luaL_loadbuffer(L,a,a.length,to_luastring(p));if(state!==lua.LUA_OK)throw Error(to_jsstring(lua.lua_tostring(L,-1)));console.log('Syntax OK:',p);lua.lua_pop(L,1);}
