// Historical comparisons admit only the ten explicit 0.16 additions and picker growth.
// verify-016 validates these additions and every retained object independently.
const assert=require('node:assert/strict'),heroes=require('../map/heroes.json');
const extra=heroes.filter(h=>h.signature);
const ids=new Set(['Fxwr',...extra.flatMap(h=>[h.id,...h.skills]),...extra.map(h=>'fp'+String(heroes.indexOf(h)).padStart(2,'0')),'fpk6']);
module.exports=function stripAdditions(current,previous){
 require('./creative-comparison.cjs').objects(current,previous);
 for(const table of ['originalTable','customTable']){
  const before=new Map(previous[table].objects.map(o=>[o.oldId+':'+o.newId,o]));
  current[table].objects=current[table].objects.filter(o=>{
   const ref=before.get(o.oldId+':'+o.newId);
   if(!ref){assert(ids.has(o.newId),'Unexpected object outside roster expansion: '+o.newId);return false;}
   if(/^fpk[0-5]$/.test(o.newId))for(const m of o.modifications)if(['unam','utra'].includes(m.id))m.value=ref.modifications.find(n=>n.id===m.id).value;
   return true;
  });
 }
 return current;
};
module.exports.runtime=function restoreRosterRuntime(current,previous){
 let s=require('./creative-comparison.cjs').runtime(current,previous).replace(/\/\/ Ten creature heroes[\s\S]*?(?=function CreateHero)/,'')
 .replace(/^\s*(?:constant integer EXPANSION_FIRST_HERO|constant (?:real|integer) XH_\w+|(?:integer|real|string|effect|unit|trigger) array Expansion\w+|group ExpansionGroup|set Expansion(?:Slot|Effect)\[).*$/gm,'')
 .replace(/^\s*call (?:ExpansionClear\(p\)|ExpansionOnDeath\(dead,killer\)|ExpansionTick\(\)|ExpansionInit\(\)).*$/gm,'')
 .replace(/^.*TriggerAddAction\(TransmuteTrigger, function OnExpansionSpell\).*$/gm,'')
 .replace(/constant integer HERO_COUNT = 46/,'constant integer HERO_COUNT = 36').replace(/constant integer PICK_PAGE_COUNT = 7/,'constant integer PICK_PAGE_COUNT = 6');
 const limits={HeroType:36,HeroName:36,HeroAlias:36,HeroGroup:36,HeroPrimary:36,HeroBotRole:36,AutoSkill:36,AutoOrder:36,HeroSkill:144,SpellAbility:144,SpellOrder:144,SpellMode:144,SpellHold:144,HeroGear:216,SuperBuild:216,HeroLearnOrder:108,PickToken:36};
 s=s.split('\n').filter(l=>{const m=l.match(/^\s*set (\w+)\[(\d+)\]/);return !m||limits[m[1]]===undefined||Number(m[2])<limits[m[1]];}).join('\n');
 for(const name of ['HeroCategory','ShowHeroGroups']){const re=new RegExp('function '+name+' takes[\\s\\S]*?endfunction');const old=previous.match(re);assert(old);s=s.replace(re,()=>old[0]);}
 return s.replaceAll('46 героев','36 героев').replaceAll('24 стандартных и 22 авторских','24 стандартных и 12 авторских').replaceAll('46 heroes including twenty-two custom.','36 heroes including twelve custom.').replaceAll('24 stock plus 22 custom creature heroes.','24 stock plus 12 custom creature heroes.').replace('навыки до 200/50','навыки до 300/50').replace('action < 209','action < 207');
};
