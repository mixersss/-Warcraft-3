// Historical release tests admit only the requested 0.17.1 wave settings/text.
// verify-0171 independently checks the exact three settings and every changed field.
const U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const Q=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
module.exports=function normalizeHistoricalWaves(archive){
 const original=archive.get.bind(archive),cache=new Map();
 archive.get=function(name){
  const file=original(name);if(!file||!['war3map.w3u','war3map.w3q','war3map.j'].includes(name))return file;
  return {bytes(){
   if(cache.has(name))return cache.get(name);
   let result;
   if(name==='war3map.j')result=Buffer.from(Buffer.from(file.bytes()).toString().replace(/constant integer SPAWN_SECONDS = \d+/,'constant integer SPAWN_SECONDS = 18').replace(/constant integer SPAWN_MIN_SECONDS = \d+/,'constant integer SPAWN_MIN_SECONDS = 18').replace(/constant integer ARMY_CAP = \d+/,'constant integer ARMY_CAP = 85').replaceAll('every 21 seconds','every 18 seconds').replaceAll('army cap 60','army cap 85'));
   else{
    const p=new (name.endsWith('w3u')?U:Q)();p.load(new Uint8Array(file.bytes()));
    for(const o of p.customTable.objects)for(const m of o.modifications){
     if(o.newId==='fbax'&&m.id==='utub')m.value=m.value.replace(/Спавн раз в \d+ секунд/,'Спавн раз в 18 секунд');
     if(o.newId==='Rfwn'&&m.id==='gub1')m.value=m.value.replace(/Предел живой армии \d+ сохранён\./,'Предел живой армии 85 сохранён.');
    }
    require('./army-branch-comparison.cjs').historical(p);
    result=Buffer.from(p.save());
   }
   cache.set(name,result);return result;
  }};
 };
};
