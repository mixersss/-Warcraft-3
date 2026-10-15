// Parse the complete released archive with an independent Warcraft format reader.
// These are structural checks; they do not emulate the Warcraft engine.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
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
assert.equal(heroes.length, 24);
assert.equal(new Set(heroes.map(h => h.id)).size, 24);
assert.deepEqual([0,1,2,3,4].map(g => heroes.filter(h => h.group === g).length), [4,4,4,4,8]);
assert.equal(custom.filter(o=>o.newId.startsWith('fm')).length,20,'Exactly one troop type per race/tier');
assert.equal(new Set(custom.map(o => o.newId)).size,custom.length,'Unique custom rawcodes');
for (let race = 0; race < 4; race++) {
  for (let tier = 0; tier < 5; tier++) {
    const troop=custom.find(o=>o.newId===`fm${race}${tier}`);
    assert.equal(troop.oldId,races[race].units[tier]);
    assert.equal(troop.modifications.find(m=>m.id==='upgr').value,'Rfat,Rfar,Rfhp');
  }
}
assert.equal(parsed['war3map.w3a'].customTable.objects.length, 0, 'Summons use explicit unit definitions per skill rank');
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
  const amount=[3,1,0.1,3000][col];
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
    const ability = abilities.find(o => o.oldId===id);
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
assert.equal(balance.spawn_seconds,16);
const shopItems = require('../map/items.json');
assert.equal(parsed['war3map.w3t'].customTable.objects.length,shopItems.length);
assert.equal(value(custom.find(o => o.newId==='fshp'),'usei'),shopItems.map(i=>i.id).join(','));
for (const item of shopItems) assert.equal(value(parsed['war3map.w3t'].customTable.objects.find(o=>o.newId===item.id),'igol'),item.cost);
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
console.log('PASS: MPQ, 14 binary formats, 4 command-card research columns (200/200/200/4), 500 hero levels, 300/50 skill caps, 10 shop items, 12 slots, 24 heroes and 20 army variants and rank-specific summons.');
