# Windows NVIDIA handoff — 23 October 2026

Windows is independent: RTX 3060 12 GB / i5-13600KF /16 GB DDR5 at 6000 MT/s, NVIDIA 610.88, llama.cpp b11630 CUDA 13.4 (`6868a52cb`). Linux remains its separate i9/64-GB/dual-7900-XTX HIP build; do not apply its policies or edit its runtime files here.

Current default: **Ornith 1.5 35B-A3B (IQ2_S) | 32K | GPU + RAM**, API ID `Ornith-1.5-35B-A3B-IQ2_S`, weights in project `models/`. Source registry retains fit on / GPU layers auto / fit-target2816 / no-host true. Q8 KV, FA on, one slot, batch512/ubatch128, thinking off, no speculation. This is not full GPU: normal buffers were 7,840.74 MiB GPU /2,643.67 MiB host. Fresh minimums:4 GiB RAM available /16 GiB commit headroom /9,728 MiB actual free VRAM. Never kill unrelated apps to satisfy these checks.

Selected decode samples: **48.24 /44.29 t/s**; chat, streaming, tool round trip and **8,080-token input retrieval** pass at32K allocation. Normal API streaming leaves1,571MiB whole-card VRAM /1.19GiB available RAM; sampled generation dipped to1,336MiB VRAM. Larger memory targets are not guaranteed real reserves. Early Ornith62–67t/s and Empero60–64t/s results used less desktop headroom; do not label them current default speed. Low-bit trials do not prove general quality superiority.

September Empero Qwen3.8 35B-A3B Distill IQ2_M remains in project `models/`, outside the active catalog. The retired Qwen3.5 9B GGUF was deleted at the user's request on October 23, freeing 5.56 GiB; do not assume its old path exists. Empero is a community Qwen3.8-teacher distillation into Qwen3.6's MoE architecture, not an official small Qwen3.8 release. It passed functional checks but had tight memory margins. Ornith and Empero weights were preserved. Strata stays disabled.

Visible `Start Local LLM.cmd` owns the API at `http://127.0.0.1:10000/v1`; real key remains private in data/credentials, client route LLAMA_CPP_API_KEY. Saved DSH default/catalog updated; Desktop GUI/SDK unverified because executable unavailable. Tailscale forwards only10000; IPv4/MagicDNS host self-checks pass, remote peer untested. LAN was not changed. Actual addresses stay in ignored state.

README is the sole root instruction file. Keep private/public GitHub current with sanitized Windows exports; preserve Linux and all dated historical evidence. Warn near70% of session context using current usage when available. Do not create root AGENTS.md. Stop the owned backend before test_models.py; its low-RAM guard only stops its own test worker. Thermal coverage is short generation GPU samples plus snapshots, not whole-run/CPU peaks.

See [current methods and limits](WINDOWS-MOE-MODELS-20261023.md). No Shared D: drive is attached; this handoff does not overwrite Linux's.

## Later October 23 candidate tests

LFM2.5 24B-A2B and official Qwen3.8 27B, both UD-IQ3_XXS, are verified in project `models/`. Separate8K profiles passed all five checks at~6K input; native total generation78.24/85.04t/s LFM (reasoning only at128-token cap),4.97/5.59t/s Qwen (thinking off). LFM's short visible marker arrived1.828s versus Qwen0.922s. Mixed GPU/RAM buffers:7426/1315MiB LFM,7140/2873MiB Qwen. See [current trial evidence](WINDOWS-LFM-QWEN-TESTS-20261023.md); no model-quality ranking is established.

Ornith's default/catalog and production limits are unchanged. Perplexity, the Quest client and Quest service were temporarily paused with explicit approval and restored; user app state is private. Production restart failed memory admission, so the owned backend is stopped at this snapshot. Do not silently lower its limits. No Linux runtime/profile or network settings were changed.

## Directory consolidation — later October 23

All four inference GGUFs are in project `models/`; source paths are project-relative. Candidate profiles are in `config/test-profiles-lfm-qwen-20261023.json`. Regenerate catalogs after moving the project. Retired Strata source is in `retired/20261023/`; inactive runtimes are in ignored `archive/retired-windows-20261023/runtimes/`. Reports and prior benchmarks remain preserved; no inference rerun. See [cleanup record](WINDOWS-CLEANUP-20261023.md).

## Current: model router — later October 23

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

## Current: optional RAM context — later October 23

Seven router/DSH IDs now reuse four files. Three new MoE alternatives put Q8 KV
in CPU RAM: Ornith128K, LFM128K, Empero64K. Original four profiles/default/limits
are unchanged; dense Qwen27B is unchanged. Native CPU allocation is verified,
all three pass functional tests and retrieval beyond their old allocations.
Full windows are untested; preserve the physical-RAM admission and continuous
guard. [Methods and proof](WINDOWS-MOE-RAM-CONTEXT-20261023.md).

## Current: one setting per model — later October 23

Exactly four canonical IDs remain: Ornith128K (default), LFM128K, Qwen27B8K and
Empero64K. They use the previously verified largest configurations. Three MoEs
keep Q8 KV in RAM; Qwen27B keeps GPU KV. Old suffixed RAM IDs and smaller active
alternatives are removed. Dated test profiles moved into retired/20261023/config.
Preserve their measured fitting/resource limits. Reopen DSH to refresh its four
entries. No inference rerun; weights/chats/history retained. README is current.

## Current: Qwen64K for harness input — later October23

Qwen27B now has one64K/Q8-CPU-KV profile, replacing8K in place. Chat/SSE/tools and24,460-input retrieval pass; installed SDK passed16,310-input system instructions/tools with a tool-result follow-up. Full64K/GUI/remote-peer are untested. Fresh6GiB RAM/20GiB commit/9216MiB VRAM, fit-target2816/no-host; loaded1024MiB and existing continuous RAM guard retained. Four profiles and Ornith128K default remain. Large dense-model prefill takes minutes. See [current proof](WINDOWS-QWEN-CONTEXT-20261023.md).
