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
    # Upgrade an old three-bot cache without touching login data or an existing PIN.
    Add-Member -InputObject $final.bots[1] -NotePropertyName 'secondary_password_dpapi' -NotePropertyValue 'keep-existing-secondary'
    $changed = Initialize-BotSecondaryPasswordState -State $final -Count 3 -CreateProtectedPassword { 'protected-secondary-placeholder' }
    Assert-True $changed 'Old cache did not receive missing secondary-password fields.'
    Assert-True ($final.bots[1].secondary_password_dpapi -eq 'keep-existing-secondary') 'Existing secondary password was replaced.'
    Assert-True ($final.bots[0].password_dpapi -eq 'encrypted-placeholder-1') 'Cache migration changed a login credential.'
    Save-BotState -State $final -Path $path
    $migrated = [IO.File]::ReadAllText($path) | ConvertFrom-Json
    $changed = Initialize-BotSecondaryPasswordState -State $migrated -Count 3 -CreateProtectedPassword { throw 'Repeated migration must not generate credentials.' }
    Assert-True (-not $changed) 'Repeated migration changed saved PINs.'
    Assert-True ($migrated.bots[2].secondary_password_dpapi -eq 'protected-secondary-placeholder') 'Migrated encrypted field was lost.'
    # The Alpha 15 launcher accepts 200, so the helper must accept them too.
    # Mix legacy missing PIN fields with already-provisioned records; never reroll.
    foreach ($populationCount in @(1, 10, 30, 60, 100, 200)) {
        $population = [PSCustomObject]@{version=1;windows_sid='test';bots=@()}
        for ($index=1; $index -le $populationCount; $index++) {
            $entry = [PSCustomObject]@{account="test$index";password_dpapi="keep-login-$index"}
            if ($index % 2 -eq 0) {
                Add-Member -InputObject $entry -NotePropertyName 'secondary_password_dpapi' -NotePropertyValue "keep-pin-$index"
            }
            $population.bots += $entry
        }
        $changed = Initialize-BotSecondaryPasswordState -State $population -Count $populationCount -CreateProtectedPassword { 'new-pin-placeholder' }
        Assert-True $changed "Missing PINs were not migrated for count $populationCount."
        Save-BotState -State $population -Path $path
        $reloaded = [IO.File]::ReadAllText($path) | ConvertFrom-Json
        Assert-True (@($reloaded.bots).Count -eq $populationCount) 'Population size changed on save.'
        for ($index=1; $index -le $populationCount; $index++) {
            $entry = @($reloaded.bots)[$index-1]
            Assert-True ($entry.password_dpapi -eq "keep-login-$index") 'Login credential was changed.'
            $expected = if ($index % 2 -eq 0) { "keep-pin-$index" } else { 'new-pin-placeholder' }
            Assert-True ($entry.secondary_password_dpapi -eq $expected) 'PIN was lost or overwritten.'
        }
        $changed = Initialize-BotSecondaryPasswordState -State $reloaded -Count $populationCount -CreateProtectedPassword { throw 'Existing population must not generate credentials.' }
        Assert-True (-not $changed) 'Population migration was not idempotent.'
    }
    foreach ($invalidCount in @(0,201)) {
        $rejected = $false
        try {
            Initialize-BotSecondaryPasswordState -State $population -Count $invalidCount -CreateProtectedPassword { throw 'Invalid count reached generator.' }
        } catch { $rejected = $_.FullyQualifiedErrorId -like 'ParameterArgumentValidationError*' }
        Assert-True $rejected 'Unsupported population count was accepted.'
    }
    [Console]::Out.WriteLine('PASS: saves, backups, restart and PIN migration preserve credentials; populations 1/10/30/60/100/200 accepted, 0/201 rejected.')
} finally {
    [IO.Directory]::Delete($root, $true)
}
