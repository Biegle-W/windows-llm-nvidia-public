# RTX 3060 repeat-boot finding and paired startup correction — October 25, 2026

**The paired startup EFI is physically verified in RUN0004.** It accepted the
70520074/5 startup pair, passed preflight/PROM checks, ran automatically once,
completed one FLR with quiesced1/maps0/retained0/fault0/safe1, restored the display,
passed9216-pixel readback with zero mismatches and handed off to Windows without
a second reboot. Captured logs were copied and hash-verified; EFI hash matches
the installed paired build. Windows boot time was13:01:18 on October25,2026,
America/New_York. RTX3060 StatusOK/error0; no NVIDIA Error/Critical events found
since boot after the benchmark. Driver610.88/170W unchanged; post-test42C.

| Same executable | Saved stock TFLOPS | Paired automatic TFLOPS | Difference |
|---|---:|---:|---:|
| FP32 pedantic | 8.643 | 8.778 | +1.6% |
| FP16 Tensor / FP32 accumulate | 26.835 | 50.459 | +88.0% |
| BF16 Tensor / FP32 accumulate | 26.788 | 50.792 | +89.6% |

The4096-square/2-second-warmup/30-sample benchmark's endpoint checks pass. No LLM
benchmark was rerun. Temporary U: was removed; no boot/partition/payload changes
or second runtime unlock were made during verification. This validates one boot
of the paired build with the nonzero pair. Its zero branch has CPU tests and a
prior successful automatic zero-only boot, but has not yet been physically
observed under this paired binary. Repeated starts, sleep/resume and updates
remain unvalidated. Earlier failure and installation details follow.

RUN0001 had automatically unlocked from initial SS0/SS1=0/0 and delivered about
50.6TFLOPS. At the later Windows boot, 10:42:26 America/New_York, RUN0003 instead
reported `70520074/00000005`, the exact pair seen before the successful manual
unlock. The zero-only guard returned EFI_NOT_READY at unlock-preflight, touched0;
no unlock transaction or FLR ran. The identical compute executable measured
FP16 26.879TFLOPS, BF16 26.838TFLOPS and FP32 8.524TFLOPS. Device StatusOK/error0,
no NVIDIA Error/Critical events found since boot at inspection, driver610.88 and
170W unchanged; post-test31C. This shows startup-state variation. A cold/warm
boot explanation has not been established by a controlled comparison.

## Exact complete pairs

The new automatic profile admits only:

| SS0 | SS1 | Successful execution evidence |
|---|---|---|
| `00000000` | `00000000` | Automatic RUN0001, safe transaction and about50.6TFLOPS |
| `70520074` | `00000005` | Prior manual RUN01, safe transaction and about50.7TFLOPS |

The components cannot be mixed. Unknown pairs and the already-unlocked
`88888888/00000008` pair are rejected. The builder verifies immutable RUN0000,
successful RUN0001 and manual RUN01 evidence, plus hash-verified RUN0003 refusal.
It patches only the initial-selector predicate in ColdCheck to call the fixed
coupled-pair matcher. Reversing that exact substitution must reproduce the pinned
original app source byte-for-byte after text decoding; unrelated edits stop the
build. Firmware transaction, ownership/containment/reset code and the tested
display adaptation retain their verified hashes. All remaining board/PROM,
firmware, memory-layout and startup checks remain active.

Thirteen evidence tests, 23 scenarios exercising the actual ColdCheck, 14
automatic-entry/internal-source scenarios, and EFI PE checks pass. The ColdCheck
tests accept each whole pair, reject both cross-pair combinations, unknown and
unlocked states, and confirm the other guards still reject bad firmware/layout.

New EFI SHA256:
`a57b0621ea87dd53c0a50aceca8de2467f2f4c3da1580f1fee230af6b8844394`.
All29 installed manifest files pass hash checks. The updater verified the same
disk/GUID/extent, retained a separate backup, preserved run logs, confirmed
unchanged partitions and firmware entries/order, and removed U:. No resize,
format, boot-order, driver or GPU-state change occurred. The previous EFI and
earlier success/failure captures remain available privately.

Private build: `data/uefi-probe/internal-startup/paired-startup-v1/`.
Immutable repeated-startup evidence: `paired-startup-repeat-evidence.private.json`
under that private state root. Keep original first-boot and successful RUN0001
capture metadata intact for future reproducible builds.

RUN0004 completes the first paired-payload boot verification. Keep checking new
logs if future startup behavior changes; long-term repeat reliability is not established. F8 ->
Windows Boot Manager bypasses it; the six-second Esc gate remains. No second
unlock should be executed in the current Windows session.

[Sanitized evidence](verification/rtx3060-automatic-paired-startup-20261025.json).
