# RTX 3080 Ti + RTX 3080: Windows preparation

The planned pair is RTX 3080 Ti 12 GB plus RTX 3080 10 GB, with 64 GB host RAM.
Both cards have separate, successful single-card unlock results. Simultaneous
Windows unlocking has **not** been validated. The new USB contains a **read-only
pair capture**, not a working dual unlock. No U confirmation is used at this stage.

## Dedicated USB

- Device: **8 GB SanDisk Cruzer Force**.
- Label after preparation: **RTX3080PAIR**. Windows letters can change.
- Intended payload: read-only board/PROM and display-ownership captures for both
  previously captured boards in one firmware session.
- Existing 16 GB Kingston/3080, 32 GB Kingston/3060 and 4 GB General/Ti USBs remain
  separate single-card packages. Do not use them to attempt sequential pair unlocks.
- The user explicitly authorized formatting this new SanDisk and discarding its
  recordings. Formatting status and identity verification are saved privately.

## Tomorrow's first boot

1. Fully shut down before installing the second GPU and the new PSU. Keep the
   display cable on the **3080 Ti**, with the Ti in its current primary slot.
2. Connect this SanDisk, leaving the three single-card unlock USBs disconnected.
3. Power on, press **F8**, and choose **UEFI: SanDisk Cruzer Force**. Secure Boot
   must remain off for this unsigned image. Do not change internal boot entries.
4. Let the read-only capture finish. It checks for exactly one of each previously
   captured board, selects the Ti first and the 3080 second, and discovers their
   actual PCI addresses. It performs no unlock, reset or driver detach.
5. Choose **Windows Boot Manager** if the firmware menu appears. The probe does
   not automatically chainload Windows. Do not boot a single-card unlock USB next.
6. Run **Collect RTX3080 Dual Captures.cmd** from the Windows project. Preserve
   the USB until the evidence is collected and reviewed.

Expected new files on a fresh USB:

| Folder | First run | Second run |
|---|---|---|
| `RTX30-PROBE` | Ti REPORT/INVENTORY/PROM and available ROM copy | 3080 equivalents |
| `RTX-UNLOCK` | Ti `GOP.TXT` ownership tree | 3080 ownership tree |

Existing runs are never overwritten; therefore run numbers can advance. Identify
each capture from its recorded board identity and address, not its directory number.
A refusal or incomplete capture must be reviewed; it does not establish unlock
compatibility. With only the Ti installed, the pair probe refuses before captures.

## Work after capture

Review both current board states, PROM correspondence, primary-display and headless
ownership, PCI/BAR layout and security prerequisites. Develop and test a coordinated,
manual-only pair image against that evidence, then stage it separately. Never copy
the primary card's display teardown onto a headless secondary GPU, widen a selector
to accept unknown states, or reset an already processed card twice in one session.

After a real pair unlock, verify FP32/FP16/BF16 reference correctness and throughput
on **each GPU independently**, plus device health and display recovery. Until then,
the single-card results are historical evidence rather than a dual-card result.

The active inference router remains single-card scoped and will refuse a second
visible NVIDIA card. Multi-GPU model profiles and admission checks require a
separate update after the pair is detected; do not lower the current memory guards.
The PCIe switch and later 3060 installation change topology again and need another
capture. This preparation does not enable P2P or change the separate AMD Linux build.

## Source and validation

`scripts/prepare_uefi_dual_probe.py` builds local overrides against the unchanged
pinned source. Only target filtering and diagnostic error propagation are adapted;
GPU read routines and the ownership walker retain their upstream implementation.
Exact subsystem selectors are generated from private audited profiles. They do not
authorize any GPU write. Mutation source APIs and final linked symbols are checked.
CPU mocks exercise pair selection, unexpected or missing cards, errors, USB-only
boot, security checks and fail-stop sequencing. Physical dual-card boot remains
untested until both cards are installed. See the saved verification summary for
completed checks and the resulting EFI hash.

Raw board profiles, PROMs, capture logs, generated policy headers, USB identities
and backups stay in ignored project data. Publish only this procedure and the
sanitized build/test status.
