# Windows LLM NVIDIA — RTX 3080 / RTX 3080 Ti / RTX 3060

## Repository and archive map

This system now has **Windows / NVIDIA RTX 3080 10 GB / i5-13600KF / 16 GB RAM**.
The existing model-router profiles remain scoped to the 12 GB RTX 3060/3080 Ti;
the 10 GB card is undergoing separate unlock diagnostics.
The RTX 3060 remains supported for swapping back; its measurements are historical.
**Current startup policy:** the3060 NVMe firmware entry and payload are removed
at the user's request; future3060 unlocks use its preserved manual USB package.
The empty dedicated512MiB ESP is retained without repartitioning. The root restore
launcher is retired. Do not recreate3060 internal startup without a new request.
[Removal and future USB workflow](reports/RTX3060-NVME-UNLOCK-REMOVED-20261025.md).
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



**RTX 3080 10 GB manual unlock ready, October 25:** its read-only ownership
RUN02 passed, and a separate exact-board candidate is now staged and verified on
the **16 GB Kingston DataTraveler 2.0 / RTX3080_10G**. All 24 package files and
16 retained capture files verify; the previous probe is backed up. The image uses
its own board/PROM/cold-state and NVIDIA GOP metadata, with no automatic mode.
Eight upstream suites, 31 display/22 simulated unlock/26 driver-policy/19 actual
cold-check/eight manual-entry cases pass; 17 ownership unit tests and 49 shared
plus 19 new USB policy checks pass. Original 3060/Ti adaptations reproduce their
saved sources. Fresh Secure Boot-off, BitLocker-off, Windows-first and removed
3060 NVMe checks pass. **No 3080 unlock has run yet. Next full shutdown -> F8 ->
the 16 GB Kingston -> U once after preflight.** Allow up to 10 minutes for Windows
to start directly; do not rerun in the same firmware session. E:/F: remain for
3060/Ti and were not changed. [First-trial instructions](reports/RTX3080-10GB-WINDOWS-FIRST-UNLOCK-TRIAL-20261025.md).

**Dedicated GPU USB drives:** D: / 16 GB Kingston DataTraveler 2.0 /
`RTX3080_10G` now holds its fixed-board manual unlock; E: / 32 GB Kingston
DataTraveler 3.0 / `RTX3060` holds the preserved manual3060 unlock; F: / 4 GB
General USB Flash Disk / `RTX3080TI` holds the preserved manual3080Ti unlock.
All24/24/24 package files verify. Each has GPU-USB.txt; no format or internal
boot change. The old F: BIOS file was removed with explicit approval. Drive
letters may change; use device name/capacity/label and unplug the other drives
if F8 is ambiguous. **For the installed3080, use the16GB Kingston2.0; U once after
preflight is required for the next manual trial.** [Assignment and boot instructions](reports/GPU-USB-ASSIGNMENTS-20261025.md).

**Historical RTX 3080 10 GB board capture verification, superseded by the manual trial above:** the card is now installed.
Both read-only board runs match the Windows identity and contain identical PROM,
ROM and register values. All 16 register reads, the 1 MiB PROM and offline
firmware/signature/DMA/memory-layout checks pass. Pre-project-unlock GEMM baseline:
FP32 **23.143**, FP16 **60.196**, BF16 **60.053 TFLOPS**; all three reference
checks pass. These are compute measurements, not LLM generation speeds.
GPU OK/error 0; no NVIDIA Error/Critical events found since this boot.
**Kingston D: now boots the read-only ownership probe**, label **RTX3080_10G**;
all 12 package files and all 15 retained capture files were independently verified.
Next restart, press **F8 -> UEFI Kingston USB**, let the probe finish, then select
**Windows Boot Manager** and report back. No U confirmation is needed for this
diagnostic. Ownership review and the exact-board manual unlock remain pending.
The 3060/Ti images stay separate; model profiles and their 12 GB admission guards
are unchanged. [Board results and next step](reports/RTX3080-10GB-UNLOCK-SETUP-20261025.md).

**Historical RTX3080 10GB unlock preparation:** a separate2206/10240MiB setup is ready.
The3080Ti is still installed. Kingston D: now boots the read-only3080 board probe,
label **RTX3080_10G**, with14 independently verified files; the Ti fallback was
backed up and all seven old capture files retained. Both new diagnostic archives
and2206 host fixtures pass; nine new guard tests pass. Baseline/ownership helpers
refuse the currently installed Ti. **Next fully shut down, install the3080 10GB,
then F8 ->UEFI Kingston for the read-only probe and return to Windows.** No3080
unlock image can be built until its own PROM/register/ownership captures arrive.
The3060/Ti manual images remain separate;12GB model-router guards are unchanged.
[Separate3080 workflow](reports/RTX3080-10GB-UNLOCK-SETUP-20261025.md).

**RTX3080Ti manual unlock verified, RUN01:** logs show U confirmed, one successful
transaction/FLR, safe cleanup, restored display with9216 matching pixels and
Windows handoff. Same-executable FP16 70.350 ->126.860TFLOPS (+80.3%), BF16
70.363 ->129.958TFLOPS (+84.7%); FP32 essentially unchanged. All three compute
reference checks pass. GPU OK/error0, no NVIDIA Error/Critical events found this
boot after compute; driver610.88/350W unchanged. **Automatic3080Ti startup is not
installed**; do not rerun an unlock in this firmware session. Post-unlock LLM
speeds and repeated starts/sleep/resume remain untested. [Execution evidence,
measurements and limits](reports/RTX3080TI-WINDOWS-UNLOCK-RESULT-20261025.md).

**Historical RTX3080Ti manual trial preparation, October25:** both read-only captures passed.
The exact-board manual candidate is staged on Kingston D:, with all24 package
files independently verified and both captures preserved. Eight upstream suites,
31 display/22 simulated unlock/26 driver-policy/19 ColdCheck/eight manual-gate
cases pass; nine ownership tests and39 staging checks pass. Fresh Secure Boot-off,
FullyDecrypted/BitLocker-off, Windows-first and preserved3060 EFI checks pass.
The new image uses its own193248-byte/version0x6000d GOP metadata and fixed
51144015/1 initial selectors; no3060 selector exceptions are reused. **No3080Ti
unlock has run.** Next full shutdown ->F8 ->UEFI Kingston, then **U once after
preflight**. Esc/30 seconds cancels. After U allow up to10 minutes for Windows
to start directly; do not rerun the unlock in the same boot. [First-trial steps,
fallback and validation](reports/RTX3080TI-WINDOWS-FIRST-UNLOCK-TRIAL-20261025.md).

**Historical capture preparation:** new **Prepare RTX3080Ti Board
Probe.cmd**, **Prepare RTX3080Ti Ownership Probe.cmd** and **Collect RTX3080Ti
Captures.cmd** handle the next two read-only USB boots. Staging checks the exact
2208/10de:1535/BDF01:00.0/VBIOS identity, requires a non-system FAT32 USB, verifies
hashes and backs up every colliding file without formatting or deleting old runs.
22 staging policy checks and7 setup tests pass; both diagnostic archives remain
hash verified. OneDrive cloud placeholders are accepted while symbolic links,
junctions and unknown reparse tags remain refused. The offline auditor rejects
other subsystems/slots. After explicit authorization to discard its recordings,
Kingston D: was formatted FAT32/RTX3080TI. Physical board RUN00 now passes exact
identity,16 valid register reads,1MiB PROM and offline FWSEC/signature/DMA/layout
checks. Captures are preserved privately and on USB. The ownership probe is now
staged with12 files independently hash verified. Next manually boot F8 ->UEFI
Kingston USB for the ownership capture, then return through Windows Boot Manager.
GPU OK/error0 and no NVIDIA Error/Critical events found this boot. No unlock ran;
ownership review and the unlock image remain pending. [Boot and collection steps](reports/RTX3080TI-WINDOWS-UNLOCK-SETUP-20261025.md).

**RTX3080Ti installed and tested, October25:** all four unchanged profiles pass
short chat, streaming and two128-token samples. Mean generation: Ornith30.72t/s,
LFM78.35t/s, Empero30.00t/s and Qwen27B6.21t/s. Versus the saved unlocked3060
means: +8.4%, +20.0%, +1.9% and -5.8%. Automatic fit left150–205MiB more weights
in RAM, including two fewer Qwen GPU layers; this is a historical current-setup
comparison, not isolated GPU or unlock gains. Same-executable FP16/BF16 baseline
is70.35/70.36TFLOPS. No3080Ti unlock has been attempted; its own read-only board
and display captures remain necessary. Driver610.88/350W unchanged; GPU OK/error0
and no NVIDIA Error/Critical events found this boot after testing. Windows-first
boot and3060 restore remain preserved. [Full comparison and placement](reports/RTX3080TI-VS-3060-20261025.md).

**3080 Ti unlock toolkit prepared, October 25:** separate board and display-
ownership diagnostic ZIPs, a guarded baseline launcher and an offline PROM/
firmware auditor are ready. Both archives pass hash checks; six new setup tests
and wrong-card rejection checks pass. Run **Capture RTX3080Ti Baseline.cmd** once
the new card is installed, then collect its own diagnostic captures. The exact-
board3080Ti unlock image cannot be generated yet because that hardware data is
not available. Windows-first boot and the verified3060 restore path remain.
[Ready packages, commands and completion steps](reports/RTX3080TI-WINDOWS-UNLOCK-SETUP-20261025.md).

**GPU swap prepared, October 25:** Windows Boot Manager is first for the incoming
RTX3080Ti. The verified3060 unlock entry/payload are preserved but bypassed by
default. CUDA now accepts exactly one RTX3060 or RTX3080Ti with12GB or more;
the four model settings and memory guards remain unchanged. The3080Ti will boot
at stock settings until its own board data is captured and reviewed. A separate
read-only probe is packaged; no USB is currently connected or changed.
The internal3060 restore launcher is retired at user request; use its preserved manual USB package instead. See the removal report above.

**Historical paired3060 success, RUN0004:** The installed
EFI accepted70520074/5, completed preflight and one safe transaction/FLR, restored
the display and booted Windows. FP16 50.459TFLOPS (+88.0% vs stock), BF16
50.792TFLOPS (+89.6%); GPU OK/error0 and no NVIDIA Error/Critical events found
since boot after the test. [Physical paired-profile result](reports/RTX3060-AUTOMATIC-PAIRED-STARTUP-20261025.md).
This validates one paired-payload boot. Other checks remain, including rejection
of mixed/unknown/unlocked selector pairs. Repeated starts, sleep/resume and updates
remain unvalidated; keep F8 Windows Boot Manager recovery and the Esc gate.

**Historical zero-state success, RUN0001:** corrected EFI RUN0001 passed
preflight, ran once without U, completed one FLR with safe cleanup, restored the
display and started Windows. The same compute executable measures FP16 50.534
TFLOPS (+88.3% vs saved stock) and BF16 50.620 TFLOPS (+89.0%); FP32 is unchanged
within the short-run variation. GPU StatusOK/error0; no NVIDIA Error/Critical
events were found since boot, including after the test. USB is not needed for
this internal startup path. [Boot logs, measurements and limits](reports/RTX3060-AUTOMATIC-UNLOCK-SUCCESS-20261025.md).
That validated one zero-state automatic boot. RUN0003 subsequently refused;
the paired payload has now succeeded in RUN0004 as recorded above. Sleep/resume and updates remain untested. Keep the six-second Esc gate and F8 Windows fallback.

**Original automatic build, historical first-boot refusal:**
Its RUN0000 logs show a strict startup-state mismatch: the saved initial SS0/SS1
values differ from this boot's zero/zero values. No unlock transaction or FLR ran.
Current FP16/BF16 are stock-like at 26.79/26.81 TFLOPS; GPU StatusOK/error0 and
no NVIDIA Error/Critical events were found this boot. [Evidence and next step](reports/RTX3060-AUTOMATIC-FIRST-BOOT-20261025.md).
The original build failed; corrected RUN0001 has now succeeded as recorded above. The earlier LLM speed results below
were measured in the prior successful manual-unlock boot. No boot payload or
startup checks were changed during this verification.

**LLM tests after unlocking, October 25:** all four existing profiles passed short
chat, streaming and two 128-token speed samples with matched sampling and unchanged
weight placement. Mean generation: Ornith 28.34 t/s, LFM 65.29 t/s (reasoning-only),
Empero 29.45 t/s and Qwen27B 6.59 t/s. Against saved October 23 locked means these are
+6.4%, +1.1%, +10.8% and -2.1%; this historical comparison does not isolate unlock
causality. [Methods, limits and models that can use FP16/BF16 throughput](reports/RTX3060-UNLOCKED-LLM-20261025.md).
Small full-GPU 16-bit models and supported W4A16 kernels are research candidates;
no new model or backend was installed and all production profiles remain unchanged.

**Successful Windows unlock, October25:** the first manual single-child3060
trial completed one FLR, safe DMA cleanup, display recovery and Windows handoff.
The unchanged-driver/170W short GEMM comparison measured FP16 26.84->50.72TFLOPS
(+89.0%) and BF16 26.79->50.59TFLOPS (+88.9%); FP32 was approximately unchanged.
The Windows GPU reports StatusOK/error0. [Physical result and measurement limits](reports/RTX3060-WINDOWS-UNLOCK-RESULT-20261025.md).
The manual USB remains preserved. The [automatic internal boot installation](reports/RTX3060-AUTOMATIC-INTERNAL-BOOT-20261025.md)
is now complete after explicit approval: C: shrank by exactly 512 MiB, a dedicated
FAT32 ESP holds 27 hash-verified payload files, and the unlock entry is first with
the original Windows Boot Manager second. Original partitions and the Windows
boot entry passed preservation checks; temporary U: was removed. The actual-partition
build passes 14 automatic/source scenarios; the corrected installer passes 20
policy/state/resume checks. A first state-writing failure was audited and recovered
without a second shrink. No VBIOS flash or reboot was initiated. **The paired replacement has now passed RUN0004 and Windows compute verification.**
F8 -> Windows Boot Manager bypasses the unlock. Do not install the preview build.
Do not rerun the unlock in the current boot. The preparation paragraphs below
describe earlier stages, not the latest hardware result.

Sanitized reference for the independent Windows RTX3080Ti 12GB /i5-13600KF /16GB
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
read-only UEFI capture, now completed. The [probe package is now prepared](reports/RTX3060-READONLY-UEFI-PROBE.md)
from pinned5c076dc with LLVM20.1.8/Bun1.4.4. Upstream/exact2503 mocks,11 parser
tests and3 negative PE cases pass. A user-authorized FAT32 USB is now staged;
all14 restored files passed independent SHA256 checks. Physical RUN00 capture
passed: exact2503/407b1458 identity,16 valid register reads and verified1MiB PROM.
The diagnostic profile retains firmware compatibility and unlock approval as
false. Windows recognizes the3060/610.88 after reboot; firmware, selector policy
and display-driver ownership still require review before an unlock experiment. Binary,
ZIP, toolchain and captures stay ignored under `data/`/`runtimes/`. No boot entry,
driver or inference setting changed.

Later October25: [Windows unlock preparation](reports/RTX3060-WINDOWS-UNLOCK-PREPARATION.md)
now passes offline FWSEC/signature/DMA-geometry/layout checks on the actual PROM.
A fixed-board manual-only unlock candidate and all five verified assets are
prepared locally; eight manual-gate/failure cases and upstream host mocks pass.
Secure Boot is confirmed off and C: fully decrypted/BitLocker off by read-only
administrator queries. The Kingston USB now boots a separate read-only ownership
tree probe, preserving the first capture; the unlock candidate stays off USB
until that display tree is reviewed. No hardware unlock has run.

Latest ownership review: the physical capture passed and shows a one-child AMI
console chain. A [separate exact-board display adaptation and first manual trial](reports/RTX3060-WINDOWS-FIRST-UNLOCK-TRIAL.md)
now replaces the incompatible generic two-child candidate on the USB. It checks
five captured driver metadata/entry-offset profiles, preserves the unchanged
firmware transaction, and passes31 display replays,22 simulated transaction/rejoin
cases and26 policy checks. The USB requires U after preflight; no actual unlock
has run. Inspect the next `RTX-UNLOCK/RUNnn/GOP.TXT` and any `UNLOCK.TXT` after
the first trial. Previous captures, the old candidate and USB backups remain private.

## One setting per model â€” October 23, 2026

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

Write all GitHub-facing documentation, comments, CLI messages, commit messages,
issues and pull requests in English. English is the primary communication
language; Chinese is secondary, when useful or requested. Preserve historical
multilingual benchmark/test payload values using Unicode escapes rather than
translating measured inputs or outputs. Explain fixtures in English and retain
attribution links when using Latin-script author names.

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
