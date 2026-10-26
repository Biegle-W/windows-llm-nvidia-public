# Dedicated GPU USB drives — October 25, 2026

Each card now has its own FAT32 USB drive. Identify the physical device by its
name and capacity, then check the volume label. Drive letters are the current
Windows assignments and may change after reconnecting.

| Current drive | Physical device | Capacity | Volume label | Assigned GPU | Current boot payload |
|---|---|---:|---|---|---|
| D: | Kingston DataTraveler 2.0 | 16 GB | `RTX3080_10G` | RTX 3080 10 GB | Read-only ownership probe; unlock still pending |
| E: | Kingston DataTraveler 3.0 | 32 GB | `RTX3060` | RTX 3060 12 GB | Preserved exact-board manual unlock |
| F: | General USB Flash Disk | 4 GB | `RTX3080TI` | RTX 3080 Ti 12 GB | Preserved exact-board manual unlock |

All package files were checked against their source manifests: 12 on D:, 24 on
E: and 24 on F:, including each manifest. Each drive also contains `GPU-USB.txt`
with its assignment and instructions. Overwritten files and old captures were
backed up privately; unrelated files were preserved. The obsolete motherboard
BIOS file on F: was removed after explicit user approval. Nothing was formatted,
no internal ESP or boot entry was changed, and no firmware was executed.

## Current RTX 3080 next boot

Use the **16 GB Kingston DataTraveler 2.0**, labeled **RTX3080_10G**. Restart,
press F8, choose that UEFI USB device, let the read-only ownership probe finish,
then select Windows Boot Manager. No U press is needed. The physical ownership
capture must be reviewed before building its exact-board manual unlock.

The firmware menu may show the USB device name instead of its volume label.
If the menu is ambiguous, disconnect the other two drives before booting. Put
matching physical stickers on the drives to make future card swaps easier.

## RTX 3060 and RTX 3080 Ti

Use only the drive assigned to the original captured matching card. Both saved
unlock images are manual: start from a fresh firmware boot, let preflight run,
and press U once if it passes. Esc cancels. Do not repeat an unlock in the same
firmware session, use another card's image or configure automatic internal startup.
The packages have prior hardware validation; booting from these newly assigned
physical USB drives remains to be checked. This preparation does not unlock the
currently installed 3080 or change the model router's 12 GB admission limits.

Private serial numbers, device identifiers, raw captures and backups stay under
ignored project data and are not included in the public assignment table.
