# Classic protocol compatibility notes

This is an owner-operated localhost diagnostic client, not a replacement server.
It implements no GM commands or gameplay AI. Alpha 02 adds scoped account inserts
using the owner's local Windows SQL identity and native network character creation.

## Evidence

The supplied GateServer.exe / GateServer.pdb have matching RSDS GUID and age.
Gate executable timestamp: 2008-10-24 08:54:40 UTC. Matching public symbols identify:

GateServer.exe SHA256:
`a8d6eaa1922ae3d80044a5764a32cbe8a670af727fb2d63e7741b263fbfae89b`.

| Native function | VA |
| --- | --- |
| ToClient::OnConnected | 0x40c900 |
| ToClient::CM_LOGIN | 0x409bc0 |
| ToClient::OnEncrypt / OnDecrypt | 0x409180 / 0x4091f0 |
| KCHAPc::GetStep1Data / GetSessionClrKey | 0x42c3c0 / 0x42c490 |
| CDES::RunDes / RunPad | 0x42d910 / 0x42e130 |
| encrypt_B | 0x42b6b0 |
| init_Noise / encrypt_Noise / decrypt_Noise | 0x42e560 / 0x42e5a0 / 0x42e6e0 |

The supplied client Game.exe SHA256 is
`c819f09bacb1f058f6040a5fe3bdab7d6264ade44c89cd93123b54c471653dd8`.
Its native Login at approximately 0x51aa30 and SC_Login at 0x50b120 establish the
legacy request/response layout. Modern public source variants use incompatible
RSA/AES or Blake2s login; their login implementation is not used here.

GameServer.exe SHA256:
`f60aa51c8a8d08ee097bc4a6003b5a07dd97f6dc5d6ea8ae4c8425fa3660f6c5`.
Its matching PDB confirms separate player and NPC control paths; an NPC spawned by
Lua is not assumed to be a full player. No original executable or private
configuration is distributed in this package.

Reference reading only: public repositories mothannakhzaleh/TalesOfPirateDX9
(SDK packet primitives and unchanged command numbers) and milten21/TalesOfPirates
(modern protocol comparison). Runtime code here is Python; DES tables are standard
FIPS 46 mathematical constants. No external package is required at runtime.

## Wire format

* u16 big-endian frame size includes its own two bytes.
* RPC header is u32 big-endian, ordinary packets use 0x80000000.
* Command is u16 big-endian. Header is six bytes including frame size.
* The first plaintext challenge detects a two-byte non-RPC header if present.
* String = u16 length including NUL, bytes, NUL. Sequence = u16 length, raw bytes.
* SDK heartbeat is a two-byte frame containing only 0x0002.
* Classic client packets have **no modern four-byte packet counter**.

940 challenge: string. 431 login: passport string (empty), account string,
proof sequence, MAC string (`Unknown`), u16 911, u16 client version 136.
Proof uses uppercase ASCII MD5 hex of the password as a 3DES EDE key (first 24 bytes),
ECB mode and zero padding; padding adds a block when already aligned.

931 response: u16 error; on success encrypted-key sequence, u8 slot count, per slot
u8 presence and, if present, two strings, u16 level, look sequence; u8 secondary-password
flag (used to create an absent secondary password before BeginPlay); u32
communication-encryption mode; u32 trailer. Decrypt the session-key sequence
with the password-derived 3DES key, then take six bytes as the B key.

After 931, encrypt command and payload only: Noise then B. Reverse order for
decryption. Each direction has an independent Noise state. Noise affects up to
32 whole-word bytes and updates its state from pre-B ciphertext. B rotations use
VC signed-char to unsigned-int conversion before remainder; negative Python modulo
would be incompatible. Initial Noise seed uses the last four non-NUL challenge
bytes and signed-short(version squared times 0x1111 times 2).

433 BeginPlay: character-name string (u16 byte length including NUL, name, NUL).
The supplied native client does not send a slot byte. 933 may report a refusal. Only a successful
516 EnterMap marks the client as in the world. The remaining world payload is not
interpreted yet. 537 answers 17; 515 echoes five u32 values in command 15.
434 EndPlay waits for 934 before 432 Logout. On timeout TCP closes through the normal
server disconnect path. No forced process termination or SQL login-status edits.

## Validation limits

### Alpha 08: fix append-look size and test the real writer

The owner's Alpha 07 run enters the world but fails in initial world decoding with
`Too many world attributes`. The ten normal equipment slots were incorrectly reused
for the separate append-look block. Native WriteAppendLook at 0x4e6070 compares its
loop index with **4** at 0x4e6092 (defESPE_KBGRID_NUM), writing a u16 per slot and an
extra valid byte for nonzero append items. Reading ten slots consumed skill data and
misaligned the subsequent attribute header. The attribute count limit is not relaxed.

The earlier synthetic native-base capture stubbed this entire method with twenty
zero bytes, hiding the error. That stub is removed. The actual append-look writer
now runs with synthetic inventory getters, covering empty and nonempty append items.
Native WriteSkillbag and WriteSkillState also run, using synthetic skill getters.
The fixture includes two skills (zero and nonzero range) followed by states and native
attributes, so tests verify the complete boundary rather than a manually invented gap.
Only actor/inventory/skill data getters and packet I/O are stubbed; counts and loops
are emitted by the actual hash-pinned native writer routines.

36 pure tests pass; full suite totals 44 including the eight existing socket tests
not repeated in this restricted environment. No new live hunt has been claimed.
World decoding diagnostics now record phase, byte offsets and counts, never names,
passwords or raw payloads. Accounts, characters, PINs and navigation policy are retained.

### Alpha 07: first bounded PvE hunter

The owner confirmed Alpha 06 enters the world. This release retains its SQL, cache,
secondary-password and login path. Default run changes to ONE saved bot / 300 seconds
in `hunt` mode; `--mode idle --count 3 --seconds 60` retains the old standing test.

Classic world layout is derived from the supplied matching GameServer/PDB, not the
modern DX9 source: WriteBaseInfo 0x4e54b0, WriteLookData 0x4e5d60, WriteSkillbag 0x4e5790,
WriteSkillState 0x505e80, WriteAttr 0x505f00 / 0x506090, Event::WriteInfo 0x4fd960,
and Cmd_EnterMap 0x4db730. No modern guild-permission long, is-player byte, IMP long,
look DBID/required-level fields or skill-state timestamps are consumed. Equipment has
10 slots and 5 instance-attribute pairs. Initial skill range extras are three shorts.
Only the entity/skills/states/attributes prefix of EnterMap is consumed; inventories,
shortcuts and boats are not manipulated. NPC/player names are skipped, not stored.

World commands: 504 begin-see, 505 end-see, 508 action notification, 509 attributes.
Movement notifications use the first point as authoritative position, not the route's
future endpoint. Skill-target notifications update remaining HP. Unknown/malformed
required world fields stop the hunt rather than guessing coordinates or health.

Native CProCirculateCS::BeginAction at 0x5198b0 is emulated with packet-writer capture
in check_native_enter.py. Both movement and normal attack match byte-for-byte:
command 6, actor u32, action-counter u32, action u8. Movement adds a sequence of raw
little-endian int32 point pairs. Attack adds chMove=2, fight-ID u8, two equal current
points, skill u32, target world-ID u32 and its native handle u32. No modern global
packet counter is added. These are serialization checks, not live action acceptance.

The original Alpha 07 capture ran native base/look/event/attribute writers with synthetic
actor getters but incorrectly stubbed append-look as ten empty slots. This gap is
corrected in Alpha 08 above. These fixtures are not captured from a live private session.
Combat notification fields still need live testing.

Navigation uses a numerical crop derived from the owner's garner.blk: MSB-first packed
bits, original 50cm grid; 100cm cells with nine clearance samples, bounds near Argent,
bounded A* and no diagonal wall cutting. Three native spawn positions have tested paths
to the scouting route. Dynamic actor collisions are not included. Movement requests are
limited to six metres, at most every 2.5 seconds; repeated blocked movement stops.

The policy only attacks control-type 5 models 71/75 (passive Sleepy Snail / Mystic Shrub),
level <= min(2, own level+1), alive, within the spawn leash. No player, NPC, pet or resource
targets. Normal server skill/cooldowns are used; no stat/loot/GM modifications. At <=35%
health it cancels the attack and returns toward its initial position; waits for >=85%.
At death it stops, without a revive workaround. No loot, equip, quests or advanced AI.

34 pure offline tests pass (18 new world/navigation/policy checks plus 16 existing pure
regressions). Eight existing real-socket tests were not rerun: sandbox approval for that
run was interrupted; the last full 24-test socket-inclusive run passed in Alpha 06.
The full current suite contains 42 tests. Native world/action captures passed separately.
Actual Windows hunting, path acceptance, collision behavior and combat remain untested
until the owner's run. Do not describe fixture/emulator tests as a successful hunt.

### Alpha 06: secondary password required before entry

The owner's Alpha 05 run receives 534 (ERR_PT_INVALID_PW2) after character selection.
The login secondary-password flag was previously read and discarded. Auto mode now
uses it: when absent, send command **346**, a string containing uppercase ASCII MD5
hex of a separate saved secondary password, then require response **941** + u16 zero
before proceeding. When the flag says set, no create/update/reset request is sent.

Native UI at **0x46390e** calls md5string **0x577680**, whose format constant at
**0x614ac8** is `%02X`. Native **CS_CreatePassword2 at 0x507e40** writes 346 and calls
WriteString. `check_native_enter.py` captures these calls from the supplied executable
as well as BeginPlay. It stubs SDK I/O; native server acceptance remains untested here.

The SQL helper adds `secondary_password_dpapi` to old cache entries only when missing,
with a separate generated nine-character password protected by DPAPI CurrentUser.
Existing login passwords, account names, character names and saved secondary secrets
are preserved. Persist before sending to the server, so an interrupted run retains the
same secret. No direct GameDB password update or server password-check bypass is used.

24 Python tests include successful encrypted PIN creation -> BeginPlay -> map entry,
skipping an already set password, failure handling, and secret exclusion from reports.
The real PowerShell persistence test covers an old-cache upgrade and an idempotent
repeat, using a dummy protected-string factory; it is not a Windows DPAPI test.

### Alpha 05: classic BeginPlay takes the character name

The owner's Alpha 04 run confirms all three characters are created successfully;
all three subsequently received 524 (ERR_PT_INVALIDCHA) on entering the world.
Alpha 04 incorrectly used the later source revision's slot-byte BeginPlay request.
The supplied native client **BeginPlay at 0x51a4d0** writes command 433 and then calls
**WriteString at 0x54f330** with the character name. It does not call WriteChar.

`tools/check_native_enter.py` executes the hash-pinned BeginPlay method in Unicorn,
stubbing SDK allocation/writers/network to capture the native serialization calls.
It confirms exactly `(command,433),(string,Bot12345678)`. This is method-call capture,
not an unmodified live client or game-server test. The encrypted socket integration
test and the new golden request test now expect the name string; an error-524 test
confirms the client stops rather than trying unrelated characters or changing SQL.
Auto mode selects the exact saved character name from the authenticated server list.
Slot numbers remain only UI information; they are not sent to classic BeginPlay.

20 Python tests pass. The existing accounts, character records, appearance data and
encrypted credentials are preserved. Live acceptance of the corrected request is
still pending the owner's next run.

### Alpha 04: creation appearance IDs

The owner's Alpha 03 run confirms SQL account insertion and native login succeed;
all three accounts then received 520 (ERR_PT_INVALIDDAT) on character creation.
The Alpha 02/03 model inputs in the UI capture were incorrect: CharacterInfo mesh
parts (100/2000) are not the selectable creation hair/face item IDs. The capture proved
the byte layout but did not establish validity of those synthetic model inputs.

The supplied client's native .data at VA **0x655848** contains CCreateChaScene's
hair starts `(2000,2062,2124,2291)` and at **0x655868** face starts
`(2554,2554,2554,2554)`. Alpha 04 selects Lance hair=2000 and face=2554. The developer
capture now reads these tables from the hash-pinned mapped executable before running
SendChaToServ; it no longer invents the appearance from renderer metadata. The packed
wire format is unchanged. The non-sensitive creation profile is included in reports.

Account and encrypted-cache handling are unchanged. The existing three accounts are
reused; no deletion, recreation or SQL login-flag reset is needed. Live acceptance
of the corrected appearance still requires the owner's next run.

### Alpha 03: persistence fix

The owner reported `save_bot_identities ArgumentException` before any account inserts.
Reproduced in real PowerShell 7.4.6: passing `$null` for the string backup-path argument
of System.IO.File.Replace becomes an empty string and throws ArgumentException.
State persistence now lives in `state_store.ps1`, uses a concrete unique backup path
and retains the previous encrypted state. Existing Alpha 02 state is read unchanged;
an incomplete `.tmp` from a failed save is replaced by the next complete serialization.
No SQL records are reset, deleted or rewritten by this fix.

`tests/test_state_store.ps1` reproduces the old failure and checks three incremental
saves, previous-state backup contents, and a restart with an existing cache and stale
temporary file. Passed with real PowerShell 7.4.6 on Linux. This does not imply a native
Windows PowerShell 5.1, Windows DPAPI or SQL Server integration test has passed.

### Alpha 02: automatic setup and classic character creation

`provision.ps1` uses System.Data.SqlClient with Windows Integrated Security against
localhost\SQLEXPRESS / AccountServer only. It validates dbo.account_login metadata,
generates its own PB + 12 hexadecimal account names, and inserts a standard uppercase
MD5 password hash. Nullable/default columns are left to database defaults. Unsupported
required columns stop setup. Identity IDs are left to SQL; non-identity integer IDs
use a serializable transaction and locked MAX(id)+1. Existing rows are read under locks
and must match the saved bot hash; no UPDATE/DELETE/DDL or GM grants are issued.

Random credentials are saved before insertion in an atomic local JSON file, with the
password encrypted using Windows DPAPI CurrentUser. A dedicated process lock prevents
two launchers for the same folder; the provisioning helper has its own file lock.
Credential JSON is passed to Python over a private child-process pipe, never logged.
Repeated launches reuse saved identities; world character creation is requested only
on an empty account. A differently named existing character causes a stop.

Native client **NewCha at 0x51a5c0** sends command 435, character name string,
birthplace string, and a **1626-byte LOOK sequence**. It does NOT send modern type/hair/
face uint32 fields. Reply 935 begins with u16 error. The default Lance LOOK is captured
from native **SendChaToServ at 0x4c16c0**, with type=1, creator hair=2000, face=2554
(appearance inputs corrected in Alpha 04):

* Zero-filled 1626 bytes.
* Little-endian u16 type at offset 2 = 1.
* Face SItemGrid at offset 166: u16 item ID=2554, availability byte at +160=1.
* Little-endian u16 hair at offset 1624 = 2000.

The native UI capture emulates the original SItemGrid constructor and memory copies;
UI text validation/serialization and network submission are stubbed. It verifies the
LOOK bytes, not live server acceptance. After successful creation, reconnect and read
the authoritative character list before entering; only three bounded relogin
attempts allow normal server-side logout to finish. Login flags are never reset by SQL.

24 tests cover the codecs, state transitions and creation packet, including failure
and reuse cases. SQL Server and DPAPI have **not** been executed in this Linux workspace.
They require the owner's Windows run. Schema checks and transaction logic have been
reviewed, but are not represented as a passing native SQL integration test.

Standard DES known-answer vector, native Gate golden vectors and a fragmented/
coalesced local socket mock cover the implemented handshake. The native vector
check uses optional development-only Unicorn, with the exact uploaded executable;
it does not launch Windows, account services or a real game world. Integration
tests use a mock, not the actual server. Windows console launch and live login
still require the owner's local run. No assertion of functioning combat AI is made.

### Alpha 09: earned attribute allocation, local chat, future population quotas

Owner confirmed Alpha08 enters, approaches mobs and attacks on their Windows server.
New Alpha09 actions have codec/policy checks, **no live acceptance confirmation yet**.

Native client `Say` **0x51a6f0** writes command1 + a sequence containing CP1251 text
and terminal NUL. Native server sender around **0x4f960e** writes501 + source worldID
u32 + NUL-terminated text sequence. The parser retains nearby character names only
in bounded transient world state for addressed replies; it logs neither names nor text.
A process-shared lock/budget permits one total line per15sec, perbot >=90sec; a
human sender is answered once per300sec by that bot. Replies expire after20sec and
only visible non-Bot-prefixed player entities are eligible. This is local rule matching.

Native client `SynBaseAttribute` **0x51a780** writes command8 + byte count + pairs
u16 attributeID/u32 **absolute new value**. Native CChaAttr values at+0x24, changed
mask+0x34c; STR25..LUK30. Emulation executes the original changed-bit/value readers
and captures STR25->17. Runtime sends exactly one +1 request against authoritative
AP6 and current attribute value, waits for both value and AP deduction, and disables
allocation after a10sec timeout. Only unpromoted Lance uses the initial melee build.
No SQL/GM grant or local authoritative stat mutation is used. Server stores progress.

Current concurrent runtime is still a bounded1..10 threaded pilot, now sharing the
read-only navigation grid and chat limiter; login launches stagger by1.5sec. It is
**not** the final400-connection manager. Offline `population.py` uses integral max
flow for body/profession compatibility from supplied MisSdk/TemplateSDK.lua lines
158..202. Defaults: bodies1..4 each100; jobs8=100,9/12/13/14/16 each60. This six-class
selection excludes unused/other jobs in the table. It neither changes appearance
nor grants professions or creates accounts. Equal100 bodies and equal~67 classes
are infeasible because body2 can only choose job8 among these six.

45 pure offline tests pass; eight existing socket tests not rerun this release.
400 chat decision policies and400 planned quota records are simulations, not live
server clients or evidence of400-user server performance.

### Alpha 10: pinned class intent, classic NPC quests and quest-only pickup

Owner confirmed Alpha09 hunting and local chat. New quest code is an owner-test pilot,
not a claim of completed live profession chains or instances.

`roles.py` atomically saves body/target job per bot character in data/bot-roles.json.
Valid target/body edges come from TemplateSDK.AddCatTable; first job mapping:
8/9->1,12->2,13/14->5,16->4. Existing actual job must be0, that first job or target;
incompatible saved/actual state stops instead of rerolling. Existing actors stay intact.
New empty accounts use four native creator bodies round-robin, with hair2000/2062/
2124/2291 and face2554. The native UI constructor capture now compares all four LOOKs.
This does not establish live server acceptance of every body.

Native client serializers executed in check_native_enter.py:
* CS_RequestTalk0x508200: command301, NPC worldID u32, subcommand302 u16, page0 u8.
* CS_SelMission0x508cf0:301, worldID,322 u16, selection4 u8, zero-based index u8.
* CS_MissionPage0x508c30:301, worldID,322 u16, button6/7, selected prize0, param0.
* BeginAction0x5198b0 item-pick8: command6, actorID/counter,8, item worldID/handle.

Incoming NPC802 and mission827 layouts are audited against the supplied NpcSdk.lua
SendMissionPage and MissionSdk.lua SendAcceptPage/SendDeliveryPage/SendPendingPage,
not assumed from the newer public source. 802 includes ordinary functions then
(name,state) mission entries. Only exact audited titles are eligible; promotion must
match the saved path again before commitment. Prize selection0=choose-one,1=all;
unknown multi-choice rewards pause. Quest texts are treated as data, never instructions.
Only real visible NPCs at audited garnernpc coordinates receive requests.

Journal828 (u8 count, u16 ID/u8 state rows) captured by executing native server
MisGetMisLog0x47e3f0 up to0x47e4a3 before transport. Add832/change830/clear831 follow
native journal state semantics; requests alone do not increment completion counters.
325 requests journal when not received on entry (native server dispatch calls
CCharacter::MisLog around0x4e6a1e). Lua script mission IDs and journal IDs differ:
script701 Welcome uses journal1; script702/703 share journal701; Sword scripts62,
66..72 use journal58,62..65; Explorer scripts65,191..197 use61,158..161. Unknown
or foreign profession journal work is not cancelled or reinterpreted.

Supported executable routing is limited to Argent tutorial, first Swordsman and
Explorer chains. Hunter59/Herbalist60 referral may be accepted for their own saved
path, then waits because other-map traversal is not implemented. Target professions
are goals, never SQL/GM grants. Advanced professions, instances, equipment and revive
remain unimplemented. No unsupported route is silently substituted with Swordsman.

World items506 fields audited at native server0x4faaf2..0x4fab9b: worldID,handle,
itemID,x,y,u16 angle,u16 count,u8 appearance,u32 source,then event.507 removes ID.
Quest pickup requires appearance0 (monster drop), needed model, recently attacked
source, observed own XP/level credit, <=12m distance, then <=1.8m pickup. Attempts
are bounded/cooldowned; neither disappearance nor request is claimed as bag credit.
Native server remains authoritative for ownership, bag capacity and quest counts.

63 pure checks pass; eight existing socket tests excluded. Actual quest completion,
new bodies, profession acceptance and hours-long operation still need the owner's
Windows server. No claim of 400 live connections or working instances is made.

### Alpha 11: continuous routes, native inventory and three home regions

Supersedes Alpha 10's 1..10 runtime and Argent-only navigation. Default is 30
workers, 1.5-second stagger, 3600-second duration; hard maximum 60. This is a
configuration and offline verification, not evidence of 30 live connections.
The credential-free population status counts only workers that decoded entry.

Movement retains the native maximum 32 contiguous points. Prediction uses only
MC508/action1 acknowledged routes, native MSPD44, clamps at their endpoint and
never mutates the stored authoritative first point. Continuation starts within
0.65 seconds of estimated arrival; request throttle is 0.65 seconds and missing
ACK grace is 1.5 seconds. In-range combat freezes prediction. This removes the
previous six-cell / 2.5–3.1-second burst cadence. A* paths have a bounded shared
256-entry cache; callers receive their own lists. Server BLOCK/ARRIVE/CANCEL
updates replace the motion route.

GameServer WriteKitbag0x4e5b00 is captured in `native_world.json` (`bag_init`,
`bag_delta`) including an instance-bearing armor, boat document, empty slot,
deletion and sword. Format: sync u8; capacity u16 only for init0; repeated slot
u16 and itemID u16, zero ID means empty; count/endurance/maxEndurance/energy/
maxEnergy are five u16; forge/valid u8; boat type43 adds u32; two u32 DB params;
instance u8 optionally adds exactly five (u16,u16) pairs. Terminator FFFF.
No modern DBID/tradable/expiration fields. Unknown item types pause inventory
rather than guessing offsets. Initial bag follows the entry attribute block.
MC508/action6 carries bag synchronization, action5 carries LOOK updates.

Native client BeginAction0x5198b0 action11 serializes bag slot i16, target i16
(-1 for double-click auto target). Equipment chooses compatible owned upgrades
using a numerical ItemInfo projection (level, body models, jobs, equip links,
attack/defense score). LOOK must show the actual item in its target slot before
confirmation. Refused items back off 300 seconds. No local inventory grants.
Apples1847 have ItemUse_APPLE HP+20 in the supplied script. The same audited
item-use request is used; both bag consumption and HP gain must be observed.
No-food/dead/healthy cases send no request; no confirmation backs off120sec.

Native client skill upgrade0x51a920 sends command11,u16 skill,u8 ranks.
First-profession reward books: sword3164->66, hunter3187->74,
herbalist3206->97, explorer3227->210; owned books use normal item-use action.
Skill and TP7 deduction must both be observed. Only these audited skills are
learned/upgraded, at most rank3, reserving two TP for upgrades. Active casting
is not implemented. Native CS_DieReturn0x5080c0 sends command10,u8 City1.
Death delay8sec, maximum3 requests/30sec spacing. MC516 return re-decodes world,
clears old motion/inventory/items and resets local pending equipment/skill use.
Normal death penalties remain server-owned.

Numerical `.blk` crops cover garner, magicsea and darkblue; 3x3 clearance and
native birthpoint coordinates derive from the supplied resources. Farm species
and their regular/quest drop IDs derive from CharacterInfo/ChaSpn, exclude event
IDs >=500 and retain reachable species level1..15 with HP<2000. No models, map
textures, NPC scripts or full game binaries are distributed. Tests cover all
nine spawn-to-beginner paths and four local profession trainers/assistants.
New role intent is pinned before native character creation; the birthplace string
uses Argent City, Shaitan City or Icicle Castle according to first profession.
Existing characters are not moved or recreated.

Local tutorial mission IDs: Argent1/701..704, Shaitan2/707..710,
Icicle3/713..716. Herb chain60/80..83, Hunter59/98/99/150/151 join the previous
Argent Sword/Explorer chains. The same exact promotion-title check runs at
selection and commit. Item-objective farming includes the lowest eligible actual
regional dropper, even when the kill-target species differs. Live completion
of these chains still requires an owner test. Cross-map travel, advanced
profession chains, instances and group play are not implemented.

Chat has107 curated phrases, bounded per-bot event queues, actual map/role
context, and unchanged shared1/15sec plus personal90sec cooldowns. Equipment,
skill and delivery events are triggered only by confirmed counters. No remote
AI, human chat transcripts or human names are saved. Public diagnostics contain
bot index, map, health, levels, movement/combat counts and class goals only.

### Alpha 12: exclusive targets, recovery and mixed progression

No native command format changes. A process-local shared Coordination object in
Regions provides atomic target leases keyed by (map,worldID,handle), one owner
per spawn, expiry8sec. The Hunter renews between normal actions and releases on
retreat/death/quest travel/map transition/exit/retarget. Candidate selection
skips already leased targets, with atomic recheck after route validation. This
is bot cooperation, not a change to server ownership or kill-credit rules.

Farm zones use expiring45sec leases, prefer lowest occupancy and stable per-bot
ordering. Leases are removed on reaching a zone, choosing a target or changing
activity. Reached goals back off20sec; unreachable goals45sec. This replaces
every adventure worker starting at the identical first farm point.
Approach selection checks twelve points inside attack range, avoids occupied
player endpoints and routes to a walkable point instead of the monster center.

Permanent stuck>=5 return was replaced with a checked200/400/600cm detour,
release/blacklist of the failed target and search retry. A target whose HP does
not decrease gets one alternate approach after6sec and a45sec blacklist after
14sec; approach-only timeout25sec. Observed HP reductions renew the progress
window, so healthy long fights are not dropped after the former absolute35sec.
MC508/action4 explicit position corrections clear stale predicted motion.
New MC504 appearances also clear motion belonging to a previous entity instance.

Default CLI mode is mixed. Odd numbered workers use quests; even workers farm,
so count30 gives15/15. Explicit adventure uses all quests, hunt uses all farm.
Both instantiate the same class-pinned Adventure controller and preserve saved
role intent. Farm ignores optional tutorial IDs without deleting journal rows;
at level9 both prioritize only their own profession-title offers and commits.
Any active own profession chain takes precedence over the tutorial. After real
job change, old quest rows no longer constrain desired farm species. Kill/item
objectives still use server journal state, loot credit evidence and earned XP.
No second-profession implementation, high-level navigation or quest grants were
introduced. Supported regional farms remain level1..15.

New diagnostics include tactic, target_id, path_recoveries, no_damage_retargets,
reserved_targets_skipped and fleet tactics counts. Offline tests include thirty
simultaneous claim attempts (one winner), thirty policies selecting thirty
unique mobs, balanced30-worker zone selection, release/expiry/respawn isolation,
no-damage and permanent-stuck recovery, both tactics' real promotion requests
for each first profession, and progressive level-appropriate mob selection.
These are synthetic policy/world tests, not a live thirty-client server run.

### Alpha 13: sixty-worker town/progression pilot

Default count60 (cap60 retained), mixed30/30. Optional Start-60-Bots and a local
Stop-Bots stop-request file. A watcher sets the shared stop Event; existing
clients take their normal logout path. No server process is terminated.

Native serializer emulation additionally executes original Game.exe functions:
* NPC function0x5082a0:301,u32 NPC,u16 303,u8 actual page,u8 function index.
* NPC buy0x508400:308,u32 NPC,u16 309,u8 buy1,u8 item page,u8 index,u8 0,u8 count.
* Party invite0x500930:6001,string character name.
* Party accept0x500a40/refuse0x5009c0:6002/6003,u32 inviter database character ID.
The original UI permission getter is stubbed true; packet writers execute native
code. This audits encoding, not successful transactions on a live server.

Party incoming5001 is name,string +u32 DBID+u16 icon.5002 is kind/count bytes,
then DBID/name/motto/icon records, cap5. Only directory-registered bots on the
same nearby map are accepted. A subset of bot leaders invite, at most one per
minute, up to three confirmed members. Unknown packet layout disables this
optional feature. Membership requires server refresh; local plans do not form
a party. Directory membership is cleared after disband/departure. No human
invitations, automatic player exchanges, shared boss AI or forced XP grants.

Shop805 parser accepts only ordinary buy type1: NPC u32,type u8,param u32,
page count u8; pages are type/count u8 followed by itemIDs u16. Boat/trade goods
pages are rejected. The actual server function menu must contain Trade; no
hard-coded unrelated menu action is clicked. Numeric ItemInfo price and real
server offer must both exist. Budget cap25% of current GD8, reserve100 gold.
Confirmation requires BOTH bag increase and GD8 reduction. Only purchases,
not NPC selling or player trading, are implemented. Unknown/timeout backs off.

LifeItems projects83 skill-book functions from supplied ItemEffect, variable.lua
and skillinfo.txt: actual skill ID, job/maxrank, learning level, prerequisite
skill ranks and TP cost. Owned usable books use BeginAction11; upgrades use
native command11, one rank, reserve2TP, max10. Server skill/rank and TP decrease
must both confirm. No general active-skill combat rotation has been added.
Known novice chests436/985/986/987/988 have level5/10/35/45/55, four empty slots
and profession requirements as in the scripts. Owned chest consumption confirms
use; equipment then follows ordinary bag/LOOK synchronization.

Class-specific earned-AP tendencies are declared in progression.BUILDS and
reported; no reset, injected AP or unconfirmed local stat changes. Full
numerical walkability projections cover the three main4096x4096 maps with
original3x3 clearance; shared runtime data ~48MiB. Octile A* heuristic matches
10/14 movement cost, cache256 routes, expansion cap25000. Farm catalogs retain
reachable ordinary model IDs<500, level<=45, HP<50000; new long routes have
speed/distance-dependent search budgets. No dungeon/island server setup changes.

Career knows six original level40 titles and journal737..742 for the pinned
class; filters title again at native accept/deliver. It uses real journal
state and collects available local objectives. Full chains require other maps,
shops, dungeon/sea transport and additional NPCs; these are NOT complete in
this release. Remote requirements are reported rather than bypassed. Story
adds only Argent200/203/204 with real receiver coordinates and item objectives;
rewards are server life EXP/points, distinct from combat TP. Other-city story
transport and the full story progression remain unimplemented.

Occasional city trips/rest40..100sec, shared chat8sec minimum, personal90sec,
189 curated lines including40 jokes. Spare-gear announcements check real bag
contents and exclude known active quest items; no actual player sale is claimed.
Ordinary loot retains own recent attack+observed XP evidence and reserves four
slots. Both synthetic policy regressions and PowerShell persistence pass, but
new shop/party/chest/level40 behavior still needs the owner's Windows game test.


## Alpha 14 — population and social scheduling

Default/enabled maximum: 100; Python and both provisioning/state PowerShell
validation ranges agree (1..100). Mixed cohorts: index modulo five 0/1 farm,
2/3/4 hybrid, giving 40/60 at 100. Hybrid phases alternate every 240–480 seconds
when no combat or NPC transaction is pending; profession logic remains mandatory.
The population report separates permanent tactic cohort and effective phase.

Local dialogue coordinator uses only native local chat command 1. Twenty paired
scripts, three turns per conversation, advance only on an exact server-delivered
peer echo. Unknown bot messages cannot start generic reply loops. Shared chat
budget is eight seconds; human broadcast intent has one shared responder lease.
The phrase bank contains 389 unique CP1251-safe lines, 200 added this release.

Party invitations share an expiring recipient reservation. After 600–1200 seconds
in a confirmed group, a safe-time leave request uses command 6004, empty body.
Native client serializer at 0x500b60 was captured and compared. Local membership
is retained until server 5002 confirms change. No human invitation policy changed.

134 offline Python tests and PowerShell state regression passed. Native action
serializers audited; live 100-worker Windows SQL/network operation remains untested.


## Alpha 15 — 200 workers and classic stalls

All population validators accept 1..200; default 200 / 7200 seconds. Stable mixed
cohorts are 80 farm / 120 hybrid. Existing DPAPI accounts are reused, not reset.

Classic client native serializers captured: 0x509450 (330 create: string title,
u8 count, repeated u8 grid/u32 unit-price/u8 count/u8 bag slot); 0x509530 (331
view: u32 owner); 0x5095b0 (332 buy: u32 owner/u8 grid/u8 count, NO modern bag
destination); 0x509650 (333 close: empty). Server PDB matched writer 0x4637e0
emulated for packet 854: u32 owner/u8 count/string title, repeated grid/item/
count/price/type and classic item endurance/energy/forge/valid/two parameters/
optional five attribute pairs. No modern tradable or expiration bytes.
`tests/fixtures/native_stall.json` contains synthetic data written by this native
server function. Notifications 856 sale units, 857 close, 858 start, 859 title.

Skill 241 is required: native GetStallNum 0x4d9a00 multiplies real skill level by
six. Book3296 Sk_Script_Btjn adds skill241 through normal AddChaSkill; use only
with earned life points, verify server skill and book consumption. NPC purchase
uses existing audited shop flow. Marketplace state is transient; character
inventory, gold and skills remain server-authoritative.

157 offline tests, native client/server captures and PowerShell state populations
1/10/30/60/100/200 passed. Live Windows 200-worker shop behavior is NOT validated.
Reference prices are pilot policy, not external market observations. Gannon rune
requirements are owner-script facts; NPC barter and dungeon farming are not
implemented. No free rare goods or gold are created.


## Alpha 16 — combat transition, activity quotas, city NPCs and chat

FIX: Client.service previously omitted stall854/856..859 despite native codecs;
these now reach the actual world handler. Added routing for public5401/5402.
Native client captured CS_EndAction0x51a3b0 -> command7, empty body;
trade0x5006a0 ->6401 string; world0x500720 ->6402 string. Own server echoes
must match the pending exact request for confirmation. No incoming world chat
text is retained in diagnostics or used for bot-to-bot reply loops.

Combat reach now comes from owner skillinfo.txt[16], IDs25..38. Server
CFightAble uses apply-distance plus actor/target radii; ATTR_ADIS alone is not
the actual unarmed/weapon skill range. Finish movement before strike; handle
native 520 six-byte actor/action/reason. Native range facts and transition
regressions are verified, not a claim of live Windows combat success.

Deterministic index home split150/25/25 at200 workers. Native NPC301 function
menus GoToWhere, known city label then Teleport. Server516 confirms transfer;
first/second class trainer trips override preferred home. No SQL relocation,
free teleport, race reset or class reassignment. Level>10 requires500G.

Voluntary rest requires12 observed target deaths or2 quest hand-ins and a
10-minute cooldown. Rest and stalls have separate10-percent live-online
quotas, leases and city weights75/15/10 percent for stalls. Low-health recovery
is separate from voluntary rest. Optional town tasks yield after35 seconds
without progress or180 seconds continuous diversion; active stalls excluded.

Local chat shared2s, background per-worker45..90s,50 finite real-echo dialogues,
589 unique CP1251-safe phrases. World shared120s/trade180s, personal1800s and
>=20000 earned gold; restrictions/fees remain server-owned. Explicit nearby
human help lasts<=120s and retains normal PvE level/ownership constraints.
174 offline tests and native serializer capture passed; live Windows transfer,
combat, paid public channels and200-worker operation need owner validation.


## Alpha 17 — corrections from the owner's Alpha16 runtime reports

Aggregate evidence:184 entered;168 had no strike requests;75 last failures
were action-busy reason1.16 failed PIN creation with532. Entered reports ended
as interrupted (user stop), not a demonstrated autonomous crash. Raw reports,
actor IDs and the uploaded archive are private and are not packaged/published.

Root protocol omissions: skillbag510 was counted as received but discarded
by Client.service. Native short skill change packet has owner:u32/default:u16/
sync:u8/count:u16; count0 still changes default25 to28 after sword equip.
Native writer0x4e5790 generated fixtures/native_skill_update.json with synthetic
actor123.531 separate default change also handled. No invented skill IDs.

Native CAction::End requests DesireMoveStop/DesireFightEnd; completion occurs
on a later game tick. EndAction7 immediately followed by BeginAction6 can
still be rejected as EXISTACT. New nonblocking action queue waits>=150ms plus
matching actor stop packet ID, or bounded1s if no stop was generated. Actual
transmission counters separate queue insertion from sent strikes. Paths and
skill/target data are refreshed on flush; dead target cancels queued strike.

Native Cmd_ReassignAttr0x4e01a0 was executed to stat writes: with AP4/BSTR5,
increment1 yields AP3/BSTR6, whereas value6 is refused. Cmd8 body layout was
already correct; the caller's meaning of its value was wrong. Now adds one
and requires server stat+AP confirmation. No SQL attribute edits.

185 offline tests passed. Native client serializers, skill writer and attribute
increment behavior compared with supplied binaries. Live Windows combat and
200-worker behavior remain unverified for this new release.


## Alpha 18 — productive activity and recoverable transport

A live target prevents optional NPC tasks from interrupting its fight. Optional
Senna/tutorial detours require proximity1500cm. Earned progress watchdog after
120s triggers180s ordinary farm focus, preserving mandatory first/second class
work, deliberate rest and active stalls. Targets use distance/health/level-gap
score, safe existing level cap, and existing per-target reservation. New numeric
farm destinations lie in owner ChaSpn rectangles and pass the existing pathfinder;
spawn counts and refresh times are unchanged.

Native NPC sale client0x508350 captured:308 with owner:u32/subcommand309:u16/
sale0:u8/slot:u8/count:u8. New vendor whitelist has38 plain common trophies,
keeps5 each and all currently-needed quest items, excludes rare/enhanced items.
Actual bag decrease AND gold increase confirm a sale. Loot still needs own
attack/earned-XP evidence; full bag does not start endless pickup requests.

Supervisor retries only network OSError (up to3) and transient1104 after a
previous established session loss. Keeps same persisted identity/class; no
account re-creation/reset, no generic protocol retry. Original finite deadline
is retained across reconnects. seconds0 supports continuous operation via
Start-World.cmd, still stoppable by stop file. Diagnostic records contain only
metadata, error location and bounded prior-session reasons, never credentials.
201 offline tests pass. Native sale serialization compared; actual live Windows
network recovery, sales and crowd activity remain unverified for Alpha18.


## Alpha 19: combined action phase continuity

Owner Alpha18 metadata: all 200 connected; 116 had zero attack requests;
73 waiting for previous action. Three detailed reports had 41/65/82 attack
requests, 10/19/19 busy-action refusals and 14/11/13 path recoveries. Their
NPC purchase/rest counters were zero; private reports are not distributed.

MC508/action1 stop (including INRANGE) is a movement phase notification;
for CS6/type2 combined movement+skill it does not prove the whole fight
is finished. Track phase plus matching packet ID, not packet ID alone.
MC508/action3 nonzero skill state terminates the combat phase. A productive
normal attack is allowed to repeat server-side; no periodic EndAction/restart
while observed target HP decreases. No-damage recovery remains bounded.
Native enum diagnostics 0x10/0x40/0x200 release disappeared/invalid/dead
targets; 520 action2 reason5 releases a missing target, reason1 does not
blacklist it. Segment continuation waits through its acknowledged endpoint
instead of deliberately cancelling the final .65 seconds on every segment.

212 pure Python regressions passed including 200 independent policy worlds
with simulated native-shaped movement/skill acknowledgements. Native client
serializer capture passed unchanged. No live 200-player Windows run is claimed.


## Alpha 20: owned ordinary drops and resilient transport

MC508/action4 source actor is the first u32 after critical/miss/knockback fields
and optional knockback coordinates; native CFightAble::NotiSkillTarToEyeshot
0x5048f0..0x504a61 verified by Unicorn in supplied SHA256-f60aa51c GameServer.
Captured synthetic prefixes with/without knockback are in native_damage_prefix.json.
Actual own damage plus subsequent observed death permits loot without personal
XP gain, including another party member's final blow. MC506 kind0/source links
to the defeated monster. Player throws/natural items are not assumed owned.
CS6/action8 still uses native world ID and handle. Bag count gain AND ground
removal confirm a pickup; timeout/retry and approach budgets are bounded.

Separate socket write timeout10s from short receive polling. A write timeout
raises ConnectionError rather than TimeoutError, so the hunt loop cannot swallow
a partially sent encrypted frame as a benign receive timeout. Never reuse that
stream. Continuous mode retries network failures with capped backoff, retains
same account/identity and <=20 diagnostic entries, never resets SQL login flags.
Protocol/program failures remain visible, not blindly retried.

Forest Spirit103 from original CharacterInfo is level3; starter character
levels1..3 explicitly permit this target in garner. New characters start in
Argent; existing newbies use paid/free native teleporter rules; no SQL warps.
Normal home-city/class routes resume after starter levels. Full suite240 passed
including8 socket integrations after sandbox permission; Windows live population
and actual disconnect causes remain unverified.
