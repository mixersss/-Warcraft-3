// Audit the test-level-only delta against the published Alpha35.
const fs=require('fs'),assert=require('node:assert/strict'),crypto=require('crypto'),MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const root=__dirname,old=new MapFile(),now=new MapFile(),file=fs.readFileSync(root+'/dist/Shinobi_Story_Alpha_36.w3x');
old.load(new Uint8Array(fs.readFileSync(root+'/../releases/shinobi-new/Shinobi_Story_Alpha_35.w3x')),true);now.load(new Uint8Array(file),true);
const a=n=>Buffer.from(old.get(n).bytes()),b=n=>Buffer.from(now.get(n).bytes());
assert.deepEqual(now.getFileNames().sort(),old.getFileNames().sort());for(const n of now.getFileNames())if(!['war3map.j','war3map.w3i'].includes(n))assert.deepEqual(b(n),a(n),n+' unchanged');
assert.deepEqual(b('war3map.w3i'),Buffer.from(a('war3map.w3i').toString('latin1').replaceAll('SHINOBI STORY ALPHA 35','SHINOBI STORY ALPHA 36'),'latin1'));
const source=fs.readFileSync(root+'/src/invasion-test35.j','utf8');
const added=`    // First team gets test levels; never lower an already stronger hero.
    loop
        exitwhen p>=3
        if FoundationAlive(Hero[p]) and GetHeroLevel(Hero[p])<45 then
            call SetHeroLevel(Hero[p],45,true)
        endif
        set p=p+1
    endloop
`;
assert(source.includes(added));
const runtimeAdded=added.split('\n').filter(l=>!l.trim().startsWith('//')).join('\n');
const current=b('war3map.j').toString();assert(current.includes(runtimeAdded));
assert.equal(current.replace(runtimeAdded,'').replace('    local integer lane=0\n    local integer p=0\n','    local integer lane=0\n').replaceAll('SHINOBI STORY ALPHA 36','SHINOBI STORY ALPHA 35'),a('war3map.j').toString());
const report={stage:36,filename:'Shinobi_Story_Alpha_36.w3x',sha256:crypto.createHash('sha256').update(file).digest('hex'),bytes:file.length,firstTeamTestLevel:45,onlyFastTest:true,allOtherRuntimeObjectsWorldMusicUnchanged:true,enginePlaytest:false};
fs.writeFileSync(root+'/dist/level36-verification.json',JSON.stringify(report,null,2)+'\n');console.log('PASS: exact Alpha35 except first-team level45 in fast invasion test and version.');
