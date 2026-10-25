# Update only the existing dedicated boot payload. No resize, format or BCD mutation.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$BuildDirectory,
    [ValidatePattern('^[A-Za-z0-9-]{1,40}$')][string]$BackupName='zero-startup-install-backup'
)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$stateRoot=Join-Path $root 'data\uefi-probe\internal-startup'
$statePath=Join-Path $stateRoot 'installed-state.private.json'
$resultPath=Join-Path $stateRoot 'zero-startup-update.private.json'
$backup=Join-Path $stateRoot $BackupName
$answer=[ordered]@{Success=$false;Error=$null;RollbackErrors=@();PhysicalBootVerified=$false;MountRemoved=$false}
$mounted=$false; $wrotePayload=$false
function BcdRead {
    $value=(& "$env:SystemRoot\System32\bcdedit.exe" /enum firmware /v 2>&1 | Out-String)
    if($LASTEXITCODE -ne 0){throw 'Firmware query failed.'}
    return $value
}
function PackagePath([string]$Base,[string]$Relative) {
    if(-not $Relative -or [IO.Path]::IsPathRooted($Relative) -or $Relative -match '[:\r\n]' -or ($Relative -split '[\\/]') -contains '..'){throw 'Unsafe manifest path.'}
    $normalized=$Relative.Replace('\','/')
    if($normalized -match '^EFI/' -and $normalized -ne 'EFI/LLMUnlock/Auto3060.efi'){throw 'Manifest targets an unrelated EFI path.'}
    if($normalized -match '^RTX-UNLOCK/' -and $normalized -notmatch '^RTX-UNLOCK/(ASSETS/|DEBUG\.ON$|NVIDIA-LICENSE$|README\.txt$)'){throw 'Manifest targets boot logs or an unrelated runtime path.'}
    $prefix=[IO.Path]::GetFullPath($Base).TrimEnd([char]92)+'\'
    $target=[IO.Path]::GetFullPath([IO.Path]::Combine($prefix,$Relative.Replace('/','\')))
    if(-not $target.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Manifest escapes its package root.'}
    return $target
}
try {
    $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
    if(-not ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Run as administrator.'}
    $build=[IO.Path]::GetFullPath($BuildDirectory)
    if(-not $build.StartsWith(($stateRoot+'\'),[StringComparison]::OrdinalIgnoreCase)){throw 'Build must be in private internal-startup state.'}
    $s=Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json -AsHashtable
    $info=Get-Content -LiteralPath (Join-Path $build 'BUILD-INFO.private.json') -Raw | ConvertFrom-Json
    if($info.preview_only -or -not $info.automatic -or -not $info.host_tests_passed -or -not $info.firmware_transaction_unchanged -or
        -not $info.hardware_tested_display_source_unchanged -or $info.host_auto_and_source_tests -ne 14 -or $info.host_actual_cold_check_tests -ne 23 -or
        -not $info.coldcheck_only_initial_pair_predicate_changed -or
        ($info.startup_profile_evidence.allowed_initial_pairs | ConvertTo-Json -Compress) -ne '[["00000000","00000000"],["70520074","00000005"]]' -or
        $info.startup_profile_evidence.fixed_initial_ss0 -ne '00000000' -or $info.startup_profile_evidence.fixed_initial_ss1 -ne '00000000' -or
        [guid]$info.internal_partition_guid -ne [guid]$s.PartitionGuid){throw 'Corrected build contract differs.'}
    if($s.EfiSha256 -ne 'f837ed1db52138125fe530460a546f9f9fdda122d76b13ef862a7036524516ca'){throw 'Expected the zero-only automatic build; do not repeat an update blindly.'}
    $disk=Get-Disk -Number $s.DiskNumber
    if($disk.UniqueId -ne $s.DiskUniqueId){throw 'Original disk identity differs.'}
    $parts=@(Get-Partition -DiskNumber $s.DiskNumber)
    $matches=@($parts | Where-Object Guid -eq $s.PartitionGuid)
    if($matches.Count -ne 1){throw 'Dedicated partition GUID missing or ambiguous.'}
    $part=$matches[0]
    if($part.Size -ne 536870912 -or $part.Offset -ne $s.NewOffset -or $part.GptType -ne '{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}' -or (Get-Partition -DriveLetter C).Size -ne $s.CTargetSize){throw 'Partition identity/size differs.'}
    if(Test-Path 'U:\'){throw 'U: is occupied.'}
    if(Test-Path -LiteralPath $backup){throw 'Update backup already exists; inspect prior update instead of repeating.'}
    $fwBefore=BcdRead
    $partsBefore=$parts | Select-Object Guid,GptType,Offset,Size | Sort-Object Guid | ConvertTo-Json -Compress
    New-Item -ItemType Directory -Path $backup | Out-Null
    Copy-Item -LiteralPath $statePath -Destination (Join-Path $backup 'installed-state.private.json')
    [IO.File]::WriteAllText((Join-Path $backup 'firmware-before.private.txt'),$fwBefore)
    Add-PartitionAccessPath -DiskNumber $s.DiskNumber -PartitionNumber $part.PartitionNumber -AccessPath 'U:\'
    $mounted=$true
    if((Get-Partition -DriveLetter U).Guid -ne $s.PartitionGuid -or [IO.DriveInfo]::new('U:\').DriveFormat -ne 'FAT32'){throw 'Mounted ESP differs.'}
    # BCDEdit renders the same volume as U: while mounted, rather than HarddiskVolumeN.
    # Compare like-for-like mounted readings, then compare unmounted readings in finally.
    $fwMountedBefore=BcdRead
    $efi='U:\EFI\LLMUnlock\Auto3060.efi'
    if((Get-FileHash -LiteralPath $efi).Hash.ToLowerInvariant() -ne $s.EfiSha256){throw 'Installed prior EFI hash differs.'}
    $logBefore=@{}
    foreach($name in @('GOP.TXT','UNLOCK.TXT')){$logBefore[$name]=(Get-FileHash -LiteralPath ('U:\RTX-UNLOCK\RUN0000\'+$name)).Hash}
    $package=Join-Path $build 'package'
    $rows=@()
    $paths=@{}
    foreach($line in Get-Content -LiteralPath (Join-Path $package 'SHA256SUMS.txt')){
        if($line -notmatch '^([0-9a-f]{64})  (.+)$'){throw 'Malformed build manifest.'}
        $digest=$matches[1];$relative=$matches[2]
        if($paths.ContainsKey($relative)){throw 'Duplicate manifest target.'};$paths[$relative]=$true
        $source=PackagePath $package $relative; $target=PackagePath 'U:\' $relative
        if((Get-FileHash -LiteralPath $source).Hash.ToLowerInvariant() -ne $digest){throw 'Source file hash differs.'}
        $rows+=@{Relative=$relative;Source=$source;Target=$target;Digest=$digest}
        if(Test-Path -LiteralPath $target){
            $save=PackagePath (Join-Path $backup 'files') $relative
            New-Item -ItemType Directory -Path (Split-Path -Parent $save) -Force | Out-Null
            Copy-Item -LiteralPath $target -Destination $save
            if((Get-FileHash -LiteralPath $save).Hash -ne (Get-FileHash -LiteralPath $target).Hash){throw 'Update backup hash differs.'}
        }
    }
    if(-not $paths.ContainsKey('EFI/LLMUnlock/Auto3060.efi')){throw 'Manifest has no automatic EFI.'}
    Copy-Item -LiteralPath 'U:\SHA256SUMS.txt' -Destination (Join-Path $backup 'SHA256SUMS.txt')
    Copy-Item -LiteralPath $efi -Destination 'U:\EFI\LLMUnlock\Auto3060.previous.efi'
    $wrotePayload=$true
    foreach($row in $rows | Where-Object Relative -ne 'EFI/LLMUnlock/Auto3060.efi'){
        if(-not (Test-Path -LiteralPath $row.Target) -or (Get-FileHash -LiteralPath $row.Target).Hash.ToLowerInvariant() -ne $row.Digest){
            New-Item -ItemType Directory -Path (Split-Path -Parent $row.Target) -Force | Out-Null
            Copy-Item -LiteralPath $row.Source -Destination $row.Target -Force
        }
    }
    $efiRow=@($rows | Where-Object Relative -eq 'EFI/LLMUnlock/Auto3060.efi')[0]
    Copy-Item -LiteralPath $efiRow.Source -Destination 'U:\EFI\LLMUnlock\Auto3060.next.efi'
    if((Get-FileHash -LiteralPath 'U:\EFI\LLMUnlock\Auto3060.next.efi').Hash.ToLowerInvariant() -ne $info.efi.sha256){throw 'Staged replacement EFI differs.'}
    Move-Item -LiteralPath 'U:\EFI\LLMUnlock\Auto3060.next.efi' -Destination $efi -Force
    foreach($row in $rows){if((Get-FileHash -LiteralPath $row.Target).Hash.ToLowerInvariant() -ne $row.Digest){throw 'Updated file hash differs.'}}
    Copy-Item -LiteralPath (Join-Path $package 'SHA256SUMS.txt') -Destination 'U:\SHA256SUMS.txt' -Force
    foreach($name in $logBefore.Keys){if((Get-FileHash -LiteralPath ('U:\RTX-UNLOCK\RUN0000\'+$name)).Hash -ne $logBefore[$name]){throw 'Original boot logs changed.'}}
    if((BcdRead) -cne $fwMountedBefore){throw 'Firmware entries/order changed during file update.'}
    $partsAfter=Get-Partition -DiskNumber $s.DiskNumber | Select-Object Guid,GptType,Offset,Size | Sort-Object Guid | ConvertTo-Json -Compress
    if($partsBefore -cne $partsAfter){throw 'Partition inventory changed during file update.'}
    $s.PreviousEfiSha256=$s.EfiSha256;$s.EfiSha256=$info.efi.sha256
    $s.Status='automatic-paired-startup-installed-awaiting-boot';$s.AutoInternalBootVerified=$false
    $s.StartupProfile='exactly 0/0 or 70520074/5; complete pairs only';$s.CorrectedBuildDirectory=$build
    $s.PartitionNumber=$part.PartitionNumber
    $temporary=$statePath+'.update.pending'
    [IO.File]::WriteAllText($temporary,($s | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
    [IO.File]::Replace($temporary,$statePath,[System.Management.Automation.Language.NullString]::Value)
    $answer.Success=$true;$answer.EfiSha256=$s.EfiSha256;$answer.ManifestFilesVerified=$rows.Count
    $answer.BootEntriesUnchanged=$true;$answer.PartitionsUnchanged=$true;$answer.OriginalLogsPreserved=$true
} catch {
    $answer.Error=$_.Exception.Message
    if($wrotePayload){
        try {
            foreach($file in Get-ChildItem -LiteralPath (Join-Path $backup 'files') -Recurse -File){
                $relative=[IO.Path]::GetRelativePath((Join-Path $backup 'files'),$file.FullName)
                Copy-Item -LiteralPath $file.FullName -Destination (PackagePath 'U:\' $relative) -Force
            }
            Copy-Item -LiteralPath (Join-Path $backup 'SHA256SUMS.txt') -Destination 'U:\SHA256SUMS.txt' -Force
            Copy-Item -LiteralPath (Join-Path $backup 'installed-state.private.json') -Destination $statePath -Force
            $answer.RollbackAttempted=$true
            $rollbackState=Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
            if((Get-FileHash -LiteralPath $efi).Hash.ToLowerInvariant() -ne $rollbackState.EfiSha256){throw 'Restored prior EFI hash differs.'}
            $answer.RollbackVerified=$true
        } catch {$answer.RollbackErrors+=@($_.Exception.Message)}
    }
} finally {
    if($mounted){
        try {
            if((Get-Partition -DriveLetter U).Guid -ne $s.PartitionGuid){throw 'Temporary mount ownership changed.'}
            Remove-PartitionAccessPath -DiskNumber $s.DiskNumber -PartitionNumber $part.PartitionNumber -AccessPath 'U:\'
            $answer.MountRemoved=$true
            if((BcdRead) -cne $fwBefore){throw 'Unmounted firmware entries differ from the original reading.'}
        } catch {$answer.Success=$false;$answer.Error=$_.Exception.Message}
    }
    [IO.File]::WriteAllText($resultPath,($answer | ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
}
if(-not $answer.Success){throw $answer.Error}
'Corrected automatic EFI installed; all manifest files verified. No boot-order, partition or GPU-state change; reboot not initiated.'
