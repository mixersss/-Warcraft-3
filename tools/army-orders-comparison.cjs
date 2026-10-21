// Exact 0.21 army-order scope; verify-021 independently audits the 0.20.1 archive.
const functions=['CommitArmyBranch','CommandArmy','OnChat','InitSlot','InitGame'];
const added=['InstallArmyOrderButtons','ArmyCornerName','ArmyDestinationBase','PlanBotArmyDestination','SetArmyDestination','ShowArmyOrders','OnArmyOrderSpell','OnArmyOrderDialog'];
function objects(p){for(const t of ['originalTable','customTable'])p[t].objects=p[t].objects.filter(o=>!/^Fa[oc][0-3]$/.test(o.newId));return p;}
function runtime(s,previous){
 for(const name of functions){const re=new RegExp('function '+name+' takes[\\s\\S]*?endfunction');const old=previous.match(re);if(old)s=s.replace(re,()=>old[0]);}
 for(const name of added)s=s.replace(new RegExp('function '+name+' takes[\\s\\S]*?endfunction\\s*'),'');
 return s.replace(/^.*(?:integer array Army(?:Destination|PlanAt)|boolean array Army(?:Redirect|WasDefending)).*\n/gm,'');
}
module.exports={objects,runtime,functions,added};
