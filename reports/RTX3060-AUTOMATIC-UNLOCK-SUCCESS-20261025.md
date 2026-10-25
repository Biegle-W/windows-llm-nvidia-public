# RTX 3060 automatic internal unlock verified — October 25, 2026

**Later repeat-boot finding:** RUN0003 returned to the original nonzero startup
pair and the zero-only profile refused. Windows is stock again. A
[two-pair correction](RTX3060-AUTOMATIC-PAIRED-STARTUP-20261025.md) is now installed,
with physical verification pending. The earlier RUN0001 success remains valid
for that boot and does not establish repeat reliability.

**The corrected internal EFI unlocked the RTX 3060 automatically and handed off
to Windows successfully.** RUN0001 records automatic start and a successful
transaction; Windows compute throughput confirms the unlocked state.

The installed EFI SHA256 is
`f837ed1db52138125fe530460a546f9f9fdda122d76b13ef862a7036524516ca`.
It ran from the dedicated internal partition. The initial 0/0 selector check,
remaining preflight and live PROM hash checks passed. No U confirmation was used.

The hash-verified GOP/UNLOCK logs show:

- `AUTO_START`: all preflight checks passed, proceeding once.
- Transaction result0, containment0, started1/quiesced1, fault0, retained0,
  maps0, FLR1, safe1.
- Unlocked SS0=`88888888`, SS1=`00000008`, retained through display recovery,
  mode changes, drawing, readback and final output.
- Display restored, final status0; 9216 framebuffer pixels checked with zero
  mismatches; internal Windows Boot Manager started without rebooting again.

Windows boot time was 03:24:10 on October 25, 2026, America/New_York. Windows
reports RTX3060 StatusOK/error0, driver610.88 and the unchanged170W limit. No
nvlddmkm Error/Critical events were found since this boot, including the check
after the short compute benchmark. Post-benchmark temperature was44C.

## Identical-executable compute verification

| Mode | Saved stock TFLOPS | Automatic-unlocked TFLOPS | Difference |
|---|---:|---:|---:|
| FP32 pedantic | 8.643 | 8.587 | -0.6% |
| FP16 Tensor / FP32 accumulate | 26.835 | 50.534 | +88.3% |
| BF16 Tensor / FP32 accumulate | 26.788 | 50.620 | +89.0% |

The same retained executable uses 4096-square GEMM, two seconds warm-up and30
samples per mode. First/last output-element reference checks passed. Results
match the earlier successful manual unlock's approximately50.7TFLOPS floating
point throughput. This does not imply an89% increase for quantized LLM serving;
the [existing LLM measurements and kernel limits](RTX3060-UNLOCKED-LLM-20261025.md)
still apply. No LLM tests were rerun for this boot-verification task.

The new logs were copied and independently hash-checked under ignored local
capture state. Original RUN0000 evidence remains unchanged for reproducible
startup-profile builds. The temporary U: inspection mount was removed. No boot
configuration, partitions, payload or GPU settings were changed during this check;
no second unlock was attempted in Windows.

This validates one successful automatic boot after the profile correction. A
later boot can still refuse unexpected hardware/firmware state. Repeated cold
starts, sleep/resume, Windows/NVIDIA updates and the future3080Ti remain untested.
Keep the exact-board profile and recovery entry. F8 -> Windows Boot Manager
bypasses the application; Esc remains available during the six-second start gate.

[Sanitized verification](verification/rtx3060-automatic-unlock-success-20261025.json).
