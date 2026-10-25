$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$python=Join-Path $root 'runtimes\python\cpython-3.11.15-windows-x86_64-none\python.exe'
$output=Join-Path $root ('data\uefi-probe\3080ti-baseline-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N'))
& $python (Join-Path $PSScriptRoot 'rtx3080ti_setup.py') baseline --output $output
if($LASTEXITCODE -ne 0){throw 'Baseline was not recorded. Check the card identity, driver and free GPU memory above.'}
Write-Output ('Saved private pre-attempt baseline: '+$output)
