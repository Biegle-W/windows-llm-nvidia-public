param([ValidateSet('Default','Q3')][string]$Profile = 'Default')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$python = Join-Path $root 'runtimes\Strata\.venv\Scripts\python.exe'
$settings = Get-Content -LiteralPath "$root\config\strata.json" -Raw | ConvertFrom-Json
if ($settings.enabled -eq $false) { throw ('Strata is disabled: ' + $settings.disabledReason) }
$port = $settings.port
& "$PSScriptRoot\Start-Strata.ps1" -Mode Launch -Profile $Profile
& $python -u -c "import sys; sys.path.insert(0, 'scripts'); import benchmark_strata_drives as b; b.BASE='http://127.0.0.1:$port'; print(b.wait_ready(), flush=True)"
if ($LASTEXITCODE -ne 0) { throw 'Server did not become ready' }
& $python -u "$PSScriptRoot\test_strata_quant.py"
if ($LASTEXITCODE -ne 0) { throw 'Quant benchmark failed' }
& $python -u "$PSScriptRoot\test_strata.py" --port $port
if ($LASTEXITCODE -ne 0) { throw 'API/tool verification failed' }
& $python -u "$PSScriptRoot\verify_strata_context.py" --port $port
if ($LASTEXITCODE -ne 0) { throw 'Larger-context verification failed' }
$catalog = 'strata-harness-provider.json'
$oldNodeMode = $env:ELECTRON_RUN_AS_NODE
try {
    $env:ELECTRON_RUN_AS_NODE = '1'
    $desktop = Join-Path $env:LOCALAPPDATA 'Programs\DeepSeek Harness\DeepSeek Harness.exe'
    $arguments = '"' + "$PSScriptRoot\test_strata_harness_client.cjs" + '" ' + $catalog
    $client = Start-Process -FilePath $desktop -ArgumentList $arguments -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput "$root\data\strata-client-$Profile.log" -RedirectStandardError "$root\data\strata-client-$Profile-error.log"
    if ($client.ExitCode -ne 0) { throw 'DSH client verification failed' }
    Get-Content -LiteralPath "$root\data\strata-client-$Profile.log"
} finally { $env:ELECTRON_RUN_AS_NODE = $oldNodeMode }
