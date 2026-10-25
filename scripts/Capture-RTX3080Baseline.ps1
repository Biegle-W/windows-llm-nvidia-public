$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$python=Join-Path $root 'runtimes\python\cpython-3.11.15-windows-x86_64-none\python.exe'
$output=Join-Path $root ('data\uefi-probe\3080-10gb-baseline-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N'))
& $python (Join-Path $PSScriptRoot 'rtx3080_setup.py') baseline --output $output
if($LASTEXITCODE -ne 0){throw '3080 baseline was not recorded. Verify the installed card and free VRAM.'}
