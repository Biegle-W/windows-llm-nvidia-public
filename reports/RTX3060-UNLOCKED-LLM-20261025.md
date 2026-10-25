# RTX 3060 unlocked LLM measurements and model research — October 25, 2026

The unlock nearly doubled short FP16/BF16 GEMM throughput, but the existing
mixed CPU/GPU IQ GGUF profiles show small or moderate historical generation
differences. They do not demonstrate an 89% LLM speedup.

## Measured existing profiles

| Model | Allocated context | Locked Oct 23 mean, tok/s | Unlocked Oct 25 mean, tok/s | Historical difference |
|---|---:|---:|---:|---:|
| Ornith 1.5 35B-A3B IQ2_S | 128K | 26.63 | 28.34 | +6.4% |
| LFM2.5 24B-A2B UD-IQ3_XXS | 128K | 64.55 | 65.29 | +1.1% |
| Empero Qwen3.8 35B-A3B IQ2_M | 64K | 26.57 | 29.45 | +10.8% |
| Qwen3.8 27B UD-IQ3_XXS | 64K | 6.73 | 6.59 | -2.1% |

Every model passed short chat, streaming and both speed requests. Each mean is
two 128-token native llama-server samples, temperature 0.1, seed 42, prompt cache
off, using the maintained `scripts/test_models.py` speed-only path. The same
maintenance-checklist prompt produces 45 tokens for LFM and 48 for the others.
One owned worker ran at a time with original RAM/VRAM guards. No production
profile, weight, driver or boot configuration was changed. An earlier exploratory
temperature0 run was stopped and excluded when the saved temperature was checked.

The runtime remains b11630/CUDA13.4 (`6868a52cb`), driver 610.88 and 170W cap.
Measured GPU/CPU model buffers and offloaded-layer counts exactly match the saved
baselines for all four models. Q8 KV stays in CPU RAM. LFM's two samples reach
the cap entirely in reasoning; its speed is total generated tokens, not completed
visible answers or a quality ranking. Allocated 64K/128K windows were not filled
or revalidated by this short test. Tools and long-prompt checks were not rerun.

These compare October 23 locked runs with October 25 unlocked runs. Desktop memory
availability, clocks, thermals and background work were not controlled across days;
the percentages cannot isolate the unlock's causal contribution. Two short samples
also do not establish statistical significance. The current short-prompt timings
are retained in [curated JSON](verification/rtx3060-unlocked-llm-20261025.json),
without comparing them to the historical long-prompt retrieval timings.

All test workers exited. Post-test GPU: 45C, 11124 MiB free VRAM, 170W limit;
no nvlddmkm Error/Critical events were found since the current Windows boot.
Raw request responses, telemetry and paths remain in ignored local state. The
curated JSON includes hashes of the four private result files for provenance.

## Why the floating-point gain does not translate directly

The [same-executable GEMM result](RTX3060-WINDOWS-UNLOCK-RESULT-20261025.md)
was FP16 +89.0%, BF16 +88.9%, FP32 approximately unchanged. The unlock does not
increase VRAM capacity, memory bandwidth, CPU throughput or PCIe bandwidth.

The [installed-revision CUDA dispatch source](https://github.com/ggml-org/llama.cpp/blob/6868a52cb/ggml/src/ggml-cuda/mmq.cu)
supports these IQ types and selects MMQ on NVIDIA architectures with Turing-style
integer MMA support. Thus much quantized matrix work follows integer kernels,
while small-batch generation can be bandwidth limited. CPU weights and CPU
attention add limits on this 16GB host. This is source-based explanation, not a
per-kernel profiler capture of these runs. A separate
[3080 unlock user's measured llama.cpp comparison](https://github.com/Zagitta/gpu-unlock/issues/14)
also found essentially unchanged quantized prompt and generation speeds.

The [pinned llama.cpp build guide](https://github.com/ggml-org/llama.cpp/blob/6868a52cb/docs/build.md)
documents `GGML_CUDA_FORCE_CUBLAS` as a **compile-time** option to force FP16
cuBLAS for quantized matrix operations. It can increase VRAM use and cause numerical
overflow; it is an experimental comparison route, not an environment switch for
the installed binary or a guaranteed optimization. The working runtime was retained.

## Models and execution paths worth trying next

The following are researched candidates, **not downloaded or benchmarked here**.
Memory figures are approximate 16-bit weight arithmetic before KV, recurrent state,
vision components, workspaces and Windows display use; they are not measured budgets.

| Candidate | Execution to test | Why it is relevant on 12GB |
|---|---|---|
| [LiquidAI LFM2.5-2.6B](https://huggingface.co/LiquidAI/LFM2.5-2.6B) | Full-GPU BF16/FP16; official Transformers example uses BF16 | About 5.2GB nominal weights; strongest first experiment with room for runtime state |
| [Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B) | Full-GPU BF16/FP16, text first | About 4GB language weights; useful small Qwen baseline with generous headroom |
| [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) | Full-GPU BF16/FP16, modest initial context | About 8GB language weights; closer to 12GB limit after overhead, so verify residency |
| [Gemma4 E2B](https://ai.google.dev/gemma/docs/core/model_card_4) | Investigate full-GPU 16-bit fit or a supported W4A16 conversion | E2B is 5.1B total parameters including embeddings, not merely 2B of weights;16-bit fit is tight |

Full-GPU FP16/BF16 prefill and concurrent/batched requests are the most direct
LLM workloads for using the additional floating-point throughput. Single-stream
decode may still be limited by weight reads and will not necessarily double.
Smaller models also trade capability for fit; do not replace the current larger
models solely to improve an unlock benchmark. Begin with2K–4K context for the
experiment, then measure memory and expand; this is not a change to the existing
maximum-context production profiles.

Larger 4-bit models can also use floating-point arithmetic: the official
[W4A16 description](https://docs.vllm.ai/projects/llm-compressor/en/0.7.1/guides/compression_schemes/)
specifies INT4 weights with 16-bit floating-point activations/arithmetic.
[vLLM's hardware table](https://docs.vllm.ai/en/latest/features/quantization/)
lists Ampere support for AWQ/GPTQ/Marlin. A supported 7B–9B W4A16 model running
fully in VRAM is another sensible experiment. Exact architecture, conversion and
kernel compatibility must be verified; a 4-bit label alone does not establish the
execution path or improvement. The current IQ GGUFs are not interchangeable with
AWQ/GPTQ artifacts.

[ExLlamaV3/TabbyAPI](https://github.com/turboderp-org/exllamav3) is another
OpenAI-compatible serving route to evaluate. Its Windows path requires compatible
CUDA PyTorch, build prerequisites and triton-windows. It was not installed here,
and no EXL3 speedup or exact model compatibility is claimed.

For this 3060, prioritize 16-bit compute paths rather than native FP8 W8A8:
[vLLM's FP8 documentation](https://docs.vllm.ai/en/latest/features/quantization/fp8/)
distinguishes Ampere's weight-only W8A16 Marlin path from native FP8 computation.
Unlocking does not add Hopper/Ada FP8 hardware. Nor does a MoE's small active count
make all its weights fit: the current 24B/27B/35B models cannot be fully resident
in 12GB at16-bit precision.

Next useful controlled experiment: LFM2.5-2.6B BF16 and Qwen3.5-4B FP16/BF16,
measuring both 2K–4K uncached prefill and decode, plus a small concurrent batch.
For a causal percentage, repeat the identical workload on a stock boot and an
unlocked boot with matched GPU memory, power, clocks and desktop conditions.
The current manual unlock should not be replayed in this firmware session.
