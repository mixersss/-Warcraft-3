// Execute actual generated JASS through Lua; native calls are mocks, not engine tests.
const fs=require('node:fs');
const {lua,lauxlib,lualib,to_luastring,to_jsstring}=require('fengari');
const translate=require('mdx-m3-viewer/dist/cjs/utils/jass2/jass2lua').default;
const L=lauxlib.luaL_newstate();lualib.luaL_openlibs(L);
function run(s){if(lauxlib.luaL_dostring(L,to_luastring(s))!==lua.LUA_OK)throw Error(to_jsstring(lua.lua_tostring(L,-1)));}
const source=fs.readFileSync(__dirname+'/dist/map/war3map.j','utf8');
run(translate(source).replace(/\bnot(?=[A-Z(])/g,'not '));
run(`
debug.setmetatable('', {__add=function(a,b) return tostring(a)..tostring(b) end})
for _,a in ipairs({AnimCursor,AudioCursor,VoiceCursor,ResumeAt}) do setmetatable(a,{__index=function() return 0 end}) end
function Player(p) return p end
function GetTriggerPlayer() return 0 end
function GetPlayerId(p) return p end
function GetEventPlayerChatString() return Message end
function SubString(s,a,b) return string.sub(s,a+1,b) end
function StringLength(s) return #s end
function S2I(s) return tonumber(s) or 0 end
function I2S(n) return tostring(n) end
function ModuloInteger(n,d) return n%d end
function GetWidgetLife(u) return 1000 end
function DisplayTimedTextToPlayer(p,x,y,t,s) Feedback=s end
function CreateSound(path,loop,is3d,range,fadein,fadeout,eax) return {path=path,is3d=is3d} end
function SetSoundChannel(s,c) s.channel=c end
function SetSoundVolume(s,v) s.volume=v end
function SetSoundPitch(s,p) s.pitch=p end
function StartSound(s) assert(s.volume==127 and s.pitch==1 and s.channel==0 and not s.is3d);Played=s end
function KillSoundWhenDone(s) assert(s==Played) end
function PauseUnit() error('Animation preview must not pause hero') end
function IssueImmediateOrder(u,s) assert(s=='stop');Stopped=u end
function SetUnitTimeScale(u,s) assert(s==1) end
function SetUnitAnimationByIndex(u,k) assert(Stopped==u);Animation=k end
function StopMusic(fade) MusicStopped=true end
function PlayMusic(path) MusicStarted=path end
function chat(msg) Message=msg;FoundationChat() end
Hero[0]={};AnimCount[0]=19;VoiceCount[0]=2;VoiceIndex[0]=10;VoiceIndex[1]=11
for i=0,173 do AudioPath[i]='audio'..i end
for i=0,18 do AnimName[i]='sequence'..i end
chat('-sound 173');assert(Played.path=='audio173' and string.find(Feedback,'173'))
chat('-sound');assert(Played.path=='audio0')
chat('-sound 174');assert(Played.path=='audio0')
chat('-voice');assert(Played.path=='audio10')
chat('-voice');assert(Played.path=='audio11')
chat('-voice');assert(Played.path=='audio10')
chat('-anim 5');assert(Animation==5 and ResumeAt[0]==4)
chat('-anim');assert(Animation==6)
chat('-anim 18');chat('-anim');assert(Animation==0)
chat('-anim 19');assert(Animation==0)
Hero[0]=nil;chat('-sound 25');assert(Played.path=='audio25')
chat('-anim');assert(Animation==0)
chat('-music');assert(MusicStopped and not MusicOn)
chat('-music');assert(MusicOn and MusicStarted)
chat('-help');assert(string.find(Feedback,'-anim'))
`);
console.log('PASS: actual chat dispatch, explicit/cyclic sound, volume/channel, voice wrap, exact animation index/wrap, invalid ranges, missing hero, music toggle (mock natives).');
