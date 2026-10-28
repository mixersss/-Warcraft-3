const fs=require('fs'),assert=require('node:assert/strict');
const {lua,lauxlib,lualib,to_luastring,to_jsstring}=require('fengari');
const translate=require('mdx-m3-viewer/dist/cjs/utils/jass2/jass2lua').default;
const source=fs.readFileSync(__dirname+'/dist/map/war3map.j','utf8');
const functions=[...source.matchAll(/^function (XH\w+) takes[^]*?^endfunction/gm)].map(m=>m[0]).join('\n');
const globals=source.match(/^globals\n[^]*?^endglobals/m)[0].split('\n').filter(l=>/^\s*(boolean|integer|real|unit|group) (array )?XH/.test(l));
const L=lauxlib.luaL_newstate();lualib.luaL_openlibs(L);
function run(s){if(lauxlib.luaL_dostring(L,to_luastring(s))!==lua.LUA_OK)throw Error(to_jsstring(lua.lua_tostring(L,-1)));}
run(fs.readFileSync(__dirname+'/test-natives.lua','utf8'));
run(translate('globals\n'+globals.join('\n')+'\nendglobals\n'+functions).replace(/\bnot(?=[A-Z(])/g,'not '));
run(`for _,name in ipairs({'XHPool','XHPurchases','XHBusy','XHCastAt','XHBuyAt','XHHealAt'})do _G[name]=setmetatable({},{__index=function()return 0 end})end;XHCreated={}`);
run(fs.readFileSync(__dirname+'/test-bots.lua','utf8'));
console.log('PASS: actual shipped JASS bot state machine under native mocks; engine combat/pathing and shop I/O remain untested.');
