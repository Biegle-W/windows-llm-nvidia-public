# Windows RTX 3080 Ti unlock preparation — October 25, 2026

**Current installed card:** RTX3080Ti12GB, PCI2208, subsystem10de:1535,
BDF0000:01:00.0, VBIOS94.02.71.00.01, driver610.88/350W. Its pre-attempt
baseline and all four LLM checks are now [recorded](RTX3080TI-VS-3060-20261025.md).
Secure Boot registry state is0/off. The Kingston USB on D: is now FAT32, labeled
RTX3080TI, with the read-only board probe staged and14 file hashes independently
verified. Physical PROM/register and ownership captures remain pending.
No3080Ti unlock has been attempted or built.

**Toolkit prepared and verified:** both diagnostic archives match their manifests
(13 board-probe and11 ownership-probe files). The ownership binary passes PE
checks, the pinned grouped ownership tests and an explicit2208 entry fixture.
Seven setup guard tests pass, including exact installed subsystem/BDF rejection;
22 USB/card/path/cloud-tag/root-parent policy checks pass on Windows PowerShell5.1
and7.6. The actual3060
inventory and real saved3060 capture were previously refused before benchmark
execution/profile creation. The current board stager refuses the disconnected
USB state without writing files. A successful physical USB staging now passes all
14 file checks. No unlock image or boot change was made.
[Sanitized preparation evidence](verification/rtx3080ti-windows-unlock-setup-20261025.json).

This setup prepares the diagnostics and offline checks needed to build a separate
unlock for the installed3080Ti. It does not reuse3060 PROM, selectors or display-driver metadata. Windows
Boot Manager stays first; the working3060 EFI and restore command are preserved.

## Ready-to-run diagnostics

**Current next step:** the board probe is already staged. Restart manually,
press **F8**, select **UEFI Kingston / RTX3080TI**, let the probe finish, then
choose **Windows Boot Manager**. Do not select RTX3060 Automatic Unlock.
Report back after booting Windows so the new capture can be collected/reviewed.

The Kingston was initially exFAT with camera recordings. The user explicitly
authorized discarding them without backup; it was formatted FAT32 on the exact
verified non-system USB. No recording backup was made. The first staging attempt
refused OneDrive cloud-placeholder attributes, and the next exposed a Windows
PowerShell drive-root directory-creation issue. Both were fixed: only documented
cloud tag variants are accepted, redirecting/unknown tags remain refused, and
existing drive-root parents are reused. The final stage and independent USB
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
`Board`, `Ownership`, `Collect`, `SelfTest` and optional `-DriveLetter X`.
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
fallback file silently. The current Kingston holds only the new board-probe
package after the explicitly authorized format. Each package writes new run directories and returns
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

The physical card is present and its baseline is saved, but PROM, cold state
and ownership tree are not available yet, so no card-specific3080Ti unlock EFI
is built or installed at this stage. A
generic GA102 label cannot supply those missing inputs. This is a hardware-data
dependency. Connect the FAT32 USB and collect the two read-only captures with
the prepared launchers to continue.

For a return to the original3060, use `Restore RTX3060 Unlock.cmd` and its exact
identity/hash checks. This setup does not affect the separate Linux AMD system.
