# Newer Windows MoE trials — 23 October 2026

Windows remains the separate **RTX 3060 12 GB / i5-13600KF / 16 GB DDR5 at 6000 MT/s** build, running llama.cpp b11630 CUDA 13.4 (`6868a52cb`, NVIDIA 610.88). Linux's dual-7900-XTX build was not changed.

The user requested newer MoE models in place of Qwen3.5 9B. Two newer community releases were downloaded to the Windows Downloads folder and checked against upstream SHA256/size. Empero's repository was created September 16 and Ornith's GGUF repository August 18; these are repository dates, not claims about a new Qwen foundation architecture. Empero explicitly identifies its model as Qwen3.8-teacher distillation into the Qwen3.6 35B-A3B architecture. GGUF metadata in both candidates reports `qwen35moe`, 256 experts and eight selected per token.

- [Empero Qwen3.8 35B-A3B Distill](https://huggingface.co/empero-ai/Qwen3.8-35B-A3B-Distill): IQ2_M, **12,558,245,760 bytes**, GGUF revision `b1f9d1dcc3de8aa867669b0ab919384aeeb9b8d5`, SHA256 `9c095175f7af0c4acc18e552f0dd7ac8180d81f9ac4bf38d62a03c76a0d6e084`. [Quantization](https://huggingface.co/empero-ai/Qwen3.8-35B-A3B-Distill-GGUF).
- [Ornith 1.5 35B-A3B](https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B-GGUF): IQ2_S, **11,486,963,360 bytes**, quant revision `64b0493d34a5ca4c1b4ad67bb99b41d74b4f07d6`, SHA256 `49b923ebe5f4d4a4384ccb86dd2b93effacc96ec1a3054a0192cc61dc045ebab`. [Bartowski quantization](https://huggingface.co/bartowski/Ornith-1.5-35B-A3B-GGUF).

NVIDIA's newer [Nemotron 3.5 Lightning](https://research.nvidia.com/labs/nemotron/Nemotron-3.5-Super-and-Lightning/) was screened, but the smallest [Unsloth quantizations](https://huggingface.co/unsloth/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF) were about 19.4 GB. Its official/other reviewed GGUFs offered no smaller complete file suitable for this comparison; it was not downloaded or benchmarked. Newer model naming does not eliminate the need to store all expert weights.

## Measured trials

All trials allocated **32,768 tokens**, used Q8 KV, Flash Attention, batch 512/microbatch 128, one slot, thinking off and no speculation. No vision projector was downloaded. All seven model/configuration trials passed chat, 64-token streaming, two 128-token-limit generations, tool call/response and **8,080-input-token retrieval**. Timings include any generated reasoning. These are short synthetic functional/performance checks, not answer-quality evaluations or full-context stress tests.

| Profile / placement | Decode samples, t/s | Lowest observed free VRAM, MiB | Selection |
|---|---:|---:|---|
| Empero-Qwen3.8-35B-A3B-IQ2_M — automatic fit, 1536 MiB target | 59.99 / 59.75 | 381 | Trial only |
| Ornith-1.5-35B-A3B-IQ2_S — automatic fit, 1536 MiB target | 62.18 / 63.63 | 363 | Trial only |
| Empero-Qwen3.8-35B-A3B-IQ2_M — automatic fit, no-host, 1536 MiB target | 60.24 / 60.81 | 303 | Trial only |
| Ornith-1.5-35B-A3B-IQ2_S — automatic fit, no-host, 1536 MiB target | 58.54 / 60.96 | 363 | Trial only |
| Empero-Qwen3.8-35B-A3B-IQ2_M — explicit CPU experts, fit off | 62.27 / 64.17 | 570 | Trial only |
| Ornith-1.5-35B-A3B-IQ2_S — explicit CPU experts, fit off | 64.98 / 66.53 | 531 | Trial only |
| Ornith-1.5-35B-A3B-IQ2_S — selected: automatic fit, no-host, 2816 MiB target | 48.24 / 44.29 | 1336 | Default |

The automatic fitter's 1,536-MiB target left only about 0.4–0.6 GiB actual whole-card free in early trials. A no-host-only trial and explicit CPU expert placement still left low margins. The selected Ornith profile raises `fit-target` to **2816 MiB**, uses `no-host true`, automatic GPU placement and **GPU + RAM** weights. The normal API reported **7,840.74 MiB GPU model buffers / 2,643.67 MiB host model buffers** and **1,571 MiB actual whole-card free VRAM** after streaming. One generation sample dipped to **1,336 MiB free**, so 2816 is a fitter target, not a guaranteed desktop reserve. RAM after normal streaming was **1.19 GiB available**. Fresh admission requires **4 GiB available physical RAM**, **16 GiB commit headroom** and **9,728 MiB actual free VRAM**; keep one model loaded and do not kill unrelated apps to make it fit.

The selected profile's short samples were **48.24 / 44.29 t/s**, with native 8K retrieval prefill **405.59 t/s**. It trades some speed for more actual desktop VRAM headroom. Early Ornith 62–67 t/s and Empero 60–64 t/s trials are not the selected setting's speed. Empero remains downloaded as an experiment; it is not in the active catalog because its higher host-weight demand and low actual VRAM margins make it a weaker daily-use fit on this 16-GB machine. After these trials, the retired Qwen3.5 9B GGUF was deleted at the user's request on October 23, freeing 5,966,095,584 bytes (5.56 GiB). Ornith and Empero were subsequently consolidated into project `models/`; their configurations and saved measurements are unchanged. Historical Qwen3.5 results remain as dated evidence.

`CPU` / `CPU_Mapped` / `CUDA_Host` weight buffers are all now counted as host weights in the maintained test parser. The first trial's omitted CUDA_Host numbers were corrected from its original saved log; no speed result was changed. Layer-count messages include the unused MTP block and must not override the actual mixed weight-buffer evidence. The selected profile is not full GPU.

GPU temperature/power were sampled every three seconds during the two short generations, with load/post-check snapshots. The numeric record contains sample counts/observed peaks. CPU temperatures and a continuous whole-run thermal peak were not captured. Do not treat the observed peaks as full-run maxima.

The normal visible launcher, authenticated API/streaming and unauthorized 401 passed with Ornith selected. Tailscale IPv4/MagicDNS host self-checks passed; a remote peer was not tested. Saved DSH catalog/default was updated through its existing LLAMA_CPP_API_KEY route, preserving unrelated settings. Its unavailable Desktop executable still prevents a GUI/installed-SDK claim. Strata remains disabled, LAN forwarding unchanged, Linux untouched.

Source configuration is in `config/selected-profiles.json` and `config/stack.json`; generated catalogs match it. Benchmark reproduction: stop the owned backend, then run `scripts/test_models.py Ornith-1.5-35B-A3B-IQ2_S --long-tokens 8192`. Do not add `--full-gpu` when registering this mixed profile. [Curated numeric record](windows-moe-summary-20261023.json). Preserve the dated initial restoration and its Qwen3.5 measurements as history.
