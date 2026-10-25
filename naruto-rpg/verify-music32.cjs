// Exact music-only delta against Alpha31: every other archive member stays identical.
const fs=require('fs'),assert=require('node:assert/strict'),crypto=require('crypto'),cp=require('child_process');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,root=__dirname;
const prior=new MapFile(),current=new MapFile(),file=fs.readFileSync(root+'/dist/Shinobi_Story_Alpha_32.w3x');
prior.load(new Uint8Array(fs.readFileSync(root+'/../releases/shinobi-new/Shinobi_Story_Alpha_31.w3x')),true);current.load(new Uint8Array(file),true);
const old=n=>Buffer.from(prior.get(n).bytes()),now=n=>Buffer.from(current.get(n).bytes()),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const data=JSON.parse(fs.readFileSync(root+'/src/user-music.json')),songs=data.tracks.filter(r=>['sasuke-a','sasuke-b'].includes(r.key));
assert.equal(songs.length,2);assert.deepEqual(songs.map(r=>r.originalName),['Takanashi_Yasuharu_-_A_Friend_s_Reminiscence_(Bib.fm).mp3','Поиск саске и финальные битвы.mp3']);
assert.deepEqual(data.chapters.find(r=>r.chapter===9).tracks,['sasuke-a','sasuke-b']);
const allowed=new Set(['war3map.j','war3map.w3i',...songs.map(r=>r.path)]);
assert.deepEqual(current.getFileNames().sort(),prior.getFileNames().sort());
for(const n of current.getFileNames())if(!allowed.has(n))assert.deepEqual(now(n),old(n),n+' unchanged');
assert.deepEqual(now('war3map.w3i'),Buffer.from(old('war3map.w3i').toString('latin1').replaceAll('SHINOBI STORY ALPHA 31','SHINOBI STORY ALPHA 32'),'latin1'));
const audio=JSON.parse(fs.readFileSync(root+'/src/all-original-audio.json')),indices=new Set(audio.map((r,i)=>songs.some(s=>s.path===r.path)?i:-1).filter(i=>i>=0));
function normalize(s){return s.replaceAll('SHINOBI STORY ALPHA 31','SHINOBI STORY ALPHA 32').split('\n').filter(l=>{const m=l.match(/set (AudioDuration|MusicTrackSeconds|PlaylistDuration)\[(\d+)\]=/);return !m||!((m[1]==='AudioDuration'&&indices.has(+m[2]))||(m[1]==='MusicTrackSeconds'&&[10,11].includes(+m[2]))||(m[1]==='PlaylistDuration'&&+m[2]===9));}).join('\n');}
assert.equal(normalize(now('war3map.j').toString()),normalize(old('war3map.j').toString()),'Entire gameplay/runtime unchanged');
const script=now('war3map.j').toString();
assert(script.includes('set MusicChapterStart[9]=10'));assert(script.includes('set MusicChapterCount[9]=2'));
for(const [i,row] of songs.entries()){
 assert.equal(hash(now(row.path)),row.sha256);assert.equal(now(row.path).length,row.bytes);
 assert(Math.abs(row.duration_ms-row.decodedSourceDurationMs)<200,'No song truncation');
 assert(script.includes(`set MusicTrackSeconds[${10+i}]=${row.duration_ms/1000}`));
 const probe=JSON.parse(cp.execFileSync('ffprobe',['-v','error','-show_entries','stream=codec_name,sample_rate,channels:format=duration','-of','json',root+'/'+row.file]));
 assert.equal(probe.streams[0].codec_name,'mp3');assert.equal(probe.streams[0].sample_rate,'22050');assert.equal(probe.streams[0].channels,1);
 assert.equal(Math.round(Number(probe.format.duration)*1000),row.duration_ms);
}
const report={stage:32,filename:'Shinobi_Story_Alpha_32.w3x',bytes:file.length,sha256:hash(file),chapter:9,orderedTracks:songs.map(r=>({name:r.originalName,durationMs:r.duration_ms,sourceSha256:r.sourceSha256})),fullTracks:true,repeatOrder:'A/B/A',allOtherGameplayModelsVoicesAndMusicUnchanged:true,enginePlaytest:false};
fs.writeFileSync(root+'/dist/music32-verification.json',JSON.stringify(report,null,2)+'\n');console.log('PASS: Alpha32 replaces only Sasuke chapter pair, full songs and timings verified, all gameplay/other assets exact Alpha31.');
