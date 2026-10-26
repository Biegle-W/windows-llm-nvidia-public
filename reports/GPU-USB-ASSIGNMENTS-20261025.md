# Dedicated GPU USB drives — October 25, 2026

Each card now has its own FAT32 USB drive. Identify the physical device by its
name and capacity, then check the volume label. Drive letters are the current
Windows assignments and may change after reconnecting.

| Current drive | Physical device | Capacity | Volume label | Assigned GPU | Current boot payload |
|---|---|---:|---|---|---|
| D: | Kingston DataTraveler 2.0 | 16 GB | `RTX3080_10G` | RTX 3080 10 GB | Manual v2 verified in RUN04 |
| E: | Kingston DataTraveler 3.0 | 32 GB | `RTX3060` | RTX 3060 12 GB | Preserved exact-board manual unlock |
| F: | General USB Flash Disk | 4 GB | `RTX3080TI` | RTX 3080 Ti 12 GB | Manual v4; exact-pair retry pending |

All package files were checked against their source manifests: 24 on D:, 24 on
E: and 24 on F:, including each manifest. Each drive also contains `GPU-USB.txt`
with its assignment and instructions. Overwritten files and old captures were
backed up privately; unrelated files were preserved. The obsolete motherboard
BIOS file on F: was removed after explicit user approval. Nothing was formatted,
no internal ESP or boot entry was changed, and no firmware was executed.

## RTX 3080 history and future boots

The3080 10GB had a successful manual v2 RUN04 in an earlier boot and is now
removed; the Ti is installed. The16GB drive remains dedicated to the3080. For future fresh
starts, use the **16 GB Kingston DataTraveler2.0 / RTX3080_10G**, F8 and U once
after preflight passes. Future unknown states must still refuse. No automatic
startup is installed. [Verified result and limits](RTX3080-10GB-WINDOWS-UNLOCK-RESULT-20261025.md).

The firmware menu may show the USB device name instead of its volume label.
If the menu is ambiguous, disconnect the other two drives before booting. Put
matching physical stickers on the drives to make future card swaps easier.

## RTX 3060 and RTX 3080 Ti

**Current Ti:** its dedicated-USB RUN00 refused untouched; corrected v4 is now
staged on4GB General USB/RTX3080TI. [Current retry instructions](RTX3080TI-DEDICATED-USB-REFUSAL-20261025.md).

Use only the drive assigned to the original captured matching card. Both saved
unlock images are manual: start from a fresh firmware boot, let preflight run,
and press U once if it passes. Esc cancels. Do not repeat an unlock in the same
firmware session, use another card's image or configure automatic internal startup.
The original images have prior hardware validation. The new Ti v4 is physically
untested; its dedicated USB already booted successfully into a safe refusal.
This preparation does not unlock the
currently installed Ti or change the model router's 12 GB admission limits.

Private serial numbers, device identifiers, raw captures and backups stay under
ignored project data and are not included in the public assignment table.
