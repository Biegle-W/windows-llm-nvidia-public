# Windows RTX 3080 Ti unlock preparation — October 25, 2026

**Toolkit prepared and verified:** both diagnostic archives match their manifests
(13 board-probe and11 ownership-probe files). The ownership binary passes PE
checks, the pinned grouped ownership tests and an explicit2208 entry fixture.
Six setup guard tests pass; the actual3060 inventory and real saved3060 capture
are refused before benchmark execution/profile creation. Double-click
**Capture RTX3080Ti Baseline.cmd** after the swap to record a fresh baseline.
No physical3080Ti or USB is present; no unlock image or boot change was made.
[Sanitized preparation evidence](verification/rtx3080ti-windows-unlock-setup-20261025.json).

The RTX3060 remains installed. This setup prepares the diagnostics, baseline and
offline checks needed to build a separate3080Ti unlock after the replacement is
present. It does not reuse3060 PROM, selectors or display-driver metadata. Windows
Boot Manager stays first; the working3060 EFI and restore command are preserved.

## Ready-to-run diagnostics

The local setup directory is `data/uefi-probe/rtx3080ti-unlock-setup/`:

- `01-board-probe/` and ZIP: read-only PCI/register/ROM/PROM capture.
- `02-ownership-probe/` and ZIP: read-only display/GOP driver-ownership capture;
  no driver detach, GPU reset or unlock is linked into this build.

These are two separate USB boot packages with different `EFI/BOOT/BOOTX64.EFI`
files. Use separate FAT32 USB drives, or preserve the first capture and switch
packages deliberately between runs. Do not merge them or replace the3060 USB's
fallback file silently. No USB is currently connected; none is formatted or
staged by this preparation. Each package writes new run directories and returns
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

The physical card, PROM, cold state and ownership tree are not available yet,
so no card-specific3080Ti unlock EFI is built or installed at this stage. A
generic GA102 label cannot supply those missing inputs. This is a hardware-data
dependency, not another approval request. After the swap, tell the agent the
3080Ti is installed; the prepared commands and packages are ready to continue.

For a return to the original3060, use `Restore RTX3060 Unlock.cmd` and its exact
identity/hash checks. This setup does not affect the separate Linux AMD system.
