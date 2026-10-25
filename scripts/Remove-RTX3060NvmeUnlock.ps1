# Remove only the recorded 3060 dedicated-ESP payload and firmware entry. Never resize/delete partitions.
[CmdletBinding()]
param([ValidateSet('Remove','SelfTest')][string]$Mode='Remove',[switch]$Elevate)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$stateRoot=Join-Path $root 'data\uefi-probe\internal-startup'
$statePath=Join-Path $stateRoot 'installed-state.private.json'
$resultPath=Join-Path $stateRoot 'nvme-removal-result.private.json'
function Assert-Partition($State,$Disk,$Partition) {
    if($Disk.Number -ne $State.DiskNumber -or $Disk.UniqueId -ne $State.DiskUniqueId -or $Disk.BusType -ne 'NVMe' -or
       $Partition.DiskNumber -ne $State.DiskNumber -or $Partition.Guid -ne $State.PartitionGuid -or
       $Partition.Size -ne 536870912 -or $Partition.Offset -ne $State.NewOffset -or
       $Partition.GptType -ne '{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}') {throw 'The dedicated 3060 ESP identity/extent differs.'}
}
function Owned-Path([string]$Relative) {
    if(-not $Relative -or [IO.Path]::IsPathRooted($Relative) -or $Relative -match '[:\r\n]' -or ($Relative -split '[\\/]') -contains '..'){throw 'Unsafe removal path.'}
    $normalized=$Relative.Replace('/','\')
    if($normalized -match '^EFI\\LLMUnlock\\Auto3060(?:\.previous|\.next)?\.efi$' -or
       $normalized -match '^(AUTOMATIC-SOURCE|LOCAL-PORT|LICENSES|RTX-UNLOCK)\\.+' -or
       $normalized -in @('BUILD-HELPERS.zip','BUILD-INFO.private.json','LICENSE','SOURCE.tar.gz','START-HERE.md','THIRD_PARTY_NOTICES.md','SHA256SUMS.txt')){return $normalized}
    throw 'Unrecognized content on dedicated ESP; removal refused.'
}
function Safe-Target([string]$Base,[string]$Relative) {
    $relative=Owned-Path $Relative
    $prefix=[IO.Path]::GetFullPath($Base).TrimEnd([char]92)+'\'
    $target=[IO.Path]::GetFullPath((Join-Path $prefix $relative))
    if(-not $target.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Removal target escapes its owned root.'}
    return $target
}
function Bcd([string[]]$Arguments) {
    $text=(& "$env:SystemRoot\System32\bcdedit.exe" @Arguments 2>&1 | Out-String)
    if($LASTEXITCODE -ne 0){throw ('BCDEdit failed: '+$text)}
    return $text
}
function Read-Order([string]$Text) {
    $m=[regex]::Match($Text,'(?m)^displayorder\s+([^\r\n]+)(?:\r?\n[ \t]+\{[^\r\n]+)*')
    $ids=@([regex]::Matches($m.Value,'\{[^}]+\}') | ForEach-Object Value)
    if(-not $m.Success -or $ids.Count -lt 1 -or $ids[0] -ne '{bootmgr}' -or @($ids | Select-Object -Unique).Count -ne $ids.Count){throw 'Windows-first firmware boot order differs.'}
    return $ids
}
function Assert-Entry([string]$Id,[string]$Text) {
    if($Id -notmatch '^\{[0-9a-fA-F-]{36}\}$' -or $Text -notmatch 'RTX 3060 Automatic Unlock' -or $Text -notmatch [regex]::Escape('\EFI\LLMUnlock\Auto3060.efi')){throw 'Recorded 3060 firmware entry ownership differs.'}
}
if($Mode -eq 'SelfTest') {
    $state=[pscustomobject]@{DiskNumber=0;DiskUniqueId='fixture';PartitionGuid='{11111111-1111-4111-8111-111111111111}';NewOffset=1000000}
    $disk=[pscustomobject]@{Number=0;UniqueId='fixture';BusType='NVMe'}
    $part=[pscustomobject]@{DiskNumber=0;Guid=$state.PartitionGuid;Size=536870912;Offset=1000000;GptType='{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}'}
    Assert-Partition $state $disk $part
    foreach($field in @('Size','Offset','Guid','GptType')){$bad=$part.PSObject.Copy();$bad.$field=if($field -in @('Size','Offset')){1}else{'invalid'};$refused=$false;try{Assert-Partition $state $disk $bad}catch{$refused=$true};if(-not $refused){throw 'Wrong ESP accepted.'}}
    foreach($path in @('EFI/LLMUnlock/Auto3060.efi','RTX-UNLOCK/RUN0004/GOP.TXT','AUTOMATIC-SOURCE/src/unlock/app.c','SHA256SUMS.txt')){$null=Owned-Path $path}
    foreach($path in @('EFI/Microsoft/Boot/bootmgfw.efi','EFI/BOOT/BOOTX64.EFI','../Windows/file','C:\Windows\file','/EFI/file','RTX-UNLOCK/../../file','unrelated.txt')){$refused=$false;try{$null=Owned-Path $path}catch{$refused=$true};if(-not $refused){throw 'Unrelated/escaping removal path accepted.'}}
    $id='{22222222-2222-4222-8222-222222222222}'
    Assert-Entry $id 'RTX 3060 Automatic Unlock path \EFI\LLMUnlock\Auto3060.efi'
    $refused=$false;try{Assert-Entry '{bootmgr}' 'RTX 3060 Automatic Unlock path \EFI\LLMUnlock\Auto3060.efi'}catch{$refused=$true};if(-not $refused){throw 'Windows entry accepted for removal.'}
    $order=@(Read-Order "displayorder            {bootmgr}`r`n                        $id`r`ntimeout 1")
    if($order.Count -ne 2){throw 'Boot-order parser failed.'}
    $refused=$false;try{$null=Read-Order "displayorder $id`r`n             {bootmgr}"}catch{$refused=$true};if(-not $refused){throw 'Non-Windows-first order accepted.'}
    'PASS 20 dedicated-ESP removal policy checks; no filesystem or boot mutation.'
    return
}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if(-not ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    if(-not $Elevate){throw 'Administrator rights required. Use -Elevate for the Windows UAC prompt.'}
    $process=Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$PSCommandPath+'"'),'-Mode','Remove') -Verb RunAs -WindowStyle Hidden -PassThru -Wait
    if(Test-Path -LiteralPath $resultPath){Get-Content -LiteralPath $resultPath -Raw}
    exit $process.ExitCode
}
$answer=[ordered]@{Success=$false;EntryRemoved=$false;PayloadRemoved=$false;PartitionDeleted=$false;PartitionsResized=$false;UsbChanged=$false;RebootInitiated=$false;Error=$null}
$mounted=$false
try {
    $s=Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    if($s.NvmeUnlockRemoved){throw 'This NVMe installation is already retired; inspect the recorded removal result.'}
    $disk=Get-Disk -Number $s.DiskNumber
    $parts=@(Get-Partition -DiskNumber $s.DiskNumber | Where-Object Guid -eq $s.PartitionGuid)
    if($parts.Count -ne 1){throw 'Dedicated ESP is absent or ambiguous.'};$part=$parts[0]
    Assert-Partition $s $disk $part
    $partitionsBefore=Get-Partition -DiskNumber $s.DiskNumber | Select-Object Guid,GptType,Offset,Size | Sort-Object Guid | ConvertTo-Json -Compress
    $windowsBefore=Bcd @('/enum','{bootmgr}')
    $firmwareBefore=Bcd @('/enum','{fwbootmgr}')
    if($firmwareBefore -match '(?m)^bootsequence\s+'){throw 'A one-time firmware boot is pending.'}
    $order=@(Read-Order $firmwareBefore)
    $entry=Bcd @('/enum',$s.EntryId);Assert-Entry $s.EntryId $entry
    if($order -notcontains $s.EntryId){throw 'Recorded entry is absent from firmware order.'}
    if(Test-Path 'U:\'){throw 'U: is occupied.'}
    $backup=Join-Path $root ('data\uefi-probe\3060-nvme-removal-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $backup | Out-Null
    Copy-Item -LiteralPath $statePath -Destination (Join-Path $backup 'installed-state.private.json')
    $firmwareBefore | Set-Content -LiteralPath (Join-Path $backup 'fwbootmgr-before.private.txt') -Encoding utf8
    $entry | Set-Content -LiteralPath (Join-Path $backup '3060-entry-before.private.txt') -Encoding utf8
    $null=Bcd @('/export',(Join-Path $backup 'system-bcd-backup.private'))
    Add-PartitionAccessPath -DiskNumber $s.DiskNumber -PartitionNumber $part.PartitionNumber -AccessPath 'U:\';$mounted=$true
    if((Get-Partition -DriveLetter U).Guid -ne $s.PartitionGuid -or [IO.DriveInfo]::new('U:\').DriveFormat -ne 'FAT32'){throw 'Dedicated ESP mount differs.'}
    if((Get-FileHash -LiteralPath 'U:\EFI\LLMUnlock\Auto3060.efi').Hash.ToLowerInvariant() -ne 'a57b0621ea87dd53c0a50aceca8de2467f2f4c3da1580f1fee230af6b8844394'){throw 'Installed 3060 payload is not the recorded verified image.'}
    $files=@(Get-ChildItem -LiteralPath 'U:\' -Recurse -File -Force | Where-Object {$_.FullName -notlike 'U:\System Volume Information\*'})
    $rows=@(foreach($file in $files){
        $relative=$file.FullName.Substring(3);$source=Safe-Target 'U:\' $relative
        if($file.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Unexpected ESP reparse point.'}
        [pscustomobject]@{Relative=$relative;Source=$source;Digest=(Get-FileHash -LiteralPath $source).Hash}
    })
    $ownedDirectories=@(Get-ChildItem -LiteralPath 'U:\' -Recurse -Directory -Force | Where-Object {$_.FullName -ne 'U:\System Volume Information' -and $_.FullName -notlike 'U:\System Volume Information\*'})
    foreach($directory in $ownedDirectories){
        if($directory.FullName -notmatch '^U:\\(EFI(?:\\LLMUnlock)?|AUTOMATIC-SOURCE(?:\\.*)?|LOCAL-PORT(?:\\.*)?|LICENSES(?:\\.*)?|RTX-UNLOCK(?:\\.*)?)$' -or ($directory.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Unknown directory on dedicated ESP; removal refused before boot changes.'}
    }
    # Validate every source and back up/hash-check the full owned payload before any removal.
    foreach($row in $rows){
        $target=Safe-Target (Join-Path $backup 'files') $row.Relative
        $parent=Split-Path -Parent $target
        if(-not (Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Path $parent -Force | Out-Null}
        Copy-Item -LiteralPath $row.Source -Destination $target
        if((Get-FileHash -LiteralPath $target).Hash -ne $row.Digest){throw 'Archive verification failed; removal refused.'}
    }
    $rows | Select-Object Relative,Digest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $backup 'files-manifest.private.json') -Encoding utf8
    $answer.Archive=$backup;$answer.ArchivedFilesVerified=$rows.Count
    $newOrder=@($order | Where-Object {$_ -ne $s.EntryId})
    $null=Bcd @('/delete',$s.EntryId)
    $answer.EntryRemoved=$true
    $null=Bcd (@('/set','{fwbootmgr}','displayorder')+$newOrder)
    if(((Read-Order (Bcd @('/enum','{fwbootmgr}')))-join ',') -ne ($newOrder-join ',')){throw 'Post-removal boot order differs.'}
    # Recheck mount identity and absolute targets immediately before deleting individual owned files.
    Assert-Partition $s (Get-Disk -Number $s.DiskNumber) (Get-Partition -DriveLetter U)
    foreach($row in $rows){
        $target=Safe-Target 'U:\' $row.Relative
        if((Get-FileHash -LiteralPath $target).Hash -ne $row.Digest){throw 'ESP file changed after archive; stop removal.'}
        Remove-Item -LiteralPath $target -Force
    }
    $directories=@(Get-ChildItem -LiteralPath 'U:\' -Recurse -Directory -Force | Where-Object {$_.FullName -ne 'U:\System Volume Information' -and $_.FullName -notlike 'U:\System Volume Information\*'} | Sort-Object @{Expression={$_.FullName.Length};Descending=$true})
    foreach($directory in $directories){
        $path=[IO.Path]::GetFullPath($directory.FullName)
        if(-not $path.StartsWith('U:\',[StringComparison]::OrdinalIgnoreCase) -or $path -notmatch '^U:\\(EFI(?:\\LLMUnlock)?|AUTOMATIC-SOURCE(?:\\.*)?|LOCAL-PORT(?:\\.*)?|LICENSES(?:\\.*)?|RTX-UNLOCK(?:\\.*)?)$'){throw 'Unknown directory is retained for review.'}
        if(-not @(Get-ChildItem -LiteralPath $path -Force).Count){Remove-Item -LiteralPath $path -Force}
    }
    $remaining=@(Get-ChildItem -LiteralPath 'U:\' -Recurse -File -Force | Where-Object {$_.FullName -notlike 'U:\System Volume Information\*'})
    if($remaining.Count -ne 0){throw 'Payload files remain.'}
    $answer.PayloadRemoved=$true
    Remove-PartitionAccessPath -DiskNumber $s.DiskNumber -PartitionNumber $part.PartitionNumber -AccessPath 'U:\';$mounted=$false
    if((Bcd @('/enum','{bootmgr}')) -cne $windowsBefore){throw 'Windows boot entry changed unexpectedly.'}
    $firmwareAfter=Bcd @('/enum','firmware')
    if($firmwareAfter -match [regex]::Escape($s.EntryId) -or $firmwareAfter -match 'RTX 3060 Automatic Unlock' -or $firmwareAfter -match [regex]::Escape('Auto3060.efi')){throw 'A 3060 firmware reference remains.'}
    $partitionsAfter=Get-Partition -DiskNumber $s.DiskNumber | Select-Object Guid,GptType,Offset,Size | Sort-Object Guid | ConvertTo-Json -Compress
    if($partitionsAfter -cne $partitionsBefore){throw 'Partition inventory changed.'}
    $s | Add-Member -NotePropertyName RemovedEntryId -NotePropertyValue $s.EntryId -Force
    $s | Add-Member -NotePropertyName NvmeUnlockRemoved -NotePropertyValue $true -Force
    $s | Add-Member -NotePropertyName InternalUnlockInstalled -NotePropertyValue $false -Force
    $s | Add-Member -NotePropertyName RemovalArchive -NotePropertyValue $backup -Force
    $s | Add-Member -NotePropertyName HistoricalAutoInternalBootVerified -NotePropertyValue $s.AutoInternalBootVerified -Force
    $s.AutoInternalBootVerified=$false
    $s.Status='removed-user-prefers-3060-usb-only';$s.EntryId=$null;$s.BootUnlockEnabled=$false;$s.NextBootVerificationPending=$false
    $temporary=$statePath+'.removal.pending'
    [IO.File]::WriteAllText($temporary,($s | ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
    [IO.File]::Replace($temporary,$statePath,[System.Management.Automation.Language.NullString]::Value)
    $answer.WindowsEntryPreserved=$true;$answer.WindowsFirst=$true;$answer.PartitionInventoryPreserved=$true;$answer.DedicatedPartitionRetained=$true
    $answer.Success=$true
} catch {$answer.Error=$_.Exception.Message}
finally {
    if($mounted){try{Remove-PartitionAccessPath -DiskNumber $s.DiskNumber -PartitionNumber $part.PartitionNumber -AccessPath 'U:\'}catch{$answer.Error=$_.Exception.Message;$answer.Success=$false}}
    [IO.File]::WriteAllText($resultPath,($answer | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
}
if(-not $answer.Success){throw $answer.Error}
'3060 NVMe boot entry and payload removed; Windows and partitions preserved. USB was not changed.'
