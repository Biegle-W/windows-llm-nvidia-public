# Windows NVIDIA fallback handoff — October 25, 2026

The user is migrating the NVIDIA workstation to native Linux. Use the separate
[Linux-agent handoff](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/main/docs/MIGRATION-HANDOFF.md).
Windows remains independently recoverable; do not deploy Linux settings here.

Current Windows evidence: i5-13600KF, 64 GiB DDR5 at 4200 MT/s and RTX 3080 Ti
12 GB, driver 610.88. Ti v4 manual USB RUN01 succeeded; FP16 126.501152 and BF16
130.344076 TFLOPS with reference checks and display recovery. No simultaneous
Windows pair unlock, native Linux unlock, P2P or new LLM speed is verified.
[Ti result](RTX3080TI-V4-64GB-UNLOCK-RESULT-20261025.md).

The router remains single-card scoped, with four existing model settings and
allocated contexts unchanged: Ornith/LFM 128K, Qwen27B/Empero 64K, Q8 KV in RAM.
No weights, runtime, driver, client state, memory guard, listener or process was
changed by repository organization. [Current settings and dated speeds](../README.md).

Four dedicated USBs are preserved. The 8 GB SanDisk RTX3080PAIR contains only a
verified read-only pair probe. If continuing the Windows pair experiment, keep
the Ti primary/display, install both cards, F8 UEFI SanDisk, capture without U,
return to Windows and run Collect RTX3080 Dual Captures.cmd. Native Linux uses
its own pre-driver module rather than this Windows UEFI/GOP procedure.
[USB map](GPU-USB-ASSIGNMENTS-20261025.md), [pair procedure](RTX3080-DUAL-WINDOWS-PREPARATION-20261025.md).

The 3060 automatic NVMe unlock remains removed. Its empty 512 MiB ESP is retained;
Windows Boot Manager remains first. Do not restore it through an archive migration.
Single-card USB images cannot be chained or generalized to unknown topology.

Old overviews, retired automatic installers, retired Strata configurations and
older-hardware experiments are in private
[retired-llm-setting](https://github.com/Biegle-W/retired-llm-setting), with byte
hashes and original commits. Required current validation and tests remain here.
The two Windows repositories preserve their independent private/public histories.
The AMD repositories are now linux-llm-amd / linux-llm-amd-public. See the
[seven-repository map](REPOSITORY-MAP.md). Private raw captures and recovery state
remain ignored at their existing local paths; never export them to public.
