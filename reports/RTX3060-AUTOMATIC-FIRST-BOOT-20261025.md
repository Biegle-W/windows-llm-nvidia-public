# RTX 3060 first automatic boot verification — October 25, 2026

Follow-up: a [corrected zero-state automatic profile](RTX3060-AUTOMATIC-ZERO-STARTUP-FIX-20261025.md)
is now installed and awaiting its own boot test. This report preserves the original
RUN0000 failure and stock compute measurements.

**The internal EFI ran, but the unlock did not execute. Windows currently has
stock FP16/BF16 throughput.** The new internal `RUN0000` log records refusal at
`unlock-preflight`, status `0x8000000000000006` (EFI_NOT_READY), `touched=0`.
No automatic start, unlock transaction or FLR followed the refusal.

## Evidence and diagnosis

The exact-GUID internal FAT32 ESP contains the installed EFI with SHA256
`7adcaa078172121a39861bf388596f161aec50ec336af57dd9f9821834cb77d8`.
The automatic entry remains first and original Windows Boot Manager second.
Its GOP and unlock logs were copied and independently hash-checked; raw logs,
firmware identifiers and paths remain in ignored local state. Windows boot time
was 03:05:45 on October 25, 2026, America/New_York.

The display preparation recognized the same single vendor child and five driver
roles. The fixed profile's earlier probe captured SS0=`70520074`, SS1=`00000005`.
This boot reported **SS0=`00000000`, SS1=`00000000`**, with the logged chip, PLM,
GFW fields and WPR2_HI matching their earlier values. The actual `ColdCheck` in
the pinned unlock source requires exact initial selector values, so it returns
EFI_NOT_READY on this mismatch. This is an observed guard refusal, not evidence
of failed firmware execution after an unlock attempt.

The mismatch happens before later layout/PROM checks complete. Do not infer that
all remaining preflight checks would pass after changing the initial selectors.
The transaction and startup checks were not changed or bypassed during this
verification. Correcting the startup profile needs separate review and a further
physical boot test; automatic unlock must not be marked successful yet.

## Same-executable compute check

| Mode | Saved stock TFLOPS | Current automatic-boot TFLOPS | Prior successful manual TFLOPS |
|---|---:|---:|---:|
| FP32 pedantic | 8.643 | 8.591 | 8.540 |
| FP16 Tensor / FP32 accumulate | 26.835 | 26.786 | 50.724 |
| BF16 Tensor / FP32 accumulate | 26.788 | 26.806 | 50.591 |

The identical retained executable uses 4096-square GEMM, two seconds warm-up
and 30 samples per mode. Its first/last output-element checks passed. Driver610.88
and the170W limit remain unchanged. This short benchmark confirms stock-like
floating-point performance in the observed boot; it is not broad numerical or
long-run stability testing. Existing LLM tests were not rerun because this check
already establishes that the unlocked state is absent.

Windows reports RTX3060 StatusOK/error0, and no nvlddmkm Error/Critical events
were found since this boot at inspection. The temporary U: capture mount was
removed. Partition numbering changed across reboot: the same dedicated GUID is
now number4 rather than the original number5. The first read-only capture refused
the stale number; the successful capture located and verified the exact GUID and
disk identity. Private bookkeeping was corrected without changing partitions,
boot priority, payload or GPU state.

[Sanitized evidence](verification/rtx3060-automatic-first-boot-20261025.json).
