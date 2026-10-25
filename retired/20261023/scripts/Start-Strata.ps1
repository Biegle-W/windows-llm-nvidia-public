param(
    [ValidateSet('Launch','Backend','Stop')][string]$Mode = 'Launch',
    [ValidateSet('Default','Q3')][string]$Profile = 'Default'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$settingsFile = 'strata.json' # Default and Q3 both select the only retained quant.
$settings = Get-Content -LiteralPath (Join-Path "$root\config" $settingsFile) -Raw | ConvertFrom-Json
$strata = Join-Path $root $settings.directory
$python = Join-Path $strata '.venv\Scripts\python.exe'
$engineConfig = Join-Path $strata $settings.engineConfig
$stateFile = Join-Path $root 'data\state\strata-process.json'
$stopSignal = Join-Path $root 'data\state\strata-stop.request'
New-Item -ItemType Directory -Force "$root\data\state", "$root\logs" | Out-Null
function Read-State {
    if (Test-Path -LiteralPath $stateFile) { Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json }
}
function Owned-Terminal($state) {
    if (-not $state) { return $null }
    $terminal = Get-Process -Id $state.terminalPid -ErrorAction SilentlyContinue
    if ($terminal -and $terminal.ProcessName -eq 'powershell' -and $terminal.StartTime.ToUniversalTime().Ticks -eq ([datetime]$state.terminalStarted).ToUniversalTime().Ticks) { return $terminal }
    return $null
}
$state = Read-State
$owner = Owned-Terminal $state
if ($Mode -eq 'Stop') {
    if ($owner) {
        Set-Content -LiteralPath $stopSignal -Value 'stop'
        $owner.WaitForExit(8000) | Out-Null
        if (-not $owner.HasExited) { Stop-Process -Id $owner.Id -Force }
    }
    Write-Host 'Strata stopped. Model files are retained.'
    return
}
if ($settings.enabled -eq $false) {
    throw ('Strata is deferred: ' + $settings.disabledReason)
}
if ($owner -and $Mode -eq 'Launch' -and $state.engineConfig -ne $engineConfig) {
    & $PSCommandPath -Mode Stop
    $state = Read-State
    $owner = Owned-Terminal $state
    if ($owner) { throw 'The previous Strata profile did not stop.' }
}
if ($owner) { Write-Host "Strata is already starting or running in Local-LLM. Open http://127.0.0.1:$($settings.port)"; return }
if (-not (Test-Path -LiteralPath $python) -or -not (Test-Path -LiteralPath $engineConfig)) { throw 'Strata installation is not complete. See logs\strata-install.log.' }
$loopbackListeners = Get-NetTCPConnection -LocalPort $settings.port -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalAddress -in @('127.0.0.1','0.0.0.0','::','::1') }
if ($loopbackListeners) { throw "Loopback port $($settings.port) is already occupied. The existing process was left running." }
if ($Mode -eq 'Launch') {
    $privateEngine = Get-Process -Name strata -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -like "$root\*" }
    if ($privateEngine) { throw 'A Strata test engine is still loaded. Wait for its Local-LLM test tab to finish before launching the server.' }
    & "$PSScriptRoot\Start.ps1" -Mode Stop
    $wt = Get-Command wt.exe -ErrorAction Stop
    $tabTitle = 'Strata Q3 - Qwen Flash-Next'
    $arguments = '-w "' + $settings.terminalWindow + '" new-tab --title "' + $tabTitle + '" --suppressApplicationTitle --tabColor "#78C99B" -d "' + $root + '" powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '" -Mode Backend -Profile ' + $Profile
    Start-Process -FilePath $wt.Source -ArgumentList $arguments -WorkingDirectory $root -WindowStyle Normal | Out-Null
    Write-Host "Strata is starting in the Local-LLM terminal. Loading may take a few minutes."
    Write-Host "Chat: http://127.0.0.1:$($settings.port) | API: http://127.0.0.1:$($settings.port)/v1"
    return
}
if (-not $env:WT_SESSION) { throw 'Start Strata using Launch mode so its backend remains visible in Windows Terminal.' }
Remove-Item Env:CUDA_VISIBLE_DEVICES -ErrorAction SilentlyContinue
$env:PYTHONUNBUFFERED = '1'
$env:PYTHONIOENCODING = 'utf-8'
# Newer Strata checks HTTP Host names. Reuse only addresses in our private
# forwarding records so the existing LAN/Tailscale clients survive upgrades.
$allowedHosts = @()
foreach ($networkRecord in @('tailscale-access.json', 'lan-access.json')) {
    $networkPath = Join-Path "$root\data\state" $networkRecord
    if (Test-Path -LiteralPath $networkPath) {
        $network = Get-Content -LiteralPath $networkPath -Raw | ConvertFrom-Json
        foreach ($field in @('ipv4', 'dnsName', 'listenAddress')) {
            $value = $network.PSObject.Properties[$field]
            if ($value -and $value.Value) { $allowedHosts += [string]$value.Value }
        }
    }
}
if ($allowedHosts.Count) {
    $env:STRATA_ALLOWED_HOSTS = (@($env:STRATA_ALLOWED_HOSTS -split ',') + $allowedHosts |
        Where-Object { $_ } | Select-Object -Unique) -join ','
}
Write-Host "=== Strata: $($settings.label) ===" -ForegroundColor Green
Write-Host "Configured GPUs: $($settings.gpus -join ', ')"
Write-Host 'Close this tab to stop Strata and free model memory.'
Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class BackendJob {
    [StructLayout(LayoutKind.Sequential)] struct Basic {
        public long ProcessTime, JobTime;
        public uint Flags;
        public UIntPtr MinWorkingSet, MaxWorkingSet;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint Priority, Scheduling;
    }
    [StructLayout(LayoutKind.Sequential)] struct Io {
        public ulong ReadOps, WriteOps, OtherOps, ReadBytes, WriteBytes, OtherBytes;
    }
    [StructLayout(LayoutKind.Sequential)] struct Extended {
        public Basic BasicLimit;
        public Io IoCounters;
        public UIntPtr ProcessMemory, JobMemory, PeakProcessMemory, PeakJobMemory;
    }
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern IntPtr CreateJobObject(IntPtr attributes, string name);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool SetInformationJobObject(IntPtr job, int infoClass, IntPtr info, uint size);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
    [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr handle);
    public static IntPtr Create() {
        IntPtr job = CreateJobObject(IntPtr.Zero, null);
        if (job == IntPtr.Zero) throw new Win32Exception();
        var limits = new Extended();
        limits.BasicLimit.Flags = 0x2000; // JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        int size = Marshal.SizeOf(limits);
        IntPtr buffer = Marshal.AllocHGlobal(size);
        try {
            Marshal.StructureToPtr(limits, buffer, false);
            if (!SetInformationJobObject(job, 9, buffer, (uint)size)) {
                int error = Marshal.GetLastWin32Error(); CloseHandle(job);
                throw new Win32Exception(error);
            }
        } finally { Marshal.FreeHGlobal(buffer); }
        return job;
    }
    public static void Assign(IntPtr job, IntPtr process) {
        if (!AssignProcessToJobObject(job, process)) throw new Win32Exception();
    }
}
'@


$job = [BackendJob]::Create()
$child = $null
$readers = @()
$failure = $null
$stopRequested = $false
Remove-Item -LiteralPath $stopSignal -ErrorAction SilentlyContinue
try {
    $outLog = "$root\logs\strata.out.log"
    $errLog = "$root\logs\strata.err.log"
    $arguments = '-u "' + (Join-Path $strata 'serve\server.py') + '" --engine strata --config "' + $engineConfig + '" --host ' + $settings.host + ' --port ' + $settings.port + ' --open'
    $child = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $strata -NoNewWindow -PassThru -RedirectStandardOutput $outLog -RedirectStandardError $errLog
    try { [BackendJob]::Assign($job, $child.Handle) } catch { $child.Kill(); throw }
    @{pid=$child.Id;started=$child.StartTime.ToUniversalTime().ToString('o');executable=$python;engineConfig=$engineConfig;profile=$Profile;terminalPid=$PID;terminalStarted=(Get-Process -Id $PID).StartTime.ToUniversalTime().ToString('o');visible=$true;terminalWindow=$settings.terminalWindow;terminalSession=$env:WT_SESSION} | ConvertTo-Json | Set-Content -LiteralPath $stateFile
    foreach ($log in @($outLog,$errLog)) {
        $stream = [IO.File]::Open($log,[IO.FileMode]::Open,[IO.FileAccess]::Read,([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
        $readers += [IO.StreamReader]::new($stream)
    }
    do {
        foreach ($reader in $readers) { while (-not $reader.EndOfStream) { Write-Host $reader.ReadLine() } }
        if (Test-Path -LiteralPath $stopSignal) { $stopRequested = $true; break }
        if ($child.HasExited) { break }
        Start-Sleep -Milliseconds 100
    } while ($true)
    foreach ($reader in $readers) { while (-not $reader.EndOfStream) { Write-Host $reader.ReadLine() } }
    if (-not $stopRequested -and $child.ExitCode -ne 0) { throw "Strata exited with code $($child.ExitCode)." }
} catch {
    $failure = $_
    Write-Host $_ -ForegroundColor Red
} finally {
    [BackendJob]::CloseHandle($job) | Out-Null
    foreach ($reader in $readers) { $reader.Dispose() }
    Remove-Item -LiteralPath $stopSignal -ErrorAction SilentlyContinue
    $state = Read-State
    if ($state -and $state.terminalPid -eq $PID) { Remove-Item -LiteralPath $stateFile -ErrorAction SilentlyContinue }
}
Write-Host 'Strata has stopped.'
if ($stopRequested) { return }
Read-Host 'Press Enter to close this terminal' | Out-Null
if ($failure) { exit 1 }
