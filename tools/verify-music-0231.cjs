// Exact music-only archive delta and actual shipped playlist callbacks.
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),crypto=require('crypto'),cp=require('child_process');
const root=path.resolve(__dirname,'..'),rows=require('../map/music.json').tracks,b=require('../map/balance.json');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const seconds=r=>r.durationMs%1000===0?(r.durationMs/1000)+'.0':String(r.durationMs/1000);
const runtime=()=>fs.readFileSync(root+'/map/music.j','utf8').replace('    // PLAYLIST_DATA',rows.flatMap((r,i)=>[`    set FFMusicPath[${i}]=${JSON.stringify(r.path)}`,`    set FFMusicSeconds[${i}]=${seconds(r)}`]).join('\n'));
const canonical=s=>s.split('\n').map(l=>l.trim()).filter(Boolean).join('\n');
function stripMusic(source){
 const module=runtime();assert(source.includes(module),'Exact audited music module');source=source.replace(module,'');
 for(const line of ['    timer FFMusicTimer = null','    integer FFMusicIndex = 0','    string array FFMusicPath','    real array FFMusicSeconds','    call FFMusicInit()']){
  assert.equal(source.split(line).length,2,'Exactly one declared music addition: '+line);source=source.replace(line,'');
 }
 return source;
}
function verify(){
 assert.equal(rows.length,8);assert.equal(new Set(rows.map(r=>r.sourceSha256)).size,8,'Eight unique uploads');
 const old=new MapFile(),current=new MapFile(),file=fs.readFileSync(root+`/build/FourFrontsFrenzy-${b.version}.w3x`);
 old.load(new Uint8Array(fs.readFileSync(root+'/releases/FourFrontsFrenzy-0.23.0-alpha.w3x')),true);current.load(new Uint8Array(file),true);
 const before=n=>Buffer.from(old.get(n).bytes()),now=n=>Buffer.from(current.get(n).bytes());
 assert(file.length<8388608,'Classic network size limit');
 assert.deepEqual(current.getFileNames().sort(),[...old.getFileNames(),...rows.map(r=>r.path)].sort(),'Only eight audio imports appended');
 for(const n of old.getFileNames())if(!['(listfile)','war3map.w3i','war3map.j','war3map.imp'].includes(n))assert.deepEqual(now(n),before(n),n+' unchanged');
 assert.deepEqual(now('war3map.w3i'),Buffer.from(before('war3map.w3i').toString('latin1').replaceAll('0.23.0-alpha',b.version),'latin1'));
 const header=Buffer.alloc(8);header.writeInt32LE(1);header.writeInt32LE(8,4);
 assert.deepEqual(now('war3map.imp'),Buffer.concat([header,...rows.map(r=>Buffer.from('\x0d'+r.path+'\0','ascii'))]));
 const script=now('war3map.j').toString();assert.equal(canonical(stripMusic(script).replaceAll(b.version,'0.23.0-alpha')),canonical(before('war3map.j').toString()),'All gameplay exact0.23.0');
 for(const r of rows){
  assert.equal(hash(now(r.path)),r.sha256);assert.equal(now(r.path).length,r.bytes);assert(Math.abs(r.durationMs-r.decodedSourceDurationMs)<200,'Full uncut source length');
  const probe=JSON.parse(cp.execFileSync('ffprobe',['-v','error','-show_entries','stream=codec_name,sample_rate,channels:format=duration','-of','json',root+'/'+r.file]));
  assert.equal(probe.streams[0].codec_name,'mp3');assert.equal(probe.streams[0].channels,1);assert.equal(probe.streams[0].sample_rate,'22050');assert.equal(Math.round(Number(probe.format.duration)*1000),r.durationMs);
 }
 const {lua,lauxlib,lualib,to_luastring,to_jsstring}=require('fengari'),translate=require('mdx-m3-viewer/dist/cjs/utils/jass2/jass2lua').default;
 const L=lauxlib.luaL_newstate();lualib.luaL_openlibs(L);const run=s=>{if(lauxlib.luaL_dostring(L,to_luastring(s))!==lua.LUA_OK)throw Error(to_jsstring(lua.lua_tostring(L,-1)));};
 const functions=[...script.matchAll(/^function FFMusic\w+ takes[^]*?^endfunction/gm)].map(m=>m[0]).join('\n');assert.equal([...functions.matchAll(/^function/gm)].length,3);
 run(translate('globals\n timer FFMusicTimer=null\n integer FFMusicIndex=0\n string array FFMusicPath\n real array FFMusicSeconds\nendglobals\n'+functions));
 run(`Created=0;Played={};Stopped=0
 function CreateTimer()Created=Created+1;return {}end
 function ModuloInteger(a,b)return a%b end
 function StopMusic(fade)assert(fade==false);Stopped=Stopped+1 end
 function PlayMusic(p)Played[#Played+1]=p end
 function TimerStart(t,d,repeatFlag,callback)assert(t==FFMusicTimer and not repeatFlag);t.duration=d;t.callback=callback end
 function ExecuteFunc(n)assert(n=='FFMusicPlay');_G[n]()end
 FFMusicInit();FFMusicInit();assert(Created==1 and #Played==1)
 for step=0,23 do
  local i=step%8;assert(FFMusicIndex==i and Played[#Played]==FFMusicPath[i] and FFMusicTimer.duration==FFMusicSeconds[i]);FFMusicTimer.callback()
 end
 assert(Created==1 and Stopped==25 and #Played==25)`);
 const report={version:b.version,bytes:file.length,sha256:hash(file),tracks:rows.map(r=>({name:r.name,durationMs:r.durationMs})),fullTracks:true,uniqueTracks:8,repeatedCyclesTested:3,timersCreated:1,gameplayAndBalanceUnchanged:true,below8MiB:true,enginePlaytest:false};
 fs.writeFileSync(root+'/build/music-verification.json',JSON.stringify(report,null,2)+'\n');console.log('PASS:8 full unique songs, actual callbacks play1..8/1 across3 cycles, one timer, exact unchanged gameplay/world/economy/skills versus0.23.0.');
}
module.exports={stripMusic,verify};if(require.main===module)verify();
