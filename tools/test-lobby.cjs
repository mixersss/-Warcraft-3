// Execute the generated config() before gameplay initialization, as in a lobby.
// Native calls are recorded and compared to the independently parsed W3I.
// This verifies configuration decisions; Warcraft's actual UI still needs a test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { lua, lauxlib, lualib, to_luastring, to_jsstring } = require('fengari');
const jass2lua = require('mdx-m3-viewer/dist/cjs/utils/jass2/jass2lua').default;
const Info = require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3i/file').default;
const root = path.join(__dirname, '../build/map');
const source = fs.readFileSync(path.join(root, 'war3map.j'), 'utf8');
const info = new Info();
info.load(new Uint8Array(fs.readFileSync(path.join(root, 'war3map.w3i'))));
assert.equal(info.players.length, 12);
const L = lauxlib.luaL_newstate();
lualib.luaL_openlibs(L);
function run(code) {
  const status = lauxlib.luaL_dostring(L, to_luastring(code));
  if (status !== lua.LUA_OK) throw new Error(to_jsstring(lua.lua_tostring(L, -1)));
}
run(jass2lua(source).replace(/\bnot(?=[A-Z(])/g, 'not '));
run(`
Config = {slots={}, locations={}, flags={}, supported={}}
MAP_CONTROL_USER, MAP_PLACEMENT_FIXED, GAME_TYPE_USE_MAP_SETTINGS = 'user', 'fixed', 'custom'
MAP_LOCK_ALLIANCE_CHANGES, RACE_PREF_HUMAN = 'locked', 'human'
ALLIANCE_PASSIVE, ALLIANCE_SHARED_VISION = 'allied', 'vision'
function Player(p)
  assert(p>=0 and p<12, 'Player index outside Classic slots')
  Config.slots[p]=Config.slots[p] or {alliances={}}
  return p
end
function SetMapName(s) Config.name=s end
function SetMapDescription(s) Config.description=s end
function SetPlayers(n) Config.players=n end
function SetTeams(n) Config.teams=n end
function SetGamePlacement(p) Config.placement=p end
function SetGameTypeSupported(t,v) Config.supported[t]=v end
function SetMapFlag(f,v) Config.flags[f]=v end
function DefineStartLocation(p,x,y) Config.locations[p]={x=x,y=y} end
function SetPlayerStartLocation(p,v) Config.slots[p].start=v end
function ForcePlayerStartLocation(p,v) Config.slots[p].fixed=v end
function ConvertPlayerColor(p) return p end
function SetPlayerColor(p,v) Config.slots[p].color=v end
function SetPlayerRacePreference(p,v) Config.slots[p].race=v end
function SetPlayerRaceSelectable(p,v) Config.slots[p].selectable=v end
function SetPlayerController(p,v) Config.slots[p].controller=v end
function SetPlayerTeam(p,v) Config.slots[p].team=v end
function SetPlayerAlliance(p,q,a,v)
  Config.slots[p].alliances[q]=Config.slots[p].alliances[q] or {}
  Config.slots[p].alliances[q][a]=v
end
config()
assert(Config.players==12 and Config.teams==4)
assert(Config.flags.locked and Config.supported.custom)
for p=0,11 do
  local slot=assert(Config.slots[p], 'Missing slot')
  assert(slot.controller=='user', 'All twelve slots must accept humans')
  assert(slot.team==math.floor(p/3), 'Exactly three consecutive slots per team')
  assert(slot.start==p and slot.fixed==p and slot.color==p)
  for q=0,11 do
    if p~=q then
      local allied=slot.alliances[q] or {}
      if math.floor(p/3)==math.floor(q/3) then
        assert(allied.allied and allied.vision)
      else
        assert(not allied.allied and not allied.vision)
      end
    end
  end
end
`);
for (const player of info.players) {
  const p = player.id;
  const [x, y] = player.startLocation;
  const team = info.forces.findIndex(force => force.playerMasks & (1 << p));
  assert.equal(player.type, 1);
  run(`assert(Config.slots[${p}].team==${team})
       assert(Config.locations[${p}].x==${x} and Config.locations[${p}].y==${y})`);
}
console.log('PASS: config() executes before gameplay initialization: 12 human-joinable slots, four teams of three, allies, fixed starts and W3I agree (mock natives).');
