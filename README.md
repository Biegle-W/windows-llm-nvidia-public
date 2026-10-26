# Windows LLM NVIDIA — public reference

Windows fallback for the **i5-13600KF / 64 GB DDR5-4200 / RTX 3080 Ti 12 GB**
workstation. The user is moving this NVIDIA machine to native Linux; Linux work
now belongs in the dedicated NVIDIA Linux pair, independently of the dual-AMD host.
[Seven-repository map](reports/REPOSITORY-MAP.md).

| Build | Private | Public |
|---|---|---|
| Windows NVIDIA | [windows-llm-nvidia](https://github.com/Biegle-W/windows-llm-nvidia) | [windows-llm-nvidia-public](https://github.com/Biegle-W/windows-llm-nvidia-public) |
| Linux NVIDIA | [linux-llm-nvidia](https://github.com/Biegle-W/linux-llm-nvidia) | [linux-llm-nvidia-public](https://github.com/Biegle-W/linux-llm-nvidia-public) |
| Linux AMD | [linux-llm-amd](https://github.com/Biegle-W/linux-llm-amd) | [linux-llm-amd-public](https://github.com/Biegle-W/linux-llm-amd-public) |
| Retired source/settings | [retired-llm-setting](https://github.com/Biegle-W/retired-llm-setting) | Private only |

## Native Linux migration

Read the [NVIDIA Linux-agent handoff](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/main/docs/MIGRATION-HANDOFF.md).
The native unlock helper/tests moved there, with explicit support for the Ti/3080
pair and later 3060. Eleven host-only tests pass; actual native installation,
unlock, P2P and inference remain unverified. Windows compute and UEFI results are
not Linux deployment proof. No OS, model weights, runtime, driver or partition was
changed by this source migration.

## Retained Windows operation

Use **Start Local LLM.cmd** for the authenticated OpenAI-compatible router at
`http://127.0.0.1:10000/v1`. It owns one worker on port 10001, loads on model
selection and keeps Ornith as default. Its visible terminal owns the process tree.
All four GGUFs remain under `models/`; source launchers and installed paths stay
unchanged. Windows llama.cpp remains b11630/CUDA 13.4 (`6868a52cb`), driver 610.88.

| API ID | Context allocation | Q8 KV placement |
|---|---:|---|
| `Ornith-1.5-35B-A3B-IQ2_S` | 131072 | CPU RAM |
| `LFM2.5-24B-A2B-UD-IQ3_XXS` | 131072 | CPU RAM |
| `Qwen3.8-27B-UD-IQ3_XXS` | 65536 | CPU RAM; dense model |
| `Qwen3.8-35B-A3B-IQ2_M` (Empero) | 65536 | CPU RAM |

These profiles mix GPU/RAM weights, split none/CUDA0, Flash Attention, Q8 K/V,
one slot, batch 512/microbatch 128, threads 6/batch 14, no speculation and no-host
true. Fit targets: 2816 MiB except LFM 3584. LFM reasoning remains required.
Fresh free-VRAM admission: 9216 MiB except LFM 8192. All require 20 GiB commit
headroom; RAM admission is 5/4.5/6/5 GiB in the table's order. Loaded workers keep
1024 MiB actual free VRAM. The continuous RAM guard stops only its owned worker
after five seconds below 0.75 GiB. Do not lower these thresholds or stop unrelated apps.

The router intentionally accepts one supported 12 GB NVIDIA GPU. A Ti/3080 pair
will need an intentional Windows guard/profile update before this launcher can
serve it. Linux profiles must be native implementations, not copies of this guard.

## Saved inference measurements

Historical **stock RTX 3060**, original 16 GB host, two 128-token native samples:

| Model | Decode samples (tokens/s) |
|---|---|
| Ornith | 26.55 / 26.71 |
| LFM | 64.75 / 64.36; reasoning-only at the output cap |
| Empero | 26.60 / 26.53 |
| Qwen27B | 6.75 / 6.71 |

These are dated sample totals, not matched completed-answer/quality rankings or
new Ti/64 GB results. [RAM-context methods](reports/WINDOWS-MOE-RAM-CONTEXT-20261023.md).
Harness validation reached 35,890 input tokens for Ornith, 16,268 for LFM, 16,270
for Empero and 24,460 for Qwen27B retrieval; Qwen also passed a 16,310-input SDK
system/tool request. Allocating 64K/128K does not establish full-window quality.
[Qwen context validation](reports/WINDOWS-QWEN-CONTEXT-20261023.md).

## Windows unlock and recovery

The latest Ti v4 manual USB boot succeeded with 64 GB RAM: FP16 **126.501 TFLOPS**
and BF16 **130.344 TFLOPS**, with reference checks and display recovery passing.
The separately tested 3080 and 3060 also have successful Windows compute results.
These are GEMM measurements, not LLM throughput or a simultaneous multi-GPU test.
[Current Ti proof](reports/RTX3080TI-V4-64GB-UNLOCK-RESULT-20261025.md).

| Dedicated USB | Label | Purpose |
|---|---|---|
| 4 GB General USB Flash Disk | RTX3080TI | Ti single-card manual v4 |
| 16 GB Kingston DataTraveler 2.0 | RTX3080_10G | 3080 single-card manual v2 |
| 32 GB Kingston DataTraveler 3.0 | RTX3060 | Original 3060 single-card manual |
| 8 GB SanDisk Cruzer Force | RTX3080PAIR | Read-only pair capture, no unlock |

Identify USBs by physical device/capacity/label; letters change. Single-card
packages are bound to captured ownership/topology and cannot be chained for a
pair. No dual Windows unlock is ready. [Pair procedure](reports/RTX3080-DUAL-WINDOWS-PREPARATION-20261025.md),
[USB assignments](reports/GPU-USB-ASSIGNMENTS-20261025.md).

The 3060 NVMe firmware entry/payload were explicitly removed. Its dedicated
512 MiB ESP remains empty; Windows Boot Manager stays first. Future 3060 Windows
unlocks are USB-only. Automatic installers and superseded source/settings are now
in the private retirement repository; do not reinstall internal startup without
a new explicit request. [Removal proof](reports/RTX3060-NVME-UNLOCK-REMOVED-20261025.md).

## Clients, history and maintenance

DSH keeps its existing provider, authentication and chats. Tailscale exposes the
authenticated router through `http://<TAILSCALE_HOST>:10000/v1`; no Funnel or new
listener was enabled by this migration. [Client handoff](reports/WINDOWS-TAILSCALE-CLIENT-HANDOFF.md).
Private keys/state remain ignored; never print or publish them.

The private [retired-llm-setting](https://github.com/Biegle-W/retired-llm-setting)
now owns retired source/settings, older hardware experiments and dated setup
overviews with original commits/paths/hashes. Local ignored recovery binaries,
weights and state remain in place. Prior public history is retained, not erased.
Current Windows operational evidence stays here. [Windows handoff](reports/WINDOWS-NVIDIA-HANDOFF.md).

This README is the sole root instruction file. Write all GitHub-facing content
in English, with English as primary chat language. Keep one setting per model at
the largest locally configured context. Preserve numerical checks, memory guards,
quality evidence, credentials, weights, applications and unrelated edits. Do not
run model tests alongside the owned production worker. Stop only owned processes.
Distinguish context allocation, actual tested length, prefill, TTFT and decode.

Maintain the appropriate private/public pair after validated changes, using only
sanitized selected exports, nonpersonal commits and no force pushes. Never copy
private history into public. Retire future unused source/settings into the central
private archive after hash verification; keep a pointer here. Keep Windows NVIDIA,
Linux NVIDIA and Linux AMD launchers, paths and validation independent. The user
controls reboot and conversation switching; continue authorized work across compaction.
