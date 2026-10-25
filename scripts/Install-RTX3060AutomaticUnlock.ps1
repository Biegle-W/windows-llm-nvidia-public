# GPL-2.0-only. Dedicated-ESP installation for this workstation's tested 3060 port.
# Boot-entry transition follows the reviewed Windows-GPU-UNLOCK approach;
# no Windows bootloader file is replaced and the original entry is retained.
[CmdletBinding()]
param(
    [ValidateSet('Plan','Install','Resume','Disable','SelfTest')][string]$Mode = 'Plan',
    [switch]$AllowResizeCBy512MiB
)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$stateRoot = Join-Path $projectRoot 'data\uefi-probe\internal-startup'
$statePath = Join-Path $stateRoot 'installed-state.private.json'
$entryName = 'RTX 3060 Automatic Unlock'
$entryPath = '\EFI\LLMUnlock\Auto3060.efi'
$espType = '{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}'
$newSize = [int64]536870912
$powerKey = 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Power'

function Save-State($Value) {
    $temporary = $statePath + '.pending'
    [IO.File]::WriteAllText($temporary,($Value | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
    if (Test-Path -LiteralPath $statePath) { [IO.File]::Replace($temporary,$statePath,[System.Management.Automation.Language.NullString]::Value) }
    else { [IO.File]::Move($temporary,$statePath) }
}
function Bcd([string[]]$Arguments) {
    $text = (& "$env:SystemRoot\System32\bcdedit.exe" @Arguments 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0) { throw ('BCDEdit failed: ' + $text) }
    return $text
}
function Boot-Order([string]$Text) {
    $match = [regex]::Match($Text,'(?m)^displayorder\s+([^\r\n]+)(?:\r?\n[ \t]+\{[^\r\n]+)*')
    if (-not $match.Success) { throw 'Cannot read the existing firmware display order.' }
    $ids = @([regex]::Matches($match.Value,'\{[^}]+\}') | ForEach-Object Value)
    if ($ids -notcontains '{bootmgr}' -or @($ids | Select-Object -Unique).Count -ne $ids.Count) { throw 'Invalid firmware boot order.' }
    return $ids
}
function Promotion-Order([string[]]$Before,[string]$NewId) {
    if ($NewId -notmatch '^\{[0-9a-f-]{36}\}$' -or $Before -notcontains '{bootmgr}' -or @($Before | Select-Object -Unique).Count -ne $Before.Count) { throw 'Invalid promotion plan.' }
    return @($NewId,'{bootmgr}') + @($Before | Where-Object { $_ -ne $NewId -and $_ -ne '{bootmgr}' })
}
function Assert-NewPartition($Partition,[int]$DiskNumber,[int64]$Offset,[string[]]$OldGuids) {
    if ($Partition.DiskNumber -ne $DiskNumber -or $Partition.Offset -ne $Offset -or $Partition.Size -ne $newSize -or
        $Partition.GptType -ne $espType -or -not $Partition.Guid -or $OldGuids -contains $Partition.Guid) {
        throw 'New partition identity/extent differs; no format is allowed.'
    }
}
function Manifest-Target([string]$Root,[string]$Relative) {
    if (-not $Relative -or $Relative -match '[:\r\n]' -or [IO.Path]::IsPathRooted($Relative) -or
        ($Relative -split '[\\/]') -contains '..') { throw 'Invalid package path.' }
    $base = [IO.Path]::GetFullPath($Root).TrimEnd([char]92) + '\'
    $target = [IO.Path]::GetFullPath([IO.Path]::Combine($base,$Relative.Replace('/', '\')))
    if (-not $target.StartsWith($base,[StringComparison]::OrdinalIgnoreCase)) { throw 'Package destination escapes its owned root.' }
    return $target
}
function Assert-ShrunkResume($State,$C,$Current,$Original) {
    if ($State.Status -notin @('prepared','c-shrunk','installation-failed-windows-order-restored') -or
        $State.PartitionGuid -or $State.PartitionNumber -or $State.EntryId -or
        $State.COriginalSize-$State.CTargetSize -ne $newSize -or
        $C.Size -ne $State.CTargetSize -or $C.Offset+$C.Size -ne $State.NewOffset -or
        @($Current).Count -ne @($Original).Count) { throw 'Interrupted-install state is not eligible for a shrink-only resume.' }
    foreach ($old in $Original) {
        $now=@($Current | Where-Object PartitionNumber -eq $old.PartitionNumber)
        if ($now.Count -ne 1 -or $now[0].Guid -ne $old.Guid -or $now[0].GptType -ne $old.GptType -or
            $now[0].Offset -ne $old.Offset -or
            ($old.PartitionNumber -eq $C.PartitionNumber -and ($old.Size -ne $State.COriginalSize -or $now[0].Size -ne $State.CTargetSize)) -or
            ($old.PartitionNumber -ne $C.PartitionNumber -and $now[0].Size -ne $old.Size)) { throw 'Original partition differs during resume.' }
    }
    foreach ($part in $Current) {
        if ($part.Offset -lt $State.NewOffset+$newSize -and $part.Offset+$part.Size -gt $State.NewOffset) { throw 'Approved released extent is occupied.' }
    }
}
if ($Mode -eq 'SelfTest') {
    $id = '{11111111-1111-4111-8111-111111111111}'
    $other = '{22222222-2222-4222-8222-222222222222}'
    if (((Promotion-Order @('{bootmgr}',$other) $id) -join ',') -ne (($id,'{bootmgr}',$other) -join ',')) { throw 'Promotion test failed.' }
    if (((Boot-Order "displayorder            {bootmgr}`r`n                        $other`r`ntimeout 1") -join ',') -ne (('{bootmgr}',$other) -join ',')) { throw 'Order parser test failed.' }
    foreach ($bad in @(@('missing'),@('{bootmgr}','{bootmgr}'))) {
        $rejected=$false;try { $null=Promotion-Order $bad $id } catch { $rejected=$true };if (-not $rejected) { throw 'Invalid order accepted.' }
    }
    $part=[pscustomobject]@{DiskNumber=0;Offset=1000000;Size=$newSize;GptType=$espType;Guid=$id}
    Assert-NewPartition $part 0 1000000 @($other)
    foreach ($badOffset in @(0,1000001)) {
        $rejected=$false;try { Assert-NewPartition $part 0 $badOffset @($other) } catch { $rejected=$true };if (-not $rejected) { throw 'Wrong format target accepted.' }
    }
    $rejected=$false;try { Assert-NewPartition $part 0 1000000 @($id) } catch { $rejected=$true };if (-not $rejected) { throw 'Existing partition accepted for formatting.' }
    foreach ($badPath in @('../Windows/file','/EFI/file','C:\Windows\file','EFI/../../file')) {
        $rejected=$false;try { $null=Manifest-Target 'U:\' $badPath } catch { $rejected=$true };if (-not $rejected) { throw 'Unsafe package path accepted.' }
    }
    if ((Manifest-Target 'U:\' 'EFI/LLMUnlock/Auto3060.efi') -ne 'U:\EFI\LLMUnlock\Auto3060.efi') { throw 'Valid path failed.' }
    $savedStatePath=$statePath
    $statePath=Join-Path ([IO.Path]::GetTempPath()) ('rtx3060-state-'+[guid]::NewGuid().ToString('N')+'.json')
    try {
        Save-State @{Status='first'}
        if ((Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json).Status -ne 'first') { throw 'Initial state write failed.' }
        Save-State @{Status='second'}
        if ((Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json).Status -ne 'second') { throw 'Atomic state replacement failed.' }
    } finally {
        foreach ($testFile in @($statePath,($statePath+'.pending'))) { if (Test-Path -LiteralPath $testFile) { Remove-Item -LiteralPath $testFile } }
        $statePath=$savedStatePath
    }
    $originalC=[pscustomobject]@{PartitionNumber=3;Guid=$other;GptType='basic';Offset=1048576;Size=4*$newSize}
    $shrunkC=[pscustomobject]@{PartitionNumber=3;Guid=$other;GptType='basic';Offset=1048576;Size=3*$newSize}
    $resumeState=@{Status='prepared';COriginalSize=4*$newSize;CTargetSize=3*$newSize;NewOffset=1048576+3*$newSize;PartitionGuid=$null;PartitionNumber=$null;EntryId=$null}
    Assert-ShrunkResume $resumeState $shrunkC @($shrunkC) @($originalC)
    foreach ($field in @('PartitionGuid','EntryId')) {
        $badState=$resumeState.Clone();$badState[$field]=$id
        $rejected=$false;try { Assert-ShrunkResume $badState $shrunkC @($shrunkC) @($originalC) } catch { $rejected=$true };if (-not $rejected) { throw 'Unsafe resume accepted.' }
    }
    $rejected=$false;try { Assert-ShrunkResume $resumeState $originalC @($originalC) @($originalC) } catch { $rejected=$true };if (-not $rejected) { throw 'Resume could repeat an uncompleted shrink.' }
    $occupied=[pscustomobject]@{PartitionNumber=5;Guid=$id;GptType='esp';Offset=$resumeState.NewOffset;Size=$newSize}
    $rejected=$false;try { Assert-ShrunkResume $resumeState $shrunkC @($shrunkC,$occupied) @($originalC,$occupied) } catch { $rejected=$true };if (-not $rejected) { throw 'Occupied resume extent accepted.' }
    'PASS 20 installation policy/state/resume checks; no partition or boot mutation'
    return
}
if(Test-Path -LiteralPath $statePath){
    $retirement=Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    if($retirement.NvmeUnlockRemoved){throw '3060 internal startup was removed at the user request. Use manual USB; a new NVMe installation requires a new user request.'}
}
if ($Mode -eq 'Plan') {
    $snapshot=Get-Content -LiteralPath (Join-Path $stateRoot 'platform.private.json') -Raw | ConvertFrom-Json
    [ordered]@{Mode='Plan only';ShrinkCBytes=$newSize;CBefore=$snapshot.cSize;CAfter=$snapshot.cSize-$newSize;ExistingEspFree=$snapshot.espFree;NewPartition='512 MiB FAT32 dedicated GPT ESP on disk 0';WindowsEsp='Preserved';BootOrder='New unlock entry, original Windows Boot Manager, existing other entries';RequiresExplicitResizeSwitch=$true;RebootsAutomatically=$false} | ConvertTo-Json
    return
}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if (-not ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Run this script as administrator.' }
if ($Mode -eq 'Disable') {
    $saved=Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    $entry=Bcd @('/enum',$saved.EntryId)
    if ($entry -notmatch [regex]::Escape($entryName) -or $entry -notmatch [regex]::Escape($entryPath)) { throw 'Saved boot-entry ownership differs.' }
    $before=@(Boot-Order (Bcd @('/enum','{fwbootmgr}')))
    $after=@('{bootmgr}')+@($before | Where-Object { $_ -ne '{bootmgr}' })
    $null=Bcd (@('/set','{fwbootmgr}','displayorder')+$after)
    if (((Boot-Order (Bcd @('/enum','{fwbootmgr}'))) -join ',') -ne ($after -join ',')) { throw 'Windows-first verification failed.' }
    $saved.Status='disabled-windows-first';Save-State $saved
    'Windows Boot Manager is first. The dedicated partition and unlock files are retained.'
    return
}
if (-not $AllowResizeCBy512MiB) { throw 'Installation requires explicit -AllowResizeCBy512MiB authorization.' }
$isResume=($Mode -eq 'Resume')
if (-not $isResume -and (Test-Path -LiteralPath $statePath)) { throw 'Installation state already exists; inspect it instead of repeating partition creation.' }
if ($isResume) { $state=Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json -AsHashtable }
if (Test-Path 'U:\') { throw 'U: is occupied; no changes made.' }
$expected=Get-Content -LiteralPath (Join-Path $stateRoot 'platform.private.json') -Raw | ConvertFrom-Json
$c=Get-Partition -DriveLetter C
$disk=Get-Disk -Number $c.DiskNumber
$expectedCSize=if ($isResume) { $state.CTargetSize } else { $expected.cSize }
if ($c.DiskNumber -ne 0 -or $disk.UniqueId -ne $expected.disk.UniqueId -or $disk.BusType -ne 'NVMe' -or $disk.PartitionStyle -ne 'GPT' -or $c.Size -ne $expectedCSize) { throw 'System-disk inventory changed; no changes made.' }
$security=Get-BitLockerVolume -MountPoint C:\
if ((Confirm-SecureBootUEFI) -or $security.VolumeStatus -ne 'FullyDecrypted' -or $security.ProtectionStatus -ne 'Off') { throw 'Unexpected Secure Boot/encryption state; no changes made.' }
$targetSize=if ($isResume) { [int64]$state.CTargetSize } else { [int64]$c.Size-$newSize }
if (-not $isResume) {
    $supported=Get-PartitionSupportedSize -DriveLetter C
    if ($targetSize -lt $supported.SizeMin) { throw 'The 512 MiB shrink is not supported.' }
}
$backup=Join-Path $stateRoot 'installation-backup'
$oldPartitions=if ($isResume) { @(Get-Content -LiteralPath (Join-Path $backup 'partitions-before.private.json') -Raw | ConvertFrom-Json) } else { @(Get-Partition -DiskNumber 0) }
$oldGuids=@($oldPartitions.Guid)
$newOffset=[int64]$c.Offset+$targetSize
$fwBefore=Bcd @('/enum','{fwbootmgr}')
if ($fwBefore -match '(?m)^bootsequence\s+') { throw 'A one-time firmware boot is already scheduled; preserve it.' }
$orderBefore=@(Boot-Order $fwBefore)
$bootmgrBefore=Bcd @('/enum','{bootmgr}')
if ($isResume) {
    if ($state.DiskUniqueId -ne $disk.UniqueId -or $state.COriginalSize -ne $expected.cSize -or
        ($orderBefore -join ',') -ne ($state.BootOrderBefore -join ',')) { throw 'Original disk/boot state differs during resume.' }
    $savedWindows=Get-Content -LiteralPath (Join-Path $backup 'bootmgr-before.private.txt') -Raw
    if ($bootmgrBefore.TrimEnd() -cne $savedWindows.TrimEnd()) { throw 'Original Windows entry changed during resume.' }
    Assert-ShrunkResume $state $c @(Get-Partition -DiskNumber 0) $oldPartitions
    $hiberBefore=$state.HiberbootBefore
} else {
    if (Test-Path -LiteralPath $backup) { throw 'Installation backup already exists.' }
    New-Item -ItemType Directory -Path $backup | Out-Null
    $fwBefore | Set-Content -LiteralPath (Join-Path $backup 'fwbootmgr-before.private.txt') -Encoding utf8
    $bootmgrBefore | Set-Content -LiteralPath (Join-Path $backup 'bootmgr-before.private.txt') -Encoding utf8
    Bcd @('/enum','firmware','/v') | Set-Content -LiteralPath (Join-Path $backup 'firmware-before.private.txt') -Encoding utf8
    $null=Bcd @('/export',(Join-Path $backup 'BCD-before.private'))
    $oldPartitions | Select-Object DiskNumber,PartitionNumber,Guid,GptType,Offset,Size | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backup 'partitions-before.private.json') -Encoding utf8
    $hiberBefore=Get-ItemPropertyValue -LiteralPath $powerKey -Name HiberbootEnabled -ErrorAction SilentlyContinue
    $state=[ordered]@{Status='prepared';DiskNumber=0;DiskUniqueId=$disk.UniqueId;COriginalSize=$c.Size;CTargetSize=$targetSize;NewOffset=$newOffset;PartitionBytes=$newSize;PartitionGuid=$null;PartitionNumber=$null;EntryId=$null;BootOrderBefore=$orderBefore;EfiPath=$entryPath;EfiSha256=$null;HiberbootBefore=$hiberBefore;AutoInternalBootVerified=$false}
    Save-State $state
}
$mounted=$false
try {
    if (-not $isResume) { Resize-Partition -DriveLetter C -Size $targetSize }
    $state.Status='c-shrunk';Save-State $state
    $part=New-Partition -DiskNumber 0 -Offset $newOffset -Size $newSize -GptType $espType -DriveLetter U
    Assert-NewPartition $part 0 $newOffset $oldGuids
    $state.PartitionGuid=[string]$part.Guid;$state.PartitionNumber=$part.PartitionNumber;$state.Status='partition-created';Save-State $state
    $null=Format-Volume -Partition $part -FileSystem FAT32 -NewFileSystemLabel 'LLM_UNLOCK' -AllocationUnitSize 4096 -Force -Confirm:$false
    $mounted=$true
    if ((Get-Partition -DriveLetter U).Guid -ne $part.Guid -or [IO.DriveInfo]::new('U:\').DriveFormat -ne 'FAT32') { throw 'Dedicated ESP mount/format differs.' }
    $build=Join-Path $stateRoot 'installed-build'
    $python=Join-Path $projectRoot 'runtimes\python\cpython-3.11.15-windows-x86_64-none\python.exe'
    & $python (Join-Path $projectRoot 'scripts\prepare_uefi_3060_automatic.py') --partition-guid ([string]$part.Guid) --output $build | Set-Content -LiteralPath (Join-Path $stateRoot 'installation-build.log') -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw 'Actual-partition automatic EFI build failed.' }
    $info=Get-Content -LiteralPath (Join-Path $build 'BUILD-INFO.private.json') -Raw | ConvertFrom-Json
    if ($info.preview_only -or ([guid]$info.internal_partition_guid -ne [guid]$part.Guid) -or -not $info.host_tests_passed -or -not $info.automatic) { throw 'Actual-partition build contract differs.' }
    $package=Join-Path $build 'package'
    $manifest=Get-Content -LiteralPath (Join-Path $package 'SHA256SUMS.txt')
    foreach ($line in $manifest) {
        if ($line -notmatch '^([0-9a-f]{64})  (.+)$') { throw 'Invalid package manifest.' }
        $digest=$matches[1];$relative=$matches[2]
        $sourceFile=Manifest-Target ($package+'\') $relative
        if ((Get-FileHash -LiteralPath $sourceFile).Hash.ToLowerInvariant() -ne $digest) { throw 'Local package hash differs.' }
        $destination=Manifest-Target 'U:\' $relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath $sourceFile -Destination $destination -ErrorAction Stop
        if ((Get-FileHash -LiteralPath $destination).Hash.ToLowerInvariant() -ne $digest) { throw 'Installed package hash differs.' }
    }
    Copy-Item -LiteralPath (Join-Path $package 'SHA256SUMS.txt') -Destination 'U:\SHA256SUMS.txt'
    $state.EfiSha256=$info.efi.sha256;$state.Status='files-verified';Save-State $state
    if ((Get-FileHash -LiteralPath 'U:\EFI\LLMUnlock\Auto3060.efi').Hash.ToLowerInvariant() -ne $state.EfiSha256) { throw 'Installed EFI hash differs.' }
    if ((Bcd @('/enum','{bootmgr}')) -cne $bootmgrBefore) { throw 'Original Windows boot entry changed unexpectedly.' }
    $created=Bcd @('/copy','{bootmgr}','/d',$entryName)
    $ids=@([regex]::Matches($created,'\{[0-9a-fA-F-]{36}\}') | ForEach-Object Value | Select-Object -Unique)
    if ($ids.Count -ne 1 -or $orderBefore -contains $ids[0]) { throw 'Cannot attribute one newly copied boot entry.' }
    $state.EntryId=$ids[0];$state.Status='entry-created';Save-State $state
    $null=Bcd @('/set',$state.EntryId,'device','partition=U:')
    $null=Bcd @('/set',$state.EntryId,'path',$entryPath)
    $configured=Bcd @('/enum',$state.EntryId)
    if ($configured -notmatch [regex]::Escape($entryName) -or $configured -notmatch [regex]::Escape($entryPath)) { throw 'New firmware entry differs.' }
    $newOrder=@(Promotion-Order $orderBefore $state.EntryId)
    $null=New-ItemProperty -LiteralPath $powerKey -Name HiberbootEnabled -PropertyType DWord -Value 0 -Force
    $null=Bcd (@('/set','{fwbootmgr}','displayorder')+$newOrder)
    if (((Boot-Order (Bcd @('/enum','{fwbootmgr}'))) -join ',') -ne ($newOrder -join ',')) { throw 'New firmware priority differs.' }
    if ((Bcd @('/enum','{bootmgr}')) -cne $bootmgrBefore) { throw 'Original Windows boot entry was altered.' }
    foreach ($oldPart in $oldPartitions) {
        $now=Get-Partition -DiskNumber 0 -PartitionNumber $oldPart.PartitionNumber
        if ($now.Guid -ne $oldPart.Guid -or $now.GptType -ne $oldPart.GptType -or $now.Offset -ne $oldPart.Offset -or ($oldPart.PartitionNumber -ne $c.PartitionNumber -and $now.Size -ne $oldPart.Size)) { throw 'An unrelated partition changed.' }
    }
    $state.Status='automatic-installed-awaiting-boot';Save-State $state
    Bcd @('/enum','firmware','/v') | Set-Content -LiteralPath (Join-Path $stateRoot 'firmware-after.private.txt') -Encoding utf8
    'Automatic internal unlock installed. Original Windows Boot Manager is the second firmware entry. No reboot was initiated.'
} catch {
    $failure=$_
    $recovery=@()
    try { $null=Bcd (@('/set','{fwbootmgr}','displayorder')+$orderBefore) } catch { $recovery += $_.Exception.Message }
    try {
        if (((Boot-Order (Bcd @('/enum','{fwbootmgr}'))) -join ',') -ne ($orderBefore -join ',')) { throw 'Original firmware order was not restored.' }
        if ($null -ne $hiberBefore) { $null=New-ItemProperty -LiteralPath $powerKey -Name HiberbootEnabled -PropertyType DWord -Value $hiberBefore -Force }
    } catch { $recovery += $_.Exception.Message }
    if ($state.EntryId) {
        try {
            $owned=Bcd @('/enum',$state.EntryId)
            if ($owned -notmatch [regex]::Escape($entryName)) { throw 'New entry ownership differs; not deleting it.' }
            $null=Bcd @('/delete',$state.EntryId)
        } catch { $recovery += $_.Exception.Message }
    }
    $state.Status=if ($recovery.Count) { 'installation-failed-recovery-needed' } else { 'installation-failed-windows-order-restored' }
    $state.Failure=$failure.Exception.Message;$state.RecoveryErrors=$recovery
    Save-State $state
    # Do not automatically delete/expand partitions after an interrupted install.
    # Any newly created ESP and the 512 MiB shrink are recorded for review.
    throw $failure
} finally {
    if ($mounted) {
        try { Remove-PartitionAccessPath -DiskNumber 0 -PartitionNumber $state.PartitionNumber -AccessPath 'U:\' -ErrorAction Stop }
        catch { & mountvol.exe U: /D | Out-Null }
    }
}
