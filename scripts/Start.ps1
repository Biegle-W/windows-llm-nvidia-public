param(
    [ValidateSet('Launch','Backend','Stop')][string]$Mode = 'Launch',
    [switch]$NoBrowser
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$stateDir = Join-Path $root 'data\state'
New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
Set-Location -LiteralPath $root
$config = Get-Content -LiteralPath "$root\config\stack.json" -Raw | ConvertFrom-Json
$runtime = Join-Path $root $config.runtime
function Get-OwnedProcess($state) {
    if (-not $state) { return $null }
    $proc = Get-Process -Id $state.pid -ErrorAction SilentlyContinue
    if ($proc -and $proc.Path -eq $state.executable -and $proc.StartTime.ToUniversalTime().Ticks -eq ([datetime]$state.started).ToUniversalTime().Ticks) { return $proc }
    return $null
}
function Read-State([string]$name) {
    $path = Join-Path $stateDir ($name + '-process.json')
    if (Test-Path -LiteralPath $path) { return Get-Content -LiteralPath $path -Raw | ConvertFrom-Json }
    return $null
}
function Stop-Owned([string]$name) {
    $state = Read-State $name
    if (-not $state) { return }
    $proc = Get-OwnedProcess $state
    if ($state.terminalPid) {
        $terminal = Get-Process -Id $state.terminalPid -ErrorAction SilentlyContinue
        if ($terminal -and $terminal.ProcessName -eq 'powershell' -and $terminal.StartTime.ToUniversalTime().Ticks -eq ([datetime]$state.terminalStarted).ToUniversalTime().Ticks) {
            if ($state.stopSignal) {
                Set-Content -LiteralPath "$stateDir\$name-stop.request" -Value 'stop'
                $terminal.WaitForExit(5000) | Out-Null
            }
            if (-not $terminal.HasExited) { Stop-Process -Id $terminal.Id -Force }
            if ($proc) { $proc.WaitForExit(5000) | Out-Null }
        }
    }
    $proc = Get-OwnedProcess $state
    if ($proc) {
        & taskkill.exe /PID $proc.Id /T /F | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Could not stop the owned $name process tree." }
    }
    Remove-Item -LiteralPath (Join-Path $stateDir ($name + '-process.json')) -ErrorAction SilentlyContinue
}
if ($Mode -eq 'Stop') {
    Stop-Owned 'router'
    Write-Host 'Local LLM stopped. Model files and saved chats are retained.'
    return
}
if (-not (Test-Path -LiteralPath $runtime)) { throw "Backend missing: $runtime" }
$python = Join-Path $root 'runtimes/python/cpython-3.11.15-windows-x86_64-none/python.exe'
New-Item -ItemType Directory -Force "$root\logs" | Out-Null
$keyFile = "$root\data\credentials\.local-api-key"
if (-not (Test-Path -LiteralPath $keyFile)) {
    New-Item -ItemType Directory -Force (Split-Path -Parent $keyFile) | Out-Null
    $bytes = New-Object byte[] 32
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    [Convert]::ToBase64String($bytes) | Set-Content -LiteralPath $keyFile -Encoding ascii
}
$env:LLAMA_CPP_API_KEY = (Get-Content -LiteralPath $keyFile -Raw).Trim()
$headers = @{Authorization="Bearer $env:LLAMA_CPP_API_KEY"}
function Test-Service([string]$name) {
    if (-not (Get-OwnedProcess (Read-State $name))) { return $false }
    try {
        $models = Invoke-RestMethod 'http://127.0.0.1:10000/v1/models' -Headers $headers -TimeoutSec 3
        $expected = @((Get-Content -LiteralPath "$root\config\selected-profiles.json" -Raw | ConvertFrom-Json).id | Sort-Object)
        $actual = @($models.data.id | Sort-Object)
        return @($actual).Contains($config.defaultModel) -and -not @(Compare-Object $expected $actual).Count
    } catch { return $false }
}
function Assert-PortFree([int]$port) {
    $probe = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback,$port)
    try { $probe.Start() } catch { throw "Port $port is occupied. Close the other service first." } finally { $probe.Stop() }
}
if ($Mode -eq 'Launch') {
    if (Test-Service 'router') { Write-Host 'The llama.cpp backend is already running in Local-LLM.'; return }
    & $python "$PSScriptRoot\model_router.py" --check-config
    if ($LASTEXITCODE -ne 0) { throw 'Model router configuration failed; existing services were left running.' }
    if (Get-OwnedProcess (Read-State 'router')) { Stop-Owned 'router' }
    $services = @(
        @{name='router';mode='Backend';title='Local Model Router';color='#4CC2FF';port=10000;timeout=45}
    )
    $needed = @($services | Where-Object { -not (Test-Service $_.name) })
    try {
        if ($needed.Count) {
            $wt = Get-Command wt.exe -ErrorAction Stop
            foreach ($service in $needed) { Assert-PortFree $service.port }
            $windowName = $config.terminalWindow
            if (-not $windowName) { $windowName = 'Local-LLM' }
            $commands = foreach ($service in $needed) {
                'new-tab --title "' + $service.title + '" --suppressApplicationTitle --tabColor "' + $service.color + '" -d "' + $root + '" powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '" -Mode ' + $service.mode
            }
            # Reuse the named backend window.
            $arguments = '-w "' + $windowName + '" ' + ($commands -join ' ; ')
            Start-Process -FilePath $wt.Source -ArgumentList $arguments -WorkingDirectory $root -WindowStyle Normal | Out-Null
            foreach ($service in $needed) {
                $deadline = (Get-Date).AddSeconds($service.timeout)
                while (-not (Test-Service $service.name)) {
                    if ((Get-Date) -gt $deadline) { throw "$($service.mode) startup timed out. Check its terminal tab or logs." }
                    Start-Sleep -Milliseconds 250
                }
            }
        }
        Write-Host 'Ready. llama.cpp API: http://127.0.0.1:10000/v1. Open your desktop app separately.'
        Write-Host 'Close the Local-LLM window to stop the backend and any loaded model.'
    } catch {
        foreach ($service in $needed) { Stop-Owned $service.name }
        throw
    }
    return
}
# Service mode: the visible terminal owns the entire service process tree.
# Output is saved to files and streamed here, including native stderr messages.
$name = 'router'
$host.UI.RawUI.WindowTitle = 'Local LLM - model router'
Write-Host ("=== " + $host.UI.RawUI.WindowTitle + " ===") -ForegroundColor Cyan
Write-Host 'Close this tab to stop the backend and any loaded model.'
if (Get-OwnedProcess (Read-State $name)) { throw "The $name service is already running." }
if ($Mode -eq 'Backend') {
    & $python "$PSScriptRoot\model_router.py" --check-config
    if ($LASTEXITCODE -ne 0) { throw 'Model router configuration failed.' }
    $executable = $python
    $arguments = '-u "' + "$PSScriptRoot\model_router.py" + '"'
}
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
$stopSignal = "$stateDir\$name-stop.request"
Remove-Item -LiteralPath $stopSignal -ErrorAction SilentlyContinue
try {
    $outLog = "$root\logs\$name.out.log"
    $errLog = "$root\logs\$name.err.log"
    $child = Start-Process -FilePath $executable -ArgumentList $arguments -WorkingDirectory $root -NoNewWindow -PassThru -RedirectStandardOutput $outLog -RedirectStandardError $errLog
    try { [BackendJob]::Assign($job, $child.Handle) } catch { $child.Kill(); throw }
    @{pid=$child.Id;started=$child.StartTime.ToUniversalTime().ToString('o');executable=$executable;terminalPid=$PID;terminalStarted=(Get-Process -Id $PID).StartTime.ToUniversalTime().ToString('o');visible=$true;stopSignal=$true;terminalWindow=$config.terminalWindow;terminalSession=$env:WT_SESSION} | ConvertTo-Json | Set-Content -LiteralPath "$stateDir\$name-process.json"
    foreach ($log in @($outLog,$errLog)) {
        $stream = [IO.File]::Open($log,[IO.FileMode]::Open,[IO.FileAccess]::Read,([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
        $readers += [IO.StreamReader]::new($stream)
    }
    do {
        foreach ($reader in $readers) {
            while (-not $reader.EndOfStream) { Write-Host $reader.ReadLine() }
        }
        if (Test-Path -LiteralPath $stopSignal) { $stopRequested = $true; break }
        if ($child.HasExited) { break }
        Start-Sleep -Milliseconds 100
    } while ($true)
    foreach ($reader in $readers) {
        while (-not $reader.EndOfStream) { Write-Host $reader.ReadLine() }
    }
    if (-not $stopRequested -and $child.ExitCode -ne 0) { throw "$Mode exited with code $($child.ExitCode)." }
} catch {
    $failure = $_
    Write-Host $_ -ForegroundColor Red
} finally {
    [BackendJob]::CloseHandle($job) | Out-Null
    foreach ($reader in $readers) { $reader.Dispose() }
    Remove-Item -LiteralPath $stopSignal -ErrorAction SilentlyContinue
    $state = Read-State $name
    if ($state -and $state.terminalPid -eq $PID) {
        Remove-Item -LiteralPath "$stateDir\$name-process.json" -ErrorAction SilentlyContinue
    }
}
Write-Host "$Mode has stopped."
if ($stopRequested) { return }
Read-Host 'Press Enter to close this terminal' | Out-Null
if ($failure) { exit 1 }
