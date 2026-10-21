// Historical checks admit only the independent verify-0201 audited Keeper hotfix.
function objects(p){for(const t of ['originalTable','customTable']){
 p[t].objects=p[t].objects.filter(o=>o.newId!=='Fent');
 for(const o of p[t].objects)if(o.oldId==='Ekee')for(const m of o.modifications)if(m.id==='uhab')m.value=m.value.replace('Fent','AEfn');
}return p;}
function runtime(s){return s.replace("set HeroSkill[54] = 'Fent'","set HeroSkill[54] = 'AEfn'").replace("set SpellAbility[54] = 'Fent'","set SpellAbility[54] = 0").replace('set SpellOrder[54] = "waterelemental"','set SpellOrder[54] = ""').replace(/^.*set Spell(?:Mode|Hold)\[54\].*\n/gm,'');}
module.exports={objects,runtime};
