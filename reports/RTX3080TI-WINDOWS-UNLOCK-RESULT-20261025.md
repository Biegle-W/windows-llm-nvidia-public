# RTX 3080 Ti manual Windows unlock result — October 25, 2026

**RUN01 succeeded.** The exact-board manual image accepted its captured initial
state, received U, completed one transaction/FLR with safe resource cleanup,
restored display output and handed off to Windows. The same retained compute
executable now measures FP16 +80.3% and BF16 +84.7% against this card's saved
pre-attempt baseline. FP32 is essentially unchanged.

## Matched short compute comparison

| Mode | Before, TFLOPS | After RUN01, TFLOPS | Difference |
|---|---:|---:|---:|
| FP32 pedantic | 25.682687 | 25.700669 | +0.07% |
| FP16 tensor, FP32 accumulation | 70.349903 | 126.859854 | +80.33% |
| BF16 tensor, FP32 accumulation | 70.363161 | 129.957548 | +84.70% |

Both runs use the same4096-square GEMM executable, sm86, CUDA13.3/cuBLAS13.6,
two-second warmup and30 timed samples. All three endpoint reference checks
passed. These checks do not establish full numerical correctness or prolonged
stability. No clocks, power limit, driver or model setting was changed. Driver
remains610.88, VBIOS94.02.71.00.01 and power limit350W on the same12GB card.
The executable SHA256 is
`aa8cca683335ee33ab000829b0aa47eceb7de04281eec39d3d36103b2338916e`.

This is a short matrix microbenchmark comparison across Windows sessions;
background load, clocks and thermal conditions are not a controlled A/B/A.
LLM generation rates have not been remeasured after this unlock. Earlier maximum-
context mixed CPU/GPU results remain the pre-attempt3080Ti measurements in the
[pre-attempt model comparison](RTX3080TI-VS-3060-20261025.md).

## Transaction, display and Windows evidence

- Identity2208/subsystem10de:1535 and live PROM matched the fixed profile.
  Initial SS0=51144015/SS1=1 passed; MANUAL_U was confirmed. There was no
  automatic start or automatic profile refresh.
- `PATCH_TRANSACTION` records result0, containment0, started1, quiesced1,
  fault0, retained0, maps0, FLR1 and safe1. Post-FLR and all display-restoration
  observations retain SS0=88888888/SS1=8. No second reset was initiated by the EFI.
- The one-child display chain recovered, all Start operations returned success,
  and the final display result is status0/touched1/restored1. Framebuffer
  readback matched all9216 pixels with zero mismatches. Physical visual
  confirmation was not separately reported by the user.
- Windows handoff intent records reboot0 and closed reports. Its logged time is
  18:02:41 local; Windows reports boot at18:02:44.5 America/New_York. The current
  Windows device and compute result provide OS observation after that handoff.
- Post-compute GPU StatusOK/error0,37C,10858MiB free VRAM; no nvlddmkm
  Error/Critical events were found since this Windows boot.

The verified USB image remains SHA256
`c13c39eb98bae5b836c80e1a4e5d7f84c05ad910f35b5b62f2ad97311052fab4`.
GOP.TXT and UNLOCK.TXT were copied and hash checked privately under
`data/uefi-probe/3080ti-usb/captures-20261025-181102-fd129b01389b4e22837518c2e0e68593/RTX-UNLOCK/RUN01/`.
The post-compute record is `data/uefi-probe/3080ti-usb/unlocked-compute-run01.private.json`;
the original pre-attempt baseline remains unchanged. Raw GPU identities, firmware
and boot data stay ignored. [Curated result and provenance hashes](verification/rtx3080ti-manual-unlock-result-20261025.json).

## Effective startup state

This validates one manual3080Ti boot and its current Windows session.
Automatic3080Ti startup is not installed. Windows Boot Manager remains the
preserved default policy; the original3060 internal EFI and restore path remain
separate. Do not rerun an unlock in this firmware session or select the3060 EFI
with the3080Ti installed. Repeated boots, sleep/resume, driver/Windows updates,
long-duration stability and post-unlock LLM speed remain unvalidated. No model,
driver, permanent boot entry or Linux AMD setting was changed during verification.
