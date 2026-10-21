// Explicit 0.19 scope for historical checks; verify-019 checks the published 0.18.1 delta.
const assert=require('node:assert/strict'),races=require('../map/races.json');
const functions=['Buy','AssignBotChoices','SelectArmyRace','ShowRaces','SetAllRandom','ShowShop','OnShop','Tick','InitSlot','InitGame','OnLeave'];
function runtime(s,previous){
 s=require('./army-traits-comparison.cjs').runtime(s,previous);
 s=s.replace('-race: choose an army branch once, also on your barracks. -hero: portrait selection before 60 seconds.','-race / -hero: portrait selection before 60 seconds.').replace('Four plus wave-size research troops per wave','Three plus wave-size research troops per wave').replace('Waves: four plus','Waves: three plus').replace('Choose hero before 60 seconds; choose an army branch once on your barracks.','Choose race and hero before 60 seconds.');
 for(const name of functions){const re=new RegExp('function '+name+' takes[\\s\\S]*?endfunction');const old=previous.match(re);if(old)s=s.replace(re,()=>old[0]);}
 for(const name of ['CommitArmyBranch','OnArmyBranchSpell'])s=s.replace(new RegExp('(?:\\/\\/ Native branch cards[^\\n]*\\n)?function '+name+' takes[\\s\\S]*?endfunction\\s*'),'');
 s=s.replace(/^.*boolean array ArmyBranchChosen.*\n/gm,'').replace(/^.*TriggerAddAction\(PickerSpellTrigger, function OnArmyBranchSpell\).*$/gm,'');
 const prior=previous.match(/constant integer SPAWN_UNITS = \d+/);if(prior)s=s.replace(/constant integer SPAWN_UNITS = \d+/,prior[0]);
 const names=new Map([...previous.matchAll(/^\s*set TierName\[(\d+)\] = .*$/gm)].map(m=>[m[1],m[0].trim()]));
 return s.replace(/^\s*set TierName\[(\d+)\] = .*$/gm,(line,k)=>'    '+(names.get(k)||line.trim()));
}
function objects(current){require('./army-traits-comparison.cjs').objects(current);for(const table of ['originalTable','customTable'])current[table].objects=current[table].objects.filter(o=>!/^Fbr[0-3]$/.test(o.newId));return current;}
function historical(p){
 for(const o of p.customTable.objects){
  const m=o.newId.match(/^fm([0-3])([0-4])$/);
  if(m){const race=Number(m[1]),tier=Number(m[2]),row=races[race],ranged=row.ranged_tiers.includes(tier);o.oldId=row.units[tier];
   const updates={unam:row.tier_names[tier],ua1r:ranged?550:100,ua1t:row.attack_types[tier],ua1g:(ranged?'air,':'')+'ground,structure,debris,item,ward',ucol:8};
   for(const mod of o.modifications)if(Object.hasOwn(updates,mod.id))mod.value=updates[mod.id];
   if(row.tier_projectiles?.[tier])for(const [id,variableType,value]of [['ua1w',3,'missile'],['ua1m',3,row.tier_projectiles[tier]],['ua1z',0,900]]){const prior=o.modifications.find(m=>m.id===id);if(prior)prior.value=value;else o.modifications.push(Object.assign(new (require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/modification').default)(),{id,variableType,value,u1:o.modifications[0].u1}));}
  }
  if(o.newId==='fbax')for(const mod of o.modifications){if(mod.id==='uabi')mod.value='Fbr0,Fbr1,Fbr2,Fbr3';if(mod.id==='utub'&&!mod.value.startsWith('Сначала выбери'))mod.value='Сначала выбери ветку армии четырьмя кнопками внизу. До развития базы у всех пехотинцы. '+mod.value;}
  if(o.newId==='Rfwn')for(const mod of o.modifications)if(mod.id==='gub1')mod.value=mod.value.replace(/Следующая волна: \d+ бойцов\./,'Следующая волна: '+(6+mod.levelOrVariation)+' бойцов.');
 }
 return p;
}
module.exports={runtime,objects,historical,functions};
