// Explicit runtime-only invasion hotfix scope; verify25 compares Alpha24 independently.
const funcs=['OrigNPC_MLE','CampaignNPCTick','CampaignInvasionEvents','CampaignSpawnStage'];
function runtime(s,prior){
 for(const name of funcs){const re=new RegExp('function '+name+' takes[\\s\\S]*?endfunction'),ref=prior.match(re);if(!ref)throw Error('Missing reference '+name);s=s.replace(re,()=>ref[0]);}
 return s.replace(/function InvasionHeroVisibility takes[\s\S]*?endfunction/,'').replace(/^.*real array SasukeHiddenSince.*$/gm,'').replace(/^.*call InvasionHeroVisibility\(\).*$/gm,'');
}
module.exports={runtime,funcs};
