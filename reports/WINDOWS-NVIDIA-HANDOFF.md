# Windows NVIDIA handoff â€” 23 October 2026

Automatic internal boot is prepared but not installed: [design, recovery and OS-update behavior](RTX3060-AUTOMATIC-INTERNAL-BOOT-20261025.md).
`prepare_uefi_3060_automatic.py` and `Install-RTX3060AutomaticUnlock.ps1` pass14
host automatic/source cases and13 installer policy checks. Preview under ignored
`data/uefi-probe/internal-startup/preview-v2/` is bound to a synthetic partition
GUID and MUST NOT be installed. Existing ESP free space is64106496 bytes, too
small for firmware assets. Explicit approval is pending for shrinking C: by
536870912 bytes and creating a new512MiB FAT32 ESP; no partition/boot order has
changed. After approval, run the installer elevated with Mode Install and
AllowResizeCBy512MiB. It compiles against the actual new ESP GUID and verifies
files before promoting a separate firmware entry, preserving Windows Boot Manager
as fallback. State/backups are private under `data/uefi-probe/internal-startup/`.
The tested manual USB and current unlocked Windows boot remain unchanged.

**Latest October25 result: first physical unlock succeeded in Windows.**
[Execution and identical-executable comparison](RTX3060-WINDOWS-UNLOCK-RESULT-20261025.md).
RUN01 logs are hash-verified in ignored `data/uefi-probe/captures/20261025-UNLOCK-RUN01/`.
One FLR, maps0/retained0/fault0/safe1, SS0=88888888/SS1=8, display restoration,
resolution cycle and9216-pixel zero-mismatch readback pass; Windows Boot Manager
starts without a reset. Driver610.88 recognizes the3060 with StatusOK/error0;
no nvlddmkm Error/Critical events since this boot were found at inspection.
At unchanged170W, the same short CUDA GEMM executable measures FP16
26.835->50.724TFLOPS (+89.0%), BF16 26.788->50.591 (+88.9%), FP32 8.643->8.540.
This is one boot and one short sample per arm; no LLM, INT8, broad numerical,
long-run, repeat-boot or sleep/resume validation. USB remains manual-only with no
ESP/BCD/boot-order/driver/VBIOS change. Do not rerun unlock in this boot. Preserve
prior build/profile flags as historical; record physical validation separately.
Earlier preparation notes below precede this successful attempt.

Current first-trial preparation, October25: the ownership capture passed but
rejects the generic two-child design. [Single-child adaptation and manual trial](RTX3060-WINDOWS-FIRST-UNLOCK-TRIAL.md)
is built under ignored `data/uefi-probe/windows3060-single-child-20261025-v3/`.
The source override changes only the display path, binds exact2503/407b1458/BDF
and five driver metadata/method-offset profiles, and retains the original firmware
transaction and manual U gate.31 full display,22 simulated unlock/rejoin and26
policy tests pass, including wrong-BDF/extra-child refusal and real-build
preprocessor verification. Driver code hashes were not captured; metadata checks
and host mocks are not hardware validation. The Kingston fallback is now this
manual candidate, SHA256 `61fa2b71d1332d4d6180610175955d3cad015420c41f393b7abea717507d09e1`,
with all five assets verified. Both earlier RUN00 captures and a complete
pre-trial USB backup remain private/preserved. No unlock has executed. Next boot
is the first manual attempt: U only after preflight, Windows in the same boot;
if stopped or no Windows within10 minutes, fully power off/remove USB/boot stock.
Inspect new `RTX-UNLOCK/RUNnn/GOP.TXT` and any `UNLOCK.TXT` before measuring.
Do not reuse the unadapted candidate or replay an unlock in the same firmware session.

Latest October25: [manual Windows unlock preparation](RTX3060-WINDOWS-UNLOCK-PREPARATION.md)
is complete locally at ignored `data/uefi-probe/windows3060-unlock-20261025-v2/`.
Actual PROM FWSEC parsing, fuse/signature selection, DMA alignment, memory layout
and FRTS command encoding pass on CPU-owned copies. A fixed generated header
binds the manual candidate to2503/407b1458 and captured state; upstream core is
unchanged, no automatic/production/SSD/profile-refresh flags are enabled, and U
is always required. The eight-flow gate test and eight upstream host suites pass.
Secure Boot=false, C:FullyDecrypted, BitLocker:Off confirmed by admin query only.
The USB fallback is now the read-only ownership probe, SHA256
`58f4d6beb444d423a8509dd4d1cdbb7a2e10a425e51ae2e65f2cceaa011342b8`.
Read `RTX-UNLOCK/RUNnn/GOP.TXT` after the next boot; review its topology before
deploying the candidate. All18 original USB files including first RUN00 were
backed up and retained except the intentionally replaced fallback EFI. No unlock
candidate or firmware assets are on USB. No GPU unlock, ESP/BCD or boot-variable
change occurred. Source profile approval flags remain false. Stock short CUDA
baseline FP16/BF16 FP32-accumulate is26.835/26.788TFLOPS; no unlocked result exists.

Read-only UEFI probe prepared October25: [USB instructions and scope](RTX3060-READONLY-UEFI-PROBE.md).
Pinned5c076dc/LLVM20.1.8/Bun1.4.4 EFI is14848 bytes, SHA256
`ae7b5cdd1cc579fc516ebda68c9d438d433697fb78d151304d56a2cbca41785a`.
Upstream and exact2503/407b1458 mocks,11 parser tests and3 negative PE cases pass.
Package/ZIP are ignored under `data/uefi-probe/`; raw captures must also remain
private. The USB is now staged as FAT32/UEFI_PROBE after explicit user approval;
all14 restored files passed independent SHA256 checks. Physical RUN00 capture
passed: exact2503/407b1458 identity,16 valid register reads, verified1MiB PROM and
157696-byte ROM image. All four files are backed up and hash-checked in ignored
`data/uefi-probe/captures/20261025-RUN00/`; never publish the raw capture or profile.
The strict parser sets probeComplete=true but retains firmwareCompatible=false
and unlockApproved=false. Observed SS0=70520074 / SS1=5; selector policy and
complete GOP ownership require review. Windows recognizes the3060/610.88 after
reboot. Unlock and performance remain pending.
[Staging proof](verification/rtx3060-uefi-usb-stage-20261025.json),
[physical capture](verification/rtx3060-uefi-physical-capture-20261025.json).

Repository organization: private `windows-llm-nvidia`, sanitized
`windows-llm-nvidia-public`; retired source/documentation is indexed in
[archives](../archives/README.md). Ubuntu AMD repositories remain independent.
GitHub renaming does not change local installation paths, API ports, selected
models, contexts, credentials or memory guards.


Windows is independent: RTX 3060 12 GB / i5-13600KF /16 GB DDR5 at 6000 MT/s, NVIDIA 610.88, llama.cpp b11630 CUDA 13.4 (`6868a52cb`). Linux remains its separate i9/64-GB/dual-7900-XTX HIP build; do not apply its policies or edit its runtime files here.

Current default: **Ornith 1.5 35B-A3B (IQ2_S) | 32K | GPU + RAM**, API ID `Ornith-1.5-35B-A3B-IQ2_S`, weights in project `models/`. Source registry retains fit on / GPU layers auto / fit-target2816 / no-host true. Q8 KV, FA on, one slot, batch512/ubatch128, thinking off, no speculation. This is not full GPU: normal buffers were 7,840.74 MiB GPU /2,643.67 MiB host. Fresh minimums:4 GiB RAM available /16 GiB commit headroom /9,728 MiB actual free VRAM. Never kill unrelated apps to satisfy these checks.

Selected decode samples: **48.24 /44.29 t/s**; chat, streaming, tool round trip and **8,080-token input retrieval** pass at32K allocation. Normal API streaming leaves1,571MiB whole-card VRAM /1.19GiB available RAM; sampled generation dipped to1,336MiB VRAM. Larger memory targets are not guaranteed real reserves. Early Ornith62â€“67t/s and Empero60â€“64t/s results used less desktop headroom; do not label them current default speed. Low-bit trials do not prove general quality superiority.

September Empero Qwen3.8 35B-A3B Distill IQ2_M remains in project `models/`, outside the active catalog. The retired Qwen3.5 9B GGUF was deleted at the user's request on October 23, freeing 5.56 GiB; do not assume its old path exists. Empero is a community Qwen3.8-teacher distillation into Qwen3.6's MoE architecture, not an official small Qwen3.8 release. It passed functional checks but had tight memory margins. Ornith and Empero weights were preserved. Strata stays disabled.

Visible `Start Local LLM.cmd` owns the API at `http://127.0.0.1:10000/v1`; real key remains private in data/credentials, client route LLAMA_CPP_API_KEY. Saved DSH default/catalog updated; Desktop GUI/SDK unverified because executable unavailable. Tailscale forwards only10000; IPv4/MagicDNS host self-checks pass, remote peer untested. LAN was not changed. Actual addresses stay in ignored state.

README is the sole root instruction file. Keep private/public GitHub current with sanitized Windows exports; preserve Linux and all dated historical evidence. Warn near70% of session context using current usage when available. Do not create root AGENTS.md. Stop the owned backend before test_models.py; its low-RAM guard only stops its own test worker. Thermal coverage is short generation GPU samples plus snapshots, not whole-run/CPU peaks.

See [current methods and limits](WINDOWS-MOE-MODELS-20261023.md). No Shared D: drive is attached; this handoff does not overwrite Linux's.

## Later October 23 candidate tests

LFM2.5 24B-A2B and official Qwen3.8 27B, both UD-IQ3_XXS, are verified in project `models/`. Separate8K profiles passed all five checks at~6K input; native total generation78.24/85.04t/s LFM (reasoning only at128-token cap),4.97/5.59t/s Qwen (thinking off). LFM's short visible marker arrived1.828s versus Qwen0.922s. Mixed GPU/RAM buffers:7426/1315MiB LFM,7140/2873MiB Qwen. See [current trial evidence](WINDOWS-LFM-QWEN-TESTS-20261023.md); no model-quality ranking is established.

Ornith's default/catalog and production limits are unchanged. Perplexity, the Quest client and Quest service were temporarily paused with explicit approval and restored; user app state is private. Production restart failed memory admission, so the owned backend is stopped at this snapshot. Do not silently lower its limits. No Linux runtime/profile or network settings were changed.

## Directory consolidation â€” later October 23

All four inference GGUFs are in project `models/`; source paths are project-relative. Candidate profiles are in `config/test-profiles-lfm-qwen-20261023.json`. Regenerate catalogs after moving the project. Retired Strata source is in `archives/2026-10-23-strata/`; inactive runtimes are in ignored `archive/retired-windows-20261023/runtimes/`. Reports and prior benchmarks remain preserved; no inference rerun. See [cleanup record](WINDOWS-CLEANUP-20261023.md).

## Current: model router â€” later October 23

The authenticated API on10000 now lists all four downloaded models and selects
by the OpenAI request's `model` field. Ornith remains default at32K; LFM, Qwen27B
and Empero have selectable8K profiles. Earlier test-only/stopped-backend snapshots
above are historical. The lightweight router is running idle without loaded
weights; its single private worker on10001 loads on demand and unloads before a
switch. Admission uses each model's own unchanged limits, plus1024MiB loaded
actual free VRAM and the0.75GiB/five-second RAM guard. Resource refusal returns503;
it never silently substitutes another model. An in-progress stream holds the
switch lock; another request returns503 `router_busy`.

DSH's installed SDK streamed through all four; its saved selector/catalog and
Ornith default are verified. The real API passed tools/JSON, bad-key/unknown-model
checks and unloading. Global thinking suppression was removed for LFM's required
reasoning template. Reopen DSH if its selector is cached; GUI/remote-peer/full
context/throughput tests were not repeated. Perplexity and Quest were terminated
as requested; Quest service remains stopped without a startup-policy change.
Chrome was reopened with session restoration requested after testing.

See [router API and proof](WINDOWS-MODEL-ROUTER-20261023.md). Keep both repositories
current, Windows-only exports sanitized, and Linux files unchanged.

## Current: optional RAM context â€” later October 23

Seven router/DSH IDs now reuse four files. Three new MoE alternatives put Q8 KV
in CPU RAM: Ornith128K, LFM128K, Empero64K. Original four profiles/default/limits
are unchanged; dense Qwen27B is unchanged. Native CPU allocation is verified,
all three pass functional tests and retrieval beyond their old allocations.
Full windows are untested; preserve the physical-RAM admission and continuous
guard. [Methods and proof](WINDOWS-MOE-RAM-CONTEXT-20261023.md).

## Current: one setting per model â€” later October 23

Exactly four canonical IDs remain: Ornith128K (default), LFM128K, Qwen27B8K and
Empero64K. They use the previously verified largest configurations. Three MoEs
keep Q8 KV in RAM; Qwen27B keeps GPU KV. Old suffixed RAM IDs and smaller active
alternatives are removed. Dated test profiles moved into retired/20261023/config.
Preserve their measured fitting/resource limits. Reopen DSH to refresh its four
entries. No inference rerun; weights/chats/history retained. README is current.

## Current: Qwen64K for harness input â€” later October23

Qwen27B now has one64K/Q8-CPU-KV profile, replacing8K in place. Chat/SSE/tools and24,460-input retrieval pass; installed SDK passed16,310-input system instructions/tools with a tool-result follow-up. Full64K/GUI/remote-peer are untested. Fresh6GiB RAM/20GiB commit/9216MiB VRAM, fit-target2816/no-host; loaded1024MiB and existing continuous RAM guard retained. Four profiles and Ornith128K default remain. Large dense-model prefill takes minutes. See [current proof](WINDOWS-QWEN-CONTEXT-20261023.md).
