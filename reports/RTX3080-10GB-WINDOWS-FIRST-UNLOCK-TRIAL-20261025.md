# RTX 3080 10 GB first Windows unlock trial — October 25, 2026

**Result update: manual v2 RUN04 succeeded. Current session is unlocked; do not repeat.**
[Read the verified physical result](RTX3080-10GB-WINDOWS-UNLOCK-RESULT-20261025.md).
The preparation/refusal text below is historical.

**Latest: first image refused before U or GPU mutation; corrected v2 is staged.**
[Use current v2 instructions and result](RTX3080-10GB-FIRST-BOOT-REFUSAL-20261025.md).
Older readiness/hash statements below describe the prior image.

**Staged and independently verified:**24 package files and16 retained capture
files pass hash checks. Manual EFI SHA256:
`bb850c2144d7a22d5934823732e0ff315f2ba823a979f873aaa3b6561b0f9075`.
Fresh platform prerequisites pass; no physical3080 unlock has run.
[Curated preparation verification](verification/rtx3080-10gb-manual-preparation-20261025.json).

This is a separate fixed-board manual trial for the captured 2206 RTX 3080 10 GB.
Its board and read-only ownership captures passed. A successful offline build is
not proof of physical unlock, display recovery, stability or speed improvement.

Use only the **16 GB Kingston DataTraveler 2.0**, labeled **RTX3080_10G**.
The other drives are dedicated to the 3060 and 3080 Ti. The current staging
status and reviewed EFI hash are recorded in the project README and verification
summary; do not boot an unverified or partly copied candidate.

The candidate uses its own PROM, exact captured initial selectors and five driver
metadata profiles. Its NVIDIA GOP is 177920 bytes, binding version 0x60009,
with start/stop RVAs 0x774/0x698. The four motherboard display roles retain their
own captured metadata. Metadata and method offsets are not driver-code hashes.
The fixed cold check and firmware transaction remain pinned and unchanged.
Zero, altered or already-unlocked initial states must refuse. No automatic,
production, SSD or profile-refresh execution mode is enabled.

Before staging, verify Secure Boot off, C: FullyDecrypted/BitLocker protection
Off, Windows Boot Manager first with no pending one-time entry, and the previous
3060 NVMe removal still intact. Preserve USB captures and back up collisions.

## First manual boot after staging is verified

1. Save work, shut down fully, start and press **F8**.
2. Choose **UEFI Kingston DataTraveler 2.0**, the **16 GB RTX3080_10G** drive.
   Keep the display connected to the 3080. Disconnect the other USBs if ambiguous.
3. Wait for fixed-board, live-PROM, cold-state and display preflight. Press **U
   once** only if the image offers it after passing those checks. Esc or 30
   seconds cancels. If refused, return to Windows and report it without bypassing.
4. After U the screen may go black. Allow up to **10 minutes** for Windows to
   start directly in the same boot. Do not restart after success or run another
   unlock in that firmware session.
5. If Windows does not appear within 10 minutes, fully power off, remove the USB,
   and select Windows Boot Manager on the next start. Do not retry in the same
   firmware session.
6. In Windows, leave the USB connected and report whether U was pressed and
   Windows started directly. The next GOP.TXT/UNLOCK.TXT, GPU health and identical
   compute executable must establish the result.

The saved pre-project-unlock GEMM baseline is FP32 23.142982, FP16 60.196178 and
BF16 60.052674 TFLOPS. These are synthetic compute results, not LLM token rates.
No improvement is claimed before physical logs and a same-executable comparison.
This preparation does not flash the VBIOS, configure internal startup, change
the driver/power cap or alter the model router's 12 GB admission guards.

The first staging attempt safely refused before USB writes because PowerShell7
materialized an ISO timestamp as DateTime and string parsing lost its UTC Kind.
The shared prerequisite helper now preserves typed UTC/local/offset timestamps,
rejects ambiguous values and passes JSON-roundtrip tests on PowerShell5.1/7.6.
Freshness and security limits were retained; the successful staging followed
those checks. This helper fix changes no EFI or GPU transaction source.
