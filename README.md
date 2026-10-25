# Windows LLM NVIDIA — RTX 3060

## Repository and archive map

This system uses **Windows / NVIDIA RTX 3060 12 GB / i5-13600KF / 16 GB RAM**.
The private operational repository is `windows-llm-nvidia`; its independently
sanitized reference is [windows-llm-nvidia-public](https://github.com/Biegle-W/windows-llm-nvidia-public).
Ubuntu AMD has separate private/public repositories named `ubuntu-llm-amd` and
`ubuntu-llm-amd-public`. Keep the existing Windows installation directory and
runtime/model/configuration paths; renaming GitHub does not relocate that install.

Current launchers remain at the root, active source in `scripts/` and selected
profiles in `config/`. [archives/](archives/README.md) contains retired Strata source
and older setup documentation. Current reports stay under `reports/`; dated
benchmark/verification payloads retain their original locations for provenance.
The archive is not an active launcher or a request to restore retired models.



Sanitized reference for the independent Windows RTX3060 12GB /i5-13600KF /16GB
build, llama.cpp b11630 CUDA13.4, NVIDIA610.88. Linux AMD remains separate in [ubuntu-llm-amd-public](https://github.com/Biegle-W/ubuntu-llm-amd-public).

October25: [native Linux gpu-unlock preparation](reports/NATIVE-LINUX-NVIDIA-GPU-UNLOCK-20261025.md)
for this NVIDIA host targets RTX3060/2503 and a future retail RTX3080Ti/2208
on an additional SSD, preserving Windows. The pinned helper refuses WSL and
includes exact-PCI selection and rollback. Ten host-only tests pass; native
installation, actual unlock and performance remain untested. This does not
change the separate AMD Linux build or the archived NVIDIA Linux setup.

[Windows UEFI unlock research](reports/WINDOWS-GPU-UNLOCK-RESEARCH-20261025.md)
now includes real desktop3060/2504 results and a no-iGPU Intel/3070Ti boot.
The reviewed craftingmod GA10x framework is a candidate for this Gigabyte2503 /
B760M host, whose own unlock boot remains untested. Next step is a separate
read-only UEFI capture. No boot entry, driver or inference setting changed.

## One setting per model — October 23, 2026

The OpenAI-compatible router exposes exactly four IDs, retaining the largest
currently configured context for each model. Ornith remains default at128K.

| API ID | Context | Q8 KV location | Available RAM before loading |
|---|---:|---|---:|
| `Ornith-1.5-35B-A3B-IQ2_S` | 128K | CPU RAM | 5 GiB |
| `LFM2.5-24B-A2B-UD-IQ3_XXS` | 128K | CPU RAM | 4.5 GiB |
| `Qwen3.8-27B-UD-IQ3_XXS` | 64K | CPU RAM | 6 GiB |
| `Qwen3.8-35B-A3B-IQ2_M` (Empero) | 64K | CPU RAM | 5 GiB |

Each model has one verified setting. Qwen27B now uses64K/Q8 CPU KV in place
of its earlier8K limit; the other three settings are unchanged. All weights remain mixed GPU/RAM. The three
MoEs and dense Qwen27B all use Q8 KV in CPU RAM; Qwen27B is now64K. Native
context allocation is not a full-window quality test: tested input lengths were
35,890/16,268/16,270 for Ornith/LFM/Empero and24,460 for Qwen27B. Qwen64K also passed a16,310-input instructions/tools SDK round trip. [Measured placement and limits](reports/WINDOWS-MOE-RAM-CONTEXT-20261023.md),
[current Qwen context proof](reports/verification/windows-qwen-context-20261023.json).

## Prepare and connect

Install the matching CUDA runtime under `runtimes/llama.cpp-b11630-cuda-13.4/`,
Python at `runtimes/python/cpython-3.11.15-windows-x86_64-none/python.exe`, and
Windows Terminal. Download all four GGUFs into `models/`; verified file names,
hashes and source links are in the [inventory](reports/WINDOWS-CLEANUP-20261023.md)
and linked trial reports. Binaries, models and private app data are not included.

Run `python scripts/build_configuration.py`, then `Start Local LLM.cmd`. The
authenticated endpoint is `http://127.0.0.1:10000/v1`; `GET /v1/models` lists the
four canonical IDs above. Send one in the chat request's `model` field. One
guarded private worker is loaded at a time. Active streams hold the switch lock;
busy/resource refusal returns503 without a fallback. Authenticated
`/router/status` and `/router/unload` remain available. Stop/start after changing
configuration. Regenerate absolute model paths after moving the project.

The private API key belongs in `data/credentials/.local-api-key`; DSH uses the
`LLAMA_CPP_API_KEY` credential route. Reopen DSH to refresh the selector. Keep
LFM's required reasoning template; do not globally disable thinking. The same
real key applies to `http://<TAILSCALE_HOST>:10000/v1`; remote-peer reachability
is not established by a host self-check. Network configuration was not changed.

All profiles need20GiB commit headroom and the physical RAM listed above.
Fresh VRAM minimums remain9216MiB for Ornith/Empero/Qwen27B and8192MiB for LFM, plus at least1024MiB after
loading. Preserve the0.75GiB/five-second RAM guard and CUDA0/split-none fitting.
CPU KV increases capacity at a speed cost. The router is left running idle.

Keep exactly one active configuration per model in `config/selected-profiles.json`.
Do not re-add smaller context alternatives. Archived trial profiles/source are
in `archives/2026-10-23-strata/`; dated reports preserve their original IDs and settings.
Historical settings may differ from the current registry. Keep weights/runtime/
state/backups ignored; publish no credentials, workstation paths or private app
data. Preserve retired Windows files and historical hardware/method attribution.

Qwen27B's8K-only setting was replaced in place by64K/Q8 KV in RAM; no extra profile was added. Large first prompts can take minutes on this dense model. [Current methods and limits](reports/WINDOWS-QWEN-CONTEXT-20261023.md).

## Public repository maintenance

This repository is the Windows half of the former combined public distribution.
The sanitized Windows files, reports and retired configurations were moved intact
from its October 24, 2026 snapshot (public commit
[`8fbe5b5`](https://github.com/Biegle-W/ubuntu-llm-amd-public/tree/8fbe5b515ba623b786d7a28d825989bcd627a725/windows)).
Scripts and configuration now live at the repository root, so the launch commands
above remain valid. Earlier public history stays accessible at that snapshot.
No private repository history is included.

Publish reviewed Windows changes here and Ubuntu changes in
[ubuntu-llm-amd-public](https://github.com/Biegle-W/ubuntu-llm-amd-public).
Keep both private operational repositories private. Never copy credentials,
private paths, hostnames, IP addresses, chat sessions, raw logs, model weights,
installed runtimes or private Git history into this distribution. Use example
paths and addresses, retain licenses and use a non-personal commit identity.
Review staged paths/content and scan files and history before each push.
Keep exactly the four selected model profiles above; Linux dual-GPU rules do not
apply to this independent Windows machine. The split changes repository layout
only; Windows runtime behavior was not retested on Linux.

The four canonical IDs must match their GGUF filename stems. Keep DSH's Ornith
default, LFM reasoning, Q8 CPU KV and SSE switch exclusion. Reject insufficient
resources without silent model fallback or terminating unrelated applications.
GUI, remote-peer and full-window quality checks remain unperformed; earlier
throughput retains its dated context (including the retired Ornith 32K result).
Maintain the [Windows handoff](reports/WINDOWS-NVIDIA-HANDOFF.md) here separately
from the Ubuntu host's handoff; never overwrite the Linux Shared handoff.
