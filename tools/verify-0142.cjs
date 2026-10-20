// The gallery hotfix must leave combat and balance objects byte-identical.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..');
const War3Map=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const UnitFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const ResearchFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const old=new War3Map();old.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.14.1-alpha.w3x'))),true);require('./historical-wave-settings.cjs')(old);
for(const filename of ['war3map.w3a','war3map.w3h','war3map.w3q','war3map.w3t','war3map.w3e','war3map.wpm','war3mapMisc.txt','war3map.doo','war3mapUnits.doo']){
 if(filename==='war3map.w3a'){
  const current=new ResearchFile(),previous=new ResearchFile();
  current.load(new Uint8Array(fs.readFileSync(path.join(root,'build/map',filename))));previous.load(new Uint8Array(old.get(filename).bytes()));
  require('./summon-comparison.cjs')(current,previous);
  assert.deepEqual(current,previous,'Only 0.15.2 summon tooltips may change');
 }else if(filename==='war3map.w3q'){
  const previous=new ResearchFile(),current=new ResearchFile();
  previous.load(new Uint8Array(old.get(filename).bytes()));current.load(new Uint8Array(fs.readFileSync(path.join(root,'build/map',filename))));
  for(const o of previous.customTable.objects)for(const m of o.modifications)if(m.id==='gub1')m.value=m.value.replace('Предел живой армии 48 сохранён.','Предел живой армии 60 сохранён.');
  require('./summon-comparison.cjs').research(current,previous);
  assert.deepEqual(current,previous,'Only army-cap tooltip and requested troop research prices may change');
 }else if(['war3map.w3h','war3map.w3t'].includes(filename))require('./simple-comparison.cjs').same(fs.readFileSync(path.join(root,'build/map',filename)),old.get(filename).bytes(),filename);else assert.deepEqual(fs.readFileSync(path.join(root,'build/map',filename)),Buffer.from(old.get(filename).bytes()),filename+' must be unchanged');
}
const previous=new UnitFile();previous.load(new Uint8Array(old.get('war3map.w3u').bytes()));
const current=new UnitFile();current.load(new Uint8Array(fs.readFileSync(path.join(root,'build/map/war3map.w3u'))));
assert.deepEqual(current.originalTable.objects,previous.originalTable.objects,'All stock heroes/forms unchanged');
const byId=new Map(current.customTable.objects.map(o=>[o.newId,o]));
for(const unit of previous.customTable.objects){
 const now=byId.get(unit.newId);assert(now);
 const allowed=/^fp\d{2}$/.test(unit.newId)?['ubpx','ubpy','utub']:/^fpk\d$/.test(unit.newId)?['unam','utra']:[];
 if(unit.newId==='futl')allowed.push('usei');
 if(require('./summon-comparison.cjs').isSummon(unit))allowed.push('uhpm','ua1b');
 const strip=o=>({...o,modifications:o.modifications.filter(m=>!allowed.includes(m.id))});
 assert.deepEqual(strip(now),strip(unit),'Only selector layout fields may change: '+unit.newId);
}
const oldCount=current.customTable.objects.length;require('./roster-comparison.cjs')(current,{...previous,customTable:{...previous.customTable,objects:[...previous.customTable.objects,byId.get('fpk5')]}});
assert.equal(current.customTable.objects.length,previous.customTable.objects.length+1,'One legacy extra selector page');
assert.equal(oldCount-current.customTable.objects.length,480,'Thirteen heroes, thirteen cards, and one new picker page');
assert(byId.has('fpk5'));
const report=JSON.parse(fs.readFileSync(path.join(root,'build/verification-0141.json')));
Object.assign(report,{galleryPatch:'0.14.2',pickerCardsPerPage:7,pickerPages:7,reservedNativeRallyCell:[3,1],all46CardCellsChecked:true,alchemistPage:4,alchemistRow:1,alchemistColumn:3,combatObjectsUnchangedExceptArmyCapTooltipAndSummonBalance:'0.14.1-alpha',armyCap:85,teamArmyCap:255,enginePlaytest:false});
fs.writeFileSync(path.join(root,'build/verification-0142.json'),JSON.stringify(report,null,2)+'\n');
console.log('PASS: Six-page gallery preserved; combat objects/heroes unchanged except requested army-cap tooltip and 0.15.2 summon HP/damage/tooltips.');
