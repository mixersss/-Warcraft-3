# Shared by the Windows setup helper and the standalone persistence regression test.
function Initialize-BotSecondaryPasswordState {
    param([Parameter(Mandatory=$true)]$State,
          [ValidateRange(1,200)][int]$Count,
          [Parameter(Mandatory=$true)][scriptblock]$CreateProtectedPassword)
    $changed = $false
    foreach ($entry in @($State.bots | Select-Object -First $Count)) {
        if ($null -eq $entry.PSObject.Properties['secondary_password_dpapi']) {
            $protected = [string](& $CreateProtectedPassword)
            if ([string]::IsNullOrWhiteSpace($protected)) { throw 'Missing protected secondary password.' }
            Add-Member -InputObject $entry -NotePropertyName 'secondary_password_dpapi' -NotePropertyValue $protected
            $changed = $true
        }
    }
    return $changed
}

function Save-BotState {
    param([Parameter(Mandatory=$true)]$State,
          [Parameter(Mandatory=$true)][string]$Path)
    $fullPath = [IO.Path]::GetFullPath($Path)
    $temporary = "$fullPath.tmp"
    $json = ConvertTo-Json -InputObject $State -Depth 8
    [IO.File]::WriteAllText($temporary, $json, (New-Object Text.UTF8Encoding($false)))
    if ([IO.File]::Exists($fullPath)) {
        # PowerShell converts $null to an empty string for this .NET string
        # parameter. File.Replace rejects it instead of meaning "no backup".
        # A concrete unique path preserves the previous state and avoids that
        # conversion as well as collisions with an existing backup.
        $backup = $fullPath + '.backup-' + [Guid]::NewGuid().ToString('N')
        [IO.File]::Replace($temporary, $fullPath, $backup)
    } else {
        [IO.File]::Move($temporary, $fullPath)
    }
}
