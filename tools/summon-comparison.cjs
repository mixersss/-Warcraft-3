// Historical regression comparisons admit only the explicit 0.15.2 summon patch.
// Exact new values and all unrelated fields are independently checked by verify-0152.
const assert=require('node:assert/strict');
const balance=require('../map/balance.json');
const hybrid={AHhb:'Hhb1',AUdc:'Udc1',AEmb:'Emb1'};
const summonBases=new Set(Object.keys(require('../map/summon-seeds.json')));
const fields=new Set('Hwe1 Osf1 Efnu Esvu Nbau Ndou Nef1 Nsy2 Nsyu Rai3 Uin4 Ntou Ulsu'.split(' '));
const summonSkills=new Set(Object.entries(require('../map/ability-seeds.json')).filter(([id,s])=>s.fields.some(f=>fields.has(f.id))).map(([id])=>id));


module.exports=function restoreSummonFields(current,historical,units=false){
 require('./roster-comparison.cjs')(current,historical);
 for(const table of ['originalTable','customTable']){
  const previous=new Map(historical[table].objects.map(o=>[o.oldId+':'+o.newId,o]));
  for(const object of current[table].objects){
   const eligible=units?(/^s[0-9a-z]{3}$/.test(object.newId)&&summonBases.has(object.oldId)):(summonSkills.has(object.oldId)||balance.spell_damage_fields[object.oldId]||hybrid[object.oldId]||/^Ft[0-9]{2}$/.test(object.newId));
   if(!eligible)continue;
   const old=previous.get(object.oldId+':'+object.newId);assert(old,'Summon object identities must remain stable');
   for(const mod of object.modifications){
    if(!(units?['uhpm','ua1b'].includes(mod.id):mod.id==='aub1'||balance.spell_damage_fields[object.oldId]?.includes(mod.id)||hybrid[object.oldId]===mod.id||(/^Ft[0-9]{2}$/.test(object.newId)&&['Tdg1','Tdg3'].includes(mod.id))))continue;
    const reference=old.modifications.find(m=>m.id===mod.id&&m.levelOrVariation===mod.levelOrVariation&&m.dataPointer===mod.dataPointer);
    assert(reference,'Cannot add summon fields under a historical exception');
    assert.equal(mod.variableType,reference.variableType);
    mod.value=reference.value;
   }
  }
 }
 return current;
};

module.exports.isSummon=o=>/^s[0-9a-z]{3}$/.test(o.newId)&&summonBases.has(o.oldId);

module.exports.research=function restoreResearch(current,historical){
 const ids=new Set(['Rfat','Rfar','Rfhp','Rfa2','Rfr2','Rfh2']);
 const previous=new Map(historical.customTable.objects.map(o=>[o.newId,o]));
 for(const o of current.customTable.objects)if(ids.has(o.newId))for(const m of o.modifications)if(['gglb','gglm','gub1'].includes(m.id)){
  const ref=previous.get(o.newId).modifications.find(n=>n.id===m.id&&n.levelOrVariation===m.levelOrVariation&&n.dataPointer===m.dataPointer);assert(ref);m.value=ref.value;
 }
 return current;
};
