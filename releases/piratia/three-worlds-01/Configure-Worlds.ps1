$ErrorActionPreference = 'Stop'
try {
    $root = $PSScriptRoot
    $gameDir = Join-Path $root '[1] GameServer'
    $baseFile = Join-Path $gameDir 'GameServer.cfg'
    $groupFile = Join-Path $root '[1] GroupServer\GroupServer.cfg'
    $encoding = [Text.Encoding]::GetEncoding(1251)
    foreach ($file in @($baseFile, $groupFile)) {
        if (!(Test-Path -LiteralPath $file)) {
            throw "Not found: $file. Extract this package into C:\PKO138 + Tools."
        }
    }
    $base = [IO.File]::ReadAllText($baseFile, $encoding)
    if ([regex]::Matches($base, '(?im)^\s*map\s*=').Count -ne 1 -or
        $base -notmatch '(?im)^\s*map\s*=\s*garner\s*$') {
        throw 'Expected the original single-map GameServer.cfg (garner). No changes made.'
    }
    $idMatch = [regex]::Match($base, '(?ims)(^\[ID\]\s*\r?\n)(.*?)(?=^\[|\z)')
    if (!$idMatch.Success -or [regex]::Matches($idMatch.Groups[2].Value, '(?im)^name\s*=').Count -ne 1) {
        throw 'Cannot identify the GameServer ID. No changes made.'
    }
    $clones = @{}
    foreach ($spec in @(
        @('GameServer2.cfg', 'GameServer01', 'magicsea'),
        @('GameServer3.cfg', 'GameServer02', 'darkblue')
    )) {
        $idBody = [regex]::Replace($idMatch.Groups[2].Value,
            '(?im)^name\s*=[^\r\n]*', ('name = ' + $spec[1]))
        $copy = $base.Substring(0, $idMatch.Index) + $idMatch.Groups[1].Value +
            $idBody + $base.Substring($idMatch.Index + $idMatch.Length)
        $copy = [regex]::Replace($copy, '(?im)^\s*map\s*=[^\r\n]*', ('map = ' + $spec[2]))
        $clones[$spec[0]] = $copy
    }
    $group = [IO.File]::ReadAllText($groupFile, $encoding)
    $bird = [regex]::Match($group, '(?ims)(^\[bird\][^\r\n]*\r?\n)(.*?)(?=^\[|\z)')
    if (!$bird.Success) { throw 'GroupServer.cfg has no [bird] section. No changes made.' }
    # Build Russian city names without depending on the PowerShell script encoding.
    $cities = @(
        @((-join ([char[]]@(0x410,0x440,0x433,0x435,0x43D,0x442))), 'garner'),
        @((-join ([char[]]@(0x428,0x430,0x439,0x442,0x430,0x43D))), 'magicsea'),
        @((-join ([char[]]@(0x41B,0x435,0x434,0x44B,0x43D,0x44C))), 'darkblue')
    )
    $body = $bird.Groups[2].Value
    foreach ($city in $cities) {
        $pattern = '(?im)^' + [regex]::Escape($city[0]) + '\s*=[^\r\n]*'
        $line = $city[0] + ' = ' + $city[1]
        if ([regex]::IsMatch($body, $pattern)) {
            $body = [regex]::Replace($body, $pattern, $line)
        } else {
            $body = $body.TrimEnd([char[]]"`r`n") + "`r`n" + $line + "`r`n"
        }
    }
    $newGroup = $group.Substring(0, $bird.Index) + $bird.Groups[1].Value +
        $body + $group.Substring($bird.Index + $bird.Length)
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    foreach ($name in $clones.Keys) {
        $target = Join-Path $gameDir $name
        if (Test-Path -LiteralPath $target) { Copy-Item -LiteralPath $target -Destination "$target.$stamp.backup" }
        [IO.File]::WriteAllText($target, $clones[$name], $encoding)
    }
    Copy-Item -LiteralPath $groupFile -Destination "$groupFile.$stamp.backup"
    [IO.File]::WriteAllText($groupFile, $newGroup, $encoding)
    Write-Host 'READY: garner + magicsea + darkblue. SQL credentials copied locally.'
    Write-Host 'Original GameServer.cfg preserved. GroupServer backup created.'
    Write-Host 'Use Start-All.bat after shutting down any running server instances safely.'
} catch {
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
