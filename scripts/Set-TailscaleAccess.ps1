param(
    [ValidateSet('Enable','Disable','Status')][string]$Mode = 'Status',
    [switch]$IncludeLlamaCpp
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$stateFile = Join-Path $root 'data/state/tailscale-access.json'
$resultFile = Join-Path $root 'data/state/tailscale-access-operation.json'
$ts = Join-Path $env:ProgramFiles 'Tailscale/tailscale.exe'
$managedPorts = @(10000,8080,8081)
$ports = @(8081)
if ($IncludeLlamaCpp) { $ports = @(10000,8081) }
$strataSettings = Get-Content -LiteralPath (Join-Path $root 'config/strata.json') -Raw | ConvertFrom-Json
if ($strataSettings.enabled -eq $false) { $ports = @(10000) }
if ($Mode -ne 'Enable') { $ports = $managedPorts } # Recognize legacy ownership for cleanup.
function Read-Serve {
    $json = & $ts serve status --json
    if ($LASTEXITCODE -ne 0) { throw 'Unable to read Tailscale Serve configuration.' }
    $json | ConvertFrom-Json
}
function Port-Entry($config, [int]$port) {
    if ($config.TCP) {
        $property = $config.TCP.PSObject.Properties["$port"]
        if ($property) { return $property.Value }
    }
    return $null
}
if (-not (Test-Path -LiteralPath $ts)) { throw 'Install and sign into Tailscale before enabling access.' }
New-Item -ItemType Directory -Force (Split-Path -Parent $stateFile) | Out-Null
try {
    $status = (& $ts status --json) | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) { throw 'Unable to read Tailscale status.' }
    $current = Read-Serve
    $state = if (Test-Path -LiteralPath $stateFile) { Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json } else { $null }
    if ($Mode -eq 'Status') {
        @{backendState=$status.BackendState;dnsName=$status.Self.DNSName;addresses=@($status.Self.TailscaleIPs);state=$state;forwarding=($ports | ForEach-Object { @{port=$_;config=(Port-Entry $current $_)} })} | ConvertTo-Json -Depth 8
        return
    }
    if ($Mode -eq 'Enable' -and ($status.BackendState -ne 'Running' -or -not $status.Self.Online)) { throw 'Tailscale must be online and signed in before enabling access.' }
    foreach ($port in $managedPorts) {
        $entry = Port-Entry $current $port
        if ($entry -and (-not $state -or @($state.ports) -notcontains $port -or $entry.TCPForward -ne "127.0.0.1:$port" -or $entry.TerminateTLS)) {
            throw "An unrelated Tailscale Serve handler owns port $port. It was preserved."
        }
        if ($current.AllowFunnel) {
            foreach ($property in $current.AllowFunnel.PSObject.Properties) {
                if ($property.Name -match (':' + $port + '$') -and $property.Value) { throw "Funnel is enabled on port $port; review it before configuring tailnet-only access." }
            }
        }
    }
    if ($Mode -eq 'Enable' -and $ports -contains 10000) {
        $stack = Get-Content -LiteralPath (Join-Path $root 'config/stack.json') -Raw | ConvertFrom-Json
        $runtime = [IO.Path]::GetFullPath((Join-Path $root $stack.runtime))
        $routerStateFile = Join-Path $root 'data/state/router-process.json'
        if (-not (Test-Path -LiteralPath $routerStateFile)) { throw 'Start the workspace llama.cpp backend before enabling port 10000.' }
        $routerState = Get-Content -LiteralPath $routerStateFile -Raw | ConvertFrom-Json
        $router = Get-Process -Id $routerState.pid -ErrorAction SilentlyContinue
        if (-not $router -or $router.Path -ne $runtime -or
            $router.StartTime.ToUniversalTime().Ticks -ne ([datetime]$routerState.started).ToUniversalTime().Ticks) {
            throw 'The recorded workspace llama.cpp backend is not running. Port 10000 was not enabled.'
        }
        # Some Windows environments return State=0 even for a live server socket.
        # A listener has no remote peer. Exclude closed/TIME_WAIT connections,
        # whose owner may be PID 0, then prove ownership and API readiness.
        $listeners = @(Get-NetTCPConnection -LocalPort 10000 -ErrorAction Stop | Where-Object {
            $_.LocalAddress -in @('127.0.0.1','0.0.0.0','::','::1') -and
            $_.RemotePort -eq 0 -and $_.RemoteAddress -in @('0.0.0.0','::')
        })
        if (-not $listeners.Count) { throw 'The llama.cpp listener is not ready on port 10000.' }
        foreach ($listener in $listeners) {
            $process = Get-Process -Id $listener.OwningProcess -ErrorAction Stop
            if ($process.Path -ne $runtime) { throw 'Port 10000 belongs to another application. Its Tailscale forwarder was not enabled.' }
        }
        $key = (Get-Content -LiteralPath (Join-Path $root 'data/credentials/.local-api-key') -Raw).Trim()
        $catalog = Invoke-RestMethod 'http://127.0.0.1:10000/v1/models' -Headers @{Authorization="Bearer $key"} -TimeoutSec 5
        if (@($catalog.data.id) -notcontains $stack.defaultModel) { throw 'The authenticated llama.cpp catalog does not match this workspace.' }
        $key = $null
    }
    $backup = Join-Path $root ('archive/before-tailscale-access-' + [datetime]::UtcNow.ToString('yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Path $backup | Out-Null
    $current | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $backup 'serve.json')
    if ($state) { Copy-Item -LiteralPath $stateFile -Destination $backup }
    if ($Mode -eq 'Disable') {
        if ($state) {
            foreach ($port in $ports) {
                if (@($state.ports) -contains $port -and (Port-Entry $current $port)) {
                    & $ts serve --bg --yes "--tcp=$port" off | Out-Null
                    if ($LASTEXITCODE -ne 0) { throw "Failed to disable managed Tailscale port $port." }
                }
            }
        }
        Remove-Item -LiteralPath $stateFile -ErrorAction SilentlyContinue
    } else {
        foreach ($port in $managedPorts) {
            if ($ports -notcontains $port -and (Port-Entry $current $port)) {
                & $ts serve --bg --yes "--tcp=$port" off | Out-Null
                if ($LASTEXITCODE -ne 0) { throw "Failed to disable deselected managed Tailscale port $port." }
            }
        }
        $ipv4 = @($status.Self.TailscaleIPs | Where-Object { $_ -notmatch ':' })
        if ($ipv4.Count -ne 1) { throw 'Expected exactly one Tailscale IPv4 address.' }
        # Save ownership before applying changes, so Disable can clean up partial setup.
        @{ipv4=$ipv4[0];dnsName=$status.Self.DNSName.TrimEnd('.');ports=$ports;transport='tailscale-serve-tcp';connectAddress='127.0.0.1';backup=$backup;enabledUtc=[datetime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $stateFile
        foreach ($port in $ports) {
            & $ts serve --bg --yes "--tcp=$port" "tcp://127.0.0.1:$port" | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Tailscale Serve failed on port $port. Check its feature/permission message; no login or policy changes were made automatically." }
        }
        $after = Read-Serve
        foreach ($port in $ports) {
            if ((Port-Entry $after $port).TCPForward -ne "127.0.0.1:$port") { throw "Tailscale forwarder verification failed on port $port." }
        }
    }
    @{success=$true;mode=$Mode;ports=$ports;completedUtc=[datetime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $resultFile
    Write-Host "Tailscale API access $Mode completed. Managed ports: $($ports -join ', ')."
} catch {
    @{success=$false;mode=$Mode;error=$_.Exception.Message;completedUtc=[datetime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $resultFile
    throw
}
