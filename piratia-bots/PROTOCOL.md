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
