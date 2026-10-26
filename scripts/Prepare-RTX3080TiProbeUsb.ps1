# Stage verified diagnostics or an explicitly selected manual candidate; never execute firmware or change boot settings.
[CmdletBinding()]
param(
    [ValidateSet('Board','Ownership','Collect','Manual','SelfTest')][string]$Mode='Board',
    [ValidatePattern('^[D-Zd-z]$')][string]$DriveLetter,
    [string]$ManualPackage,
    [string]$ExpectedManualSha256
)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$private=Join-Path $root 'data\uefi-probe\3080ti-usb'
if(-not ('ProbeUsbReparse' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class ProbeUsbReparse {
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
    private struct FindData {
        public uint Attributes;
        public System.Runtime.InteropServices.ComTypes.FILETIME Creation, Access, Write;
        public uint SizeHigh, SizeLow, Tag, Reserved;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=260)] public string Name;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=14)] public string Alternate;
    }
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    private static extern IntPtr FindFirstFileW(string name, out FindData data);
    [DllImport("kernel32.dll", SetLastError=true)]
    private static extern bool FindClose(IntPtr handle);
    public static bool IsCloudTag(uint tag) { return (tag & 0xffff0fffu) == 0x9000001au; }
    public static bool IsCloudPlaceholder(string path) {
        FindData data;
        IntPtr handle=FindFirstFileW(path, out data);
        if(handle == new IntPtr(-1)) throw new Win32Exception();
        try { return IsCloudTag(data.Tag); }
        finally { FindClose(handle); }
    }
}
'@
}
function Safe-Child([string]$Base,[string]$Relative) {
    if(-not $Relative -or [IO.Path]::IsPathRooted($Relative) -or $Relative -match '[:\r\n]' -or ($Relative -split '[\\/]') -contains '..'){throw 'Unsafe package path.'}
    $prefix=[IO.Path]::GetFullPath($Base).TrimEnd([char]92)+'\'
    $path=[IO.Path]::GetFullPath((Join-Path $Base $Relative))
    if(-not $path.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Path escapes its root.'}
    $cursor=$path
    while($cursor.Length -ge $prefix.Length){
        if((Test-Path -LiteralPath $cursor) -and ((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -and -not [ProbeUsbReparse]::IsCloudPlaceholder($cursor)){throw 'Only OneDrive cloud-placeholder reparse tags are permitted; links and other tags are refused.'}
        $cursor=Split-Path -Parent $cursor
    }
    return $path
}
function Assert-Usb($Disk,$Volume) {
    if($Disk.BusType -ne 'USB' -or $Disk.IsBoot -or $Disk.IsSystem -or $Volume.FileSystem -ne 'FAT32' -or $Volume.DriveLetter -notmatch '^[D-Z]$'){throw 'Use a non-system FAT32 USB volume with a drive letter. Nothing was formatted.'}
}
function Ensure-Parent([string]$Path) {
    $parent=Split-Path -Parent $Path
    if(-not (Test-Path -LiteralPath $parent -PathType Container)){New-Item -ItemType Directory -Path $parent -Force | Out-Null}
}
function Assert-ManualInfo($Info,[string]$Expected) {
    if($Expected -notmatch '^[0-9a-f]{64}$' -or $Info.efi.sha256 -cne $Expected -or
       $Info.source_commit -ne '5c076dc4ee7fa369639669fa591ac74d8f6dfcd8' -or
       $Info.mode -ne 'fixed rtx3080ti single-child AMI manual experiment' -or
       $Info.manual_u_required -ne $true -or $Info.automatic_execution -ne $false -or
       $Info.mock_flag_in_efi -ne $false -or $Info.physical_unlock_tested -ne $false -or
       $Info.display_children -ne 1 -or $Info.driver_roles -ne 5 -or $Info.firmware_assets_verified -ne 5){throw 'Manual package policy or reviewed EFI hash differs.'}
}
function Assert-ManualPrerequisites($Info,[datetimeoffset]$Now) {
    # PowerShell7 JSON may materialize ISO dates as DateTime; string conversion
    # would discard its UTC Kind and reinterpret it in the local time zone.
    $stamp=$Info.CheckedAtUtc
    if($stamp -is [datetimeoffset]){$checked=$stamp}
    elseif($stamp -is [datetime]){
        if($stamp.Kind -eq [DateTimeKind]::Unspecified){throw 'Prerequisite timestamp has no time zone.'}
        $checked=[datetimeoffset]::new($stamp)
    }elseif($stamp -is [string] -and $stamp -match '(Z|[+-]\d{2}:\d{2})$'){
        $checked=[datetimeoffset]::Parse($stamp,[Globalization.CultureInfo]::InvariantCulture)
    }else{throw 'Prerequisite timestamp type or time zone is invalid.'}
    $age=($Now-$checked).TotalMinutes
    $legacyVerified=($Info.Verified3060EfiPreserved -eq $true -or $Info.Verified3060NvmeRemoval -eq $true)
    if(-not $Info.Success -or $Info.SecureBootEnabled -ne $false -or $Info.BitlockerVolumeStatus -ne 'FullyDecrypted' -or $Info.BitlockerProtection -ne 'Off' -or -not $Info.WindowsFirst -or -not $legacyVerified -or $age -gt 60 -or $age -lt -5){throw 'Fresh manual-platform prerequisite verification is required.'}
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
    foreach($tag in @('9000001a','9000101a','9000f01a')){if(-not [ProbeUsbReparse]::IsCloudTag([Convert]::ToUInt32($tag,16))){throw 'Cloud placeholder tag refused.'}}
    foreach($tag in @('a000000c','a0000003','80000017')){if([ProbeUsbReparse]::IsCloudTag([Convert]::ToUInt32($tag,16))){throw 'Link or unknown reparse tag accepted.'}}
    Ensure-Parent (Join-Path ([IO.Path]::GetPathRoot($root)) 'probe-usb-parent-policy-fixture.txt')
    $hash='a'*64
    $manual=@{efi=@{sha256=$hash};source_commit='5c076dc4ee7fa369639669fa591ac74d8f6dfcd8';mode='fixed rtx3080ti single-child AMI manual experiment';manual_u_required=$true;automatic_execution=$false;mock_flag_in_efi=$false;physical_unlock_tested=$false;display_children=1;driver_roles=5;firmware_assets_verified=5}
    Assert-ManualInfo $manual $hash
    foreach($field in @('automatic_execution','mock_flag_in_efi','physical_unlock_tested','manual_u_required','display_children','driver_roles','firmware_assets_verified','mode','source_commit')){
        $bad=$manual.Clone();$bad[$field]=if($manual[$field] -is [bool]){-not $manual[$field]}else{'invalid'}
        $rejected=$false;try{Assert-ManualInfo $bad $hash}catch{$rejected=$true};if(-not $rejected){throw 'Unsafe manual package metadata accepted.'}
    }
    foreach($badHash in @(('b'*64),'invalid')){$rejected=$false;try{Assert-ManualInfo $manual $badHash}catch{$rejected=$true};if(-not $rejected){throw 'Unreviewed EFI hash accepted.'}}
    $now=[datetimeoffset]::Parse('2026-10-25T22:00:00Z')
    $prereq=@{Success=$true;SecureBootEnabled=$false;BitlockerVolumeStatus='FullyDecrypted';BitlockerProtection='Off';WindowsFirst=$true;Verified3060EfiPreserved=$true;CheckedAtUtc='2026-10-25T21:59:00Z'}
    Assert-ManualPrerequisites $prereq $now
    $prereq.CheckedAtUtc='2026-10-25T17:59:00-04:00';Assert-ManualPrerequisites $prereq $now
    foreach($time in @('2026-10-25T20:59:00Z','2026-10-25T22:06:00Z')){$bad=$prereq.Clone();$bad.CheckedAtUtc=$time;$rejected=$false;try{Assert-ManualPrerequisites $bad $now}catch{$rejected=$true};if(-not $rejected){throw 'Stale/future prerequisites accepted.'}}
    $bad=$prereq.Clone();$bad.WindowsFirst=$false;$rejected=$false;try{Assert-ManualPrerequisites $bad $now}catch{$rejected=$true};if(-not $rejected){throw 'Changed boot policy accepted.'}
    $usbOnly=$prereq.Clone();$usbOnly.Verified3060EfiPreserved=$false;$usbOnly.Verified3060NvmeRemoval=$true
    Assert-ManualPrerequisites $usbOnly $now
    $usbOnly.Verified3060NvmeRemoval=$false;$rejected=$false;try{Assert-ManualPrerequisites $usbOnly $now}catch{$rejected=$true};if(-not $rejected){throw 'Unverified legacy boot state accepted.'}
    $utc=[datetime]::Parse('2026-10-25T21:59:00Z',[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind)
    foreach($stamp in @($utc,$utc.ToLocalTime(),[datetimeoffset]::Parse('2026-10-25T17:59:00-04:00'))){$typed=$prereq.Clone();$typed.CheckedAtUtc=$stamp;Assert-ManualPrerequisites $typed $now}
    foreach($stamp in @([datetime]::SpecifyKind($utc,[DateTimeKind]::Unspecified),12345,'2026-10-25T21:59:00')){
        $typed=$prereq.Clone();$typed.CheckedAtUtc=$stamp;$rejected=$false;try{Assert-ManualPrerequisites $typed $now}catch{$rejected=$true};if(-not $rejected){throw 'Ambiguous timestamp accepted.'}
    }
    foreach($stamp in @('2026-10-25T21:59:00Z','2026-10-25T17:59:00-04:00')){
        $roundtrip=$prereq.Clone();$roundtrip.CheckedAtUtc=$stamp
        $roundtrip=$roundtrip | ConvertTo-Json | ConvertFrom-Json;Assert-ManualPrerequisites $roundtrip $now
    }
    'PASS 49 USB/card/path/manual-package/prerequisite policy checks; no USB or GPU changes.'
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
                Ensure-Parent $target
                Copy-Item -LiteralPath $sourceFile -Destination $target
                if((Get-FileHash -LiteralPath $sourceFile).Hash -ne (Get-FileHash -LiteralPath $target).Hash){throw 'Capture copy differs.'}
            }
        }
    }
    Write-Output ('Private captures copied and hash checked: '+$out)
    Write-Output 'Old 3060 runs may be included. Audit only a report with actual 2208/10de:1535 identity.'
    return
}
if($Mode -eq 'Manual') {
    if(-not $ManualPackage){throw 'Manual staging requires the reviewed package path and expected EFI SHA256.'}
    $package=[IO.Path]::GetFullPath($ManualPackage)
    $allowed=[IO.Path]::GetFullPath((Join-Path $root 'data')).TrimEnd([char]92)+'\'
    if(-not $package.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Manual package must be below private project data.'}
    $info=Get-Content -LiteralPath (Join-Path $package 'BUILD-INFO.json') -Raw | ConvertFrom-Json
    Assert-ManualInfo $info $ExpectedManualSha256
    $expected=$ExpectedManualSha256
    $prereq=Get-Content -LiteralPath (Join-Path $private 'manual-platform-prerequisites.private.json') -Raw | ConvertFrom-Json
    Assert-ManualPrerequisites $prereq ([datetimeoffset]::UtcNow)
} else {
    $packageName=if($Mode -eq 'Board'){'01-board-probe'}else{'02-ownership-probe'}
    $expected=if($Mode -eq 'Board'){'ae7b5cdd1cc579fc516ebda68c9d438d433697fb78d151304d56a2cbca41785a'}else{'58f4d6beb444d423a8509dd4d1cdbb7a2e10a425e51ae2e65f2cceaa011342b8'}
    $package=Join-Path $root ('data\uefi-probe\rtx3080ti-unlock-setup\'+$packageName)
}
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
        Ensure-Parent $saved
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
foreach($e in ($entries | Sort-Object @{Expression={if($_.Relative -eq 'EFI/BOOT/BOOTX64.EFI'){1}else{0}}})){
    $target=Safe-Child $usbRoot $e.Relative
    Ensure-Parent $target
    Copy-Item -LiteralPath $e.Source -Destination $target -Force
    if((Get-FileHash -LiteralPath $target).Hash.ToLowerInvariant() -ne $e.Digest){throw 'USB staging verification failed. Restore the backed-up files before booting.'}
}
$record.Success=$true;$record.VerifiedFiles=$entries.Count
$record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $recordPath -Encoding utf8
Write-Output ($Mode+' package staged; '+$entries.Count+' file hashes verified. Existing files backed up under '+$backup)
if($Mode -eq 'Manual') {
    Write-Output 'Manual unlock candidate: full shutdown, F8 -> UEFI USB; press U only after preflight. Esc/30 seconds cancels.'
    Write-Output 'After U, allow up to 10 minutes for Windows to start directly; do not rerun the unlock in the same firmware session.'
} else {Write-Output 'Restart manually, press F8 and choose UEFI USB. After capture returns, choose Windows Boot Manager.'}
Write-Output 'Do not select RTX 3060 Automatic Unlock with the 3080 Ti installed.'
