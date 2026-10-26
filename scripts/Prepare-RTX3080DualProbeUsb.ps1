# Stage or collect the read-only pair probe. Never formats or executes firmware.
[CmdletBinding()]
param(
    [ValidateSet('Stage','Collect','SelfTest')][string]$Mode='Collect',
    [ValidatePattern('^[D-Zd-z]$')][string]$DriveLetter,
    [string]$Package,
    [string]$ExpectedSha256,
    [string]$AssignmentFile
)
$ErrorActionPreference='Stop'
$requestedDualMode=$Mode;$requestedDualLetter=$DriveLetter
# Load existing path/reparse helpers through their CPU-only test branch.
. (Join-Path $PSScriptRoot 'Prepare-RTX3080TiProbeUsb.ps1') -Mode SelfTest | Out-Null
$Mode=$requestedDualMode;$DriveLetter=$requestedDualLetter
$dualPrivate=Join-Path $root 'data\uefi-probe\dual-3080-usb'
if(-not $AssignmentFile){$AssignmentFile=Join-Path $dualPrivate 'assignment.private.json'}

function Assert-DualPackage($Info,[string]$Digest){
    if($Digest -notmatch '^[0-9a-f]{64}$' -or $Info.efi.sha256 -cne $Digest -or
       $Info.source_commit -ne '5c076dc4ee7fa369639669fa591ac74d8f6dfcd8' -or
       $Info.mode -ne 'read-only dual-card preparation'){throw 'Unreviewed pair-probe package.'}
    foreach($field in @('unlock_code_linked','firmware_assets_included','gpu_writes','gpu_resets',
        'driver_detach','automatic_unlock','internal_boot_changes','physical_pair_tested')){
        if($Info.$field -ne $false){throw ('Pair probe must remain read-only: '+$field)}
    }
}
function Assert-DualUsbIdentity($Disk,$Partition,$Assignment){
    if(-not $Assignment -or $Disk.BusType -ne 'USB' -or $Disk.IsBoot -or $Disk.IsSystem -or
       [string]::IsNullOrWhiteSpace($Assignment.DiskUniqueId) -or
       [string]::IsNullOrWhiteSpace($Assignment.SerialNumber) -or
       $Disk.UniqueId -ne $Assignment.DiskUniqueId -or
       $Disk.SerialNumber.Trim() -ne $Assignment.SerialNumber -or
       $Disk.Size -ne $Assignment.Size -or $Disk.FriendlyName -ne $Assignment.FriendlyName -or
       $Partition.DiskNumber -ne $Disk.Number -or
       $Partition.Offset -ne $Assignment.PartitionOffset -or
       $Partition.Size -ne $Assignment.PartitionSize){throw 'Dedicated pair USB identity changed.'}
}
if($Mode -eq 'SelfTest'){
    $digest='a'*64
    $info=@{efi=@{sha256=$digest};source_commit='5c076dc4ee7fa369639669fa591ac74d8f6dfcd8';mode='read-only dual-card preparation';
        unlock_code_linked=$false;firmware_assets_included=$false;gpu_writes=$false;gpu_resets=$false;
        driver_detach=$false;automatic_unlock=$false;internal_boot_changes=$false;physical_pair_tested=$false}
    Assert-DualPackage $info $digest;$checks=1
    foreach($field in @('unlock_code_linked','firmware_assets_included','gpu_writes','gpu_resets',
        'driver_detach','automatic_unlock','internal_boot_changes','physical_pair_tested','mode','source_commit')){
        $bad=$info.Clone();$bad[$field]=if($info[$field] -is [bool]){$true}else{'bad'}
        $refused=$false;try{Assert-DualPackage $bad $digest}catch{$refused=$true}
        if(-not $refused){throw 'Unsafe pair metadata accepted.'};$checks++
    }
    $disk=[pscustomobject]@{Number=1;BusType='USB';IsBoot=$false;IsSystem=$false;UniqueId='mock-id';SerialNumber='mock-serial';Size=8000000000;FriendlyName='mock-usb'}
    $part=[pscustomobject]@{DiskNumber=1;Offset=16384;Size=7999983616}
    $assignment=[pscustomobject]@{DiskUniqueId='mock-id';SerialNumber='mock-serial';Size=8000000000;FriendlyName='mock-usb';PartitionOffset=16384;PartitionSize=7999983616}
    Assert-DualUsbIdentity $disk $part $assignment;$checks++
    foreach($field in @('UniqueId','SerialNumber','Size','FriendlyName','BusType','IsBoot','IsSystem')){
        $bad=$disk.PSObject.Copy();$bad.$field=if($disk.$field -is [bool]){$true}elseif($disk.$field -is [string]){'bad'}else{1}
        $refused=$false;try{Assert-DualUsbIdentity $bad $part $assignment}catch{$refused=$true}
        if(-not $refused){throw 'Wrong USB accepted.'};$checks++
    }
    foreach($field in @('DiskNumber','Offset','Size')){
        $bad=$part.PSObject.Copy();$bad.$field=2
        $refused=$false;try{Assert-DualUsbIdentity $disk $bad $assignment}catch{$refused=$true}
        if(-not $refused){throw 'Wrong partition accepted.'};$checks++
    }
    Write-Output ('PASS '+$checks+' pair-package/USB identity checks plus shared path checks; no hardware changes.')
    return
}
$assignment=Get-Content -LiteralPath $AssignmentFile -Raw | ConvertFrom-Json
$candidates=@(foreach($volume in Get-Volume){
    if($volume.DriveLetter -match '^[D-Z]$' -and (-not $DriveLetter -or $volume.DriveLetter -eq $DriveLetter)){
        $partition=Get-Partition -DriveLetter $volume.DriveLetter
        $disk=Get-Disk -Number $partition.DiskNumber
        if($disk.UniqueId -eq $assignment.DiskUniqueId){[pscustomobject]@{Volume=$volume;Partition=$partition;Disk=$disk}}
    }
})
if($candidates.Count -ne 1){throw 'Connect the assigned SanDisk pair USB, or specify its current drive letter.'}
$usb=$candidates[0];Assert-Usb $usb.Disk $usb.Volume
Assert-DualUsbIdentity $usb.Disk $usb.Partition $assignment
$usbRoot=[string]$usb.Volume.DriveLetter+':\'
$stamp=(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N')
if($Mode -eq 'Collect'){
    $out=Join-Path $dualPrivate ('captures-'+$stamp)
    New-Item -ItemType Directory -Path $out | Out-Null
    $count=0
    foreach($folder in @('RTX30-PROBE','RTX-UNLOCK')){
        $parent=Safe-Child $usbRoot $folder
        foreach($run in Get-ChildItem -LiteralPath $parent -Directory -Force){
            if($run.Name -notmatch '^RUN[0-9]{2}$'){continue}
            $null=Safe-Child $usbRoot ($folder+'/'+$run.Name)
            foreach($file in Get-ChildItem -LiteralPath $run.FullName -Recurse -File -Force){
                $relative=$file.FullName.Substring($usbRoot.Length)
                $source=Safe-Child $usbRoot $relative;$target=Safe-Child $out $relative
                Ensure-Parent $target;Copy-Item -LiteralPath $source -Destination $target
                if((Get-FileHash -LiteralPath $source).Hash -ne (Get-FileHash -LiteralPath $target).Hash){throw 'Capture copy hash differs.'}
                $count++
            }
        }
    }
    $inventory=(& nvidia-smi --query-gpu=name,pci.bus_id,pci.device_id,pci.sub_device_id,vbios_version,memory.total,driver_version,uuid --format=csv,noheader,nounits | Out-String)
    if($LASTEXITCODE -ne 0){throw 'NVIDIA inventory failed; copied logs are retained.'}
    $inventory | Set-Content -LiteralPath (Join-Path $out 'windows-gpus.private.csv') -Encoding utf8
    [ordered]@{CaptureFiles=$count;UnlockVerified=$false;FirmwareExecutedByCollector=$false;UsbWrites=$false;CollectedAtUtc=[datetimeoffset]::UtcNow} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'collection.private.json') -Encoding utf8
    Write-Output ('Copied and hash checked '+$count+' capture files to '+$out)
    if(-not $count){throw 'No firmware captures found yet. Boot the read-only pair probe with both cards installed first.'}
    return
}
if(-not $Package -or -not $ExpectedSha256){throw 'Explicit reviewed package and EFI hash required.'}
$Package=[IO.Path]::GetFullPath($Package)
$dataPrefix=[IO.Path]::GetFullPath((Join-Path $root 'data')).TrimEnd([char]92)+'\'
if(-not $Package.StartsWith($dataPrefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Package must be in ignored project data.'}
$info=Get-Content -LiteralPath (Join-Path $Package 'BUILD-INFO.json') -Raw | ConvertFrom-Json
Assert-DualPackage $info $ExpectedSha256
$entries=@(foreach($line in Get-Content -LiteralPath (Join-Path $Package 'SHA256SUMS.txt')){
    if($line -notmatch '^([0-9a-f]{64})  (.+)$'){throw 'Invalid manifest.'}
    $digest=$Matches[1];$relative=$Matches[2];$source=Safe-Child $Package $relative
    if((Get-FileHash -LiteralPath $source).Hash.ToLowerInvariant() -ne $digest){throw 'Package hash differs.'}
    [pscustomobject]@{Relative=$relative;Source=$source;Digest=$digest;Target=(Safe-Child $usbRoot $relative)}
})
if((Get-FileHash -LiteralPath (Join-Path $Package 'EFI\BOOT\BOOTX64.EFI')).Hash.ToLowerInvariant() -ne $ExpectedSha256){throw 'EFI hash differs.'}
$manifest=Join-Path $Package 'SHA256SUMS.txt'
$entries+=[pscustomobject]@{Relative='SHA256SUMS.txt';Source=$manifest;Digest=(Get-FileHash -LiteralPath $manifest).Hash.ToLowerInvariant();Target=(Safe-Child $usbRoot 'SHA256SUMS.txt')}
$backup=Join-Path $dualPrivate ('before-stage-'+$stamp);New-Item -ItemType Directory -Path $backup | Out-Null
foreach($entry in $entries){
    if(Test-Path -LiteralPath $entry.Target){
        $saved=Safe-Child $backup $entry.Relative;Ensure-Parent $saved
        Copy-Item -LiteralPath $entry.Target -Destination $saved
        if((Get-FileHash -LiteralPath $entry.Target).Hash -ne (Get-FileHash -LiteralPath $saved).Hash){throw 'Collision backup differs.'}
    }
}
$fresh=Get-Partition -DriveLetter $usb.Volume.DriveLetter
Assert-DualUsbIdentity (Get-Disk -Number $fresh.DiskNumber) $fresh $assignment
# Copy the boot image last; preserve every existing RUN directory.
foreach($entry in ($entries | Sort-Object @{Expression={if($_.Relative -eq 'EFI/BOOT/BOOTX64.EFI'){1}else{0}}})){
    Ensure-Parent $entry.Target;Copy-Item -LiteralPath $entry.Source -Destination $entry.Target -Force
    if((Get-FileHash -LiteralPath $entry.Target).Hash.ToLowerInvariant() -ne $entry.Digest){throw 'Staging verification failed.'}
}
[ordered]@{Success=$true;Mode='read-only dual-card preparation';DriveLetter=$usb.Volume.DriveLetter;
    EfiSha256=$ExpectedSha256;VerifiedFiles=$entries.Count;FormatPerformed=$false;UnlockExecuted=$false;
    BootSettingsChanged=$false;PhysicalPairTested=$false;Backup=$backup} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $dualPrivate 'staging.private.json') -Encoding utf8
Write-Output ('Read-only pair probe staged; '+$entries.Count+' hashes verified. No unlock image is installed.')
