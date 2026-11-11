# Runs in Windows PowerShell 5.1 or PowerShell 7; does not access SQL or DPAPI.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path (Split-Path $PSScriptRoot -Parent) 'src/state_store.ps1')

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}

$root = Join-Path ([IO.Path]::GetTempPath()) ('piratia-state-test-' + [Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($root)
try {
    # Reproduce the old failure, including PowerShell's null->empty conversion.
    $old = Join-Path $root 'old.json'
    $tmp = Join-Path $root 'old.tmp'
    [IO.File]::WriteAllText($old, 'previous')
    [IO.File]::WriteAllText($tmp, 'replacement')
    $caught = $false
    try { [IO.File]::Replace($tmp, $old, $null) } catch {
        $failure = $_.Exception
        while ($null -ne $failure.InnerException) { $failure = $failure.InnerException }
        $caught = $failure -is [ArgumentException]
    }
    Assert-True $caught 'The original ArgumentException was not reproduced.'
    Assert-True ([IO.File]::ReadAllText($old) -eq 'previous') 'Original state changed on failed replace.'

    $path = Join-Path $root 'bot-local.json'
    $state = [PSCustomObject]@{version=1;windows_sid='test';bots=@()}
    for ($index=1; $index -le 3; $index++) {
        $state.bots += [PSCustomObject]@{account="test$index";password_dpapi="encrypted-placeholder-$index"}
        Save-BotState -State $state -Path $path
        $loaded = [IO.File]::ReadAllText($path) | ConvertFrom-Json
        Assert-True (@($loaded.bots).Count -eq $index) 'Not all appended bot records were saved.'
        Assert-True ($loaded.bots[0].account -eq 'test1') 'Previously saved identity was changed.'
        Assert-True (-not [IO.File]::Exists("$path.tmp")) 'Temporary file was not consumed.'
    }
    $backups = @([IO.Directory]::GetFiles($root, 'bot-local.json.backup-*'))
    Assert-True ($backups.Count -eq 2) 'Expected two preserved backups.'
    $counts = @($backups | ForEach-Object { @(([IO.File]::ReadAllText($_) | ConvertFrom-Json).bots).Count })
    Assert-True ($counts -contains 1 -and $counts -contains 2) 'Backup contents are not the previous states.'
    # Restart with an existing cache plus a stale temp from the failed Alpha 02 run.
    [IO.File]::WriteAllText("$path.tmp", 'incomplete older attempt')
    $resumed = [IO.File]::ReadAllText($path) | ConvertFrom-Json
    $resumed.bots = @($resumed.bots)
    Save-BotState -State $resumed -Path $path
    $final = [IO.File]::ReadAllText($path) | ConvertFrom-Json
    Assert-True (@($final.bots).Count -eq 3) 'Restart lost bot identities.'
    Assert-True ($final.bots[0].password_dpapi -eq 'encrypted-placeholder-1') 'Restart changed a saved credential.'
    [Console]::Out.WriteLine('PASS: old ArgumentException reproduced; three saves, backups and restart preserve identities.')
} finally {
    [IO.Directory]::Delete($root, $true)
}
