const fs=require('fs'),assert=require('node:assert/strict'),crypto=require('crypto');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const root=__dirname,old=new MapFile(),now=new MapFile(),file=fs.readFileSync(root+'/dist/Shinobi_Story_Alpha_53.w3x');
old.load(new Uint8Array(fs.readFileSync(root+'/../releases/shinobi-new/Shinobi_Story_Alpha_52.w3x')),true);now.load(new Uint8Array(file),true);
const bytes=(map,n)=>Buffer.from(map.get(n).bytes());assert.deepEqual(now.getFileNames().sort(),old.getFileNames().sort());
for(const n of now.getFileNames())if(!['war3map.w3i','war3map.j'].includes(n))assert.deepEqual(bytes(now,n),bytes(old,n),n+' unchanged');
assert.deepEqual(bytes(now,'war3map.w3i'),Buffer.from(bytes(old,'war3map.w3i').toString('latin1').replaceAll('ALPHA 52','ALPHA 53'),'latin1'));
const source=bytes(now,'war3map.j').toString(),prev=bytes(old,'war3map.j').toString();
const block=`    elseif CampaignStage==31 then
        if not ExamNear(Hero[p],15932.,-13600.,192.) then
            call IssuePointOrder(Hero[p],"attack",15932.,-13600.)
        else
            call IssueImmediateOrder(Hero[p],"holdposition")
        endif
    elseif CampaignStage==12 and HeroRole[p]<9 then`;
assert(source.includes(block));assert.equal(source.replaceAll('ALPHA 53','ALPHA 52').replace(block,'    elseif (CampaignStage==12 and HeroRole[p]<9) or CampaignStage==31 then'),prev,'Whole JASS exact52 outside idle rally branch/version');
const report={filename:'Shinobi_Story_Alpha_53.w3x',bytes:file.length,sha256:crypto.createHash('sha256').update(file).digest('hex'),endlessIdleRally:[15932,-13600],holdRadius:192,all12BotRolesCovered:true,combatRetreatShoppingPreserved:true,originalInvasionLanesUnchanged:true,allOtherObjectsAssetsAndGameplayUnchanged:true,enginePlaytest:false};fs.writeFileSync(root+'/dist/rally53-verification.json',JSON.stringify(report,null,2)+'\n');console.log('PASS: exact52 archive/JASS outside endless idle rally/version; combat/shopping/retreat unchanged.');
