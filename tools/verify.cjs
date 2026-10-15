// Parse the complete released archive with an independent Warcraft format reader.
// These are structural checks; they do not emulate the Warcraft engine.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const prefix = 'mdx-m3-viewer/dist/cjs/parsers/';
const War3Map = require(prefix + 'w3x/map').default;
const balance = require('../map/balance.json');
const target = path.join(root, 'build', `FourFrontsFrenzy-${balance.version}.w3x`);
const data = fs.readFileSync(target);
const map = new War3Map();
// Use a true Uint8Array: Node Buffer.slice() shares a larger backing allocation.
map.load(new Uint8Array(data), true);
assert.equal(map.maxPlayers, 12);
const formats = {
  'war3map.w3i': 'w3i', 'war3map.w3e': 'w3e', 'war3map.wpm': 'wpm',
  'war3map.w3u': 'w3u', 'war3map.w3q': 'w3d',
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
assert.equal(custom.length, 12, 'Five melee, five ranged, barracks, tower');
assert.equal(new Set(custom.map(o => o.newId)).size, 12, 'Unique custom rawcodes');
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
console.log('PASS: MPQ extraction, 11 binary formats, Classic versions, 12 slots / 4 forces, terrain, pathing, object IDs and embedded JASS.');
