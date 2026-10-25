param(
    [ValidateSet('Default','Q3')][string]$Profile = 'Default',
    [string]$Settings,
    [string[]]$Splits
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
& "$PSScriptRoot\Start-Strata.ps1" -Mode Stop
$existingEngine = Get-Process strata -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$root\runtimes\Strata\*" }
if ($existingEngine) { throw 'A private Strata engine is already running. Close its calibration terminal first.' }
$python = Join-Path $root 'runtimes\Strata\.venv\Scripts\python.exe'
$arguments = @('-u', "$PSScriptRoot\tune_strata.py", '--profile', $Profile)
if ($Splits) {
    $arguments += @('--splits') + $Splits
    if ($Settings) { $arguments += @('--settings', $Settings) }
}
# Invoked inside a visible Local-LLM terminal; Tee keeps the same progress for audit.
& $python @arguments 2>&1 | Tee-Object -FilePath "$root\data\strata-tuning-$Profile.log"
if ($LASTEXITCODE -ne 0) { throw "Calibration failed with exit code $LASTEXITCODE. Restore the visible backend before use." }
