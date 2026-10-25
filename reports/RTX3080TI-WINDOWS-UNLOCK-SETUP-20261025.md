# Windows RTX 3080 Ti unlock preparation — October 25, 2026

**Latest:** [manual RUN01 succeeded and compute verification passed](RTX3080TI-WINDOWS-UNLOCK-RESULT-20261025.md).
FP16/BF16 increased80.3%/84.7% in the retained short GEMM; safe cleanup and
display/Windows recovery are recorded. Automatic3080Ti startup is not installed.
Do not rerun the unlock in the current session. Diagnostic/pre-trial setup
history follows below; its pending-state descriptions are historical.

**Current installed card:** RTX3080Ti12GB, PCI2208, subsystem10de:1535,
BDF0000:01:00.0, VBIOS94.02.71.00.01, driver610.88/350W. Its pre-attempt
baseline and all four LLM checks are now [recorded](RTX3080TI-VS-3060-20261025.md).
Secure Boot registry state is0/off. The Kingston USB on D: is now FAT32, labeled
RTX3080TI. Physical board-probe RUN00 passed and is privately preserved; the
read-only ownership probe was subsequently staged with12 file hashes independently
verified. Its RUN00 is now captured and reviewed: the same one-child chain with
this card's different NVIDIA GOP metadata. The USB now holds the manual candidate.
No3080Ti hardware unlock has been attempted.

**Toolkit prepared and verified:** both diagnostic archives match their manifests
(13 board-probe and11 ownership-probe files). The ownership binary passes PE
checks, the pinned grouped ownership tests and an explicit2208 entry fixture.
Seven setup guard tests pass, including exact installed subsystem/BDF rejection;
39 USB/card/path/manual-package/prerequisite policy checks pass on Windows PowerShell5.1
and7.6. The actual3060
inventory and real saved3060 capture were previously refused before benchmark
execution/profile creation. The current board stager refuses the disconnected
USB state without writing files. A successful physical USB staging now passes all
14 file checks for that diagnostic stage. The manual image is now built/staged
as described in the linked first-trial report; internal boot settings are unchanged.
[Sanitized preparation evidence](verification/rtx3080ti-windows-unlock-setup-20261025.json).

This setup prepares the diagnostics and offline checks needed to build a separate
unlock for the installed3080Ti. It does not reuse3060 PROM, selectors or display-driver metadata. Windows
Boot Manager stays first; the working3060 EFI and restore command are preserved.

## Ready-to-run diagnostics

**Current next step:** follow the [full shutdown/F8/U procedure and fallback](RTX3080TI-WINDOWS-FIRST-UNLOCK-TRIAL-20261025.md).
Press U only after its preflight; Esc/30 seconds cancels. It should start Windows
directly after a successful transaction. Do not rerun it in the same firmware
session or select RTX3060 Automatic Unlock. Then report the result for log review.

## Physical board RUN00 result

The first USB diagnostic boot captured the exact2208/10de:1535 device at
0000:01:00.0. All16 register reads succeeded. PROM is1048576bytes; the captured
ROM image is164352bytes. Report completion explicitly records no GPU writes,
no GPU resets and no boot-variable changes. The four capture files were copied
and hash verified under ignored
`data/uefi-probe/3080ti-usb/captures-20261025-170200-5156551ec31e4c2d80848e60b4258684/`.
The strict report/PROM parser and exact-board audit passed under
`data/uefi-probe/3080ti-board-audit-20261025-run00/`.

Offline CPU-only checks passed FWSEC parsing, fuse/signature selection (FWSEC
version2, booter version1), aligned DMEM/IMEM geometry, GSP boot descriptor,
memory layout and FRTS command encoding in a host copy. Truncated-ROM and missing-
signature negative cases were rejected. Expected errors in those two negative
cases are not a failed audit. No firmware was executed by the auditor. Original
diagnostic approval/compatibility/hardware-tested flags remain false; offline
parser success does not establish a safe hardware unlock.

The board capture remains intact both locally and on the USB after switching
packages. The ownership stager backed up every collision, and all12 current
ownership package files including its manifest were independently checked.
GPU StatusOK/error0 and zero nvlddmkm Error/Critical events found since this
Windows boot. The ownership image used for the second diagnostic boot had no
unlock code or firmware assets. Its completed capture now supports the separately
staged manual candidate described in the first-trial report.

## USB preparation history

The Kingston was initially exFAT with camera recordings. The user explicitly
authorized discarding them without backup; it was formatted FAT32 on the exact
verified non-system USB. No recording backup was made. The first staging attempt
refused OneDrive cloud-placeholder attributes, and the next exposed a Windows
PowerShell drive-root directory-creation issue. Both were fixed: only documented
cloud tag variants are accepted, redirecting/unknown tags remain refused, and
existing drive-root parents are reused. The final board stage and independent USB
manifest comparison succeed. The reusable staging helper itself never formats.

If staging again later, connect the FAT32 Kingston USB. No further formatting is needed.
Use these root launchers, with only one USB connected (or pass a drive letter
explicitly to the PowerShell helper):

1. Run **Prepare RTX3080Ti Board Probe.cmd**. It checks the exact Windows card,
   USB bus/non-system/FAT32 identity and every package hash, then backs up all
   colliding files privately before staging. Existing RUN folders are retained.
2. Restart manually, press **F8**, choose the **UEFI USB** entry. The board probe
   records read-only PCI/register/PROM data. After it returns, choose **Windows
   Boot Manager**. Do not select the3060 automatic unlock entry.
3. Run **Collect RTX3080Ti Captures.cmd**. It copies/hash-checks the USB capture
   directories into ignored `data/uefi-probe/3080ti-usb/captures-*/`. Older3060
   captures may be included; select only this2208/subsystem1535 run for audit.
4. Run **Prepare RTX3080Ti Ownership Probe.cmd**, boot the USB again and return
   to Windows in the same way. This image only reads/logs display ownership.
5. Run **Collect RTX3080Ti Captures.cmd** again, then have the agent audit both
   current-card captures before building a manual unlock.

The USB staging helper is `scripts/Prepare-RTX3080TiProbeUsb.ps1`, with modes
`Board`, `Ownership`, `Collect`, `Manual`, `SelfTest` and optional `-DriveLetter X`.
Manual additionally requires an explicit private package path, reviewed EFI hash
and fresh administrator prerequisite evidence; it copies the EFI last.
It never formats, changes BCD, repartitions, reboots or executes an unlock.
Staging backups and private USB identity records are under
`data/uefi-probe/3080ti-usb/before-*/`. Neither packaged diagnostic image is an
unlock image. The copied guides inside the original ZIPs describe preparation
before the card was installed; this maintained document supersedes that status.

The local setup directory is `data/uefi-probe/rtx3080ti-unlock-setup/`:

- `01-board-probe/` and ZIP: read-only PCI/register/ROM/PROM capture.
- `02-ownership-probe/` and ZIP: read-only display/GOP driver-ownership capture;
  no driver detach, GPU reset or unlock is linked into this build.

These are two separate USB boot packages with different `EFI/BOOT/BOOTX64.EFI`
files. Use separate FAT32 USB drives, or preserve the first capture and switch
packages deliberately between runs. Do not merge them or replace the3060 USB's
fallback file silently. The Kingston now boots the manual candidate, while both
diagnostic RUN00 folders remain preserved. The read-only packages write new runs and return
to firmware. Use F8 to boot it, then Windows Boot Manager afterward if necessary.
The ownership probe uses `RTX-UNLOCK/RUNnn/GOP.TXT`; the board probe uses
`RTX30-PROBE/RUNnn/REPORT.TXT`, `PROM.BIN` and optional ROM/inventory files.

## After installing the card

Boot Windows normally first. Verify the driver and the single physical card.
The baseline command below refuses the3060, multiple cards and non2208 devices.
It records BDF, subsystem, VBIOS, VRAM, driver and the current power limit, then
runs the retained FP32/FP16/BF16 benchmark without changing GPU settings. It will
not stop unrelated apps. Raw identifiers and measurements remain ignored.

From the project directory, using the bundled Python:

```powershell
$python = '.\runtimes\python\cpython-3.11.15-windows-x86_64-none\python.exe'
& $python scripts/rtx3080ti_setup.py baseline --output data/uefi-probe/3080ti-stock-baseline
```

Do this before the project's first3080Ti unlock attempt. The helper labels the
result a pre-attempt baseline; a board already modified elsewhere is not thereby
proven locked. Do not impose the3060's170W limit on the new card.

Run each diagnostic USB and retain both captures. Then import/audit them:

```powershell
& $python scripts/rtx3080ti_setup.py audit --capture-dir X:\RTX30-PROBE\RUN00 --ownership-log Y:\RTX-UNLOCK\RUN00\GOP.TXT --output data/uefi-probe/3080ti-board-audit
```

Replace X:/Y: and run numbers with the actual capture locations. The helper
validates the strict upstream report/PROM parser, requires2208/GA102, copies the
capture privately, generates an exact-board header and calls the existing pure
FWSEC/signature/DMA/layout parsers on CPU-owned bytes. Original compatibility,
hardware-tested and approval flags remain false. It never executes firmware or
installs an unlock. Unsupported firmware/layout is a refusal requiring review.

## Board-specific unlock completion

The resulting data lets the next agent review this card's display topology and
driver roles, adapt the manual unlock if needed, and run host tests. It must keep
the3060 build separate. A one-time manual3080Ti boot should establish safe reset,
display recovery, Windows handoff and compute benefit before automatic startup
is configured for this new card. The future automatic profile should use only
complete initial-selector pairs observed and validated on the3080Ti itself.

The physical card, baseline, PROM, first preboot state and reviewed ownership tree
are now available. The separate card-specific manual candidate is built/tested
and staged on USB; its first hardware transaction and Windows recovery remain
unvalidated. Automatic startup is not configured for the3080Ti.

For a return to the original3060, use its preserved manual USB package. Its NVMe
EFI and restore launcher were subsequently retired at the user's request;
see [current USB-only policy](RTX3060-NVME-UNLOCK-REMOVED-20261025.md).
This setup does not affect the separate Linux AMD system.
