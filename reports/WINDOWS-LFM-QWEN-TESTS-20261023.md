# Windows LFM2.5 and Qwen3.8 tests — 23 October 2026

The user requested both models downloaded into Windows Downloads and tested. Both IQ3_XXS files passed upstream byte-size/SHA256 checks. They were subsequently consolidated into project `models/`; the saved benchmark results are unchanged. The active registry/default remains **Ornith-1.5-35B-A3B-IQ2_S**; these are separate test profiles, not active production entries. No Linux files/settings were changed.

Hardware: RTX 3060 12 GB, i5-13600KF, 16 GB DDR5 at 6000 MT/s, NVIDIA 610.88. Runtime: existing llama.cpp b11630 /CUDA13.4, commit `6868a52cb`.

| Model | File bytes | Pinned source / verified SHA256 |
|---|---:|---|
| LFM2.5-24B-A2B-UD-IQ3_XXS.gguf | 8,959,328,480 | [aacc7783](https://huggingface.co/unsloth/LFM2.5-24B-A2B-GGUF/tree/aacc77834f6aa568c93b4dbd6d295059736be98c); `e06694b1f0bb322ecfde6bf9af260d2f2047ed1b30bbfdd04d97bf55472bfeec` |
| Qwen3.8-27B-UD-IQ3_XXS.gguf | 10,934,860,704 | [4ca72078](https://huggingface.co/unsloth/Qwen3.8-27B-GGUF/tree/4ca720788d1e01f1bff70c033e0d0028fd02e502); `c0b7c3038681ed2e3040456c1dd45f9858b6c2290bed172c70388a94874f3eee` |

## Method and results

Tests ran sequentially on loopback10001 after stopping only the owned production backend. Other GPU applications were temporarily paused with user approval, then restored. No model download was deleted or moved to another drive.

Both used **8,192 allocated context**, split none/CUDA0, Q8 K/V, Flash Attention, batch512/microbatch128, threads6/batch14, **fit on /target3584 MiB /no-host true**, no speculation or projector. Each passed chat, streaming, two128-token generation samples, a forced function-call/response round trip and fresh marker retrieval at approximately6K input. LFM follows its required reasoning template; Qwen uses `enable_thinking:false`. LFM correctness sampling uses temperature0.1, Qwen0; speed samples both use0.1. LFM's check/stream budget is2048; Qwen's check budget2048/stream64.

| Measurement | LFM2.5 24B-A2B UD-IQ3_XXS | Qwen3.8 27B UD-IQ3_XXS |
|---|---:|---:|
| Two short native generation samples | **78.24 /85.04 t/s** | **4.97 /5.59 t/s** |
| First generated token, short marker stream | 0.110 s | 0.922 s |
| First visible answer, same marker question | **1.828 s** | **0.922 s** |
| Whole marker reply time | 1.953 s | 1.782 s |
| Fresh retrieval input tokens | 6,023 | 6,025 |
| Native retrieval prefill | 665.55 t/s | 164.48 t/s |
| GPU model buffers | 7,426.41 MiB | 7,140.20 MiB |
| Host model buffers | 1,315.08 MiB | 2,872.55 MiB |
| Available RAM after load | 2.44 GiB | 1.53 GiB |
| All five checks | Pass | Pass |

**Throughput counts all generated tokens.** Both128-token LFM speed samples contained reasoning only, with no visible answer before the cap. Qwen's samples contained visible prose with thinking disabled. Thus these rates are not an apples-to-apples completed-answer speed or quality ranking. LFM did complete visible answers in the separate chat, stream, tools and retrieval checks; its short marker reply generated153 tokens including reasoning. Qwen's marker reply generated5. Cold model loading8.56/10.53s is excluded from request timings. Allocation is not full-window testing; these synthetic smokes do not establish general answer quality or long-agent reliability.

Both are **GPU + RAM** profiles. LFM reports41/41 layers offloaded but still has1,315MiB host weight buffers for CPU expert work; that message does not prove full GPU weights. Qwen reports44/66 layers on GPU with2,873MiB host weights. Its dense CPU layer computation makes this IQ3 configuration a poor speed fit for the current machine. LFM is the more practical candidate based on these bounded performance/memory checks; no default change was made.

## Admission, thermal coverage and final state

Initial attempts stopped at admission, not model-quality checks: the old active-profile budget blocked both while other apps occupied VRAM. After approved app pausing, LFM loaded at target2816 but left920MiB actual whole-card free, below the unchanged1024MiB loaded-test requirement; Qwen's first retry was refused for available RAM. The successful pass raised the fitter target to3584 and used model-specific fresh admission:8192MiB free VRAM; LFM3GiB RAM/12GiB commit, Qwen3.5GiB RAM/16GiB commit. Production Ornith's4GiB/16GiB/9728MiB limits were not lowered. The continuous test guard still terminates only its own worker after five seconds below0.75GiB available RAM.

The fitter target is not guaranteed real headroom. The numeric record retains actual VRAM minima, RAM snapshots and sampled GPU temperature peaks. GPU readings cover three-second generation samples plus before/after snapshots; CPU temperatures and continuous whole-run thermal maxima were not captured. No DSH Desktop or remote-client test was performed for these models.

The approved apps/service were restored. **Ornith remains the configured default, but its restart was refused by existing production memory admission; the owned inference backend was left stopped.** Free the required resources before normal launch. This result does not authorize weakening production limits or closing unrelated apps automatically.

Reproduce with the saved separate profiles, after stopping the owned backend:

```powershell
python scripts/test_models.py --profiles-file retired/20261023/config/test-profiles-lfm-qwen-20261023.json --long-tokens 6144 --speed-temperature 0.1
```

Adjust example model paths first in public exports. The CLI does not stop/restart production automatically. LFM's reasoning behavior and Pythonic native tools follow the [publisher card](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B); Qwen thinking control follows its [official card](https://huggingface.co/Qwen/Qwen3.8-27B). Tool round trips here passed through llama.cpp's native OpenAI-compatible parser. [Curated numeric evidence](windows-lfm-qwen-summary-20261023.json). Earlier failed admission records and successful raw test outputs are preserved privately; weights, raw logs and private app state remain outside Git.
