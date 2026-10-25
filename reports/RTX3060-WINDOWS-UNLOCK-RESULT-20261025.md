# RTX 3060 Windows unlock result — October 25, 2026

**The first manual hardware attempt succeeded, and Windows Tensor GEMM throughput
increased by about89%.** This validates one boot of the specific Gigabyte3060 /
ASUS B760M / BIOS1836 single-child adaptation. It does not establish universal
compatibility, repeat-boot reliability, sustained stability or LLM speed gains.

## Hardware and executable

Gigabyte RTX3060 12GB, `10de:2503`, subsystem `1458:407b`, i5-13600KF and ASUS
TX GAMING B760M WIFI / BIOS1836. Windows NVIDIA driver610.88 and the170W limit
are unchanged. Secure Boot was confirmed off; C: was fully decrypted with
BitLocker protection off. No settings or recovery keys were changed.

The [manual single-child candidate](RTX3060-WINDOWS-FIRST-UNLOCK-TRIAL.md) uses
craftingmod source pin `5c076dc4ee7fa369639669fa591ac74d8f6dfcd8`, the unchanged
firmware transaction, and a separate display-source override based on the actual
ownership capture. EFI SHA256:
`61fa2b71d1332d4d6180610175955d3cad015420c41f393b7abea717507d09e1`.
The original generic two-child candidate was not used for this attempt.

## Physical execution evidence

USB `RTX-UNLOCK/RUN01/` contains GOP.TXT21170 bytes and UNLOCK.TXT13584 bytes.
Both were copied to ignored `data/uefi-probe/captures/20261025-UNLOCK-RUN01/`
and hash-verified against the USB. Raw logs, addresses and firmware remain private.

The logs record:

- The exact card/profile and five display-driver roles pass preflight; manual U
  is confirmed. No automatic execution mode is enabled.
- FWSEC and Booter complete. The transaction writes SS0=`88888888`, SS1=`8`.
  Readback matches before and after the **single FLR** and throughout display
  restoration, mode switching, drawing/readback and final console output.
- Transaction result0, containment0, started1/quiesced1, fault0, retained0,
  maps0, FLR1 and safe1. Bus mastering is off at handoff and temporary DMA
  resources are released. The source's documented pre-reset timeout tolerance
  is logged; it is not an unlock failure or a newly removed check.
- All display release/isolation/exclusive-close/restore/verify statuses are0,
  touched1/restored1. Resolution changes to640x480 and back pass. The green
  framebuffer readback checks9216 pixels with **zero mismatches**.
- The application starts the internal Windows Boot Manager without a reset.
  Subsequent Windows observation recognizes the3060 with driver610.88,
  ConfigManagerErrorCode0 and StatusOK. Tensor GEMM gains below confirm an
  effective unlocked Windows compute state, beyond the UEFI readbacks alone.

No NVIDIA `nvlddmkm` Error/Critical events were found in the System log since
this Windows boot at the time of the check. Post-benchmark GPU temperature was
39C. These are short observations, not long-duration error/thermal coverage.

## Identical-executable comparison

The same privately retained `rtx3060-compute-baseline.exe` ran before and after
the unlock. It was built from the pinned upstream `src/gop/compute-benchmark.cu`
with nvcc13.3 forsm86, using CUDA runtime13.3 and cuBLAS13.6. Each mode uses
4096-square all-ones GEMM,2 seconds warm-up and30 event-timed samples. FP16/BF16
use FP32 accumulation; FP32 uses pedantic math. The benchmark's first/last
output-element reference checks passed in both arms.

| Mode | Stock TFLOPS | Unlocked TFLOPS | Throughput change | Stock median | Unlocked median |
|---|---:|---:|---:|---:|---:|
| FP32 pedantic | 8.643 | 8.540 | -1.2% | 15.902496 ms | 16.093697 ms |
| FP16 Tensor / FP32 accumulate | 26.835 | 50.724 | +89.0% | 5.121536 ms | 2.709520 ms |
| BF16 Tensor / FP32 accumulate | 26.788 | 50.591 | +88.9% | 5.130560 ms | 2.716672 ms |

This is one short desktop measurement per arm, without repeated A/B/A boots,
matched full thermal histories or desktop-workload isolation. All-ones first/last
element checks are not broad numerical validation. No INT8, quantized llama.cpp
decode, real-model inference or long-context benchmark was run after the unlock.
Do not replace the saved model throughput figures with these GEMM measurements.

## Current operation and limits

The unlock is effective in the observed Windows boot. The USB still requires U;
the normal Windows boot order, system ESP/BCD, driver and power limit were not
changed. No VBIOS was flashed and no permanent automatic unlock was installed.
Do not run the unlock again in this same boot.

Persistence through restart, full shutdown and sleep/resume has not been tested.
For a later manual trial, use the documented full-shutdown / one-time USB / U
procedure and inspect its new logs; do not assume a successful past boot means
an unlock is active in a later session. Original diagnostic-profile approval
flags and build-time HardwareTested=false metadata remain preserved as historical
evidence; this new result records the physical success separately.

[Sanitized execution and benchmark evidence](verification/rtx3060-windows-unlock-success-20261025.json).
