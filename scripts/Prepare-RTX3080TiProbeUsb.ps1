# Stage verified read-only diagnostics; never format a drive or install an unlock.
[CmdletBinding()]
param(
    [ValidateSet('Board','Ownership','Collect','SelfTest')][string]$Mode='Board',
    [ValidatePattern('^[D-Zd-z]$')][string]$DriveLetter
)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$private=Join-Path $root 'data\uefi-probe\3080ti-usb'
function Safe-Child([string]$Base,[string]$Relative) {
    if(-not $Relative -or [IO.Path]::IsPathRooted($Relative) -or $Relative -match '[:\r\n]' -or ($Relative -split '[\\/]') -contains '..'){throw 'Unsafe package path.'}
    $prefix=[IO.Path]::GetFullPath($Base).TrimEnd([char]92)+'\'
    $path=[IO.Path]::GetFullPath((Join-Path $Base $Relative))
    if(-not $path.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Path escapes its root.'}
    $cursor=$path
    while($cursor.Length -ge $prefix.Length){
        if((Test-Path -LiteralPath $cursor) -and ((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Reparse points are not permitted in package paths.'}
        $cursor=Split-Path -Parent $cursor
    }
    return $path
}
function Assert-Usb($Disk,$Volume) {
    if($Disk.BusType -ne 'USB' -or $Disk.IsBoot -or $Disk.IsSystem -or $Volume.FileSystem -ne 'FAT32' -or $Volume.DriveLetter -notmatch '^[D-Z]$'){throw 'Use a non-system FAT32 USB volume with a drive letter. Nothing was formatted.'}
}
function Assert-Card([string]$Text) {
    $rows=@($Text.Trim() -split '\r?\n')
    $fields=@($rows[0].Split(',') | ForEach-Object {$_.Trim()})
    if($rows.Count -ne 1 -or $fields.Count -ne 6 -or $fields[0] -ne 'NVIDIA GeForce RTX 3080 Ti' -or $fields[1] -notmatch '^(00000000|0000):01:00\.0$' -or $fields[2] -ne '0x220810DE' -or $fields[3] -ne '0x153510DE' -or $fields[4] -ne '94.02.71.00.01' -or $fields[5] -ne '12288'){throw 'The captured Windows identity of this exact 3080 Ti differs.'}
}
if($Mode -eq 'SelfTest') {
    $card='NVIDIA GeForce RTX 3080 Ti, 00000000:01:00.0, 0x220810DE, 0x153510DE, 94.02.71.00.01, 12288'
    Assert-Card $card
    foreach($bad in @($card.Replace('153510DE','407B1458'),$card.Replace('220810DE','220610DE'),$card.Replace('71.00.01','71.00.02'),($card+"`n"+$card))){$rejected=$false;try{Assert-Card $bad}catch{$rejected=$true};if(-not $rejected){throw 'Wrong card accepted.'}}
    $disk=[pscustomobject]@{BusType='USB';IsBoot=$false;IsSystem=$false}
    $vol=[pscustomobject]@{FileSystem='FAT32';DriveLetter='D'}
    Assert-Usb $disk $vol
    foreach($bad in @([pscustomobject]@{BusType='NVMe';IsBoot=$false;IsSystem=$false},[pscustomobject]@{BusType='USB';IsBoot=$true;IsSystem=$false},[pscustomobject]@{BusType='USB';IsBoot=$false;IsSystem=$true})){$rejected=$false;try{Assert-Usb $bad $vol}catch{$rejected=$true};if(-not $rejected){throw 'System disk accepted.'}}
    $rejected=$false;try{Assert-Usb $disk ([pscustomobject]@{FileSystem='NTFS';DriveLetter='D'})}catch{$rejected=$true};if(-not $rejected){throw 'NTFS accepted.'}
    foreach($bad in @('../file','C:\Windows\file','/EFI/file','EFI/../../file')){$rejected=$false;try{$null=Safe-Child $root $bad}catch{$rejected=$true};if(-not $rejected){throw 'Unsafe path accepted.'}}
    if((Safe-Child $root 'EFI/BOOT/BOOTX64.EFI') -ne (Join-Path $root 'EFI\BOOT\BOOTX64.EFI')){throw 'Valid path failed.'}
    'PASS 15 USB/card/path policy checks; no USB or GPU changes.'
    return
}
$inventory=(& nvidia-smi --query-gpu=name,pci.bus_id,pci.device_id,pci.sub_device_id,vbios_version,memory.total --format=csv,noheader,nounits | Out-String)
if($LASTEXITCODE -ne 0){throw 'NVIDIA inventory failed.'};Assert-Card $inventory
$candidates=@(foreach($v in Get-Volume){
    if($v.DriveLetter -match '^[D-Z]$' -and (-not $DriveLetter -or $v.DriveLetter -eq $DriveLetter)){
        $p=Get-Partition -DriveLetter $v.DriveLetter
        $d=Get-Disk -Number $p.DiskNumber
        if($d.BusType -eq 'USB') { [pscustomobject]@{Volume=$v;Partition=$p;Disk=$d} }
    }
})
if($candidates.Count -ne 1){throw 'Connect exactly one FAT32 USB, or pass -DriveLetter X. No files or boot settings changed.'}
$usb=$candidates[0];Assert-Usb $usb.Disk $usb.Volume
$usbRoot=[string]$usb.Volume.DriveLetter+':\'
$stamp=(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N')
if($Mode -eq 'Collect') {
    $out=Join-Path $private ('captures-'+$stamp)
    New-Item -ItemType Directory -Path $out | Out-Null
    foreach($folder in @('RTX30-PROBE','RTX-UNLOCK')){
        $source=Safe-Child $usbRoot $folder
        if(Test-Path -LiteralPath $source){
            foreach($file in Get-ChildItem -LiteralPath $source -Recurse -File -Force){
                $relative=$file.FullName.Substring($usbRoot.Length)
                $sourceFile=Safe-Child $usbRoot $relative;$target=Safe-Child $out $relative
                New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
                Copy-Item -LiteralPath $sourceFile -Destination $target
                if((Get-FileHash -LiteralPath $sourceFile).Hash -ne (Get-FileHash -LiteralPath $target).Hash){throw 'Capture copy differs.'}
            }
        }
    }
    Write-Output ('Private captures copied and hash checked: '+$out)
    Write-Output 'Old 3060 runs may be included. Audit only a report with actual 2208/10de:1535 identity.'
    return
}
$packageName=if($Mode -eq 'Board'){'01-board-probe'}else{'02-ownership-probe'}
$expected=if($Mode -eq 'Board'){'ae7b5cdd1cc579fc516ebda68c9d438d433697fb78d151304d56a2cbca41785a'}else{'58f4d6beb444d423a8509dd4d1cdbb7a2e10a425e51ae2e65f2cceaa011342b8'}
$package=Join-Path $root ('data\uefi-probe\rtx3080ti-unlock-setup\'+$packageName)
$manifest=Join-Path $package 'SHA256SUMS.txt'
if((Get-FileHash -LiteralPath (Join-Path $package 'EFI\BOOT\BOOTX64.EFI')).Hash.ToLowerInvariant() -ne $expected){throw 'Read-only EFI hash differs.'}
$entries=@(foreach($line in Get-Content -LiteralPath $manifest){
    if($line -notmatch '^([0-9a-f]{64})  (.+)$'){throw 'Invalid manifest.'}
    $digest=$Matches[1];$relative=$Matches[2];$source=Safe-Child $package $relative
    if((Get-FileHash -LiteralPath $source).Hash.ToLowerInvariant() -ne $digest){throw 'Package manifest mismatch.'}
    [pscustomobject]@{Relative=$relative;Source=$source;Digest=$digest;Target=(Safe-Child $usbRoot $relative)}
})
if($usb.Volume.SizeRemaining -lt 33554432){throw 'At least 32 MiB free USB space required.'}
$backup=Join-Path $private ('before-'+$Mode.ToLowerInvariant()+'-'+$stamp)
New-Item -ItemType Directory -Path $backup | Out-Null
$entries+= [pscustomobject]@{Relative='SHA256SUMS.txt';Source=$manifest;Digest=(Get-FileHash -LiteralPath $manifest).Hash.ToLowerInvariant();Target=(Safe-Child $usbRoot 'SHA256SUMS.txt')}
# Complete backup of every collision before the first USB write. Existing RUN directories are retained.
foreach($e in $entries){
    if(Test-Path -LiteralPath $e.Target){
        if(-not (Test-Path -LiteralPath $e.Target -PathType Leaf)){throw 'A destination is not a file.'}
        $saved=Safe-Child $backup $e.Relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $saved) -Force | Out-Null
        Copy-Item -LiteralPath $e.Target -Destination $saved
        if((Get-FileHash -LiteralPath $e.Target).Hash -ne (Get-FileHash -LiteralPath $saved).Hash){throw 'USB backup differs; staging refused.'}
    }
}
$record=[ordered]@{Mode=$Mode;GpuIdentity=$inventory.Trim();DiskNumber=$usb.Disk.Number;DiskUniqueId=$usb.Disk.UniqueId;PartitionGuid=$usb.Partition.Guid;DriveLetter=$usb.Volume.DriveLetter;Backup=$backup;EfiSha256=$expected;Success=$false;FormatPerformed=$false;BootSettingsChanged=$false;UnlockExecuted=$false}
$recordPath=Join-Path $backup 'stage.private.json'
$record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $recordPath -Encoding utf8
# Recheck disk identity immediately before writing; do not follow a swapped drive letter.
$now=Get-Partition -DriveLetter $usb.Volume.DriveLetter
if($now.Guid -ne $usb.Partition.Guid -or $now.DiskNumber -ne $usb.Disk.Number -or $now.Offset -ne $usb.Partition.Offset -or $now.Size -ne $usb.Partition.Size -or (Get-Disk -Number $now.DiskNumber).UniqueId -ne $usb.Disk.UniqueId){throw 'USB identity changed.'}
foreach($e in $entries){
    $target=Safe-Child $usbRoot $e.Relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $e.Source -Destination $target -Force
    if((Get-FileHash -LiteralPath $target).Hash.ToLowerInvariant() -ne $e.Digest){throw 'USB staging verification failed. Restore the backed-up files before booting.'}
}
$record.Success=$true;$record.VerifiedFiles=$entries.Count
$record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $recordPath -Encoding utf8
Write-Output ($Mode+' read-only probe staged; '+$entries.Count+' file hashes verified. Existing files backed up under '+$backup)
Write-Output 'Restart manually, press F8 and choose UEFI USB. After capture returns, choose Windows Boot Manager.'
Write-Output 'Do not select RTX 3060 Automatic Unlock with the 3080 Ti installed.'
