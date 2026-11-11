$ErrorActionPreference = 'Stop'
try {
    $root = $PSScriptRoot
    $running = @(Get-Process -Name AccountServer,GroupServer,GateServer,GameServer -ErrorAction SilentlyContinue)
    if ($running.Count -gt 0) {
        throw 'Server processes are already running. Stop them safely before using Start-All.bat.'
    }
    $files = @(
        '[1] AccountServer\AccountServer.exe',
        '[1] GroupServer\GroupServer.exe',
        '[1] GateServer\GateServer.exe',
        '[1] GameServer\GameServer.exe',
        '[1] GameServer\GameServer.cfg',
        '[1] GameServer\GameServer2.cfg',
        '[1] GameServer\GameServer3.cfg'
    )
    foreach ($file in $files) {
        if (!(Test-Path -LiteralPath (Join-Path $root $file))) {
            throw "Not found: $file. Run Setup-Worlds.bat first."
        }
    }
    function Start-ServiceExe($folder, $exe) {
        $directory = Join-Path $root $folder
        Start-Process -FilePath (Join-Path $directory $exe) -WorkingDirectory $directory -PassThru
    }
    function Wait-LocalPort($port, $process) {
        $deadline = [DateTime]::UtcNow.AddSeconds(30)
        while ([DateTime]::UtcNow -lt $deadline) {
            if ($process.HasExited) { throw "A server process exited before opening port $port. Check its log." }
            $socket = New-Object Net.Sockets.TcpClient
            try {
                $socket.Connect('127.0.0.1', $port)
                return
            } catch {
                Start-Sleep -Milliseconds 500
            } finally {
                $socket.Dispose()
            }
        }
        throw "Port $port did not open. Check the server window/log. Started processes remain open."
    }
    $account = Start-ServiceExe '[1] AccountServer' 'AccountServer.exe'
    Wait-LocalPort 1978 $account
    $group = Start-ServiceExe '[1] GroupServer' 'GroupServer.exe'
    Wait-LocalPort 1975 $group
    $gate = Start-ServiceExe '[1] GateServer' 'GateServer.exe'
    Wait-LocalPort 1971 $gate
    $gameDir = Join-Path $root '[1] GameServer'
    foreach ($cfg in @('GameServer.cfg','GameServer2.cfg','GameServer3.cfg')) {
        Start-Process -FilePath (Join-Path $gameDir 'GameServer.exe') -WorkingDirectory $gameDir -ArgumentList $cfg
        Start-Sleep -Seconds 2
    }
    Write-Host 'All processes launched. Wait for GameDB: ok, map: ok and Gate: connected in EACH GameServer window.'
    Write-Host 'A launched process is not confirmation that its map loaded successfully.'
} catch {
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
