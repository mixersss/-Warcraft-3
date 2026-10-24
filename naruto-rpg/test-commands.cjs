// Execute actual generated JASS through Lua; native calls are mocks, not engine tests.
const fs=require('node:fs');
const {lua,lauxlib,lualib,to_luastring,to_jsstring}=require('fengari');
const translate=require('mdx-m3-viewer/dist/cjs/utils/jass2/jass2lua').default;
const L=lauxlib.luaL_newstate();lualib.luaL_openlibs(L);
function run(s){if(lauxlib.luaL_dostring(L,to_luastring(s))!==lua.LUA_OK)throw Error(to_jsstring(lua.lua_tostring(L,-1)));}
const source=fs.readFileSync(__dirname+'/dist/map/war3map.j','utf8');
run(translate(source).replace(/\bnot(?=[A-Z(])/g,'not '));
const musicLines=source.split('\n').filter(s=>/^\s*set (Playlist(Audio|Duration)|Music(ChapterStart|ChapterCount|TrackPath|TrackSeconds))\[/.test(s));
run(translate('function MusicFixtureData takes nothing returns nothing\n'+musicLines.join('\n')+'\nendfunction\n'));run('MusicFixtureData()');
run(`
debug.setmetatable('', {__add=function(a,b) return tostring(a)..tostring(b) end})
for _,a in ipairs({AnimCursor,AudioCursor,VoiceCursor,ResumeAt}) do setmetatable(a,{__index=function() return 0 end}) end
function ExecuteFunc(name)_G[name]()end
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
function GetUnitTypeId(u) return 0 end
function DisplayTimedTextToPlayer(p,x,y,t,s) Feedback=s end
Created=0
function CreateSound(path,loop,is3d,range,fadein,fadeout,eax) Created=Created+1;return {path=path,is3d=is3d,eax=eax} end
function SetSoundDuration(s,d) assert(d>0);s.duration=d end
function StopSound(s,kill,fade) assert(not kill);s.stopped=true end
function TimerStart(t,delay,loop,callback)
 assert(not loop)
 if t==MusicClock then MusicDelay=delay;MusicCallback=callback else assert(delay==.2);Deferred=callback end
end
function PauseTimer(t) assert(t==MusicClock);MusicPaused=true end
function flush() if Deferred then local cb=Deferred;Deferred=nil;cb() end end
function SetSoundChannel(s,c) s.channel=c end
function SetSoundVolume(s,v) s.volume=v end
function SetSoundPitch(s,p) s.pitch=p end
function StartSound(s) assert(s.volume==127 and s.pitch==1 and s.channel==0 and not s.is3d and s.stopped);Played=s end
function KillSoundWhenDone(s) error('Imported sounds must remain cached') end
function PauseUnit() error('Animation preview must not pause hero') end
function IssueImmediateOrder(u,s) assert(s=='stop');Stopped=u end
function SetUnitTimeScale(u,s) assert(s==1) end
function SetUnitAnimationByIndex(u,k) assert(Stopped==u);Animation=k end
function StopMusic(fade) MusicStopped=true end
MusicStarts=0
function PlayMusic(path) MusicStarted=path;MusicStarts=MusicStarts+1 end
function chat(msg) Message=msg;FoundationChat();flush() end
MusicClock='music';HeroType[0]=0;HeroTemplate[0]=0;HeroRole[0]=0;Hero[0]={};AnimCount[0]=19;VoiceCount[0]=2;VoiceIndex[0]=10;VoiceIndex[1]=11
for i=0,173 do AudioPath[i]='audio'..i;AudioDuration[i]=1000;AudioEAX[i]='' end
for i=0,18 do AnimName[i]='sequence'..i end
chat('-sound 173');assert(Played.path=='audio173' and string.find(Feedback,'173'))
chat('-sound');assert(Played.path=='audio0')
chat('-sound 174');assert(Played.path=='audio0')
chat('-voice');assert(Played.path=='audio10')
chat('-voice');assert(Played.path=='audio11')
chat('-voice');assert(Played.path=='audio10')
local before=Created;chat('-voice');assert(Created==before and Played.path=='audio11')
AudioPath[174]='stock';AudioEAX[174]='';chat('-soundtest');assert(Played.path=='stock')
Message='-sound 1';FoundationChat();assert(PendingAudio==1 and Played.path=='stock');flush();assert(Played.path=='audio1' and PendingAudio==-1)
chat('-anim 5');assert(Animation==5 and ResumeAt[0]==4)
chat('-anim');assert(Animation==6)
chat('-anim 18');chat('-anim');assert(Animation==0)
chat('-anim 19');assert(Animation==0)
Hero[0]=nil;chat('-sound 25');assert(Played.path=='audio25')
chat('-anim');assert(Animation==0)
chat('-music');assert(MusicStopped and not MusicOn)
chat('-music');assert(MusicOn and MusicStarted)
chat('-help');assert(string.find(Feedback,'-anim'))
-- Each chapter plays its own list; paired songs advance A/B/A without switching chapter.
assert(MusicChapterCount[0]==2 and MusicChapterCount[2]==2 and MusicChapterCount[9]==2)
for chapter=0,9 do
 FoundationMusicSetChapter(chapter)
 local start=MusicChapterStart[chapter];local count=MusicChapterCount[chapter]
 assert(MusicStarted==MusicTrackPath[start] and MusicDelay==MusicTrackSeconds[start])
 for step=1,count*3 do
  MusicCallback()
  local song=step%count
  assert(MusicCursor==chapter and MusicSong==song and MusicStarted==MusicTrackPath[start+song] and MusicDelay==MusicTrackSeconds[start+song])
 end
end
-- Repeated stage setup with the same soundtrack must not restart its timer or song.
FoundationMusicSetChapter(9);MusicCallback();local song=MusicSong;local before=MusicStarted;local timer=MusicCallback;local starts=MusicStarts
FoundationMusicStart();assert(MusicSong==song and MusicStarted==before and MusicCallback==timer and MusicStarts==starts)
-- Invasion intro and combat share the same track; no8-second restart.
FoundationMusicSetChapter(6);local invasion=MusicStarted;local starts=MusicStarts;FoundationMusicSetChapter(7);assert(MusicStarted==invasion and MusicStarts==starts)
local old=MusicStarted;chat('-music');assert(not MusicOn and MusicPaused)
FoundationMusicSetChapter(2);chat('-nextmusic');assert(MusicCursor==2 and MusicSong==0 and MusicStarted==old,'Muted chapter changes remain silent')
chat('-music');assert(MusicOn and MusicStarted==MusicTrackPath[MusicChapterStart[2]])
MusicCallback();assert(MusicSong==1);chat('-music');chat('-music');assert(MusicSong==1 and MusicStarted==MusicTrackPath[MusicChapterStart[2]+1],'Unmute resumes current track')
local playing=MusicStarted;chat('-sound 1');assert(Played.path=='audio1' and MusicStarted==playing,'Voices must not replace background music')
local chapter=MusicCursor;FoundationMusicSetChapter(-1);FoundationMusicSetChapter(10);assert(MusicCursor==chapter)
`);
console.log('PASS: actual chat dispatch, explicit/cyclic sound, duration/cache/deferred playback, volume/channel, voice wrap, exact animation index/wrap, invalid ranges, missing hero, user chapter playlists, A/B/A loops for3 paired stages, persistent music across shared chapter transitions, mute/resume, per-track durations and separate voice playback (mock natives).');
