# Dedicated GPU USB drives — October 25, 2026

Each card has its own FAT32 USB drive; a fourth drive now prepares the planned
Ti/3080 pair. Identify the physical device by name, capacity and volume label.
Only the new SanDisk is currently connected, as D:. Older letters below are
historical and can be reassigned after reconnecting.

| Last recorded drive | Physical device | Capacity | Volume label | Assigned GPU | Current boot payload |
|---|---|---:|---|---|---|
| Disconnected; formerly D: | Kingston DataTraveler 2.0 | 16 GB | `RTX3080_10G` | RTX 3080 10 GB | Manual v2 verified in RUN04 |
| Disconnected; formerly E: | Kingston DataTraveler 3.0 | 32 GB | `RTX3060` | RTX 3060 12 GB | Preserved exact-board manual unlock |
| Disconnected; formerly F: | General USB Flash Disk | 4 GB | `RTX3080TI` | RTX 3080 Ti 12 GB | Manual v4 verified in dedicated RUN01 |
| D: now | SanDisk Cruzer Force | 8 GB | `RTX3080PAIR` | Ti + 3080 pair preparation | Read-only pair capture; no unlock |

The new SanDisk was explicitly authorized for erasure, formatted FAT32 and staged
with 22 verified package files. Boot it only after installing both captured cards,
then collect its logs in Windows. It does not unlock either card and does not
replace the three single-card packages. [Pair procedure](RTX3080-DUAL-WINDOWS-PREPARATION-20261025.md).

At the original three-drive assignment, all package files were checked against
their source manifests: 24 per drive, including each manifest. Each original drive also contains `GPU-USB.txt`
with its assignment and instructions. Overwritten files and old captures were
backed up privately; unrelated files were preserved. The obsolete motherboard
BIOS file on F: was removed after explicit user approval. That original assignment
formatted nothing. The later SanDisk format is recorded above; neither operation
changed an internal ESP or boot entry or executed firmware.

## RTX 3080 history and future single-card boots

The3080 10GB had a successful manual v2 RUN04 in an earlier boot and is now
removed; the Ti is installed. The16GB drive remains dedicated to the3080. For future fresh
starts, use the **16 GB Kingston DataTraveler2.0 / RTX3080_10G**, F8 and U once
after preflight passes. Future unknown states must still refuse. No automatic
startup is installed. [Verified result and limits](RTX3080-10GB-WINDOWS-UNLOCK-RESULT-20261025.md).

The firmware menu may show the USB device name instead of its volume label.
If the menu is ambiguous, disconnect the other two drives before booting. Put
matching physical stickers on the drives to make future card swaps easier.

## RTX 3060 and RTX 3080 Ti

**Current Ti session is unlocked:** dedicated4GB USB v4 RUN01 succeeded with64GB
system RAM. Do not repeat in this firmware session. Future fresh starts use this
same4GB General USB/RTX3080TI. [Verified result](RTX3080TI-V4-64GB-UNLOCK-RESULT-20261025.md).

Use only the drive assigned to the original captured matching card. Both saved
unlock images are manual: start from a fresh firmware boot, let preflight run,
and press U once if it passes. Esc cancels. Do not repeat an unlock in the same
firmware session, use another card's image or configure automatic internal startup.
The original images have prior hardware validation. The Ti v4 now has one verified
physical success on its dedicated USB.
This preparation does not unlock the
currently installed Ti or change the model router's 12 GB admission limits.

Private serial numbers, device identifiers, raw captures and backups stay under
ignored project data and are not included in the public assignment table.
