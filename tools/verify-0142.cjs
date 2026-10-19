// The gallery hotfix must leave combat and balance objects byte-identical.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..');
const War3Map=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const UnitFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const old=new War3Map();old.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.14.1-alpha.w3x'))),true);
for(const filename of ['war3map.w3a','war3map.w3h','war3map.w3q','war3map.w3t','war3map.w3e','war3map.wpm','war3mapMisc.txt','war3map.doo','war3mapUnits.doo']){
 assert.deepEqual(fs.readFileSync(path.join(root,'build/map',filename)),Buffer.from(old.get(filename).bytes()),filename+' must be unchanged');
}
const previous=new UnitFile();previous.load(new Uint8Array(old.get('war3map.w3u').bytes()));
const current=new UnitFile();current.load(new Uint8Array(fs.readFileSync(path.join(root,'build/map/war3map.w3u'))));
assert.deepEqual(current.originalTable.objects,previous.originalTable.objects,'All stock heroes/forms unchanged');
const byId=new Map(current.customTable.objects.map(o=>[o.newId,o]));
for(const unit of previous.customTable.objects){
 const now=byId.get(unit.newId);assert(now);
 const allowed=/^fp\d{2}$/.test(unit.newId)?['ubpx','ubpy','utub']:/^fpk\d$/.test(unit.newId)?['unam','utra']:[];
 const strip=o=>({...o,modifications:o.modifications.filter(m=>!allowed.includes(m.id))});
 assert.deepEqual(strip(now),strip(unit),'Only selector layout fields may change: '+unit.newId);
}
assert.equal(current.customTable.objects.length,previous.customTable.objects.length+1,'One extra selector page');
assert(byId.has('fpk5'));
const report=JSON.parse(fs.readFileSync(path.join(root,'build/verification-0141.json')));
Object.assign(report,{galleryPatch:'0.14.2',pickerCardsPerPage:7,pickerPages:6,reservedNativeRallyCell:[3,1],all36CardCellsChecked:true,alchemistPage:4,alchemistRow:1,alchemistColumn:3,combatObjectsByteIdenticalTo:'0.14.1-alpha',enginePlaytest:false});
fs.writeFileSync(path.join(root,'build/verification-0142.json'),JSON.stringify(report,null,2)+'\n');
console.log('PASS: Gallery-only hotfix, extra sixth page, every combat object/hero unchanged from 0.14.1.');
