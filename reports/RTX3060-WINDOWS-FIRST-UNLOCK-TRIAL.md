# RTX 3060 first Windows unlock trial — October 25, 2026

**Result update:** the first physical trial succeeded. Windows FP16/BF16 Tensor
GEMM throughput increased about89%, with safe transaction/display logs and a
healthy NVIDIA device. See [execution evidence and limits](RTX3060-WINDOWS-UNLOCK-RESULT-20261025.md).
The following text preserves the pre-trial design and procedure.

The physical ownership capture completed successfully without a detach or GPU
write. It reveals a **single-child AMI aggregate-console chain**, not the
two-child layout expected by the earlier generic candidate. A separate fixed-board
adaptation is now prepared for a **manual hardware experiment**. No unlock has
run yet, and host tests do not establish real display recovery or performance.

## What the capture establishes

- Exact Gigabyte RTX3060 `10de:2503`, subsystem `1458:407b`, at `0000:01:00.0`.
- Four handles form GPU PCI root -> physical GOP -> aggregate GOP/text handle ->
  shared console. The shared handle carries console input, output and standard
  error. One runtime driver owns EDID on the physical display and two shared
  input-related protocols. Those input bindings must remain unchanged.
- Exactly five driver roles are present: NVIDIA GOP, AMI GOP bridge, aggregate
  GOP, text member and runtime EDID/input driver. The complete ten active
  ownership edges match the scoped design. The capture visited all four queued
  handles, recorded five driver bindings and completed with status0/touched0.
- Raw GOP.TXT is hash-verified in ignored
  `data/uefi-probe/captures/20261025-OWNERSHIP-RUN00/`. It is not published.

The [published AMI single-GPU reference](https://github.com/impacifist/Windows-GPU-UNLOCK/blob/e3f03cd9389195adcabda4743d8fc2922b32498c/internal-boot/unlock/machine-profile.h)
helps explain the topology, but its motherboard/GPU fingerprints are different.
Its verified profile was not reused. This adaptation retains the
[craftingmod base](https://github.com/craftingmod/rtx30-unlock/tree/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8)
and binds its separate display implementation to the actual capture.

## Candidate changes and checks

`scripts/prepare_uefi_3060_single_child.py` keeps the upstream checkout and earlier
candidate unchanged. It generates a separate display-source override and reviewable
patch in ignored local storage. The firmware transaction, asset hashes, cold-state,
PROM, DMA, reset and selector code remain unchanged.

The display plan requires exactly one vendor display child and five distinct
driver roles. It rejects a second child rather than ignoring it. Teardown stops
only the captured text/aggregate/GOP/EDID chain, preserving shared input guards;
recovery requires the same one-child shape. Residual owners/GOPs, changed input,
unsafe DMA/transaction state, incomplete recovery and failed logging block handoff.

Hardware preflight additionally checks each driver's captured image size, binding
version and Start/Stop offsets before U. These are **metadata checks, not hashes
of driver code**; this capture did not dump the loaded images. The existing
live-driver consistency checks remain in force throughout the operation.

| Role | Image bytes | Binding version | Start RVA | Stop RVA |
|---|---:|---:|---:|---:|
| NVIDIA GOP | 179904 | 0x6000b | 0x774 | 0x698 |
| AMI GOP bridge | 8576 | 0x11 | 0x6b0 | 0x88c |
| Aggregate GOP | 15296 | 0x10 | 0x844 | 0xb2c |
| Text member | 27360 | 0x10 | 0xf6c | 0x104c |
| Runtime EDID/input | 36864 | 0x1 | 0x1384 | 0x14d4 |

Validation includes31 display teardown/rejoin scenarios,22 simulated unlock/rejoin
scenarios,26 driver-metadata policy checks, wrong-BDF/extra-child preflight
refusals and the earlier eight manual-gate tests. The driver callbacks in the
teardown mocks are ordinary host functions, so real UEFI method offsets are
tested separately. The mock-only switch is absent from the EFI build, and
preprocessing verifies that the hardware driver checks are compiled in.

The image remains a fixed-profile, logged, manual-only build: **no automatic,
production, SSD or automatic-profile flags**. It always requires U after preflight;
Esc or30 seconds cancels. The initial captured selectors remain SS0=`70520074`,
SS1=`5`; the unmodified experimental transaction targets SS0=`88888888`, SS1=`8`.
Changed cold state causes refusal, not automatic recapture or a relaxed check.

All five firmware assets are verified against their pinned hashes. The prior
offline PROM/signature/layout checks and the confirmed Secure Boot-off,
FullyDecrypted/BitLocker-off state remain documented in the
[preparation report](RTX3060-WINDOWS-UNLOCK-PREPARATION.md).

## USB and first hardware attempt

The Kingston FAT32 USB fallback is the **manual single-child unlock candidate**.
Its payload is in `RTX-UNLOCK/ASSETS/`. `UNLOCK-TRIAL/` retains the package,
source correspondence, local patch, licenses and these instructions. Both earlier
read-only captures and a private backup of the pre-trial USB remain preserved.
No system ESP, BCD, boot order, firmware variables, Windows driver or power limit
has been changed. This does not flash a VBIOS; executing U changes volatile GPU
state, runs the firmware sequence and performs one FLR before Windows handoff.

1. Save work and use **Shift + Shut down**, then start and press **F8**.
2. Choose the Kingston **UEFI USB** using the one-time menu. Leave the monitor
   connected to the3060. Do not install a persistent boot entry.
3. Let preflight finish. It should identify a full GOP-release/unlock experiment
   and offer **U**. Press U once only when ready for this first hardware trial.
   Esc or30 seconds cancels. A refusal is a result to inspect, not a reason to
   run another image or bypass a check.
4. After U the screen can go black. Allow up to **10 minutes** for Windows.
   Successful execution starts Windows directly in the same boot; do not reboot
   or manually rerun the unlock to reach Windows.
5. If it reports a stop/refusal or Windows does not appear within10 minutes,
   power off fully, remove the USB and boot the existing Windows Boot Manager
   normally. Do not repeat the experiment in the same firmware session.
6. On reaching Windows, keep the USB connected and report whether U was pressed,
   Windows started directly, and any visible error. Inspect the next unused
   `RTX-UNLOCK/RUNnn/GOP.TXT` and `UNLOCK.TXT` before inferring success.

Windows driver recognition, selector/readback logs, resource containment and an
identical-executable compute comparison are required after the attempt. The saved
stock FP16/BF16 baseline is about26.8TFLOPS with FP32 accumulation. No unlocked
speedup, stability, sleep/resume support or quantized LLM improvement is claimed.

Local candidate: ignored `data/uefi-probe/windows3060-single-child-20261025-v3/`.
[Sanitized evidence](verification/rtx3060-single-child-preparation-20261025.json).
