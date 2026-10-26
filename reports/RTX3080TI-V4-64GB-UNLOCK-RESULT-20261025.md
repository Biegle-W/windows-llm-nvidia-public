# RTX 3080 Ti v4 unlock and 64 GB RAM verification — October 25, 2026

**The current Windows session is unlocked.** Dedicated4GB USB v4 RUN01 passed
preflight and live-PROM checks, received U, completed one safe transaction/FLR,
restored display output and started Windows directly.

| Compute mode | Saved stock TFLOPS | Current unlocked TFLOPS | Change |
|---|---:|---:|---:|
| FP32 pedantic | 25.682687 | 25.281169 | -1.56% |
| FP16 tensor, FP32 accumulation | 70.349903 | 126.501152 | +79.82% |
| BF16 tensor, FP32 accumulation | 70.363161 | 130.344076 | +85.24% |

All three endpoint reference checks pass. The same sm86 executable uses
4096-square GEMM, two-second warmup and30 samples, CUDA13.3/cuBLAS13.6.
Executable SHA256:
`aa8cca683335ee33ab000829b0aa47eceb7de04281eec39d3d36103b2338916e`.
The GPU identity, VBIOS, driver610.88 and350W cap match the original baseline.
System RAM changed from16GB to64GB between the original baseline and this run,
and background load/clocks/thermals are not controlled A/B/A. The small FP32
change is not evidence of an FP32 unlock or regression caused by this patch.
These are short compute measurements; LLM rates and prolonged stability remain
untested in the new configuration.

## Verified hardware

- RTX3080Ti,12288MiB VRAM.
- Four16GiB Corsair DIMMs,64GiB installed; Windows reports about63.76GiB usable.
- All four report configured speed4200MT/s. The previous6000MT/s documentation
  describes the older16GB configuration, not this four-DIMM setup.
- i5-13600KF and the existing Windows NVIDIA runtime/model configuration remain.
  No memory timing, XMP, driver, power cap or model-profile change was made here.

## Physical evidence and health

Manual U was confirmed once. Both live-PROM comparisons matched. Transaction
result0/containment0/started1/quiesced1/fault0/retained0/maps0/FLR1/safe1, with
exactly one logged PCIe FLR. The unlocked state remains through all display and
console-output observations. FULL_FINAL status0/touched1/restored1 and all9216
framebuffer readback pixels match with zero mismatches. The user has not separately
confirmed the visual marker; framebuffer readback is the recorded check.

Report-complete time21:44:08 precedes Windows boot21:44:11.5 America/New_York;
handoff records reboot0. Current device health and compute supply OS observation.
Post-compute GPU OK/error0,42C,11106MiB free; no NVIDIA Error/Critical events found
since this boot. USB v4 EFI SHA256 remains
`4649c0ed12800ce5c8f6988f637bf5319809c4153d2f1249e0107abc7571f632`.
All24 package files and four retained capture files independently verify.
[Curated result](verification/rtx3080ti-v4-64gb-unlock-result-20261025.json).

**Do not repeat the unlock in this firmware session.** Future fresh starts remain
manual using the4GB General USB Flash Disk / RTX3080TI. No automatic/internal Ti
startup is installed. The3060 NVMe payload remains removed and the other two USBs
are unchanged. This verifies one successful v4 boot; repeated v4 starts, further
initial-state variation, sleep/resume, updates and prolonged stability remain
unvalidated. Raw firmware/captures, UUIDs and private board bindings stay ignored.
