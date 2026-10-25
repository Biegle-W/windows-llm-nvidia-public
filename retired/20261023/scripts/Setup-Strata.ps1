param([ValidateSet('Default','Q3')][string]$Profile = 'Default')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$settingsFile = 'strata.json' # Retain -Profile Q3 as a compatibility alias.
$settings = Get-Content -LiteralPath (Join-Path "$root\config" $settingsFile) -Raw | ConvertFrom-Json
if ($settings.enabled -eq $false) { throw ('Strata is deferred: ' + $settings.disabledReason) }
$strata = Join-Path $root $settings.directory
$sourceCommit = (& git -C $strata rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $sourceCommit -ne $settings.sourceCommit) {
    throw "Strata source differs from the pinned revision $($settings.sourceCommit). Check out that revision before setup."
}
$python = Join-Path $strata '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'The private Strata Python environment is missing. See reports/STRATA.md.' }
& "$PSScriptRoot\Start-Strata.ps1" -Mode Stop
$vision = if ($settings.vision) { 'gpu' } else { 'no' }
$projection = if ($settings.experimentalSpeedProjection) { 'on' } else { 'off' }
$arguments = @('-u', (Join-Path $strata 'setup.py'), '--family', $settings.family,
    '--model', $settings.quantization, '--context', [string]$settings.context,
    '--kv', $settings.kv, '--vision', $vision, '--experimental-speed-projection', $projection,
    '--data-dir', $settings.dataDirectory, '--host', $settings.host,
    '--port', [string]$settings.port, '--yes', '--no-start')
if ($settings.lowRamMode) { $arguments += @('--low-ram', [string]$settings.lowRamMode) }
if ($settings.kvStreaming) { $arguments += @('--kv-streaming', [string]$settings.kvStreaming) }
if (@($settings.gpus).Count -eq 1) {
    $arguments += @('--gpu', [string]$settings.gpus[0])
} elseif (@($settings.gpus).Count -gt 1) {
    $arguments += @('--gpus', ($settings.gpus -join ','), '--layer-split', $settings.layerSplit)
} else { throw 'Configure at least one GPU in config/strata.json.' }
& $python @arguments
if ($LASTEXITCODE -ne 0) { throw "Strata setup failed with exit code $LASTEXITCODE. Rerun to resume." }
$enginePath = Join-Path $strata $settings.engineConfig
$engine = Get-Content -LiteralPath $enginePath -Raw | ConvertFrom-Json
$build = Get-Content -LiteralPath (Join-Path $strata 'engine\BUILD.json') -Raw | ConvertFrom-Json
if ($settings.engineVersion -and $build.version -ne $settings.engineVersion) {
    throw "Expected engine $($settings.engineVersion), installed $($build.version). Review the upstream update before launching."
}
if ($settings.lowRamMode -eq 'resident') {
    # Validate that regeneration preserved the measured resident mode.
    if (@($settings.gpus).Count -gt 1 -and [version]$build.version -lt [version]'0.1.40') {
        throw 'Resident experts on a layer split require Strata 0.1.40 or newer.'
    }
    $experts = Join-Path $settings.dataDirectory ('packs\' + $settings.quantization.ToLowerInvariant() + '\experts.bin')
    if (-not (Test-Path -LiteralPath $experts -PathType Leaf)) {
        throw "Resident expert pack is missing: $experts"
    }
    if ('--resident-experts' -notin $engine.args -or '--mmap-experts' -in $engine.args) {
        throw 'Setup did not preserve resident experts. Review the generated configuration before launching.'
    }
}
if ($settings.vramReserveMiB) {
    $engineArgs = [Collections.Generic.List[string]]::new()
    $engineArgs.AddRange([string[]]$engine.args)
    $reserveIndex = $engineArgs.IndexOf('--vram-reserve-mib')
    if ($reserveIndex -ge 0) { $engineArgs.RemoveRange($reserveIndex, 2) }
    $engineArgs.Add('--vram-reserve-mib')
    $engineArgs.Add([string]$settings.vramReserveMiB)
    $engine.args = $engineArgs.ToArray()
    [IO.File]::WriteAllText($enginePath, ($engine | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
}
if ($null -ne $settings.engineOptions) {
    $engineArgs = [Collections.Generic.List[string]]::new()
    $engineArgs.AddRange([string[]]$engine.args)
    $defaults = @{
        '--pcie-frac' = $null; '--spec-min-p' = '0.5'; '--pool-workers' = $null
        '--spec' = '4'; '--vram-reserve-later-mib' = $null
        '--pipeline-windows' = $null; '--adapt-async' = $null
        '--adapt-every' = $null; '--adapt-swaps' = $null; '--adapt-decay' = $null
        '--mtp-window' = $null
    }
    foreach ($option in $settings.engineOptions.PSObject.Properties) {
        if (-not $defaults.ContainsKey($option.Name)) { throw "Unsupported tuning option: $($option.Name)" }
    }
    foreach ($flag in $defaults.Keys) {
        $index = $engineArgs.IndexOf($flag)
        if ($index -ge 0) { $engineArgs.RemoveRange($index, 2) }
        $value = $defaults[$flag]
        $property = $settings.engineOptions.PSObject.Properties[$flag]
        if ($null -ne $property) { $value = $property.Value }
        if ($null -ne $value) { $engineArgs.Add($flag); $engineArgs.Add([string]$value) }
    }
    $engine.args = $engineArgs.ToArray()
    [IO.File]::WriteAllText($enginePath, ($engine | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
}
if ($null -ne $settings.engineEnvironment) {
    $engine | Add-Member -NotePropertyName env -NotePropertyValue $settings.engineEnvironment -Force
    [IO.File]::WriteAllText($enginePath, ($engine | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
}
$launcher = 'Start Strata.cmd'
Write-Host "Strata setup completed. Double-click $launcher to load the model."
