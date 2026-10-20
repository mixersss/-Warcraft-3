// Narrow historical exception for the three explicitly added 0.17 heroes.
const assert=require('node:assert/strict');
const ids=new Set(['Fy00','Fy01','Fy02',...Array.from({length:12},(_,i)=>'Y'+String(i).padStart(3,'0')),'fp46','fp47','fp48']);
function objects(current,previous){
 for(const table of ['originalTable','customTable']){
  const old=new Map(previous[table].objects.map(o=>[o.oldId+':'+o.newId,o]));
  current[table].objects=current[table].objects.filter(o=>{
   const ref=old.get(o.oldId+':'+o.newId);
   if(!ref){if(ids.has(o.newId))return false;return true;}
   if(o.newId==='fpk6')for(const m of o.modifications)if(m.id==='utra')m.value=ref.modifications.find(n=>n.id==='utra').value;
   return true;
  });
 }
 return current;
}
function runtime(current,previous){
 let s=current.replace(/\/\/ Three original kits[\s\S]*?(?=function CreateHero)/,'')
 .replace(/\/\/ Combo-aware native orders[\s\S]*?(?=function TryBotSpell)/,'')
 .replace(/^\s*(?:integer|real|unit|effect|trigger) array Creative\w+.*$/gm,'')
 .replace(/^\s*call Creative(?:Clear\(p\)|Tick\(\)|Init\(\)).*$/gm,'')
 .replace(/^.*TriggerAddAction\(TransmuteTrigger, function OnCreativeSpell\).*$/gm,'')
 .replace(/    if IsUnitType\(dead,UNIT_TYPE_HERO\) and dead == Hero\[GetPlayerId\(GetOwningPlayer\(dead\)\)\] then\n        call CreativeClear\(GetPlayerId\(GetOwningPlayer\(dead\)\)\)\n    endif\n/,'')
 .replace(/    if HeroKind\[p\] >= 46 then\n        set h = null\n        return TryCreativeBotSpell\(p,enemy\)\n    endif\n/,'')
 .replace('constant integer HERO_COUNT = 49','constant integer HERO_COUNT = 46');
 const limits={HeroType:46,HeroName:46,HeroAlias:46,HeroGroup:46,HeroPrimary:46,HeroBotRole:46,AutoSkill:46,AutoOrder:46,HeroSkill:184,SpellAbility:184,SpellOrder:184,SpellMode:184,SpellHold:184,HeroGear:276,SuperBuild:276,HeroLearnOrder:138,PickToken:46};
 s=s.split('\n').filter(l=>{const m=l.match(/^\s*set (\w+)\[(\d+)\]/);return !m||limits[m[1]]===undefined||Number(m[2])<limits[m[1]];}).join('\n');
 for(const name of ['HeroCategory','ShowHeroGroups']){const re=new RegExp('function '+name+' takes[\\s\\S]*?endfunction');const old=previous.match(re);assert(old);s=s.replace(re,()=>old[0]);}
 return s.replaceAll('49 героев','46 героев').replaceAll('24 стандартных и 25 авторских','24 стандартных и 22 авторских').replaceAll('49 heroes including twenty-five custom.','46 heroes including twenty-two custom.').replaceAll('24 stock plus 25 custom creature heroes.','24 stock plus 22 custom creature heroes.').replace('action < 210','action < 209');
}
module.exports={objects,runtime};
module.exports.sameObjects=function(currentBytes,oldBytes,name){
 const Parser=require('mdx-m3-viewer/dist/cjs/parsers/w3x/'+(name.endsWith('w3u')?'w3u':'w3d')+'/file').default;
 const current=new Parser(),previous=new Parser();current.load(new Uint8Array(currentBytes));previous.load(new Uint8Array(oldBytes));
 assert.deepEqual(objects(current,previous),previous,name+' preserves every pre-0.17 field');
};
