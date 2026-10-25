# Optional MoE context in CPU RAM — October 23, 2026
> Later October 23: the active catalog was consolidated to one setting per model. See [current README](../README.md). Dated trial IDs and original settings below are preserved as evidence.

Three additional router profiles reuse the existing GGUFs and keep Q8 K/V in CPU
RAM using `--no-kv-offload`. The original four profiles and Ornith default are
unchanged. Select a RAM profile in DSH or send its complete API ID to the existing
authenticated endpoint on10000. There are now seven profile IDs for four files.

| API ID | Allocated context | Retrieval input tested | CPU Q8 KV allocation | Available RAM after load |
|---|---:|---:|---:|---:|
| `LFM2.5-24B-A2B-UD-IQ3_XXS-128K-RAM` | 131,072 | 16,268 | 1,360 MiB | 2.10 GiB |
| `Ornith-1.5-35B-A3B-IQ2_S-128K-RAM` | 131,072 | 35,890 | 1,360 MiB | 1.63 GiB |
| `Qwen3.8-35B-A3B-IQ2_M-64K-RAM` | 65,536 | 16,270 | 680 MiB | 1.88 GiB |

Native logs explicitly report `CPU KV buffer size` with Q8 K and Q8 V. KV was
not left in VRAM, and no model file was duplicated. Weight placement still mixes
GPU and RAM. Empero's heavier host weights make64K the more conservative choice
on this16GB build;128K Empero was not tested. LFM and Ornith allocate128K.

## Usability and limits

All three profiles passed chat, SSE, forced tool-call/response round trips and
fresh passphrase retrieval. Ornith's test exceeds the previous32K allocation;
LFM/Empero tests exceed their previous8K allocation. Full64K/128K prompt windows
were not filled, and synthetic retrieval is not a general long-context quality
benchmark. These allocations are below the recorded model-native context limits;
no RoPE extension or GGUF change was made.

All three new profile IDs also streamed a valid reply through the installed DSH
Desktop pi-ai SDK via the production router. This verifies model-ID selection;
the GUI selector itself and a remote Tailscale peer were not retested.

Two128-token native samples at short prompt length:

- `LFM2.5-24B-A2B-UD-IQ3_XXS-128K-RAM`: 64.75 / 64.36 total generated tokens/s.
- `Ornith-1.5-35B-A3B-IQ2_S-128K-RAM`: 26.55 / 26.71 total generated tokens/s.
- `Qwen3.8-35B-A3B-IQ2_M-64K-RAM`: 26.60 / 26.53 total generated tokens/s.

LFM's short samples are reasoning-only at the cap; the others use thinking off.
Rates count all generated tokens, not completed answers. They do not describe a
filled128K window or establish a controlled speed comparison with earlier GPU-KV
results. Longer CPU-attention histories can be substantially slower. Use the
original profiles for routine short chats; choose RAM profiles when the larger
window is useful. First use also includes loading time.

The source registry specifies Q8 K/V, Flash Attention, one slot and
`no-kv-offload:true`. LFM retains fit-target3584; RAM Ornith/Empero use2816.
Fresh admission requires4.5GiB available RAM for LFM and5GiB for Ornith/Empero,
20GiB commit headroom,8192MiB actual free VRAM for LFM and9216MiB for the other
RAM profiles. Those GPU limits belong only to the new cache-placement profiles;
the original profiles' limits were not lowered. Every loaded worker still needs
at least1024MiB actual free VRAM. The existing continuous guard stops only its
owned worker if available RAM stays below0.75GiB for five seconds.

Physical RAM remains limited to16GB; Windows pagefile space is not treated as a
substitute for available physical RAM. Desktop apps can make a RAM profile fail
admission. Chrome was temporarily closed under the earlier testing authorization
and reopened afterward. No other apps, driver/startup policy, network routes or
Linux settings were changed for these trials.

The original default remains `Ornith-1.5-35B-A3B-IQ2_S`. DSH's saved selector was
updated after the trials; reopen DSH if it caches the old list. The router is
left running idle, with the same API key and one-worker switching behavior.
See [numeric results](verification/windows-moe-ram-context-20261023.json).

## Sources

- [llama.cpp server flags](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md): `--no-kv-offload` and Q8 KV types; also verified against this installed build's help and allocation logs.
- [LFM2.5 publisher card](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B):131072 native context and required reasoning behavior.
- [Ornith publisher card](https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B):262144 native context.
- [Empero publisher card](https://huggingface.co/empero-ai/Qwen3.8-35B-A3B-Distill):262144 native context inherited from its base.
