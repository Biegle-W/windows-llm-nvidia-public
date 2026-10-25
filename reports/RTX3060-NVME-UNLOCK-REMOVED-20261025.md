# RTX 3060 NVMe unlock removed — October 25, 2026

The user requested removing the3060 unlock UEFI from the NVMe and using manual
USB unlocks for that card in the future. The recorded firmware entry and all
project payload files on its dedicated EFI partition have now been removed.
Windows Boot Manager remains first and its entry is unchanged. No reboot or
GPU reset was initiated; the current verified3080Ti session is unaffected.

## What was removed and retained

The remover validated the saved NVMe disk identity and exact dedicated512MiB ESP
GUID, offset, size and type before mounting it temporarily. It matched the
installed3060 paired EFI hash, rejected unrelated EFI paths, then archived and
hash-verified all41 owned payload/log/source files before removing anything.
The exact3060 firmware entry was deleted and the remaining firmware order verified.
Files were deleted individually only after checking their absolute owned paths
and matching archive hashes. Windows EFI files were outside the allowed scope.

The dedicated partition itself remains in place without the unlock payload.
The full partition inventory is unchanged: no partition was deleted, resized or
formatted. Windows' original EFI, MSR, C: and recovery partitions are preserved.
The temporary U: mount was removed. The current Kingston USB was not modified.

The old **Restore RTX3060 Unlock.cmd** was retired from the project root and
preserved as a disabled historical file under
`archives/2026-10-25-3060-nvme-startup/`. The old boot-mode helper now reports the
retirement or refuses restoration before UAC/BCD changes. Installer/updater
guards refuse the removal-marked state. Do not recreate3060 NVMe startup without
a new explicit user request.

## Future 3060 USB use

The original validated manual3060 package remains privately available at
`data/uefi-probe/windows3060-single-child-20261025-v3/manual-unlock-candidate/`.
All23 manifest files were rechecked. Its EFI SHA256 is
`61fa2b71d1332d4d6180610175955d3cad015420c41f393b7abea717507d09e1`.
This is the manual USB image, distinct from the retired automatic NVMe payload.
It still requires the original Gigabyte2503/1458:407b board, its exact evidence
and a manual U after preflight. Never use it for the3080Ti or another3060 board.

When that card is installed again, stage the preserved manual package onto a
FAT32 USB after backing up any colliding USB files and current captures. Verify
the complete manifest and exact card identity. The connected Kingston currently
retains the3080Ti image; it was deliberately left untouched by this removal.

The earlier3080Ti prerequisite evidence was archived and marked stale because
its assertion that the3060 NVMe EFI remained installed is no longer current.
Future manual platform checks accept either a verified preserved installation
or a verified intentional removal, while still requiring Secure Boot off,
FullyDecrypted/BitLocker-off and Windows-first state. No check is skipped merely
because the3060 setup was retired.

## Verification and private archive

Removal policy tests pass20 cases on PowerShell5.1 and7.6. The updated USB/card/
manual-prerequisite policy tests pass41 cases on both versions, including USB-only
legacy state and refusal when neither preservation nor removal was verified.
The legacy boot-mode policy tests pass10 cases; actual restoration of the retired
state refuses before elevation. [Curated removal evidence](verification/rtx3060-nvme-removal-20261025.json).

Private file/BCD/state snapshots remain under ignored
`data/uefi-probe/3060-nvme-removal-20261025-181709-4e8c5f3c98cd45998a3725aa829d0cb5/`.
Historical successful3060 automatic-boot reports remain as history. The separate
Linux AMD build, model profiles, weights, drivers and credentials were not changed.
