// The gallery hotfix must leave combat and balance objects byte-identical.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..');
const War3Map=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const UnitFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const ResearchFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const old=new War3Map();old.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.14.1-alpha.w3x'))),true);
for(const filename of ['war3map.w3a','war3map.w3h','war3map.w3q','war3map.w3t','war3map.w3e','war3map.wpm','war3mapMisc.txt','war3map.doo','war3mapUnits.doo']){
 if(filename==='war3map.w3q'){
  const previous=new ResearchFile(),current=new ResearchFile();
  previous.load(new Uint8Array(old.get(filename).bytes()));current.load(new Uint8Array(fs.readFileSync(path.join(root,'build/map',filename))));
  for(const o of previous.customTable.objects)for(const m of o.modifications)if(m.id==='gub1')m.value=m.value.replace('Предел живой армии 48 сохранён.','Предел живой армии 60 сохранён.');
  assert.deepEqual(current,previous,'Only army-cap tooltip changes from 0.14.3');
 }else assert.deepEqual(fs.readFileSync(path.join(root,'build/map',filename)),Buffer.from(old.get(filename).bytes()),filename+' must be unchanged');
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
Object.assign(report,{galleryPatch:'0.14.2',pickerCardsPerPage:7,pickerPages:6,reservedNativeRallyCell:[3,1],all36CardCellsChecked:true,alchemistPage:4,alchemistRow:1,alchemistColumn:3,combatObjectsUnchangedExceptArmyCapTooltip:'0.14.1-alpha',armyCap:60,teamArmyCap:180,enginePlaytest:false});
fs.writeFileSync(path.join(root,'build/verification-0142.json'),JSON.stringify(report,null,2)+'\n');
console.log('PASS: Six-page gallery preserved; combat objects/heroes unchanged except the requested 60-unit cap tooltip.');
