param([ValidateRange(1,60)][int]$Count = 3)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName System.Security
Add-Type -AssemblyName System.Data
. (Join-Path $PSScriptRoot 'state_store.ps1')

# Only the owner's local SQL instance, using the current Windows identity.
# No SQL credentials, server configuration changes or GM grants are required.
$dataPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'data'
[void][IO.Directory]::CreateDirectory($dataPath)
$statePath = Join-Path $dataPath 'bot-local.json'
$lock = $null
$connection = $null
$transaction = $null
$setupStage = 'local_state'

function Protect-Password([string]$Password) {
    $bytes = [Text.Encoding]::UTF8.GetBytes($Password)
    $cipher = [Security.Cryptography.ProtectedData]::Protect($bytes, $null,
        [Security.Cryptography.DataProtectionScope]::CurrentUser)
    return [Convert]::ToBase64String($cipher)
}

function Unprotect-Password([string]$Cipher) {
    $bytes = [Security.Cryptography.ProtectedData]::Unprotect(
        [Convert]::FromBase64String($Cipher), $null,
        [Security.Cryptography.DataProtectionScope]::CurrentUser)
    return [Text.Encoding]::UTF8.GetString($bytes)
}

function New-Password {
    $alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $bytes = New-Object byte[] 9
        $rng.GetBytes($bytes)
        return -join @($bytes | ForEach-Object { $alphabet[[int]$_ % $alphabet.Length] })
    } finally { $rng.Dispose() }
}

function Password-Hash([string]$Password) {
    $md5 = [Security.Cryptography.MD5]::Create()
    try {
        return [BitConverter]::ToString($md5.ComputeHash([Text.Encoding]::ASCII.GetBytes($Password))).Replace('-', '')
    } finally { $md5.Dispose() }
}

try {
    $lock = [IO.File]::Open((Join-Path $dataPath 'provision.lock'),
        [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    if ([IO.File]::Exists($statePath)) {
        $state = [IO.File]::ReadAllText($statePath) | ConvertFrom-Json
        if ($state.version -ne 1 -or $state.windows_sid -ne $sid) {
            throw 'State belongs to another Windows user or format.'
        }
        $state.bots = @($state.bots)
    } else {
        $state = [PSCustomObject]@{version=1; windows_sid=$sid; bots=@()}
    }
    $setupStage = 'sql_connection'
    $connection = New-Object Data.SqlClient.SqlConnection
    $connection.ConnectionString = 'Server=localhost\SQLEXPRESS;Database=AccountServer;Integrated Security=True;Encrypt=False;Application Name=PiratiaBotSetup;Connect Timeout=10'
    $connection.Open()
    $setupStage = 'schema_check'
    $command = $connection.CreateCommand()
    $command.CommandText = @'
SELECT name, is_identity, is_nullable, default_object_id, is_computed, system_type_id, max_length
FROM sys.columns WHERE object_id=OBJECT_ID(N'dbo.account_login', N'U');
'@
    $reader = $command.ExecuteReader()
    $columns = @{}
    while ($reader.Read()) {
        $columns[$reader.GetString(0)] = @{
            identity=$reader.GetBoolean(1); nullable=$reader.GetBoolean(2)
            default=$reader.GetInt32(3); computed=$reader.GetBoolean(4)
            type=[int]$reader.GetByte(5); length=[int]$reader.GetInt16(6)
        }
    }
    $reader.Close()
    foreach ($required in @('id','name','password')) {
        if (-not $columns.ContainsKey($required)) { throw 'Unexpected account table schema.' }
    }
    if ($columns['id'].type -ne 56 -or $columns['id'].computed) { throw 'Unexpected ID type.' }
    foreach ($field in @('name','password')) {
        if ($columns[$field].type -notin @(167,175,231,239) -or
            $columns[$field].identity -or $columns[$field].computed) {
            throw 'Unexpected credential column type.'
        }
    }
    $nameMinimum = 14
    $hashMinimum = 32
    if ($columns['name'].type -in @(231,239)) { $nameMinimum *= 2 }
    if ($columns['password'].type -in @(231,239)) { $hashMinimum *= 2 }
    if (($columns['name'].length -ne -1 -and $columns['name'].length -lt $nameMinimum) -or
        ($columns['password'].length -ne -1 -and $columns['password'].length -lt $hashMinimum)) {
        throw 'Credential columns are too short.'
    }
    foreach ($field in $columns.Keys) {
        $column = $columns[$field]
        if ($field -notin @('id','name','password') -and -not $column.nullable -and
            -not $column.identity -and -not $column.computed -and $column.default -eq 0 -and $column.type -ne 189) {
            throw 'An additional required column has no default. No account was inserted.'
        }
    }
    # Save new identities before inserting: interrupted setup retries the same bots.
    $setupStage = 'save_bot_identities'
    while ($state.bots.Count -lt $Count) {
        $suffix = [Guid]::NewGuid().ToString('N').Substring(0,12)
        $state.bots += [PSCustomObject]@{
            account="PB$suffix"; character=('Bot' + $suffix.Substring(0,8))
            password_dpapi=(Protect-Password (New-Password))
            secondary_password_dpapi=(Protect-Password (New-Password))
        }
        $script:setupStage = 'write_bot_state'
        Save-BotState -State $state -Path $statePath
        $setupStage = 'save_bot_identities'
    }
    # Upgrade the saved Alpha 02-05 cache without changing any login credentials.
    $setupStage = 'prepare_secondary_passwords'
    $stateChanged = Initialize-BotSecondaryPasswordState -State $state -Count $Count -CreateProtectedPassword { Protect-Password (New-Password) }
    if ($stateChanged) {
        $script:setupStage = 'write_bot_state'
        Save-BotState -State $state -Path $statePath
    }
    $outputBots = @()
    foreach ($entry in @($state.bots | Select-Object -First $Count)) {
        $setupStage = 'account_creation'
        # A saved record cannot redirect this helper onto arbitrary existing accounts.
        if ($entry.account -cnotmatch '^PB[0-9a-f]{12}$' -or
            $entry.character -cnotmatch '^Bot[0-9a-f]{8}$') { throw 'Invalid saved bot identity.' }
        $password = Unprotect-Password $entry.password_dpapi
        $secondaryPassword = Unprotect-Password $entry.secondary_password_dpapi
        $hash = Password-Hash $password
        $transaction = $connection.BeginTransaction([Data.IsolationLevel]::Serializable)
        $command = $connection.CreateCommand()
        $command.Transaction = $transaction
        $command.CommandTimeout = 15
        $command.CommandText = @'
SELECT [password] FROM dbo.account_login WITH (UPDLOCK,HOLDLOCK) WHERE [name]=@name;
'@
        [void]$command.Parameters.Add('@name', [Data.SqlDbType]::VarChar, 32)
        $command.Parameters['@name'].Value = $entry.account
        $existing = $command.ExecuteScalar()
        if ($null -ne $existing) {
            if ($existing -is [DBNull] -or -not [string]::Equals([string]$existing, $hash, [StringComparison]::OrdinalIgnoreCase)) {
                throw 'An account already exists with different credentials. Nothing was overwritten.'
            }
        } else {
            [void]$command.Parameters.Add('@hash', [Data.SqlDbType]::VarChar, 32)
            $command.Parameters['@hash'].Value = $hash
            if ($columns['id'].identity) {
                $command.CommandText = 'INSERT dbo.account_login ([name],[password]) VALUES (@name,@hash);'
            } else {
                $command.CommandText = @'
DECLARE @next int;
SELECT @next=ISNULL(MAX([id]),0)+1 FROM dbo.account_login WITH (TABLOCKX,HOLDLOCK);
INSERT dbo.account_login ([id],[name],[password]) VALUES (@next,@name,@hash);
'@
            }
            [void]$command.ExecuteNonQuery()
        }
        $transaction.Commit()
        $transaction.Dispose()
        $transaction = $null
        $outputBots += [PSCustomObject]@{account=$entry.account; character=$entry.character; password=$password; secondary_password=$secondaryPassword}
    }
    # Private pipe to the Python parent, never printed by the launcher or put in reports.
    [Console]::Out.Write((ConvertTo-Json -InputObject @{bots=@($outputBots)} -Depth 4 -Compress))
} catch {
    $sqlCode = ''
    $failure = $_.Exception
    while ($null -ne $failure.InnerException) { $failure = $failure.InnerException }
    if ($failure -is [Data.SqlClient.SqlException]) { $sqlCode = ' SQL=' + $failure.Number }
    $location = ' Line=' + $_.InvocationInfo.ScriptLineNumber
    [Console]::Error.WriteLine('Account setup failed. Stage=' + $setupStage + $sqlCode + ' ' + $failure.GetType().Name + $location)
    exit 1
} finally {
    if ($null -ne $transaction) { try { $transaction.Rollback() } catch {}; $transaction.Dispose() }
    if ($null -ne $connection) { $connection.Dispose() }
    if ($null -ne $lock) { $lock.Dispose() }
}
