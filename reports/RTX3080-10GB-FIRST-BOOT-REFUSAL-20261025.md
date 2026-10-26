# RTX 3080 10 GB first-boot refusal and v2 correction — October 25, 2026

**Result update: manual v2 RUN04 succeeded. Current session is unlocked; do not repeat.**
[Read the verified physical result](RTX3080-10GB-WINDOWS-UNLOCK-RESULT-20261025.md).
The preparation/refusal text below is historical.

**RUN03 did not unlock the card.** The image refused during unlock preflight
with EFI_NOT_READY and touched=0. Manual U confirmation was never reached;
no unlock transaction, display teardown or FLR was attempted. Its exact initial
selector differed from the earlier read-only board capture. Other values in the
logged cold-state tuple match the expected board state. This is not an unlock
or a physical test of the GPU firmware transaction.

The same compute executable confirms near-baseline performance after refusal:

| Mode | Original TFLOPS | After refusal | Change |
|---|---:|---:|---:|
| FP32 | 23.142982 | 23.103147 | -0.17% |
| FP16 | 60.196178 | 60.268402 | +0.12% |
| BF16 | 60.052674 | 60.626983 | +0.96% |

All three reference checks pass. These synthetic GEMM measurements are not LLM
token rates or an unlock gain. GPU OK/error0, no NVIDIA Error/Critical events
found since this boot after compute; driver610.88 and320W cap remain unchanged.

**Corrected v2 is staged on the16GB Kingston DataTraveler2.0 / RTX3080_10G.**
All24 package files and18 retained captures independently verify. The first image
and colliding files were backed up. Its EFI SHA256 is
`c5a04df68ed1eeb4fc9e427f0a70a8c0845aa01f1d44168cd33e750a6fc80a10`.

The original diagnostic profile is retained unchanged. A separately derived
header accepts only the exact new tuple from the untouched RUN03 preflight logs,
including board/slot binding and an untouched refusal in the paired GOP log.
It changes only the fixed expected initial selector. The original PROM hash,
memory-layout, GFW/PLM, PCI and display-driver checks remain enforced at runtime;
the firmware transaction and actual ColdCheck code remain unchanged. Arbitrary,
zero, mixed, previously expected or already-unlocked selector states are refused.
If a future boot differs again, the image must refuse; further boot variability
is not established by these two observations.

Checks pass:23 Python policy tests including six new refusal-evidence methods;
20 actual ColdCheck scenarios including rejection of the earlier expected value;
eight upstream host suites/eight manual flows/31 display rejoin/22 simulated
unlock/26 driver-policy scenarios. The added tests reject altered/ambiguous
samples, wrong card/slot, mutation/confirmation markers and touched evidence.
Host tests do not prove physical unlock or display recovery.

Fresh administrator checks confirm Secure Boot off, C: FullyDecrypted/protection
Off, Windows-first boot and removed3060 NVMe payload/entry. No internal startup,
driver, power cap, model profile or other card's USB was changed.

Next full shutdown, F8 ->the16GB Kingston2.0 / RTX3080_10G. Press **U once only
after preflight passes**. Esc/30sec cancels. Allow up to10 minutes for Windows to
start directly. Do not repeat in the same firmware session. If Windows does not
appear, fully power off, remove USB and boot Windows normally. Leave the USB
connected when reporting back. No successful3080 unlock is claimed yet.
[Verification](verification/rtx3080-10gb-refused-run03-v2-20261025.json).
