# RTX 3060 automatic internal boot — October 25, 2026

**Later repeat-boot finding:** RUN0003 returned to the original nonzero startup
pair and the zero-only profile refused. Windows is stock again. A
[two-pair correction](RTX3060-AUTOMATIC-PAIRED-STARTUP-20261025.md) is now installed,
with physical verification pending. The earlier RUN0001 success remains valid
for that boot and does not establish repeat reliability.

**Follow-up: corrected RUN0001 automatically unlocked the GPU and booted Windows.**
FP16/BF16 are 50.534/50.620TFLOPS; logs record safe one-FLR execution and display
restoration. [Physical verification and limits](RTX3060-AUTOMATIC-UNLOCK-SUCCESS-20261025.md).
The preparation/pending-test statements below describe the earlier installation
stage; they are preserved as history, not the latest status.

The automatic EFI build and installer policy tests pass. Installation uses a
512MiB shrink of C: to create a dedicated FAT32 EFI system partition. The
[current installation/verification status](verification/rtx3060-automatic-internal-boot-20261025.json)
is recorded separately; preparing this package alone does not change partitions.
The existing100MiB system ESP has61.1MiB free, less than the approximately81MiB
firmware payload, so the package does not fit there.

The base [manual hardware trial succeeded](RTX3060-WINDOWS-UNLOCK-RESULT-20261025.md),
with about89% higher FP16/BF16 Tensor GEMM throughput. Automatic internal boot is
a separate integration step and needs a subsequent physical boot check.

## Corrected startup profile installed — next boot pending

The [zero-startup correction](RTX3060-AUTOMATIC-ZERO-STARTUP-FIX-20261025.md) is now
installed with 28 verified files. It changes only the two fixed initial selector
constants to the observed zero/zero pair and preserves all other checks. The
corrected build still needs a physical boot and compute verification. The first
boot refusal below belongs to the superseded original automatic EFI.

## First physical boot result: unlock refused

The internal EFI executed RUN0000 but stopped at unlock-preflight on a mismatch
between the saved initial SS0/SS1 pair and this boot's zero/zero state. No unlock
transaction or FLR ran. The current same-executable FP16/BF16 results are stock-like,
26.786/26.806TFLOPS. [First-boot evidence and diagnosis](RTX3060-AUTOMATIC-FIRST-BOOT-20261025.md).
Automatic unlock is not successful yet. No startup checks or boot payload were
changed during verification; the fixed startup profile needs review and retest.
The installation notes below describe the earlier on-disk installation checks.

## Installation status before the first boot

The user approved the partition change and installation. C: was reduced by
exactly 536870912 bytes once. A new 512 MiB FAT32 ESP now holds the actual-partition
automatic EFI and its firmware payload. Independent administrator verification
confirmed all 27 manifest files and EFI SHA256
`7adcaa078172121a39861bf388596f161aec50ec336af57dd9f9821834cb77d8`,
original partition identities/unrelated sizes, unchanged Windows boot entry,
unlock-first/Windows-second priority, Fast Startup/Secure Boot off, and removal
of the temporary U: mount. The new ESP has 446058496 bytes free.

The first installation attempt completed the approved shrink, then stopped on
a state-write bug: PowerShell passed an empty backup filename instead of a .NET
null to `File.Replace`. Its recovery restored the original firmware order. A
separate read-only audit confirmed the exact shrink, original four partitions,
and absence of a new unlock entry. The corrected writer uses `NullString.Value`.
The new guarded `-Mode Resume -AllowResizeCBy512MiB` accepts only this shrink-only
state, checks the original disk/partition inventory and boot entry/order, verifies
the released extent is empty, and does not call Resize-Partition again. It then
completed the approved installation. Both attempts and backups remain private.
The 20 installer checks include first/replacement state writes and unsafe-resume
rejection; the actual-partition EFI build passed 14 automatic/source cases.

**No restart or unlock replay was initiated.** The user must restart without USB,
then the next agent should inspect the new internal `RTX-UNLOCK/RUNnnnn` logs and
verify Windows GPU health and the same compute test. First automatic internal
boot, repeat-boot reliability and update compatibility are not yet validated.
F8 -> Windows Boot Manager bypasses the application if needed. The six-second
Esc cancellation remains in the automatic application. Keep the manual USB intact.

## Installation procedure


`scripts/Install-RTX3060AutomaticUnlock.ps1` defaults to Plan. Install requires
administrator rights and the explicit `-AllowResizeCBy512MiB` switch. The plan is:

1. Preserve and back up the original BCD/firmware order and partition inventory.
   Verify the expected system NVMe/GPT disk, original C: size, supported shrink,
   Secure Boot-off and FullyDecrypted/BitLocker-off state.
2. Shrink C: by exactly536870912 bytes. Create a new512MiB GPT ESP only in that
   released extent. Before formatting, verify its new GUID, disk, offset, size
   and type against the original partition inventory. Format only that new
   partition as FAT32, label `LLM_UNLOCK`.
3. Build an EFI bound to that exact internal partition GUID, stage and hash-check
   its files, then add `RTX 3060 Automatic Unlock` as a separate firmware entry.
   Put it first, retain the original Windows Boot Manager second, and preserve
   other firmware entries. Windows EFI files are not replaced.
4. Keep Fast Startup off. Unmount the temporary U: access path. Do not reboot
   automatically; verify the next full startup separately.

The installer saves private state under ignored
`data/uefi-probe/internal-startup/`. If a later step fails, it attempts to restore
the prior firmware order and remove only its attributed new boot entry. It does
not automatically delete/expand partitions after an interrupted installation;
any newly allocated space is recorded for review.

## Automatic build behavior

`scripts/prepare_uefi_3060_automatic.py` reuses the hardware-tested single-child
display source and unchanged firmware transaction, PCI/PROM/cold-state checks,
driver-method metadata checks, DMA containment, one-FLR rule and recovery gates.
It does not enable upstream production, SSD, quiet-log or auto-profile modes.

The entry waits six seconds after successful preflight. **Esc cancels**; no U
confirmation is required. It logs `AUTO_START`, and successful recovery starts
the original internal Windows Boot Manager in the same boot. Before a hardware
change, F8 -> Windows Boot Manager bypasses this application entirely.

Only the exact configured GPT ESP and matching disk device-path signature are
accepted as the payload source. USB and other partitions are refused. The GPU
profile remains fixed; no user-editable profile file can grant new compatibility.

Logs use `RTX-UNLOCK/RUN0000` through `RUN9999`, preserving prior runs instead of
overwriting the last failure. The old100-run limit is raised to10000. Storage or
logging failures still block execution/continuation rather than bypassing checks;
long-term log housekeeping may eventually be needed.

The automatic gate/internal-source replay has14 host scenarios, including
automatic execution without input, Esc, missing/failed input, Secure Boot,
preflight/log/transaction failure, more than100 existing logs, wrong partition,
USB, wrong disk signature/type and malformed path. The installer has 20 policy/state/resume checks covering firmware ordering,
format-target ownership, copy-path bounds, atomic state updates and shrink-only recovery.
The EFI also passes AMD64/subsystem10/entrypoint/NX/ASLR/relocation checks with
zero imports. These are software checks; the internal startup remains untested
until a new physical boot.

## Recovery and disabling

If the unlock application stops or Windows does not appear within10 minutes,
fully power off. Start with F8 and select **Windows Boot Manager**, bypassing the
unlock. Do not run another unlock in the same firmware session.

After reaching Windows, an administrator can restore Windows-first ordering:

```powershell
pwsh -NoProfile -File scripts/Install-RTX3060AutomaticUnlock.ps1 -Mode Disable
```

This retains the dedicated partition and files for diagnosis. The successful
manual USB package is also retained as a separate recovery/test artifact.

## Windows updates and changing to Linux

| Change | Expected effect and required action |
|---|---|
| Ordinary Windows update | The unlock runs before Windows and its files are on a separate ESP, so the design is independent of ordinary Windows file replacement. This is an inference, not a tested update guarantee. |
| Windows feature update, boot repair or reinstall | Boot configuration can be recreated or reprioritized. If the unlock entry remains but Windows becomes first, review and restore the desired firmware order. Do not overwrite Microsoft's bootloader. |
| NVIDIA driver update | The pre-OS profile/transaction does not patch the installed Windows driver, but preservation of the unlock and compute gains must be rechecked with the new driver.610.88 is the locally measured version. |
| BIOS/UEFI or GPU VBIOS update | Driver metadata, GOP topology, PROM hash or cold state may change. The fixed profile should refuse mismatches; boot Windows directly and recapture/review before rebuilding. |
| Adding/replacing a GPU, motherboard or moving the card | This build is exact3060/BDF/single-NVIDIA-display scoped. Adding the future3080Ti is not covered; a new profile and topology review are required. |
| Secure Boot or device-encryption changes | This unsigned EFI needs Secure Boot off. Reassess boot/recovery implications before enabling encryption or changing those protections. |
| Switching to native Linux | This EFI explicitly chainloads Windows, so selecting it still boots Windows. Booting GRUB/Linux directly bypasses it. Use the native Linux early-initramfs module or separately adapt/test the UEFI handoff to the Linux loader. Do not run two unlock implementations in the same boot. |

Microsoft documents that BCDBoot can recreate BCD entries and place Windows Boot
Manager first in UEFI NVRAM; this is why boot priority needs rechecking after
repair or some upgrades. [Microsoft BCDBoot documentation](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/bcdboot-command-line-options-techref-di?view=windows-11).

The Linux route runs before the unmodified NVIDIA driver binds and is distinct
from a Windows startup task or UEFI application. [Pinned upstream Linux design](https://github.com/Zagitta/gpu-unlock/blob/af28cbbfd3d922a659227ecfb7369adfd924cf03/README.md).
Existing [native Linux preparation](NATIVE-LINUX-NVIDIA-GPU-UNLOCK-20261025.md)
is for this NVIDIA host on a future separate SSD, not the independent AMD Linux
machine. It has not been installed or validated on this PC.
