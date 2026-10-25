# RTX 3080 Ti first Windows unlock trial — October 25, 2026

**Result update:** manual RUN01 succeeded, with safe transaction/display logs,
Windows observation and FP16/BF16 compute improvements of80.3%/84.7%.
[Physical result and limits](RTX3080TI-WINDOWS-UNLOCK-RESULT-20261025.md).
The text below preserves the pre-trial design and instructions. Do not rerun the
unlock in the current Windows/firmware session. Automatic3080Ti startup is not installed.

This is a fixed-board, manual-only experiment for the installed RTX3080Ti12GB,
device2208/subsystem10de:1535, BDF0000:01:00.0, VBIOS94.02.71.00.01.
Both read-only captures passed. No3080Ti unlock has run yet. Host tests cannot
establish actual display recovery, stability or performance.

**Ready for the first manual trial:** the Kingston FAT32 USB now contains the
manual candidate. All24 package files including the manifest were independently
hash checked. Both original RUN00 capture folders remain intact on USB and in
private storage. EFI SHA256:
`c13c39eb98bae5b836c80e1a4e5d7f84c05ad910f35b5b62f2ad97311052fab4`.

Fresh administrator checks confirm Secure Boot off, C: FullyDecrypted/BitLocker
Off, Windows-first firmware order and the exact preserved3060 EFI hash. GPU
StatusOK/error0 and no NVIDIA Error/Critical events found this boot. No internal
ESP payload, boot order, driver or power setting was changed by this preparation.

The separate image uses this card's own PROM and initial selectors, and its own
five captured display-driver metadata profiles. It retains the pinned firmware
transaction, cold-state checks, live PROM comparison, logging, DMA containment,
single FLR and display recovery rules. No automatic, production, SSD experiment,
automatic profile creation or relaxed initial-selector flags are used.

## Captured policy and validation

The completed ownership tree has four handles, five distinct driver roles and
exactly ten active ownership edges, with detach_attempted0/touched0. It is the
one-child AMI display chain. This card's NVIDIA GOP is193248bytes/version0x6000d;
the old3060 GOP was179904bytes/version0x6000b. Its own metadata is used, never the
3060 policy. The live method/image-consistency checks remain enforced.

| Role | Image bytes | Binding version | Start RVA | Stop RVA |
|---|---:|---:|---:|---:|
| NVIDIA GOP | 193248 | 0x6000d | 0x774 | 0x698 |
| AMI GOP bridge | 8576 | 0x11 | 0x6b0 | 0x88c |
| Aggregate GOP | 15296 | 0x10 | 0x844 | 0xb2c |
| Text member | 27360 | 0x10 | 0xf6c | 0x104c |
| Runtime EDID/input | 36864 | 0x1 | 0x1384 | 0x14d4 |

These are captured metadata and method offsets, not cryptographic driver-code
hashes. The probe did not dump the loaded driver code. The build uses this
board's live-PROM hash and exact initial SS0=51144015/SS1=1; zero, changed, mixed
or already-unlocked selectors are refused. No3060 zero-state startup exception
is carried into this image. The firmware transaction itself remains pinned to
craftingmod source5c076dc4ee7fa369639669fa591ac74d8f6dfcd8.

Checks passed: eight upstream host suites;31 display teardown/reset/rejoin
scenarios;22 simulated unlock/rejoin scenarios;26 driver policy cases; wrong-BDF
and extra-child refusals;19 actual unchanged ColdCheck scenarios; eight manual
entry/gate flows; nine synthetic ownership-policy tests; seven setup tests; and
39 USB/card/manual-package/prerequisite checks on Windows PowerShell5.1 and7.6.
PE inspection confirms AMD64 EFI/subsystem10, NX/ASLR and no imports. Hardware
preprocessing confirms the driver-offset checks are present and mock flags absent.
The original3060 display adaptation still reproduces its saved validated C source
exactly; its installed EFI remains hash verified. None of these host checks proves
a successful3080Ti firmware transaction or real display recovery.

The build is under ignored `data/uefi-probe/windows3080ti-manual-20261025-v3/`.
Earlier v1/v2 stopped at build/packaging errors and were never staged. The guarded
USB stager initially rejected a timezone-misparsed prerequisite timestamp before
writing; it now uses DateTimeOffset and tests equivalent UTC/offset timestamps,
stale/future records and changed boot policy. The final39-check run and physical
USB verification passed. USB collisions were backed up before writes; the EFI
was copied last after all other package files. Raw captures, generated headers,
firmware binaries and private platform state remain ignored.

## First manual boot

The candidate is now staged and verified. Preserve Windows Boot Manager and the
3060 restore path. This USB boot can run an unlock only after the explicit U gate.

1. Save work, shut down fully, then start and press **F8**.
2. Choose **UEFI Kingston USB**. Keep the display connected to the3080Ti.
3. Let fixed-board/PROM/cold-state/display preflight finish. Press **U once**
   only when it offers the manual unlock. Esc or30 seconds cancels. If any check
   refuses, return to Windows normally and report it; do not bypass the check.
4. After U the display may go black. Allow up to **10 minutes** for Windows.
   Success starts Windows directly in the same boot. Do not restart or run another
   unlock to reach Windows after a successful transaction.
5. If the EFI stops or Windows does not appear within10 minutes, power off fully,
   remove the USB, then boot **Windows Boot Manager**. Do not retry in the same
   firmware session or select the3060 automatic unlock entry.
6. Once in Windows, leave the USB connected and report whether U was pressed and
   Windows started directly. The next GOP.TXT/UNLOCK.TXT, GPU health and identical-
   executable compute baseline comparison must establish what actually happened.

No VBIOS flash or permanent startup installation is performed. U executes a
volatile GPU firmware transaction and one FLR. The saved pre-attempt compute
baseline is FP16/BF16 about70.35TFLOPS; no speedup is claimed until measured.
The independent Linux AMD build is unaffected.
