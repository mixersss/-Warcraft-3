// Explicit 0.18 replacement scope; verify-018 checks all new data independently.
const assert=require('node:assert/strict');
const helpers=['Clif','Csum','Cuba','Cubd','Crag','Cvam','Cdet','Bcbs','Bcas','Bcar','Bcsm','Bcua','Bcud','Bcrg','fvlm','ftot','fpk7'];
const ids=new Set([...helpers,...Array.from({length:4},(_,i)=>'Fz0'+i),...Array.from({length:16},(_,i)=>'V'+String(i).padStart(3,'0')),...Array.from({length:4},(_,i)=>'fp'+(46+i)),...Array.from({length:450},(_,i)=>i<200?'k0'+i.toString(16).padStart(2,'0'):i<400?'k1'+(i-200).toString(16).padStart(2,'0'):'k2'+(i-400).toString(16).padStart(2,'0'))]);
function objects(current,previous){
 require('./army-branch-comparison.cjs').objects(current);
 for(const table of ['originalTable','customTable']){
  const old=new Map(previous[table].objects.map(o=>[o.oldId+':'+o.newId,o]));
  current[table].objects=current[table].objects.filter(o=>{
   const ref=old.get(o.oldId+':'+o.newId);
   if(!ref&&ids.has(o.newId))return false;
   if(ref&&/^fpk[0-6]$/.test(o.newId))for(const m of o.modifications)if(['unam','utra'].includes(m.id))m.value=ref.modifications.find(n=>n.id===m.id).value;
   if(ref&&o.newId==='futl')for(const m of o.modifications)if(m.id==='usei'){assert.equal(m.value.split(',').filter(x=>!['fvlm','ftot'].includes(x)).join(','),ref.modifications.find(n=>n.id==='usei').value);m.value=ref.modifications.find(n=>n.id==='usei').value;}
   return true;
  });
 }
 return current;
}
function runtime(s){return s.replace(/^.*constant integer SUMMON_(?:ULTIMATE_)?KILL_GOLD = .*$/gm,'').replace(/    \/\/ Pet gold is independent[\s\S]*?(?=    if dead == Base\[p\] then\n        call CheckTeam)/,'').replace('constant integer HERO_COUNT = 50','constant integer HERO_COUNT = 49').replace('constant integer PICK_PAGE_COUNT = 8','constant integer PICK_PAGE_COUNT = 7').replace(/^.*set CreativePetType\[.*$/gm,'').replaceAll('50 героев','49 героев').replaceAll('24 стандартных и 26 авторских','24 стандартных и 25 авторских').replaceAll('50 heroes including twenty-six custom.','49 heroes including twenty-five custom.').replaceAll('24 stock plus 26 custom creature heroes.','24 stock plus 25 custom creature heroes.');}
function same(currentBytes,previousBytes,name){
 const Parser=require('mdx-m3-viewer/dist/cjs/parsers/w3x/'+(['war3map.w3u','war3map.w3h','war3map.w3t'].includes(name)?'w3u':'w3d')+'/file').default;
 const current=new Parser(),previous=new Parser();current.load(new Uint8Array(currentBytes));previous.load(new Uint8Array(previousBytes));
 require('./creative-comparison.cjs').objects(current,previous);assert.deepEqual(current,previous,name+' unchanged outside four hero replacements, pets and two shop items');
}
module.exports={objects,runtime,same,ids};
