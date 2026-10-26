# RTX 3080 10 GB unlock preparation — October 25, 2026

**Current result:** the RTX 3080 10 GB is installed. Its two read-only board
captures, RUN01 and RUN02, pass identity and capture checks. The PROM, ROM and
all 16 captured register values agree between the runs. The 1 MiB PROM passes
CPU-only firmware descriptor, fuse/signature selection, aligned DMA and 10 GB
memory-layout checks. Deliberate truncated-ROM/missing-signature cases refuse.
No firmware was executed by the offline auditor, and diagnostic approval flags
remain false. Display ownership still needs its physical capture and review.

The retained compute executable records this pre-project-unlock baseline:

| Mode | TFLOPS | Reference check |
|---|---:|---|
| FP32 pedantic | 23.142982 | Pass |
| FP16 tensor, FP32 accumulation | 60.196178 | Pass |
| BF16 tensor, FP32 accumulation | 60.052674 | Pass |

Each uses a 4096-square GEMM, two-second warmup and 30 samples. These synthetic
compute rates are not LLM generation speed; no gain is claimed before a later
same-executable comparison. Third-party lock state is not independently asserted.
Driver 610.88 and 320 W cap are unchanged. GPU reports OK/error 0, and no NVIDIA
Error/Critical events were found since this Windows boot after the baseline.

**Next boot:** Kingston D:, FAT32/RTX3080_10G, now contains the read-only
GC_TREE_ONLY ownership probe. All 12 package files independently match source
and manifest; all 15 prior raw capture files still match their private copies.
Colliding files were backed up, EFI copied last, and no formatting, internal ESP,
BCD or model-profile change was performed. Restart, F8 -> UEFI Kingston USB,
let the probe finish, then select Windows Boot Manager. There is no U unlock
confirmation in this diagnostic. Return for ownership review and a separate
exact-board manual candidate. Neither an unlock nor automatic startup is staged.

The original preparation notes below are historical; this section supersedes
their statements that the Ti remains installed or that no board capture exists.
[Curated board-stage verification](verification/rtx3080-10gb-board-capture-20261025.json).

**Prepared and staged:** Kingston D: is FAT32, labeled **RTX3080_10G**, and now
boots the read-only board probe. All14 staged files were independently verified.
The previous3080Ti manual fallback and colliding files were archived before any
overwrite. All seven prior board/ownership/unlock capture files remain intact.
The current3080Ti Windows session was not reset or changed.

This setup targets the2206 RTX3080 with10240MiB from the earlier benchmark.
The3080Ti remains installed. No3080 PROM/register/ownership capture exists yet,
so no exact-board3080 unlock image can be built. The3060 and3080Ti manual images
remain separately preserved. No internal EFI or automatic startup is installed.

The first step uses a generic read-only GA10x board probe, packaged separately
with2206 host mocks. It may be staged before swapping cards; it does not unlock
or reset any GPU. The later baseline, capture collection and offline audit refuse
the3060,3080Ti, other PCI IDs and non10GB variants. A2216/LHR or other variant
requires its own reviewed preparation rather than reusing this2206 scope.

## First boot after swapping cards

1. Fully shut down and install the RTX3080 10GB.
2. Start and press F8, then choose UEFI Kingston USB for the read-only board probe.
3. Let it finish, choose Windows Boot Manager and tell the agent you are back.
4. The agent records this card's Windows identity and pre-unlock compute baseline,
   preserves its board capture, then stages the separate read-only ownership probe.
5. After the ownership boot, review both captures and offline firmware checks
   before building a guarded manual-only unlock for this card.

Do not boot either existing3060 or3080Ti unlock image on the3080. Do not press U
in either of those images. The correct first3080 probe has no unlock linked.

The project helpers and prepared packages are separate:

- `scripts/rtx3080_setup.py`:2206/10240MiB identity guard, baseline, ownership
  package preparation and CPU-only report/PROM audit.
- `scripts/Prepare-RTX3080ProbeUsb.ps1`:Board/Ownership/Collect staging. Only
  Board may be prepared before installing the card; later modes require2206.
- `data/uefi-probe/rtx3080-10gb-readonly/` and adjacent ZIP: board diagnostics.
- `data/uefi-probe/rtx3080-10gb-ownership/` and adjacent ZIP: ownership diagnostics.

Both boot packages use EFI/BOOT/BOOTX64.EFI and must be staged one at a time.
The stager verifies source and destination hashes, backs up overwritten USB files,
retains old RUN folders and copies the EFI last. It never formats or changes BCD.
Use a FAT32 non-system USB. Raw captures and board identifiers remain ignored.

The existing3080Ti model-router profiles remain12GB scoped; this unlock
preparation does not lower their admission limits or approve them for10GB.
The earlier3080 `llama-bench` result is historical and cannot supply firmware
fingerprints or prove this card is unlocked.

## Preparation verification

The board EFI is unchanged pinned read-only code, SHA256
`ae7b5cdd1cc579fc516ebda68c9d438d433697fb78d151304d56a2cbca41785a`.
Its build, generic probe/parser mocks,2206/GA102 fixture and PE negative checks
pass. The ownership EFI is SHA256
`58f4d6beb444d423a8509dd4d1cdbb7a2e10a425e51ae2e65f2cceaa011342b8`;
grouped ownership mocks, an explicit2206 entry fixture and PE checks pass, with
no mutating unlock symbols or firmware assets linked. Both archives match their
13/11-file manifests. The generic images have prior physical validation on the
other cards; a physical2206 run remains pending.

Nine new identity/profile guard tests pass. The actual installed3080Ti is refused
before baseline compute/output creation and before ownership staging. Shared
41-case USB/path/prerequisite policies still pass through the test-only import.
Board mode deliberately supports staging before a swap, because that binary
only reads diagnostics. Ownership/collection require the actual2206/10GB card.
No production model profile or hardware admission limit was changed.

After the board boot, run **Capture RTX3080 10GB Baseline.cmd** and **Collect
RTX3080 10GB Captures.cmd**. These preserve new private evidence. The agent can
then invoke the auditor with the actual baseline and report paths:

```powershell
& .\runtimes\python\cpython-3.11.15-windows-x86_64-none\python.exe scripts/rtx3080_setup.py audit --baseline <baseline.private.json> --capture-dir <RTX30-PROBE-RUN-folder> --output data/uefi-probe/3080-10gb-board-audit
```

The auditor binds subsystem and PCI address to that physical Windows identity,
keeps diagnostic approval flags false, and calls only CPU byte parsers. Add
`--ownership-log <GOP.TXT>` after the second capture. It does not build an unlock.
[Curated readiness](verification/rtx3080-10gb-unlock-setup-20261025.json).
