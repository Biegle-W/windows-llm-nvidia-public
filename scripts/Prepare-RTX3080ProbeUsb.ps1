# Separate read-only2206/10GB staging. Board mode can prepare the USB before the card swap.
[CmdletBinding()]
param([ValidateSet('Board','Ownership','Collect')][string]$Mode='Board',[ValidatePattern('^[D-Zd-z]$')][string]$DriveLetter)
$ErrorActionPreference='Stop'
$requested3080Mode=$Mode;$requested3080Letter=$DriveLetter
# Load the existing verified path/reparse/USB helpers through its test-only branch.
# This branch returns before any GPU query, USB selection, backup or write.
. (Join-Path $PSScriptRoot 'Prepare-RTX3080TiProbeUsb.ps1') -Mode SelfTest
$Mode=$requested3080Mode;$DriveLetter=$requested3080Letter
$private=Join-Path $root 'data\uefi-probe\3080-10gb-usb'
if($Mode -ne 'Board'){
    $identity=(& nvidia-smi --query-gpu=name,pci.device_id,memory.total --format=csv,noheader,nounits | Out-String).Trim()
    if($LASTEXITCODE -ne 0 -or $identity -notmatch '^NVIDIA GeForce RTX 3080,\s*0x220610DE,\s*10240$'){throw 'Ownership/collection requires the installed2206 RTX3080 10GB. Current3060/3080Ti are refused.'}
}
$candidates=@(foreach($v in Get-Volume){
    if($v.DriveLetter -match '^[D-Z]$' -and (-not $DriveLetter -or $v.DriveLetter -eq $DriveLetter)){
        $part3080=Get-Partition -DriveLetter $v.DriveLetter;$disk3080=Get-Disk -Number $part3080.DiskNumber
        if($disk3080.BusType -eq 'USB'){[pscustomobject]@{Volume=$v;Partition=$part3080;Disk=$disk3080}}
    }
})
if($candidates.Count -ne 1){throw 'Select exactly one FAT32 USB, or pass -DriveLetter X.'}
$usb=$candidates[0];Assert-Usb $usb.Disk $usb.Volume
$usbRoot=[string]$usb.Volume.DriveLetter+':\';$stamp=(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N')
if($Mode -eq 'Collect'){
    $out=Join-Path $private ('captures-'+$stamp);New-Item -ItemType Directory -Path $out | Out-Null
    $count=0
    foreach($folder in @('RTX30-PROBE','RTX-UNLOCK')){
        $source=Safe-Child $usbRoot $folder
        if(Test-Path -LiteralPath $source){
            foreach($run in Get-ChildItem -LiteralPath $source -Directory | Where-Object Name -match '^RUN\d{2,4}$'){
                foreach($file in Get-ChildItem -LiteralPath $run.FullName -File -Recurse -Force){
                    $relative=$file.FullName.Substring($usbRoot.Length);$sourceFile=Safe-Child $usbRoot $relative;$target=Safe-Child $out $relative
                    Ensure-Parent $target;Copy-Item -LiteralPath $sourceFile -Destination $target
                    if((Get-FileHash -LiteralPath $sourceFile).Hash -ne (Get-FileHash -LiteralPath $target).Hash){throw 'Capture copy differs.'};$count++
                }
            }
        }
    }
    Write-Output ('Copied/hash-verified '+$count+' capture files to '+$out+'. Prior-card runs may be present; audit only2206 matching the new baseline.')
    return
}
if($Mode -eq 'Board'){
    $package=Join-Path $root 'data\uefi-probe\rtx3080-10gb-readonly'
    $expected='ae7b5cdd1cc579fc516ebda68c9d438d433697fb78d151304d56a2cbca41785a'
}else{
    $package=Join-Path $root 'data\uefi-probe\rtx3080-10gb-ownership\package'
    $expected='58f4d6beb444d423a8509dd4d1cdbb7a2e10a425e51ae2e65f2cceaa011342b8'
}
$info=Get-Content -LiteralPath (Join-Path $package 'BUILD-INFO.json') -Raw | ConvertFrom-Json
if($info.expected_pci_id -ne '10de:2206' -or $info.source_commit -ne '5c076dc4ee7fa369639669fa591ac74d8f6dfcd8' -or (Get-FileHash -LiteralPath (Join-Path $package 'EFI\BOOT\BOOTX64.EFI')).Hash.ToLowerInvariant() -ne $expected){throw 'Reviewed2206 read-only package differs.'}
if($Mode -eq 'Ownership' -and ($info.mode -ne 'GC_TREE_ONLY' -or $info.unlock_code_linked -ne $false -or $info.firmware_assets_included -ne $false)){throw 'Ownership package is not read-only.'}
$manifest=Join-Path $package 'SHA256SUMS.txt'
$rows=@(foreach($line in Get-Content -LiteralPath $manifest){
    if($line -notmatch '^([0-9a-f]{64})  (.+)$'){throw 'Invalid manifest.'}
    $digest=$Matches[1];$relative=$Matches[2];$source=Safe-Child $package $relative
    if((Get-FileHash -LiteralPath $source).Hash.ToLowerInvariant() -ne $digest){throw 'Source package hash mismatch.'}
    [pscustomobject]@{Relative=$relative;Source=$source;Target=(Safe-Child $usbRoot $relative);Digest=$digest}
})
$rows+=[pscustomobject]@{Relative='SHA256SUMS.txt';Source=$manifest;Target=(Safe-Child $usbRoot 'SHA256SUMS.txt');Digest=(Get-FileHash -LiteralPath $manifest).Hash.ToLowerInvariant()}
if($usb.Volume.SizeRemaining -lt 33554432){throw 'At least32MiB free USB space required.'}
$backup=Join-Path $private ('before-'+$Mode.ToLowerInvariant()+'-'+$stamp);New-Item -ItemType Directory -Path $backup | Out-Null
foreach($row in $rows){
    if(Test-Path -LiteralPath $row.Target){
        $target=Safe-Child $backup $row.Relative;Ensure-Parent $target;Copy-Item -LiteralPath $row.Target -Destination $target
        if((Get-FileHash -LiteralPath $target).Hash -ne (Get-FileHash -LiteralPath $row.Target).Hash){throw 'Backup mismatch; staging refused.'}
    }
}
$now=Get-Partition -DriveLetter $usb.Volume.DriveLetter
if($now.DiskNumber -ne $usb.Disk.Number -or $now.Offset -ne $usb.Partition.Offset -or $now.Size -ne $usb.Partition.Size -or (Get-Disk -Number $now.DiskNumber).UniqueId -ne $usb.Disk.UniqueId){throw 'USB identity changed.'}
foreach($row in ($rows | Sort-Object @{Expression={if($_.Relative -eq 'EFI/BOOT/BOOTX64.EFI'){1}else{0}}})){
    $target=Safe-Child $usbRoot $row.Relative;Ensure-Parent $target;Copy-Item -LiteralPath $row.Source -Destination $target -Force
    if((Get-FileHash -LiteralPath $target).Hash.ToLowerInvariant() -ne $row.Digest){throw 'Staged file hash differs.'}
}
[IO.DriveInfo]::new($usbRoot).VolumeLabel='RTX3080_10G'
$record=@{Success=$true;Target='2206 RTX3080 10GB';Mode=$Mode;UsbLabel='RTX3080_10G';VerifiedFiles=$rows.Count;EfiSha256=$expected;Backup=$backup;FormatPerformed=$false;BootSettingsChanged=$false;UnlockExecuted=$false}
$record | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $backup 'stage.private.json') -Encoding utf8
Write-Output ('3080 10GB '+$Mode+' read-only package staged; '+$rows.Count+' files verified. Previous USB files backed up under '+$backup)
Write-Output 'Install RTX3080 10GB before the next probe boot. This image only captures diagnostics; it does not unlock a GPU.'
