# RTX 3080 10 GB manual Windows unlock result — October 25, 2026

**Manual v2 RUN04 succeeded.** The card passed fixed-board, live-PROM and
cold-state checks, received U, completed one unlock transaction and FLR with safe
cleanup, restored display output and handed off to the current Windows session.
The same compute executable measured FP16 +88.34% and BF16 +88.93% against the
saved pre-attempt baseline. FP32 is essentially unchanged.

| Mode | Before, TFLOPS | After RUN04, TFLOPS | Change |
|---|---:|---:|---:|
| FP32 pedantic | 23.142982 | 23.155024 | +0.05% |
| FP16 tensor, FP32 accumulation | 60.196178 | 113.374534 | +88.34% |
| BF16 tensor, FP32 accumulation | 60.052674 | 113.455387 | +88.93% |

Both runs use the retained sm86 executable, 4096-square GEMM, CUDA13.3/cuBLAS13.6,
two-second warmup and30 timed samples. All three endpoint reference checks pass.
The executable SHA256 is
`aa8cca683335ee33ab000829b0aa47eceb7de04281eec39d3d36103b2338916e`.
Driver610.88,320W cap, board identity and VBIOS are unchanged. No clocks or model
profiles were changed. Background load and thermals were not controlled in an
A/B/A; these short compute tests do not establish prolonged stability or full
numerical correctness. LLM token rates have not been retested after unlocking.

## Physical evidence

- Manual U was confirmed once. Both live-PROM comparisons matched, and preflight
  passed using the exact state derived from the prior untouched refusal. The
  original board diagnostic evidence remains unchanged.
- The transaction records result0, containment0, started1, quiesced1, fault0,
  retained0, maps0, FLR1 and safe1. Exactly one PCIe FLR is logged. The unlocked
  state persists through all recorded display recovery and console-output checks.
- Final display status0/touched1/restored1. All9216 framebuffer readback pixels
  match, with zero mismatches. The user has not separately reported the visual
  color marker; readback is the recorded display check.
- Windows handoff logs reboot0 after the21:13:40 local report-complete marker.
  Windows reports boot at21:13:42.5 America/New_York. Current GPU health and compute
  provide OS observation after that handoff.
- Post-compute GPU StatusOK/error0,36C and9248MiB free VRAM. No nvlddmkm
  Error/Critical events were found since this Windows boot after compute.

The USB still matches the verified v2 EFI SHA256
`c5a04df68ed1eeb4fc9e427f0a70a8c0845aa01f1d44168cd33e750a6fc80a10`.
All24 package files and20 retained capture files independently match their
source/private copies. Raw logs, UUIDs, PROM data, exact board bindings and
generated headers remain private and ignored by Git.
[Curated result](verification/rtx3080-10gb-unlock-result-20261025.json).

## Current session and future starts

**The current session is unlocked. Do not run the unlock again in this firmware
session.** Future fresh starts still use the manual16GB Kingston DataTraveler2.0,
label RTX3080_10G. No automatic/internal3080 startup is installed. The3060 NVMe
payload remains removed, and the other two card-specific USBs are unchanged.

This verifies one successful v2 boot. Repeated starts, further initial-state
variation, sleep/resume, Windows/driver updates and prolonged stability remain
untested. A future unknown initial state must still refuse. No VBIOS flash,
permanent boot entry, driver, power cap, model guard or Linux AMD setting changed.
The model router retains its12GB admission scope; this result alone does not
validate its existing maximum-context profiles on the10GB card.
