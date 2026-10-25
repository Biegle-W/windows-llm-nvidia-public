# Qwen3.8 27B: harness-sized context — October 23, 2026

The sole active `Qwen3.8-27B-UD-IQ3_XXS` profile now allocates **65536 tokens**,
replacing its old8192-token test limit. The API ID and model file are unchanged;
there are still exactly four active model profiles. Other models and the Ornith
default are unchanged. DSH's saved selector advertises64K for Qwen27B.

## Verified configuration

Q8 K and V are explicitly in CPU RAM using `--no-kv-offload`; the native log
reports **2176MiB CPU KV**, with no GPU KV buffer. The same RTX3060/16GB Windows
build uses llama.cpp b11630/CUDA13.4, CUDA0/split-none, one slot, Flash Attention,
fit on/target2816/no-host true, batch512/microbatch128, threads6/batch14 and
thinking off. No speculation, model redownload or quantization change occurred.

The larger CPU cache frees GPU space for dense layers: this configuration measured
51/66 layers on GPU,7960.59MiB GPU model buffers and2060.60MiB host model buffers,
versus44/66 layers in the old8K setup. It is still mixed GPU/RAM, not full GPU.
The new fitting target and placement differ, so these are complete-profile
measurements rather than an isolated context-size or KV-placement experiment.

Fresh admission requires6GiB available physical RAM,20GiB commit headroom and
9216MiB actual free VRAM. After loading,2.03GiB system RAM and1583MiB whole-card
VRAM remained free. Keep the1024MiB loaded VRAM requirement and existing continuous
RAM guard: terminate only the owned worker after five seconds below0.75GiB.
Do not lower the guards to make a busy desktop admit the model.

## Functional and harness checks

The isolated candidate passed chat, streaming, a forced tool-call/response round
trip and fresh passphrase retrieval from **24,460 input tokens**. The installed
DSH Desktop pi-ai SDK separately passed a synthetic harness-style start with
**16,310 input tokens**, including system instructions and a
declared tool; the tool-result follow-up retained
16,362 input tokens (23 new +16,339 cached) and returned the expected marker.
That demonstrates a combined instructions/tools request beyond8K, not just a
short SDK greeting. It is not a GUI or complete agent-session/workspace test.

The installed SDK declares instructions/tools in system transcript messages using
`toolsAdded`; older top-level `systemPrompt`/`tools` fields were ignored by this
installed version. The final test verifies actual input-token usage rather than
assuming those fields were sent. The application itself was not modified.

Two128-output-token native short samples: **6.75/6.71t/s**.
The24K retrieval prefill took223.03s (109.67t/s), and its short decode was3.44t/s.
Large initial harness prompts can therefore take minutes on this dense model.
These are synthetic functional/performance probes, not general answer-quality
or full64K-window validation. Full-window and remote-peer/GUI tests remain undone.

No unrelated apps were closed for this follow-up; the production router was
already stopped when inspection began. The final router is running idle with
one64K Qwen setting, the same private API key and four total model choices.
Reopen DSH if its selector caches the earlier8K value. Historical8K reports and
the retired test fixture remain dated evidence.

See [numeric verification](verification/windows-qwen-context-20261023.json) and
[harness-style SDK proof](verification/windows-qwen-harness-start-20261023.json).
