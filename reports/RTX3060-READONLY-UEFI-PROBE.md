# Read-only RTX 3060 UEFI probe

**Current USB mode:** the first register/PROM capture below is complete. The
Kingston fallback now runs the separate read-only **ownership-tree** probe for
[Windows unlock preparation](RTX3060-WINDOWS-UNLOCK-PREPARATION.md). Its new logs
are under `RTX-UNLOCK/RUNnn/GOP.TXT`; the original `RTX30-PROBE/RUN00` remains
preserved and backed up. The following register-probe boot instructions describe
the earlier package, not the current USB fallback.

This package contains the **standalone read-only probe**, not an unlock image.
Target host: Gigabyte RTX 3060 12 GB, PCI `10de:2503`, subsystem `1458:407b`,
ASUS TX GAMING B760M WIFI / BIOS1836 / i5-13600KF. The EFI also inventories other
NVIDIA display devices; detail reads require exactly one unambiguous target.

Deployment update, October25: the user-authorized USB was quick-formatted from
exFAT to FAT32, labelled `UEFI_PROBE`, and all14 probe files restored from a
verified private backup. An independent SHA256 check passed for every restored
file, including the fallback EFI. [Sanitized staging record](verification/rtx3060-uefi-usb-stage-20261025.json).
The first physical UEFI capture now passed: see the results below. Staging did
not change Windows boot entries, the system disk, driver settings or GPU state.

## Physical capture results — October 25, 2026

The USB boot produced `RUN00` with a complete inventory/report, a 1 MiB PROM
window and a 157,696-byte firmware ROM image. It detected exactly one NVIDIA
display device matching `10de:2503` / `1458:407b`; the chip register identifies
GA106. All 16 sampled registers were valid. The strict upstream parser accepted
the report and verified the PROM signature, size and SHA256 against the report.
All four capture files were copied to ignored local storage and independently
hash-checked against the USB. The USB EFI still matches the audited build hash.
Windows recognizes the RTX 3060 with driver610.88 after the reboot.

The report explicitly records no GPU writes, resets or boot-variable changes.
This validates the read-only capture, not an unlock. The generated diagnostic
profile keeps `firmwareCompatible`, `unlockApproved`, `hardwareTested` and
`architectureVerified` false; `probeComplete` is true. Raw reports, ROM/PROM,
dump hashes and device paths remain private under ignored
`data/uefi-probe/captures/20261025-RUN00/`.
[Sanitized physical-capture evidence](verification/rtx3060-uefi-physical-capture-20261025.json).

The preboot selectors were SS0=`70520074`, SS1=`5`. Do not substitute the
desktop2504 example's SS1=`2` or assume that the generic framework's SS1=`8`
target is validated for this board. A display GOP path descends from this GPU,
but the probe does not capture the complete driver-ownership graph. Firmware
compatibility, selector policy and the single-GPU display handoff need review
before preparing a guarded unlock experiment. No unlock EFI has been staged.

## Prepare the USB

The prepared local folder is `data/uefi-probe/rtx3060-readonly/`; the adjacent ZIP
contains the same files. Use a separate, writable **FAT32 USB** with at least
64 MB free. No USB was connected during preparation. No disk was formatted,
system ESP mounted, boot entry registered or firmware setting changed.

Copy the **contents** of the prepared folder to the USB root. Do not copy the
outer folder as a subdirectory. Use another USB if it already has boot files;
do not overwrite an unrelated `EFI/BOOT/BOOTX64.EFI`.

```text
USB root/
  EFI/BOOT/BOOTX64.EFI
  RTX30-PROBE/README.txt
  START-HERE.md
  BUILD-INFO.json
  SHA256SUMS.txt
  SOURCE/                       corresponding source and build helper
  LICENSE, LICENSES/, THIRD_PARTY_NOTICES.md
```

Verify the copied EFI against `BUILD-INFO.json` or `SHA256SUMS.txt`, for example
with `Get-FileHash -Algorithm SHA256 X:\EFI\BOOT\BOOTX64.EFI` (replace `X:`).
The marker directory `RTX30-PROBE` must stay beside `EFI` at the USB root.
Keep the source and license files with the package.

## Run one capture

1. Save work. Confirm access to the Windows recovery key if device encryption is
   enabled. A prior registry read showed Secure Boot and Fast Startup off;
   BitLocker status was not confirmed because its query needed administrator
   privileges. Preparation does not change any of these settings.
2. Fully shut down Windows using Shift + Shut down, then start the PC and open
   the motherboard's one-time UEFI boot menu (typically F8 on ASUS).
3. Select the **UEFI entry for the USB**, leaving Windows Boot Manager and its
   default boot order unchanged. Keep the monitor connected to the RTX 3060.
4. Expect `RTX 30 read-only diagnostic v1`. Do not run any application labelled
   unlock. The probe prints its capture result and returns after 15 seconds.
5. If a firmware menu appears, choose the existing Windows Boot Manager. No
   special same-boot handoff is needed for this read-only probe.
6. Back in Windows, retain the entire new `RTX30-PROBE/RUN00/` directory (or the
   next unused RUN number). Return with the USB connected for inspection.

If the USB is not listed, check FAT32 and the exact fallback EFI path. If firmware
blocks the unsigned image, stop and report the message rather than changing
Secure Boot. If the probe stalls, fully power off, remove the USB and boot the
normal Windows entry. No recovery or unlock boot entry has been installed.

## Files to inspect

- `INVENTORY.TXT`: NVIDIA PCI devices, BARs and GOP display modes/device paths;
  persisted before detailed MMIO reads.
- `REPORT.TXT`: complete capture, register read statuses, SS0/SS1, VRAM/WPR
  inputs, capture hashes and explicit no-write/no-reset/no-boot-change markers.
- `PROM.BIN`: optional 1 MiB live PROM window, read only when memory decoding,
  BAR bounds, actual GA10x chip and all register checks permit it.
- `ROMIMAGE.BIN`: optional firmware-provided ROM copy, which may be incomplete.

Missing optional dumps are diagnostic findings; do not bypass checks to obtain
them. Multiple NVIDIA GPUs, inaccessible MMIO or unavailable USB logging cause
detailed reads to be skipped. This first probe records GOP modes/paths rather
than a complete driver-ownership graph; further read-only capture may be needed
before adapting a headless unlock.

Captures can contain device paths and board-specific identifiers. Keep them in
the project's ignored `data/` area; do not commit raw reports or ROM/PROM dumps
to either GitHub repository.

## Source, validation and reproduction

Source is pinned to [craftingmod/rtx30-unlock at5c076dc](https://github.com/craftingmod/rtx30-unlock/tree/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8).
Only `probe_app.c`, `probe_core.c`, `probe_profile.c`, `efi_runtime.c` and
`sha256.c` link into the image. They perform PCI/MMIO/ROM reads and bounded file
I/O; no GPU configuration/MMIO writes, bus-master enable, firmware transaction,
DMA mapping, FLR, GOP release or boot-variable writes are included. Ordinary host
RAM copies and writes to new USB files are necessary for capture.

`scripts/prepare_uefi_probe.py` verifies the source pin and unchanged checkout,
audits the standalone build source list, builds with LLVM20.1.8/Bun1.4.4, runs
upstream mocked PCI/USB tests and 11 parser tests, and repeats the capture mock
with the exact2503/407b1458 identity. It also verifies that bad machine,
subsystem and import-table mutations are rejected by the PE verifier.

The mock executable uses simulated PCI/USB services, not the physical GPU.
PE validation requires AMD64 EFI subsystem10, matching entrypoint, relocations,
NX/ASLR and zero imports/IAT/delay imports. Compiler/runtime downloads were
verified against official release SHA256 digests; the LLVM installer was only
extracted, never executed. See `BUILD-INFO.json` for actual build/check outcomes.

The pinned source lives in ignored `runtimes/rtx30-uefi-probe-source/`. Build tools
live in ignored `runtimes/uefi-probe-tools/`. With those tools prepared, run:

Official toolchain sources: [LLVM20.1.8](https://github.com/llvm/llvm-project/releases/tag/llvmorg-20.1.8)
(`LLVM-20.1.8-win64.exe`, SHA256 `3197846a2b19063687dd56e93e34cd941e3548d907f23a6131571321bdf9fe7b`)
and [Bun1.4.4](https://github.com/oven-sh/bun/releases/tag/bun-v1.4.4)
(`bun-windows-x64.zip`, SHA256 `cd2c0fccc78f3ede1f50ca827a15f063eda13d4d150a3d0674f4f6e323d864a5`).
The LLVM executable is an extractable archive; this preparation did not run its installer.

```powershell
python scripts/prepare_uefi_probe.py
# For a later rebuild, select a fresh project-local output directory:
python scripts/prepare_uefi_probe.py --output data/uefi-probe/rebuild-01
```

Host mock tests also require installed MSVC C/C++ headers/libraries and Windows
SDK, detected by clang. The helper stages a new local folder/ZIP and never
selects, formats or copies to a physical drive. Source archive and upstream
licenses are included locally; EFI/toolchain binaries remain ignored by Git.
**The physical read-only capture passed. Unlock compatibility, an unlock boot
and any performance benefit remain untested.**
