param(
    [ValidateSet('Enable','Disable','Status','Prune')][string]$Mode = 'Status',
    [string]$InterfaceAlias = 'Wi-Fi'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$stateFile = Join-Path $root 'data/state/lan-access.json'
$resultFile = Join-Path $root 'data/state/lan-access-operation.json'
$allowName = 'LocalLLM-LAN-Allow-v1'
$blockName = 'LocalLLM-LAN-BlockOutside-v1'
$group = 'Local LLM LAN'
$proxyKey = 'HKLM:\SYSTEM\CurrentControlSet\Services\PortProxy\v4tov4\tcp'
$ports = @(10000,8081)
$strataSettings = Get-Content -LiteralPath (Join-Path $root 'config/strata.json') -Raw | ConvertFrom-Json
if ($strataSettings.enabled -eq $false) { $ports = @(10000) }
function Read-State {
    if (Test-Path -LiteralPath $stateFile) { Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json }
}
function Proxy-Value([string]$address, [int]$port) {
    if (Test-Path -LiteralPath $proxyKey) {
        $properties = Get-ItemProperty -LiteralPath $proxyKey
        $property = $properties.PSObject.Properties["$address/$port"]
        if ($property) { return [string]$property.Value }
    }
    return $null
}
function Netsh-Proxy([string]$operation, [string]$address, [int]$port) {
    $arguments = @('interface','portproxy',$operation,'v4tov4',"listenaddress=$address", "listenport=$port",'protocol=tcp')
    if ($operation -eq 'add') { $arguments += @('connectaddress=127.0.0.1',"connectport=$port") }
    & netsh.exe @arguments | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "TCP forwarding $operation failed on port $port." }
}
function Address-Number([string]$address) {
    $bytes = [Net.IPAddress]::Parse($address).GetAddressBytes()
    [uint64]$bytes[0]*16777216 + [uint64]$bytes[1]*65536 + [uint64]$bytes[2]*256 + [uint64]$bytes[3]
}
function Number-Address([uint64]$number) {
    (@([int][math]::Floor($number/16777216), [int][math]::Floor(($number%16777216)/65536), [int][math]::Floor(($number%65536)/256), [int]($number%256)) -join '.')
}
New-Item -ItemType Directory -Force (Split-Path -Parent $stateFile) | Out-Null
if ($Mode -eq 'Status') { Read-State | ConvertTo-Json -Depth 5; return }
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Windows requires administrator privileges to change TCP forwarding and firewall rules.'
}
try {
    $state = Read-State
    foreach ($name in @($allowName,$blockName)) {
        $rule = Get-NetFirewallRule -Name $name -ErrorAction SilentlyContinue
        if ($rule -and $rule.Group -ne $group) { throw "Firewall rule $name belongs to another application." }
    }
    if ($Mode -eq 'Disable') {
        if ($state) {
            foreach ($port in $state.ports) {
                if ((Proxy-Value $state.listenAddress $port) -eq "127.0.0.1/$port") { Netsh-Proxy 'delete' $state.listenAddress $port }
            }
        }
        Get-NetFirewallRule -Name $allowName,$blockName -ErrorAction SilentlyContinue | Remove-NetFirewallRule
        Remove-Item -LiteralPath $stateFile -ErrorAction SilentlyContinue
        @{success=$true;mode=$Mode;completedUtc=[datetime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $resultFile
        Write-Host 'Local LLM LAN forwarding disabled.'
        return
    }
    if ($Mode -eq 'Prune') {
        if ($state) {
            $backup = Join-Path $root ('archive/before-lan-prune-' + [datetime]::UtcNow.ToString('yyyyMMdd-HHmmss'))
            New-Item -ItemType Directory -Path $backup | Out-Null
            Copy-Item -LiteralPath $stateFile -Destination $backup
            & netsh.exe interface portproxy dump | Set-Content -LiteralPath (Join-Path $backup 'portproxy.txt')
            foreach ($port in @($state.ports | Where-Object { $ports -notcontains $_ })) {
                $existing = Proxy-Value $state.listenAddress $port
                if ($existing -and $existing -ne "127.0.0.1/$port") { throw "Retired port $port belongs to another mapping; it was preserved." }
                if ($existing) { Netsh-Proxy 'delete' $state.listenAddress $port }
            }
            $remaining = @($state.ports | Where-Object { $ports -contains $_ })
            if (-not $remaining.Count) { throw 'No retained LAN ports are owned. Review state before pruning.' }
            Get-NetFirewallRule -Name $allowName,$blockName -ErrorAction SilentlyContinue | Set-NetFirewallRule -LocalPort $remaining
            $state.ports = $remaining
            $state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $stateFile
        }
        @{success=$true;mode=$Mode;completedUtc=[datetime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $resultFile
        Write-Host 'Retired LAN ports removed; retained mappings and access restrictions preserved.'
        return
    }
    $retired = @($state.ports | Where-Object { $ports -notcontains $_ })
    if ($retired.Count) { throw 'Run Prune to remove retired owned ports before enabling access again.' }
    $addresses = @(Get-NetIPAddress -InterfaceAlias $InterfaceAlias -AddressFamily IPv4 | Where-Object { $_.AddressState -eq 'Preferred' -and $_.IPAddress -notlike '169.254.*' })
    if ($addresses.Count -ne 1) { throw 'Expected exactly one preferred IPv4 address on the selected LAN interface.' }
    $address = $addresses[0].IPAddress
    $prefix = [int]$addresses[0].PrefixLength
    if ($prefix -lt 16 -or $prefix -gt 30) { throw 'Review the LAN subnet before enabling access; expected a /16 to /30 prefix.' }
    $number = Address-Number $address
    $privateAddress = ($number -ge (Address-Number '10.0.0.0') -and $number -le (Address-Number '10.255.255.255')) -or
        ($number -ge (Address-Number '172.16.0.0') -and $number -le (Address-Number '172.31.255.255')) -or
        ($number -ge (Address-Number '192.168.0.0') -and $number -le (Address-Number '192.168.255.255'))
    if (-not $privateAddress) { throw 'The selected interface does not have a private LAN address.' }
    $hostMask = [uint64][math]::Pow(2,32-$prefix)-1
    $network = $number -band ([uint64]4294967295 - $hostMask)
    $last = $network + $hostMask
    $subnet = "$(Number-Address $network)/$prefix"
    $outside = @("0.0.0.0-$(Number-Address ($network-1))", "$(Number-Address ($last+1))-255.255.255.255")
    if ($state -and $state.listenAddress -ne $address) { throw 'The LAN address changed. Run Disable, then Enable to replace the old forwarding rules.' }
    foreach ($port in $ports) {
        $existing = Proxy-Value $address $port
        if ($existing -and (-not $state -or $existing -ne "127.0.0.1/$port")) { throw "An unrelated forwarding rule already owns $address port $port." }
        $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalAddress -in @($address,'0.0.0.0','::') }
        if ($listener -and -not $existing) { throw "Another listener already owns LAN port $port." }
    }
    if ((Get-Service iphlpsvc).Status -ne 'Running') { throw 'Start the Windows IP Helper service before enabling TCP forwarding.' }
    $backup = Join-Path $root ('archive/before-lan-access-' + [datetime]::UtcNow.ToString('yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Path $backup | Out-Null
    & netsh.exe interface portproxy dump | Set-Content -LiteralPath (Join-Path $backup 'portproxy.txt')
    Get-NetConnectionProfile | Select-Object InterfaceAlias,NetworkCategory | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backup 'network-profiles.json')
    if ($state) { Copy-Item -LiteralPath $stateFile -Destination $backup }
    # A block rule takes precedence over any pre-existing broad allow rule.
    $common = @{Direction='Inbound';Enabled='True';Protocol='TCP';LocalPort=$ports;LocalAddress=$address;InterfaceAlias=$InterfaceAlias;Profile='Any';Group=$group;EdgeTraversalPolicy='Block'}
    foreach ($name in @($blockName,$allowName)) {
        Get-NetFirewallRule -Name $name -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    }
    New-NetFirewallRule @common -Name $blockName -DisplayName 'Local LLM: block sources outside home subnet' -Action Block -RemoteAddress $outside | Out-Null
    New-NetFirewallRule @common -Name $allowName -DisplayName 'Local LLM: allow home subnet' -Action Allow -RemoteAddress $subnet | Out-Null
    $saved = @{listenAddress=$address;remoteSubnet=$subnet;interfaceAlias=$InterfaceAlias;ports=$ports;connectAddress='127.0.0.1';firewallRules=@($allowName,$blockName);networkProfileChanged=$false;enabledUtc=[datetime]::UtcNow.ToString('o');backup=$backup}
    # Record ownership before applying mappings, so Disable can clean up a partial operation.
    $saved | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $stateFile
    foreach ($port in $ports) { Netsh-Proxy 'add' $address $port }
    @{success=$true;mode=$Mode;listenAddress=$address;remoteSubnet=$subnet;ports=$ports;completedUtc=[datetime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $resultFile
    Write-Host "LAN forwarding enabled on $address for $subnet. Start one inference backend using its normal launcher."
} catch {
    @{success=$false;mode=$Mode;error=$_.Exception.Message;completedUtc=[datetime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $resultFile
    throw
}
