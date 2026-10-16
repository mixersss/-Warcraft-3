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
  'war3map.w3t': 'w3u',
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
assert.equal(heroes.length, 36);
assert.equal(new Set(heroes.map(h => h.id)).size, 36);
assert.deepEqual([0,1,2,3,4,5,6].map(g => heroes.filter(h => h.group === g).length), [4,4,4,4,8,6,6]);
assert.equal(custom.filter(o=>o.newId.startsWith('fm')).length,20,'Exactly one troop type per race/tier');
assert.equal(new Set(custom.map(o => o.newId)).size,custom.length,'Unique custom rawcodes');
for (let race = 0; race < 4; race++) {
  for (let tier = 0; tier < 5; tier++) {
    const troop=custom.find(o=>o.newId===`fm${race}${tier}`);
    assert.equal(troop.oldId,races[race].units[tier]);
    assert.equal(troop.modifications.find(m=>m.id==='upgr').value,'Rfat,Rfar,Rfhp');
  }
}
const gear=require('../map/equipment.json');
const gearAbilities=parsed['war3map.w3a'].customTable.objects;
assert.equal(gearAbilities.length,114,'Passive equipment effects');
assert.equal(parsed['war3map.w3b'].customTable.objects[0].newId, 'fwll');
const research = parsed['war3map.w3q'].customTable.objects;
const fieldIndex=new WeakMap();
const value=(object,id,level=0)=>{
  if(!fieldIndex.has(object)) fieldIndex.set(object,new Map(object.modifications.map(m=>[m.id+':'+(m.levelOrVariation||0),m.value])));
  return fieldIndex.get(object).get(id+':'+level);
};
assert.equal(research.length, 4);
for (const [col,id,effect] of [[0,'Rfat','ratx'],[1,'Rfar','rarm'],[2,'Rfhp','rhpo'],[3,'Rfti','rhpx']]) {
  const upgrade = research.find(o => o.newId===id);
  assert.equal(value(upgrade,'glvl'),col===3 ? 4 : 200);
  assert.equal(value(upgrade,'gbpx'),col);
  assert.equal(value(upgrade,'gbpy'),0);
  assert.equal(value(upgrade,'gef1'),effect);
  const amount=[6,2,0.2,15000][col];
  assert.ok(Math.abs(value(upgrade,'gba1')-amount)<1e-6);
  assert.ok(Math.abs(value(upgrade,'gmo1')-amount)<1e-6,'Every additional research rank must increase the effect');
  for (const rank of col===3 ? [1,2,4] : [1,2,10,200]) {
    const total=value(upgrade,'gba1')+value(upgrade,'gmo1')*(rank-1);
    assert.ok(Math.abs(total-amount*rank)<1e-4,'Classic effect = base + increment x (rank - 1)');
  }
  for (let rank=1;rank<=(col===3 ? 4 : 200);rank++) assert.ok(value(upgrade,'gtp1',rank), 'Every research rank has a command-card tooltip');
}
const barracks = custom.find(o => o.newId==='fbax');
assert.equal(value(barracks,'ures'),'Rfat,Rfar,Rfhp,Rfti');
assert.equal(value(barracks,'uabi'),'','No modal upgrade-menu ability');
assert.equal(value(barracks,'upgr'),'Rfti','Barracks receives its HP research');
const abilities = parsed['war3map.w3a'].originalTable.objects;
assert.equal(abilities.length,105,'96 hero skills plus 9 engineering variants');
for (const hero of heroes) {
  for (const [slot,id] of hero.skills.entries()) {
    const ability = abilities.find(o => o.oldId===id) || gearAbilities.find(o=>o.newId===id);
    const cap = slot===3 ? 50 : 300;
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
for(let rank=1;rank<=300;rank++) {
  const pet=unitById.get(value(lava,'Hwe1',rank));
  assert.ok(value(pet,'uhpm')>previousHP,'Lava Spawn HP grows at every skill rank');
  assert.ok(value(pet,'usca')>previousSize,'Lava Spawn size grows at every skill rank');
  assert.ok(value(pet,'ua1b')>previousDamage,'Lava Spawn damage grows at every skill rank');
  assert.equal(value(lava,'Hwe2',rank),1+Math.floor(rank/10),'Extra summon at ranks 10, 20, ... 300');
  previousHP=value(pet,'uhpm');previousSize=value(pet,'usca');previousDamage=value(pet,'ua1b');
}
assert.ok(previousHP>30000,'High-rank summons are substantially stronger');
const abilityById=new Map(abilities.map(o=>[o.oldId,o]));
assert.equal(value(abilityById.get('ANms'),'Nms2',300),1,'Mana Shield absorption remains a valid fraction');
assert.ok(value(abilityById.get('AOcl'),'Ocl3',300)<=value(abilityById.get('AOcl'),'Ocl3',3),'Chain lightning falloff improves');
assert.ok(value(abilityById.get('AUts'),'Uts2',300)<=1,'Thorns must not increase damage received');
assert.ok(value(abilityById.get('AOae'),'Oae2',300)>value(abilityById.get('AOae'),'Oae2',3),'Endurance Aura continues growing');
assert.equal(balance.spawn_seconds,12);
const shopItems = require('../map/items.json');
assert.equal(parsed['war3map.w3t'].customTable.objects.length,shopItems.length+gear.length);
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
for(const item of gear) {
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
assert.equal(value(barracks,'uhpm'),30000);
assert.equal(value(custom.find(o=>o.newId==='ftow'),'uhpm'),6000);
const bastion=custom.find(o=>o.newId==='fbst');
assert.equal(value(bastion,'uhpm'),60000);
assert.equal(value(bastion,'udef'),24);
assert.equal(value(bastion,'ua1b'),700);
assert.equal(value(bastion,'ua1r'),1000);
assert.ok(Math.abs(value(bastion,'ua1c')-0.75)<1e-6);
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
for(const rank of [1,10,300]) {
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
console.log('PASS: MPQ, 14 binary formats, 4 command-card research columns (200/200/200/4), 500 hero levels, 300/50 skill caps, 46 shop items, 12 slots, 36 heroes and 20 army variants and rank-specific summons.');

// Native portrait picker: every card is free and appears on exactly one page.
for(let page=0;page<5;page++) {
 const picker=custom.find(o=>o.newId===`fpk${page}`);
 assert.equal(picker.oldId,'hbar');
 assert.equal(value(picker,'utra'),heroes.slice(page*8,page*8+8).map((h,i)=>`fp${String(page*8+i).padStart(2,'0')}`).join(','));
 assert.equal(value(picker,'uabi'),'Fprv,Fnxt,Frnd,Fmod');
 assert.equal(value(picker,'upat'),'');
}
for(const [idx,hero] of heroes.entries()) {
 const card=custom.find(o=>o.newId===`fp${String(idx).padStart(2,'0')}`);
 assert.equal(card.oldId,'hpea','No native hero training limit for selection cards');
 assert.equal(value(card,'uico'),hero.icon);
 assert.equal(value(card,'ugol'),0);assert.equal(value(card,'ufoo'),0);
 assert.equal(value(card,'ubpx'),idx%4);assert.equal(value(card,'ubpy'),Math.floor(idx%8/4));
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
for(const troop of custom.filter(o=>/^fm[0-3][0-4]$/.test(o.newId))) assert.equal(value(troop,'udup'),2);

// Fifth, native learnable skill: cumulative +2/rank, not a paid chat upgrade.
const stats=gearAbilities.find(o=>o.newId==='Fatr');
assert.equal(stats.oldId,'Aamk');assert.equal(value(stats,'aher'),1);assert.equal(value(stats,'alev'),500);
for(let rank=1;rank<=500;rank++) for(const field of ['Istr','Iagi','Iint']) assert.equal(value(stats,field,rank),rank*2);
const originalHeroes=parsed['war3map.w3u'].originalTable.objects;
for(const h of heroes.filter(h=>!h.base)) assert.equal(value(originalHeroes.find(o=>o.oldId===h.id),'uhab'),[...h.skills,'Fatr'].join(','));
const customHeroes=heroes.filter(h=>h.base);
assert.equal(customHeroes.length,12);
assert.equal(new Set(customHeroes.map(h=>h.model.toLowerCase())).size,12);
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
for(let rank=4;rank<=300;rank++) assert.ok(value(immo,'Eim1',rank)>value(immo,'Eim1',rank-1),'Immolation damage improves at EVERY rank, despite interval in label');
assert.ok(value(immo,'Eim1',300)>1000);assert.equal(value(immo,'Eim2',300),7,'Do not amplify ongoing mana drain');
assert.ok(value(abilityById.get('AEev'),'Eev1',10)<0.4,'Evasion must not hit its cap early');
assert.equal(value(abilityById.get('AEev'),'Eev1',300),0.75);
const alliedFont=unitById.get('fbfn');assert.equal(value(alliedFont,'uabi'),'Avul,FbHP,FbMP');
for(const [id,field,flag] of [['FbHP','Oar1','Oar2'],['FbMP','Arm1','Arm2']]) {
 const a=gearAbilities.find(o=>o.newId===id);assert.equal(value(a,'aare',1),1200);
 assert.equal(value(a,'atar',1),'ground,air,hero,friend,self,vuln,invu');
 assert.ok(Math.abs(value(a,field,1)-0.005)<1e-6);assert.equal(value(a,flag,1),1);
}
assert.equal(balance.army_cap,48);assert.equal(balance.spawn_units,3);assert.equal(balance.spawn_seconds,12);
console.log('PASS: 36 heroes / 12 unique creature models, +2 native attributes, 75% evasion, per-rank Immolation, allied native fountains and unchanged army/summon counts.');
for(const [id,gap] of [['AHds',8],['AHtb',1],['AEer',1],['AOhx',1]]) {
 const a=abilityById.get(id);assert.ok(value(a,'acdn',300)>=value(a,'ahdu',300)+gap-0.001,'No permanent shield/control from cooldown scaling');
}
for(const unit of customHeroes.map(h=>unitById.get(h.id))) for(const id of ['ustp','uagp','uinp']) assert.equal(unit.modifications.find(m=>m.id===id).variableType,2,'Classic hero growth uses unreal');
// Compare shipped 0.8.1 counts independently: optimization may not reduce creatures.
const previous=new War3Map();previous.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.8.1-alpha.w3x'))),true);
const PreviousAbilities=require(prefix+'w3x/w3d/file').default;
const previousAbilities=new PreviousAbilities();previousAbilities.load(new Uint8Array(previous.get('war3map.w3a').bytes()));
const quantities=new Set(['Hwe2','Osf2','Efn1','Esv1','Nba2','Ndo2','Rai1','Ucb5','Omi1','Hre1']);
for(const old of previousAbilities.originalTable.objects) {
 const current=abilityById.get(old.oldId);
 for(const mod of old.modifications) if(quantities.has(mod.id)) assert.equal(value(current,mod.id,mod.levelOrVariation),mod.value,'Creature/resurrection counts must match 0.8.1');
}
console.log('PASS: Creature, illusion and resurrection counts match previous release at every rank.');
// Startup optimization must preserve every combat field from 0.9.0.
const baseline=new War3Map();baseline.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.9.0-alpha.w3x'))),true);
const baselineSkills=new PreviousAbilities();baselineSkills.load(new Uint8Array(baseline.get('war3map.w3a').bytes()));
for(const table of ['originalTable','customTable']) {
 const current=parsed['war3map.w3a'][table].objects;
 const previous=baselineSkills[table].objects;
 assert.equal(current.length,previous.length);
 for(let idx=0;idx<current.length;idx++) {
  assert.equal(current[idx].oldId,previous[idx].oldId);assert.equal(current[idx].newId,previous[idx].newId);
  const combat=o=>o.modifications.filter(m=>m.id!=='atp1' && m.id!=='aub1');
  assert.deepEqual(combat(current[idx]),combat(previous[idx]),'All non-tooltip ability data matches 0.9.0');
 }
}
console.log('PASS: Startup patch preserves every non-tooltip ability field from 0.9.0.');
