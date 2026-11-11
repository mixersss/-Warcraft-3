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
flag; u32 communication-encryption mode; u32 trailer. Decrypt the session-key sequence
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

20 tests cover the codecs, state transitions and creation packet, including failure
and reuse cases. SQL Server and DPAPI have **not** been executed in this Linux workspace.
They require the owner's Windows run. Schema checks and transaction logic have been
reviewed, but are not represented as a passing native SQL integration test.

Standard DES known-answer vector, native Gate golden vectors and a fragmented/
coalesced local socket mock cover the implemented handshake. The native vector
check uses optional development-only Unicorn, with the exact uploaded executable;
it does not launch Windows, account services or a real game world. Integration
tests use a mock, not the actual server. Windows console launch and live login
still require the owner's local run. No assertion of functioning combat AI is made.
