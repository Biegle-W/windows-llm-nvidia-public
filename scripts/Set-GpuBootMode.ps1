# Preserve the verified 3060 EFI while using ordinary Windows startup for a GPU swap.
[CmdletBinding()]
param(
    [ValidateSet('Status','Stock','3060','SelfTest')][string]$Mode='Status',
    [switch]$Elevate
)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$stateRoot=Join-Path $root 'data\uefi-probe\internal-startup'
$statePath=Join-Path $stateRoot 'installed-state.private.json'
$resultPath=Join-Path $stateRoot 'gpu-swap-boot-mode.private.json'
function Read-Bcd([string]$Id) {
    $text=(& "$env:SystemRoot\System32\bcdedit.exe" /enum $Id 2>&1 | Out-String)
    if($LASTEXITCODE -ne 0){throw 'Boot entry query failed.'}
    return $text
}
function Read-Order([string]$Text) {
    $match=[regex]::Match($Text,'(?m)^displayorder\s+([^\r\n]+)(?:\r?\n[ \t]+\{[^\r\n]+)*')
    if(-not $match.Success){throw 'Firmware boot order is missing.'}
    $ids=@([regex]::Matches($match.Value,'\{[^}]+\}') | ForEach-Object Value)
    if($ids -notcontains '{bootmgr}' -or @($ids | Select-Object -Unique).Count -ne $ids.Count){throw 'Unexpected boot order.'}
    return $ids
}
function Planned-Order([string[]]$Before,[string]$Entry,[string]$Choice) {
    if($Entry -notmatch '^\{[0-9a-fA-F-]{36}\}$' -or $Before -notcontains $Entry -or $Before -notcontains '{bootmgr}' -or @($Before | Select-Object -Unique).Count -ne $Before.Count){throw 'Saved unlock entry is missing or ambiguous.'}
    if($Choice -eq 'Stock'){return @('{bootmgr}')+@($Before | Where-Object {$_ -ne '{bootmgr}'})}
    if($Choice -eq '3060'){return @($Entry,'{bootmgr}')+@($Before | Where-Object {$_ -ne '{bootmgr}' -and $_ -ne $Entry})}
    throw 'Unknown boot choice.'
}
function Assert-Original3060($Cards,[string]$Inventory) {
    if(@($Cards).Count -ne 1 -or $Cards[0].Name -ne 'NVIDIA GeForce RTX 3060' -or $Cards[0].PNPDeviceID -notmatch '^PCI\\VEN_10DE&DEV_2503&SUBSYS_407B1458&REV_A1\\'){throw 'Only the original Gigabyte 3060 board may enable this EFI.'}
    $lines=@($Inventory.Trim() -split '\r?\n');if($lines.Count -ne 1){throw 'One physical NVIDIA GPU is required.'}
    $fields=@($lines[0].Split(',') | ForEach-Object {$_.Trim()})
    if($fields.Count -ne 4 -or $fields[0] -ne 'NVIDIA GeForce RTX 3060' -or $fields[1] -notmatch '^(00000000|0000):01:00\.0$' -or $fields[2] -ne '94.06.14.40.b2' -or $fields[3] -ne '12288'){throw 'Original 3060 BDF/VBIOS/VRAM identity differs.'}
}
if($Mode -eq 'SelfTest') {
    $id='{11111111-1111-4111-8111-111111111111}';$other='{22222222-2222-4222-8222-222222222222}'
    if(((Planned-Order @($id,'{bootmgr}',$other) $id Stock)-join ',') -ne (('{bootmgr}',$id,$other)-join ',')){throw 'Stock ordering test failed.'}
    if(((Planned-Order @('{bootmgr}',$id,$other) $id 3060)-join ',') -ne (($id,'{bootmgr}',$other)-join ',')){throw 'Restore ordering test failed.'}
    $card=[pscustomobject]@{Name='NVIDIA GeForce RTX 3060';PNPDeviceID='PCI\VEN_10DE&DEV_2503&SUBSYS_407B1458&REV_A1\fixture'}
    $inventory='NVIDIA GeForce RTX 3060, 00000000:01:00.0, 94.06.14.40.b2, 12288'
    Assert-Original3060 @($card) $inventory
    foreach($bad in @($inventory.Replace('RTX 3060','RTX 3080 Ti'),$inventory.Replace('01:00','02:00'),$inventory.Replace('40.b2','40.b3'),$inventory.Replace('12288','8192'))){$rejected=$false;try{Assert-Original3060 @($card) $bad}catch{$rejected=$true};if(-not $rejected){throw 'Unknown GPU identity accepted.'}}
    $rejected=$false;try{Assert-Original3060 @($card,$card) $inventory}catch{$rejected=$true};if(-not $rejected){throw 'Multiple GPUs accepted.'}
    $bad=[pscustomobject]@{Name=$card.Name;PNPDeviceID=$card.PNPDeviceID.Replace('407B1458','12341458')}
    $rejected=$false;try{Assert-Original3060 @($bad) $inventory}catch{$rejected=$true};if(-not $rejected){throw 'Other board accepted.'}
    $rejected=$false;try{$null=Planned-Order @('{bootmgr}',$other) $id 3060}catch{$rejected=$true};if(-not $rejected){throw 'Missing entry accepted.'}
    'PASS 10 GPU-swap boot policy checks; no boot/GPU mutation'
    return
}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if(-not ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    if(-not $Elevate){throw 'Administrator rights required; use -Elevate to display the UAC prompt.'}
    $shell="$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    $process=Start-Process -FilePath $shell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$PSCommandPath+'"'),'-Mode',$Mode) -Verb RunAs -WindowStyle Hidden -Wait -PassThru
    if(Test-Path -LiteralPath $resultPath){$result=Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json;Write-Output $result.Message}
    exit $process.ExitCode
}
$result=[ordered]@{Success=$false;Mode=$Mode;Error=$null;Message=$null;RebootInitiated=$false;FilesAndPartitionsPreserved=$true}
$changed=$false;$mounted=$false
try {
    $s=Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    $entry=Read-Bcd $s.EntryId
    if($entry -notmatch 'RTX 3060 Automatic Unlock' -or $entry -notmatch [regex]::Escape('\EFI\LLMUnlock\Auto3060.efi')){throw 'Saved boot entry ownership differs.'}
    $firmware=Read-Bcd '{fwbootmgr}';$before=@(Read-Order $firmware)
    $windowsBefore=Read-Bcd '{bootmgr}'
    if($Mode -eq 'Status') {$result.Message='Boot entries inspected; no change.';$result.Order=$before}
    else {
        if($firmware -match '(?m)^bootsequence\s+'){throw 'A one-time firmware boot is scheduled; inspect it before changing order.'}
        if($Mode -eq '3060') {
            $cards=@(Get-CimInstance Win32_VideoController | Where-Object Name -match '^NVIDIA ')
            $inventory=(& nvidia-smi --query-gpu=name,pci.bus_id,vbios_version,memory.total --format=csv,noheader,nounits | Out-String)
            if($LASTEXITCODE -ne 0){throw 'NVIDIA inventory failed.'}
            Assert-Original3060 $cards $inventory
            if(Confirm-SecureBootUEFI){throw 'This unsigned EFI requires Secure Boot off.'}
            if($s.EfiSha256 -ne 'a57b0621ea87dd53c0a50aceca8de2467f2f4c3da1580f1fee230af6b8844394'){throw 'The verified paired 3060 payload is not selected.'}
            $disk=Get-Disk -Number $s.DiskNumber
            if($disk.UniqueId -ne $s.DiskUniqueId){throw 'Disk identity differs.'}
            $parts=@(Get-Partition -DiskNumber $s.DiskNumber | Where-Object Guid -eq $s.PartitionGuid)
            if($parts.Count -ne 1 -or $parts[0].Size -ne 536870912 -or $parts[0].Offset -ne $s.NewOffset -or $parts[0].GptType -ne '{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}'){throw 'Dedicated ESP identity differs.'}
            $part=$parts[0]
            if(Test-Path 'U:\'){throw 'U: is occupied.'}
            Add-PartitionAccessPath -DiskNumber $s.DiskNumber -PartitionNumber $part.PartitionNumber -AccessPath 'U:\';$mounted=$true
            if((Get-Partition -DriveLetter U).Guid -ne $s.PartitionGuid -or (Get-FileHash -LiteralPath 'U:\EFI\LLMUnlock\Auto3060.efi').Hash.ToLowerInvariant() -ne $s.EfiSha256){throw 'Installed 3060 EFI differs.'}
            Remove-PartitionAccessPath -DiskNumber $s.DiskNumber -PartitionNumber $part.PartitionNumber -AccessPath 'U:\';$mounted=$false
        }
        $after=@(Planned-Order $before $s.EntryId $Mode)
        $backup=Join-Path $stateRoot ('gpu-swap-backup-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $backup | Out-Null
        Copy-Item -LiteralPath $statePath -Destination (Join-Path $backup 'installed-state.private.json')
        $firmware | Set-Content -LiteralPath (Join-Path $backup 'fwbootmgr-before.private.txt') -Encoding utf8
        & "$env:SystemRoot\System32\bcdedit.exe" /set '{fwbootmgr}' displayorder @after | Out-Null
        if($LASTEXITCODE -ne 0){throw 'Firmware order change failed.'};$changed=$true
        if(((Read-Order (Read-Bcd '{fwbootmgr}'))-join ',') -ne ($after-join ',') -or (Read-Bcd '{bootmgr}') -cne $windowsBefore){throw 'Boot order/Windows entry verification failed.'}
        $s | Add-Member -NotePropertyName GpuSwapBootMode -NotePropertyValue $Mode -Force
        $s | Add-Member -NotePropertyName BootUnlockEnabled -NotePropertyValue ($Mode -eq '3060') -Force
        $s | Add-Member -NotePropertyName NextBootVerificationPending -NotePropertyValue $true -Force
        $s.Status=if($Mode -eq 'Stock'){'windows-first-for-gpu-swap'}else{'3060-unlock-reenabled-awaiting-boot'}
        $temporary=$statePath+'.swap.pending'
        [IO.File]::WriteAllText($temporary,($s | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
        [IO.File]::Replace($temporary,$statePath,[System.Management.Automation.Language.NullString]::Value)
        $result.Message=if($Mode -eq 'Stock'){'Windows Boot Manager is first for the GPU swap. The verified 3060 EFI and entry are preserved.'}else{'Original 3060 verified; its automatic unlock entry is first. Verify the next boot.'}
        $result.OrderVerified=$true;$result.WindowsEntryPreserved=$true
    }
    $result.Success=$true
} catch {
    $result.Error=$_.Exception.Message;$result.Message=$result.Error
    if($changed){& "$env:SystemRoot\System32\bcdedit.exe" /set '{fwbootmgr}' displayorder @before | Out-Null;$result.OrderRestoreExitCode=$LASTEXITCODE}
} finally {
    if($mounted){try{if((Get-Partition -DriveLetter U).Guid -ne $s.PartitionGuid){throw 'Mount ownership changed.'};Remove-PartitionAccessPath -DiskNumber $s.DiskNumber -PartitionNumber $part.PartitionNumber -AccessPath 'U:\'}catch{$result.Success=$false;$result.Error=$_.Exception.Message}}
    [IO.File]::WriteAllText($resultPath,($result | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
}
if(-not $result.Success){throw $result.Error}
$result.Message
