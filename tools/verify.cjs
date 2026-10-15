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
const map = new War3Map();
// Use a true Uint8Array: Node Buffer.slice() shares a larger backing allocation.
map.load(new Uint8Array(data), true);
assert.equal(map.maxPlayers, 12);
const formats = {
  'war3map.w3i': 'w3i', 'war3map.w3e': 'w3e', 'war3map.wpm': 'wpm',
  'war3map.w3u': 'w3u', 'war3map.w3q': 'w3d',
  'war3map.w3a': 'w3d', 'war3map.w3b': 'w3u',
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
assert.equal(races.length, 4);
assert.equal(heroes.length, 24);
assert.equal(new Set(heroes.map(h => h.id)).size, 24);
assert.deepEqual([0,1,2,3,4].map(g => heroes.filter(h => h.group === g).length), [4,4,4,4,8]);
assert.equal(custom.length, 42, 'Four races x five tiers x two roles, barracks, tower');
assert.equal(new Set(custom.map(o => o.newId)).size, 42, 'Unique custom rawcodes');
for (let race = 0; race < 4; race++) {
  for (let tier = 0; tier < 5; tier++) {
    for (const role of ['fm', 'fr']) assert.ok(custom.some(o => o.newId === `${role}${race}${tier}`));
  }
}
assert.equal(parsed['war3map.w3a'].customTable.objects[0].newId, 'Fmen');
assert.equal(parsed['war3map.w3b'].customTable.objects[0].newId, 'fwll');
assert.equal(parsed['war3map.w3q'].customTable.objects.length, 2);
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
console.log('PASS: MPQ, 13 binary formats, Classic versions, 12 slots / 4 forces, 24 heroes, 40 army variants, menu ability, walls, identifiers and embedded JASS.');
