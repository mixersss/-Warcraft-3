// Parse the complete released archive with an independent Warcraft format reader.
// These are structural checks; they do not emulate the Warcraft engine.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');
const root = path.resolve(__dirname, '..');
const prefix = 'mdx-m3-viewer/dist/cjs/parsers/';
const War3Map = require(prefix + 'w3x/map').default;
const balance = require('../map/balance.json');
const races = require('../map/races.json');
const heroes = require('../map/heroes.json');
const target = path.join(root, 'build', `FourFrontsFrenzy-${balance.version}.w3x`);
const data = fs.readFileSync(target);
assert.ok(data.length<4*1024*1024,'Compressed map fits the conservative Classic download limit');
const map = new War3Map();
// Use a true Uint8Array: Node Buffer.slice() shares a larger backing allocation.
map.load(new Uint8Array(data), true);
assert.equal(map.maxPlayers, 12);
// 0.4.0 used compressed SINGLE_UNIT files. Modern readers accepted them but
// the user's Classic loader failed in SFile.cpp. Require ordinary 4 KiB
// sector files and decode every sector independently of the MPQ reader.
assert.equal(map.archive.sectorSize,4096);
for(const file of map.archive.files) {
  const block=file.block;
  assert.equal(block.flags & 0x01000000,0,'No SINGLE_UNIT files in Classic releases');
  const count=Math.ceil(block.normalSize/4096);
  if(!count) continue;
  assert.equal(block.flags>>>0,0x80000200,'Standard sector compression only');
  const stored=data.subarray(map.archive.headerOffset+block.offset,map.archive.headerOffset+block.offset+block.compressedSize);
  assert.equal(stored.readUInt32LE(0),(count+1)*4,'Exact sector offset table size');
  assert.equal(stored.readUInt32LE(count*4),stored.length,'Last sector ends at the block boundary');
  const decoded=[];
  for(let n=0;n<count;n++) {
    const start=stored.readUInt32LE(n*4),end=stored.readUInt32LE((n+1)*4);
    const expected=Math.min(4096,block.normalSize-n*4096);
    assert.ok(end>start && end-start<=expected,'Bounded compressed/stored sector');
    const sector=stored.subarray(start,end);
    let bytes=sector;
    if(sector.length<expected) {
      assert.equal(sector[0],2,'Classic zlib compression mask');
      bytes=zlib.inflateSync(sector.subarray(1),{maxOutputLength:4096});
    }
    assert.equal(bytes.length,expected,'Each sector expands to at most 4096 bytes');
    decoded.push(bytes);
  }
  const restored=Buffer.concat(decoded);
  assert.deepEqual(restored,Buffer.from(file.bytes()),'Native zlib and MPQ reader agree');
  if(file.name!=='(listfile)') assert.deepEqual(restored,fs.readFileSync(path.join(root,'build/map',file.name)),`Sector round trip: ${file.name}`);
}
const formats = {
  'war3map.w3i': 'w3i', 'war3map.w3e': 'w3e', 'war3map.wpm': 'wpm',
  'war3map.w3u': 'w3u', 'war3map.w3q': 'w3d',
  'war3map.w3a': 'w3d', 'war3map.w3b': 'w3u',
  'war3map.w3t': 'w3u', 'war3map.w3h': 'w3u',
  'war3map.doo': 'doo', 'war3mapUnits.doo': 'unitsdoo',
  'war3map.w3r': 'w3r', 'war3map.w3c': 'w3c', 'war3map.w3s': 'w3s',
  'war3map.imp': 'imp',
};
const parsed = {};
for (const [name, format] of Object.entries(formats)) {
  const file = map.get(name);
  assert.ok(file, name);
  const payload = new Uint8Array(file.arrayBuffer());
  assert.deepEqual(Buffer.from(payload), fs.readFileSync(path.join(root, 'build/map', name)), `MPQ extraction: ${name}`);
  const Parser = require(prefix + `w3x/${format}/file`).default;
  const object = new Parser();
  object.load(payload);
  assert.equal(object.getByteLength(), payload.byteLength, `No trailing or missing bytes: ${name}`);
  parsed[name] = object;
}
const info = parsed['war3map.w3i'];
// A structurally valid W3T can still crash Classic when an oldId does not exist.
// Check emitted objects and their references against independent stock SLK IDs.
const stockIds=require('../map/classic-object-ids.json').tables;
const objectTables={items:'war3map.w3t',units:'war3map.w3u',abilities:'war3map.w3a',upgrades:'war3map.w3q',destructables:'war3map.w3b',buffs:'war3map.w3h'};
const knownIds={};
for(const [kind,file] of Object.entries(objectTables)) {
  const stock=new Set(stockIds[kind]);
  const table=parsed[file];
  knownIds[kind]=new Set(stock);
  for(const object of table.originalTable.objects) assert.ok(stock.has(object.oldId),`${file}: unknown original ${object.oldId}`);
  for(const object of table.customTable.objects) {
    assert.ok(stock.has(object.oldId),`${file}: ${object.newId} has nonexistent Classic base ${object.oldId}`);
    assert.ok(!knownIds[kind].has(object.newId),`${file}: duplicate/stock collision ${object.newId}`);
    knownIds[kind].add(object.newId);
  }
}
const referenceKinds={usei:'items',iabi:'abilities',uabi:'abilities',uhab:'abilities',utra:'units',uupt:'units',ures:'upgrades',upgr:'upgrades',abuf:'buffs'};
for(const file of Object.values(objectTables)) for(const object of [...parsed[file].originalTable.objects,...parsed[file].customTable.objects]) {
  for(const mod of object.modifications) {
    const kind=referenceKinds[mod.id];
    if(!kind || !mod.value) continue;
    for(const id of mod.value.split(',')) assert.ok(knownIds[kind].has(id),`${file}: ${object.newId || object.oldId} ${mod.id} references nonexistent ${id}`);
  }
}
assert.ok(knownIds.items.has('gcel') && knownIds.items.has('rwiz'));
assert.ok(!knownIds.items.has('glov') && !knownIds.items.has('sobi'),'Reject the invalid bases from 0.10.0');
console.log('PASS: All object bases, rawcode uniqueness, shop stock and unit/item ability references exist in Classic data.');
assert.equal(info.version, 25, 'Classic TFT info format');
assert.equal(info.players.length, 12);
assert.equal(info.forces.length, 4);
for (let t = 0; t < 4; t++) {
  const force = info.forces[t];
  assert.equal(force.playerMasks, 7 << (t*3), `Team ${t+1} has exactly three players`);
  assert.equal(force.flags & 0x0B, 0x0B, 'Allied, shared victory, shared vision');
}
const terrain = parsed['war3map.w3e'];
assert.equal(terrain.version, 11);
assert.deepEqual(Array.from(terrain.mapSize), [97, 97]);
assert.equal(terrain.corners.length, 97);
assert.equal(terrain.corners[0].length, 97);
const wpm = parsed['war3map.wpm'];
assert.deepEqual(Array.from(wpm.size), [384, 384]);
assert.equal(wpm.pathing[192*384+192] & 2, 0, 'Center must be walkable');
assert.ok(wpm.pathing[0] & 2, 'Outer boundary must block walking');
const custom = parsed['war3map.w3u'].customTable.objects;
// UnitMetaData.slk: defense and defense upgrade are int; modelScale is real.
// A float carrying the number 1 is not an integer carrying the number 1.
for(const unit of custom) for(const mod of unit.modifications) {
  const expected={udef:0,udup:0,usca:1}[mod.id];
  if(expected!==undefined) assert.equal(mod.variableType,expected,`${unit.newId}: Classic ${mod.id} binary type`);
}
assert.equal(races.length, 4);
assert.equal(heroes.length, 50);
assert.equal(new Set(heroes.map(h => h.id)).size, 50);
assert.deepEqual([0,1,2,3,4,5,6,7,8].map(g => heroes.filter(h => h.group === g).length), [4,4,4,4,8,6,6,5,5]);
assert.equal(custom.filter(o=>o.newId.startsWith('fm')).length,20,'Exactly one troop type per race/tier');
assert.equal(new Set(custom.map(o => o.newId)).size,custom.length,'Unique custom rawcodes');
for (let race = 0; race < 4; race++) {
  for (let tier = 0; tier < 5; tier++) {
    const troop=custom.find(o=>o.newId===`fm${race}${tier}`);
    assert.equal(troop.oldId,races[race].units[tier]);
    assert.equal(troop.modifications.find(m=>m.id==='upgr').value,'Rfat,Rfar,Rfhp,Rfa2,Rfr2,Rfh2');
  }
}
const gear=require('../map/equipment.json');
const supreme=require('../map/supreme.json');const potions=require('../map/potions.json');const books=require('../map/books.json');const utility=require('../map/utility.json');
const gearAbilities=parsed['war3map.w3a'].customTable.objects;
assert.equal(gearAbilities.length,516,'Equipment, 100 custom hero skills and bounded expansion aura');
assert.equal(parsed['war3map.w3b'].customTable.objects[0].newId, 'fwll');
const research = parsed['war3map.w3q'].customTable.objects;
const fieldIndex=new WeakMap();
const value=(object,id,level=0)=>{
  if(!fieldIndex.has(object)) fieldIndex.set(object,new Map(object.modifications.map(m=>[m.id+':'+(m.levelOrVariation||0),m.value])));
  return fieldIndex.get(object).get(id+':'+level);
};
assert.equal(research.length, 8);
assert.equal(balance.health_percent,0.1);
assert.equal(value(research.find(o=>o.newId==='Rfhp'),'gglb'),151);
assert.equal(value(research.find(o=>o.newId==='Rfhp'),'gglm'),101);
assert.equal(balance.bot_tactics.length,5);
assert.ok(balance.bot_tactics[1].gear_percent>balance.bot_tactics[0].gear_percent);
assert.ok(balance.bot_tactics[2].gear_percent<balance.bot_tactics[0].gear_percent);
for (const [col,id,effect] of [[0,'Rfat','ratx'],[1,'Rfar','rarm'],[2,'Rfhp','rhpo'],[3,'Rfti','rhpx']]) {
  const upgrade = research.find(o => o.newId===id);
  assert.equal(value(upgrade,'glvl'),col===3 ? 4 : 10);
  assert.equal(value(upgrade,'gbpx'),col);
  assert.equal(value(upgrade,'gbpy'),0);
  assert.equal(value(upgrade,'gef1'),effect);
  const amount=[4,1.5,0.1,25350][col];
  assert.ok(Math.abs(value(upgrade,'gba1')-amount)<1e-6);
  assert.ok(Math.abs(value(upgrade,'gmo1')-amount)<1e-6,'Every additional research rank must increase the effect');
  const advanced=col===3 ? null : research.find(o=>o.newId===['Rfa2','Rfr2','Rfh2'][col]);
  if(advanced) {
   assert.equal(value(advanced,'glvl'),190);assert.equal(value(advanced,'gbpx'),col);
   assert.equal(value(advanced,'gglb'),(value(upgrade,'gglb')+10*value(upgrade,'gglm'))*1);
   assert.equal(value(advanced,'gglm'),value(upgrade,'gglm')*1);
   assert.equal(value(advanced,'gef1'),effect);
  }
  for (const rank of col===3 ? [1,2,4] : [1,2,10,11,20,200]) {
    const early=Math.min(rank,col===3 ? 4 : 10);
    let total=value(upgrade,'gba1')+value(upgrade,'gmo1')*(early-1);
    if(rank>10 && advanced) total+=value(advanced,'gba1')+value(advanced,'gmo1')*(rank-11);
    assert.ok(Math.abs(total-amount*rank)<1e-4,'Combined native research effects keep the same total bonuses');
  }
  for (let rank=1;rank<=(col===3 ? 4 : 10);rank++) assert.ok(value(upgrade,'gtp1',rank));
  if(advanced) for(let rank=1;rank<=190;rank++) {
   assert.ok(value(advanced,'gtp1',rank).includes(String(rank+10)));
   assert.equal(value(advanced,'greq',rank),id);assert.equal(value(advanced,'grqc',rank),'10');
  }
}
const barracks = custom.find(o => o.newId==='fbax');
assert.equal(value(barracks,'ures'),'Rfat,Rfar,Rfhp,Rfti,Rfa2,Rfr2,Rfh2,Rfwn');
assert.equal(value(barracks,'uabi'),'Fbr0,Fbr1,Fbr2,Fbr3','Four native army branch cards, no modal research menu');
assert.equal(value(barracks,'upgr'),'Rfti','Barracks receives its HP research');
const abilities = parsed['war3map.w3a'].originalTable.objects;
assert.equal(abilities.length,105,'96 hero skills plus 9 engineering variants');
for (const hero of heroes) {
  for (const [slot,id] of hero.skills.entries()) {
    const ability = abilities.find(o => o.oldId===id) || gearAbilities.find(o=>o.newId===id);
    const cap = slot===3 ? 50 : 200;
    assert.equal(value(ability,'alev'),cap);
    assert.equal(value(ability,'arlv'),slot===3 ? 6 : 1);
    assert.equal(value(ability,'alsk'),slot===3 ? 10 : 1);
    for (let rank=1;rank<=cap;rank++) assert.ok(value(ability,'atp1',rank),`${id}: level ${rank} exists`);
  }
}
const misc = map.get('war3mapMisc.txt').text();
assert.match(misc,/MaxHeroLevel=500/);
assert.match(misc,/NeedHeroXPFormulaA=1.0/,'Classic experience formula explicitly configured through level 500');
const unitById=new Map(custom.map(o=>[o.newId,o]));
const summonFields=new Set(['Hwe1','Osf1','Efnu','Esvu','Nbau','Ndou','Nef1','Nsy2','Nsyu','Rai3','Uin4','Ntou','Ulsu']);
for(const ability of abilities) {
  for(const mod of ability.modifications) {
    if(!summonFields.has(mod.id)) continue;
    for(const id of mod.value.split(',')) {
      const pet=unitById.get(id);
      assert.ok(pet,`${ability.oldId} rank ${mod.levelOrVariation}: summon exists`);
      assert.ok(value(pet,'uhpm')>0);
      assert.ok(value(pet,'usca')>0 && value(pet,'ucol')<=40,'Visual growth must not block tunnels');
      assert.equal(value(pet,'upgr'),'','Pet strength follows its skill, not army research');
    }
  }
}
const lava=abilities.find(o=>o.oldId==='ANlm');
let previousHP=0,previousSize=0,previousDamage=-1;
for(let rank=1;rank<=200;rank++) {
  const pet=unitById.get(value(lava,'Hwe1',rank));
  assert.ok(value(pet,'uhpm')>previousHP,'Lava Spawn HP grows at every skill rank');
  assert.ok(value(pet,'usca')>previousSize,'Lava Spawn size grows at every skill rank');
  assert.ok(value(pet,'ua1b')>previousDamage,'Lava Spawn damage grows at every skill rank');
  assert.equal(value(lava,'Hwe2',rank),1+Math.floor(rank/10),'Extra summon at ranks 10, 20, ... 300');
  previousHP=value(pet,'uhpm');previousSize=value(pet,'usca');previousDamage=value(pet,'ua1b');
}
assert.ok(previousHP>30000*balance.summon_hp_multiplier,'High-rank summons are substantially stronger');
const abilityById=new Map(abilities.map(o=>[o.oldId,o]));
assert.equal(value(abilityById.get('ANms'),'Nms2',200),1,'Mana Shield absorption remains a valid fraction');
assert.ok(value(abilityById.get('AOcl'),'Ocl3',200)<=value(abilityById.get('AOcl'),'Ocl3',3),'Chain lightning falloff improves');
assert.ok(value(abilityById.get('AUts'),'Uts2',200)<=1,'Thorns must not increase damage received');
assert.ok(value(abilityById.get('AOae'),'Oae2',200)>value(abilityById.get('AOae'),'Oae2',3),'Endurance Aura continues growing');
assert.equal(balance.spawn_seconds,18);
const shopItems = require('../map/items.json');
assert.equal(parsed['war3map.w3t'].customTable.objects.length,shopItems.length+gear.length+supreme.length+potions.length+books.length+utility.length);
assert.equal(value(custom.find(o => o.newId==='fshp'),'usei'),shopItems.map(i=>i.id).join(','));
for (const item of shopItems) assert.equal(value(parsed['war3map.w3t'].customTable.objects.find(o=>o.newId===item.id),'igol'),item.cost);
assert.equal(gear.length,36);
assert.match(misc,/StrHitPointBonus=30/);
assert.match(misc,/IntManaBonus=18/);
const effectSpec={attack:['Iatt',0,1],armor:['Idef',0,1],strength:['Istr',0,3],agility:['Iagi',0,1],intelligence:['Iint',0,2],health:['Ilif',0,1],mana:['Iman',0,1],health_regen:['Ihpr',0,1],mana_regen:['Imrp',2,1],move_speed:['Imvb',0,1],attack_speed:['Isx1',2,1],fire_dps:['Icfd',0,1],lifesteal:['Ivam',2,1],critical_chance:['Ocr1',2,1],critical_multiplier:['Ocr2',2,2]};
for(let shop=0;shop<5;shop++) {
  const seller=custom.find(o=>o.newId===`fs${shop}p`);
  assert.equal(value(seller,'usei'),gear.filter(i=>i.shop===shop).map(i=>i.id).join(','));
  assert.ok(gear.filter(i=>i.shop===shop).length<=9,'Room for native shop controls');
}
for(const item of [...gear,...supreme]) {
  const obj=parsed['war3map.w3t'].customTable.objects.find(o=>o.newId===item.id);
  assert.equal(value(obj,'igol'),item.cost);
  const effects=value(obj,'iabi').split(',').map(id=>gearAbilities.find(o=>o.newId===id));
  assert.equal(effects.length,Object.keys(item.stats).length-('critical_multiplier' in item.stats ? 1 : 0));
  for(const [stat,amount] of Object.entries(item.stats)) {
    const [field,type,column]=effectSpec[stat];
    const mod=effects.flatMap(o=>o.modifications).find(m=>m.id===field);
    assert.ok(mod,`${item.id}: ${stat} has a real ability effect`);
    assert.equal(mod.variableType,type);assert.equal(mod.levelOrVariation,1);assert.equal(mod.dataPointer,column);
    assert.ok(Math.abs(mod.value-amount)<1e-5);
  }
}
assert.equal(value(barracks,'uhpm'),50700);
assert.equal(value(custom.find(o=>o.newId==='ftow'),'uhpm'),7800);
const bastion=custom.find(o=>o.newId==='fbst');
assert.equal(value(bastion,'uhpm'),156000);
assert.equal(value(bastion,'udef'),24);
assert.equal(value(bastion,'ua1b'),1750);
assert.equal(value(bastion,'ua1r'),1400);
assert.ok(Math.abs(value(bastion,'ua1c')-0.2)<1e-6);
assert.equal(value(bastion,'uabi'),'','Bastions must remain vulnerable');
assert.equal(value(bastion,'uhpr'),0,'No hidden tower healing');
assert.match(misc,/HeroFactorXP=50,50,50,50,50/);
assert.match(misc,/GrantHeroXP=50,60,80,110,150/);
assert.match(misc,/GrantHeroXPFormulaC=50/);
for(const h of heroes) {
 assert.equal(new Set(h.gear_families).size,6,'Unique categories in each hero loadout');
 assert.ok(h.gear_families.every(f=>f>=0 && f<12));
 if(h.skills.includes('AOcr') || h.skills.includes('ANdb')) assert.ok(!h.gear_families.includes(11),'No redundant critical-strike item');
 if(h.skills.includes('AUav')) assert.ok(!h.gear_families.includes(10),'Dreadlord already has vampirism');
 if(h.autocast) assert.ok(!h.gear_families.includes(10),'No competing lifesteal orb on autocast arrow heroes');
}
assert.equal(value(custom.find(o=>o.newId==='ffnt'),'uabi'),'Avul,FfHP,FfMP','Both native regeneration auras are installed on the fountain');
assert.equal(value(custom.find(o=>o.newId==='ffnt'),'upat'),'','Fountain has no large blocking footprint at the rally point');
for(const [id,base,field,flag] of [['FfHP','ACnr','Oar1','Oar2'],['FfMP','ANre','Arm1','Arm2']]) {
 const aura=gearAbilities.find(o=>o.newId===id);
 assert.equal(aura.oldId,base,'Use proven native fountain aura prototypes');
 assert.equal(value(aura,'atar',1),'ground,air,hero,vuln,invu','Every hero: no organic, allied or enemy-only restriction');
 assert.equal(value(aura,'aare',1),1000);
 assert.ok(Math.abs(value(aura,field,1)-0.015)<1e-6);
 assert.equal(value(aura,flag,1),1,'Regeneration is a percentage of maximum pool');
}
assert.match(misc,/MaxUnitSpeed=480/);
const arrow=abilityById.get('ANba');
for(const rank of [1,10,200]) {
 assert.equal(value(arrow,'atar',rank),'air,ground,enemy,neutral','Black Arrow includes undead troop classes');
 assert.equal(value(arrow,'ahdu',rank),2);
 assert.ok(unitById.has(value(arrow,'Nbau',rank)) && value(arrow,'Nba2',rank)>0);
}
for (const player of info.players) {
  const [x, y] = player.startLocation;
  assert.ok(Math.abs(x) < 5888 && Math.abs(y) < 5888, 'Start inside playable bounds');
  const px = Math.floor((x+6144)/32), py = Math.floor((y+6144)/32);
  assert.equal(wpm.pathing[py*384+px] & 2, 0, 'Base starts must be walkable');
}
const script = map.get('war3map.j').text();
assert.equal(script, fs.readFileSync(path.join(root, 'build/map/war3map.j'), 'utf8'));
assert.ok(!/\b(?:Blz\w+|Dz\w+|ExecuteFunc)\s*\(/.test(script), 'No modern or external API');
// Legacy Warcraft's parser must not see type names reused as identifiers.
// A permissive pjass invocation accepts e.g. "boolean force"; use +shadow too.
const jassTypes = new Set(`integer real boolean string code handle nothing
agent event player widget unit destructable item ability buff force group trigger
triggercondition triggeraction timer location region rect boolexpr sound conditionfunc
filterfunc unitpool itempool race alliancetype racepreference gamestate igamestate
fgamestate playerstate playerscore playergameresult unitstate aidifficulty eventid
gameevent playerevent playerunitevent unitevent limitop widgetevent dialogevent
unittype gamespeed gamedifficulty gametype mapflag mapvisibility mapsetting mapdensity
mapcontrol playerslotstate volumegroup camerafield camerasetup playercolor placement
startlocprio raritycontrol blendmode texmapflags effect effecttype weathereffect
terraindeformation fogstate fogmodifier dialog button quest questitem defeatcondition
timerdialog leaderboard multiboard multiboarditem trackable gamecache version itemtype
texttag attacktype damagetype weapontype soundtype lightning pathingtype image ubersplat
hashtable`.split(/\s+/));
function checkIdentifiers(source) {
  for (const match of source.matchAll(/^function\s+(\w+)\s+takes\s+(.+?)\s+returns\s+\w+/gm)) {
    assert.ok(!jassTypes.has(match[1]), `Function shadows JASS type: ${match[1]}`);
    if (match[2] !== 'nothing') {
      for (const argument of match[2].split(',')) {
        const name = argument.trim().split(/\s+/)[1];
        assert.ok(!jassTypes.has(name), `Parameter shadows JASS type: ${name}`);
      }
    }
  }
  for (const match of source.matchAll(/^\s*(?:local\s+|constant\s+)?\w+\s+(?:array\s+)?(\w+)\s*(?:=|$)/gm)) {
    assert.ok(!jassTypes.has(match[1]), `Variable shadows JASS type: ${match[1]}`);
  }
}
assert.throws(() => checkIdentifiers('function Example takes boolean force returns nothing\nendfunction'), /Parameter shadows JASS type: force/, 'Detect the 0.1.0 Classic parser regression');
checkIdentifiers(script);
console.log('PASS: MPQ, 15 binary formats, five research buttons (200/200/200/4/20), 500 hero levels, 200/50 skill caps, 61 shop items, 12 slots, 50 heroes and 20 army variants and rank-specific summons.');

// Native portrait picker: every card is free and appears on exactly one page.
// Classic ARal reserves (3,1) even on a building with a custom ability list.
// The user's screenshot confirmed it hid every eighth card (including Alchemist).
const visibleCards=[];
for(let page=0;page<8;page++) {
 const picker=custom.find(o=>o.newId===`fpk${page}`);
 assert.equal(picker.oldId,'hbar');
 assert.equal(value(picker,'utra'),heroes.slice(page*7,page*7+7).map((h,i)=>`fp${String(page*7+i).padStart(2,'0')}`).join(','));
 assert.equal(value(picker,'uabi'),'Fprv,Fnxt,Frnd,Fmod');
 assert.equal(value(picker,'upat'),'');
 const occupied=new Set(['3,1']); // native rally point
 for(const id of value(picker,'uabi').split(',')){
  const control=gearAbilities.find(a=>a.newId===id);
  const cell=`${value(control,'abpx')},${value(control,'abpy')}`;
  assert(!occupied.has(cell),'Picker control cannot overlap a native command');occupied.add(cell);
 }
 for(const id of value(picker,'utra').split(',')){
  const card=custom.find(u=>u.newId===id);
  const cell=`${value(card,'ubpx')},${value(card,'ubpy')}`;
  assert(!occupied.has(cell),`${id} must not be hidden by Rally or another button`);occupied.add(cell);visibleCards.push(id);
 }
}
assert.equal(visibleCards.length,50);assert.equal(new Set(visibleCards).size,50);
assert.equal(value(custom.find(u=>u.newId==='fpk3'),'utra').split(',')[2],'fp23','Alchemist visible on page4 row1 column3');
assert.match(script,/constant integer PICK_CARDS_PER_PAGE = 7/);
assert.match(script,/constant integer PICK_PAGE_COUNT = 8/);
for(const [idx,hero] of heroes.entries()) {
 const card=custom.find(o=>o.newId===`fp${String(idx).padStart(2,'0')}`);
 assert.equal(card.oldId,'hpea','No native hero training limit for selection cards');
 assert.equal(value(card,'uico'),hero.icon);
 assert.equal(value(card,'ugol'),0);assert.equal(value(card,'ufoo'),0);
 assert.equal(value(card,'ubpx'),idx%7%4);assert.equal(value(card,'ubpy'),Math.floor(idx%7/4));
 if(hero.base) {
  const unit=custom.find(o=>o.newId===hero.id);
  assert.equal(unit.oldId,hero.base);assert.equal(value(unit,'uhab'),[...hero.skills,'Fatr'].join(','));
  for(const [slot,id] of hero.skills.entries()) {
   const skill=gearAbilities.find(o=>o.newId===id);
   assert.equal(skill.oldId,hero.skill_sources[slot]);
   assert.equal(value(skill,'arpx'),slot);assert.equal(value(skill,'arpy'),0);
   assert.equal(value(skill,'abpx'),slot);assert.equal(value(skill,'abpy'),2);
  }
 }
}
for(const troop of custom.filter(o=>/^fm[0-3][0-4]$/.test(o.newId))) assert.equal(value(troop,'udup'),1);

// Fifth, native learnable skill: cumulative +2/rank, not a paid chat upgrade.
const stats=gearAbilities.find(o=>o.newId==='Fatr');
assert.equal(stats.oldId,'Aamk');assert.equal(value(stats,'aher'),1);assert.equal(value(stats,'alev'),500);
for(let rank=1;rank<=500;rank++) for(const field of ['Istr','Iagi','Iint']) assert.equal(value(stats,field,rank),rank*2);
const originalHeroes=parsed['war3map.w3u'].originalTable.objects;
for(const h of heroes.filter(h=>!h.base)) assert.equal(value(originalHeroes.find(o=>o.oldId===h.id),'uhab'),[...h.skills,'Fatr'].join(','));
const customHeroes=heroes.filter(h=>h.base);
assert.equal(customHeroes.length,26);
assert.equal(new Set(customHeroes.map(h=>h.model.toLowerCase())).size,26);
for(const h of customHeroes) {
 assert.ok(!heroes.filter(s=>!s.base).some(s=>s.stock_model.toLowerCase()===h.model.toLowerCase()));
 const u=unitById.get(h.id);assert.equal(value(u,'umdl'),h.model);assert.equal(value(u,'umvt'),'foot');
 assert.equal(value(u,'ustr'),h.stats.strength);assert.equal(value(u,'uagi'),h.stats.agility);assert.equal(value(u,'uint'),h.stats.intelligence);
 assert.equal(value(u,'uico'),h.icon);
}
// Evasion never exceeds 75%, including the alternate drunken-brawler field.
for(const a of [...abilities,...gearAbilities.filter(o=>o.newId!=='Fatr')]) {
 for(const m of a.modifications) if(m.id==='Eev1' || m.id==='Ocr4') assert.ok(m.value>=0 && m.value<=0.750001);
}
const immo=abilityById.get('AEim');
for(let rank=4;rank<=200;rank++) assert.ok(value(immo,'Eim1',rank)>value(immo,'Eim1',rank-1),'Immolation damage improves at EVERY rank, despite interval in label');
assert.ok(value(immo,'Eim1',200)>1000);assert.equal(value(immo,'Eim2',200),7,'Do not amplify ongoing mana drain');
assert.ok(value(abilityById.get('AEev'),'Eev1',10)<0.4,'Evasion must not hit its cap early');
assert.equal(value(abilityById.get('AEev'),'Eev1',200),0.75);
const alliedFont=unitById.get('fbfn');assert.equal(value(alliedFont,'uabi'),'Avul,FbHP,FbMP');
for(const [id,field,flag] of [['FbHP','Oar1','Oar2'],['FbMP','Arm1','Arm2']]) {
 const a=gearAbilities.find(o=>o.newId===id);assert.equal(value(a,'aare',1),1200);
 assert.equal(value(a,'atar',1),'ground,air,hero,friend,self,vuln,invu');
 assert.ok(Math.abs(value(a,field,1)-0.005)<1e-6);assert.equal(value(a,flag,1),1);
}
assert.equal(balance.army_cap,85);assert.equal(balance.spawn_units,6);assert.equal(balance.spawn_seconds,18);
console.log('PASS: 50 heroes / 26 unique creature models, +2 native attributes, 75% evasion, per-rank Immolation, allied native fountains and unchanged army/summon counts.');
for(const [id,gap] of [['AHds',8],['AHtb',1],['AEer',1],['AOhx',1]]) {
 const a=abilityById.get(id);assert.ok(value(a,'acdn',200)>=value(a,'ahdu',200)+gap-0.001,'No permanent shield/control from cooldown scaling');
}
for(const unit of customHeroes.map(h=>unitById.get(h.id))) for(const id of ['ustp','uagp','uinp']) assert.equal(unit.modifications.find(m=>m.id===id).variableType,2,'Classic hero growth uses unreal');
// Compare shipped 0.8.1 counts independently: optimization may not reduce creatures.
const previous=new War3Map();previous.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.8.1-alpha.w3x'))),true);require('./historical-wave-settings.cjs')(previous);
const PreviousAbilities=require(prefix+'w3x/w3d/file').default;
const previousAbilities=new PreviousAbilities();previousAbilities.load(new Uint8Array(previous.get('war3map.w3a').bytes()));
const quantities=new Set(['Hwe2','Osf2','Efn1','Esv1','Nba2','Ndo2','Rai1','Ucb5','Omi1']);
for(const old of previousAbilities.originalTable.objects) {
 const current=abilityById.get(old.oldId);
 for(const mod of old.modifications) if(quantities.has(mod.id) && mod.levelOrVariation<=value(current,'alev')) assert.equal(value(current,mod.id,mod.levelOrVariation),mod.value,'Creature/resurrection counts must match 0.8.1');
}
console.log('PASS: Unchanged creature and illusion counts match previous release at every rank.');
// Preserve technical flags/intervals against the historical baseline at retained ranks.
// New 200-rank curves and targeted Alchemist changes intentionally replace magnitudes.
const baseline=new War3Map();baseline.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.9.1-alpha.w3x'))),true);require('./historical-wave-settings.cjs')(baseline);
const baselineSkills=new PreviousAbilities();baselineSkills.load(new Uint8Array(baseline.get('war3map.w3a').bytes()));
const skillSeeds=require('../map/ability-seeds.json');
let technicalCompared=0;
for(const old of baselineSkills.originalTable.objects) {
 const now=abilityById.get(old.oldId),seed=skillSeeds[old.oldId];
 for(const f of seed.fields) {
  const technical=/flag|interval|unit type|normal form|mana cost|casting time|buffs|effects/i.test(f.label);
  if(summonFields.has(f.id) || !technical || /damage per interval|damage interval amount/i.test(f.label) || ['Emeu'].includes(f.id))continue;
  for(const m of old.modifications)if(m.id===f.id && m.levelOrVariation<=value(now,'alev')){
   assert.equal(value(now,m.id,m.levelOrVariation),m.value,'Preserve actual mechanics: '+old.oldId+':'+m.id);technicalCompared++;
  }
 }
}
assert.ok(technicalCompared>1000);
for(const id of ['AHtb','AHbz','AOsh','ANcs','ANab','ANfl']) assert.ok(value(abilityById.get(id),'acdn',1)>0);
console.log('PASS: Technical flags, intervals, stock mana costs and native effect references preserved across retained ranks.');
const allItems=parsed['war3map.w3t'].customTable.objects;
assert.equal(supreme.length,7);assert.deepEqual(supreme.map(i=>Object.keys(i.stats)[0]),['strength','agility','intelligence','armor','attack_speed','mana_regen','health_regen']);
assert.equal(value(custom.find(u=>u.newId==='fsup'),'usei'),supreme.map(i=>i.id).join(','));
assert.equal(value(custom.find(u=>u.newId==='fpot'),'usei'),potions.map(i=>i.id).join(','));
for(const i of supreme) {assert.ok(i.cost>=44000 && i.cost<=48000);assert.equal(value(allItems.find(o=>o.newId===i.id),'igol'),i.cost);}
for(const i of potions) {
 const obj=allItems.find(o=>o.newId===i.id);assert.equal(obj.oldId,i.base);assert.equal(value(obj,'igol'),i.cost);assert.equal(value(obj,'iabi'),i.ability);
 if(i.base_ability) {
  const effect=gearAbilities.find(o=>o.newId===i.ability);assert.equal(effect.oldId,i.base_ability);
  assert.equal(value(effect,i.field,1),i.amount);assert.equal(value(effect,'acdn',1),30);
 }
}
const previousUnits=new (require(prefix+'w3x/w3u/file').default)();previousUnits.load(new Uint8Array(baseline.get('war3map.w3u').bytes()));
for(const id of ['fbax','ftow','fbst','ffnt','fbfn','fshp','fs0p','fs1p','fs2p','fs3p','fs4p']) {
 const old=previousUnits.customTable.objects.find(o=>o.newId===id),now=unitById.get(id);
 assert.equal(value(now,'uhpm'),id==='fbax'?50700:id==='fbst'?156000:value(old,'uhpm')*1.3,'Requested building HP');
}
for(let kind=0;kind<heroes.length;kind++) {
 const list=[heroes[kind].primary,6,3,4,5,heroes[kind].primary===0?2:0];assert.equal(new Set(list).size,6);
}
// Army tiers and research are independently observable in the emitted objects.
for(let race=0;race<4;race++) for(let tier=0;tier<5;tier++) {
 const unit=unitById.get(`fm${race}${tier}`);
 assert.ok(Math.abs(value(unit,'usca')-0.7)<1e-6);assert.equal(value(unit,'ucol'),8);
 const traits=require('../map/army-traits.json').troops[unit.newId];
 const pyRound=x=>{const n=Math.floor(x);return x-n===.5?n+n%2:Math.round(x);};
 assert.equal(value(unit,'uhpm'),pyRound(balance.tiers[tier].hp*(traits?.hp_multiplier??1)));assert.equal(value(unit,'ua1b'),pyRound(balance.tiers[tier].damage*(traits?.damage_multiplier??1)));
 assert.equal(value(unit,'udup'),1);assert.equal(value(unit,'udu1'),3);
 if(tier>0) {
  assert.ok(balance.tiers[tier].hp>=balance.tiers[tier-1].hp*1.2 && balance.tiers[tier].hp<=balance.tiers[tier-1].hp*1.4);
  assert.ok(balance.tiers[tier].damage>=balance.tiers[tier-1].damage*1.2 && balance.tiers[tier].damage<=balance.tiers[tier-1].damage*1.4);
 }
}
assert.equal(value(research.find(o=>o.newId==='Rfat'),'gglb'),84);
assert.equal(value(research.find(o=>o.newId==='Rfat'),'gglm'),63);
assert.equal(value(research.find(o=>o.newId==='Rfar'),'gglb'),84);
assert.equal(value(research.find(o=>o.newId==='Rfar'),'gglm'),63);
assert.equal(value(custom.find(o=>o.newId==='fbks'),'usei'),books.map(i=>i.id).join(','));
assert.deepEqual(books.map(i=>[i.base,i.cost]),[['tst2',280],['tdx2',280],['tin2',280],['tkno',960]]);
for(const book of books) {
 const item=allItems.find(o=>o.newId===book.id);assert.equal(item.oldId,book.base);assert.equal(value(item,'igol'),book.cost);
 assert.equal(value(item,'ilum'),0);assert.ok(!item.modifications.some(m=>m.id==='iabi'),'Inherit the native +2 / level power-up effect');
}
for(let rank=1;rank<=50;rank++) {
 const pad=String(rank).padStart(2,'0');
 const infernal=unitById.get(value(abilityById.get('AUin'),'Uin4',rank));
 assert.ok(value(infernal,'uhpm')>=2295 && value(infernal,'ua1b')>=55);
 assert.ok(value(infernal,'uabi').includes('Fi'+pad));
 const fire=gearAbilities.find(a=>a.newId==='Fi'+pad);
 assert.equal(fire.oldId,'ANpi');assert.ok(Math.abs(value(fire,'Eim1',1)-36*(1+0.18*(rank-1)))<0.001);
 assert.equal(value(fire,'atar',1),'ground,air,enemy,neutral');
 const vengeance=gearAbilities.find(a=>a.newId==='Fv'+pad);
 const spirit=unitById.get(value(vengeance,'Rai3',1));assert.equal(spirit.oldId,'even');assert.ok(value(spirit,'ua1b')>0);
 const rebirth=gearAbilities.find(a=>a.newId==='Fh'+pad);
 const phoenix=unitById.get(value(rebirth,'Eme1',1)),egg=unitById.get(value(rebirth,'Emeu',1));
 assert.equal(phoenix.oldId,'hphx');assert.equal(egg.oldId,'hpxe');
 assert.ok(value(phoenix,'uabi').includes(rebirth.newId) && value(egg,'uabi').includes(rebirth.newId),'Phoenix keeps its rank after hatching');
 const tornado=gearAbilities.find(a=>a.newId==='Ft'+pad);
 assert.equal(tornado.oldId,'Atdg');assert.ok(!tornado.modifications.some(m=>m.id==='Tdg2'),'Do not scale the medium damage radius as damage');
 assert.ok(!gearAbilities.some(a=>a.newId==='Fq'+pad),'Keep native tornado control timing');
 assert.ok(value(abilityById.get('AUdd'),'Udd1',rank)<=0.350001,'Percent max-HP damage remains bounded');
}
console.log('PASS: Stronger army tiers, reviewed research effects and 20% lower prices, compact models, four native books and rank-specific ultimate secondary effects.');
const auraLimits={AUau:{Uau1:[0.15,0.30],Uau2:[6,80]},AHab:{Hab1:[3,40]},AHad:{Had1:[6,35]},AOae:{Oae1:[0.15,0.30],Oae2:[0.15,0.60]},AEar:{Ear1:[0.20,0.60]},AEah:{Eah1:[0.20,0.50]},AUav:{Uav1:[0.20,0.50]}};
for(const [id,fields] of Object.entries(auraLimits)) {
 const aura=abilityById.get(id);
 const copies=heroes.filter(h=>!h.simple&&h.skill_sources?.includes(id)).map(h=>gearAbilities.find(a=>a.newId===h.skills[h.skill_sources.indexOf(id)]));
 for(const [field,[start,cap]] of Object.entries(fields)) for(const effect of [aura,...copies]) {
  let previous=start-1;
  for(let rank=1;rank<=200;rank++) {
   const amount=value(effect,field,rank);
   assert.ok(amount>=start-1e-5 && amount<=cap+1e-5);
   assert.ok(amount>previous,'Aura ranks progress monotonically without runaway growth');previous=amount;
   if(rank===1) assert.ok(Math.abs(amount-start)<1e-5,'Useful aura bonus from rank one');
   if(rank===200) assert.ok(Math.abs(amount-cap)<1e-5,'Exact final aura cap');
  }
 }
 assert.match(value(aura,'aub1',1),/предел/,'Aura tooltip explains the limit');
}
assert.equal(value(abilityById.get('AUau'),'Uau3',1),0,'Unholy uses flat HP/sec, not a percentage of natural regeneration');
assert.equal(value(abilityById.get('AHab'),'Hab2',1),0,'Brilliance uses flat mana/sec');
// Summon rawcodes are regenerated after reducing the cap; compare mechanics by
// each ability's referenced unit, not by obsolete generated array indices.
for(const a of abilities)for(const m of a.modifications)if(summonFields.has(m.id))for(const id of m.value.split(',')){
 const u=unitById.get(id);assert(u && value(u,'uhpm')>0 && value(u,'ua1b')>=0);
}
console.log('PASS: Seven useful capped auras, all 200 ranks/custom copies, and the reviewed Infernal/troop tier reductions.');
console.log('PASS: Seven supreme items, four consumable potions, +30% building HP and full item effect/price validation.');

assert.deepEqual(balance.tiers.map(t=>[t.hp,t.damage,t.armor]),[[380,13,1],[500,18,2],[650,23,3],[850,30,4],[1100,40,5]]);
const recentMap=new War3Map();recentMap.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.13.1-alpha.w3x'))),true);require('./historical-wave-settings.cjs')(recentMap);
const recentUnits=new (require(prefix+'w3x/w3u/file').default)();recentUnits.load(new Uint8Array(recentMap.get('war3map.w3u').bytes()));
const recentAbilityData=new PreviousAbilities();recentAbilityData.load(new Uint8Array(recentMap.get('war3map.w3a').bytes()));
const recentInferno=recentAbilityData.originalTable.objects.find(a=>a.oldId==='AUin');
for(let rank=1;rank<=50;rank++){
 const old=recentUnits.customTable.objects.find(u=>u.newId===value(recentInferno,'Uin4',rank));
 const current=unitById.get(value(abilityById.get('AUin'),'Uin4',rank));
 for(const field of ['uhpm','ua1b','udef']) assert.ok(Math.abs(value(current,field)-value(old,field)*0.6*(field==='uhpm'?balance.summon_hp_multiplier:field==='ua1b'?balance.summon_damage_multiplier:1))<=(field==='udef'?1:1.35),'Infernal reduction preserved by skill rank despite regenerated IDs');
}
console.log('PASS: Moderate 20-40% tier steps and a further 40% Infernal reduction at every rank.');
