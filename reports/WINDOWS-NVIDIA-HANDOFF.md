# Windows NVIDIA handoff — 25 October 2026

LATEST RTX3080 10GB board audit: installed2206/10240MiB, driver610.88/320W.
RUN01 and RUN02 are complete; PROM/ROM/registers agree and match actual Windows
identity. All16 reads,1MiB PROM and CPU-only FWSEC fuse2/booter1, signature,
aligned DMA and10GB memory layout checks pass; truncated ROM/missing signature
negative checks reject as expected. Diagnostic approval flags remain false.
Same retained compute executable: FP32 23.142982 / FP16 60.196178 /
BF16 60.052674 TFLOPS,4096-square,2s warmup,30 samples,all reference checks pass.
This is a pre-project-unlock compute baseline, not an LLM speed measurement or
independent lock-state proof. GPU OK/error0,zero NVIDIA Error/Critical this boot.
CURRENT USB: read-only ownership GC_TREE_ONLY, EFI58f4...42b8,12 files verified,
15 retained raw capture files verified, collisions backed up; no formatting/BCD
or GPU firmware change. Next user F8 -> UEFI Kingston, then Windows Boot Manager.
Collect new2206 GOP.TXT, bind it to this baseline, review exact topology/driver
metadata, then extend the board-scoped manual builder. No3080 unlock built/run.
Do not reuse3060/Ti state or install automatic startup.12GB router guards remain.

LATEST next-card preparation: [RTX3080 10GB workflow](RTX3080-10GB-UNLOCK-SETUP-20261025.md).
User requests2206/10GB unlock next;3080Ti still installed. Board package
data/uefi-probe/rtx3080-10gb-readonly/ and ZIP built from unchanged5c076dc source,
including2206/GA102 mocks; ownership package under rtx3080-10gb-ownership/package/
and adjacent ZIP passes grouped and explicit2206 entry tests. EFI hashes remain
ae7b...785a (board) and58f4...42b8 (ownership); neither links an unlock.
New scripts/rtx3080_setup.py handles identity/baseline/offline audit; accepts only
nameRTX3080/PCI2206/10240MiB and binds reports to baseline subsystem/BDF. Nine
unit tests pass; actual Ti refused before baseline compute/output and ownership
staging. New Board/Ownership/Collect launchers and Capture RTX3080 10GB Baseline.cmd
are at root. Stager loads shared path/USB policies via test-only import (41 pass).
Board mode permits pre-swap staging; later modes require the installed3080.
CURRENT USB: FAT32/RTX3080_10G, read-only board fallback,14 files independently
verified. Previous Ti fallback/collisions backed up below
data/uefi-probe/3080-10gb-usb/before-board-20261025-193231-01ab90b436764c8989d06dd32080e306/.
All seven old capture files preserved. Next user full-shutdown/swaps3080/F8 USB,
then Windows. Capture Windows identity/compute baseline and new2206 board run,
then stage/boot/review ownership before adapting any manual unlock. No3080 PROM/
topology is known yet and no unlock image built;2216/other variants require
separate review. Current Ti session,3060 USB-only policy,empty NVMe ESP and12GB
LLM/router admission limits unchanged. Older USB-mode paragraphs are historical.

LATEST startup cleanup: [3060 NVMe unlock removed](RTX3060-NVME-UNLOCK-REMOVED-20261025.md)
at explicit user request; future3060 unlocks USB-only. Exact dedicated ESP/disk/
payload identity checked,41 files archived/hash verified, firmware entry deleted,
all owned payload files removed. Windows entry/order and complete partition
inventory verified preserved; empty512MiB partition retained; U: removed. No USB,
GPU, driver or model change and no reboot. Root Restore RTX3060 Unlock.cmd retired
to archives/2026-10-25-3060-nvme-startup/*.disabled. Old restore/install/update
helpers refuse NvmeUnlockRemoved state. Do not recreate3060 internal startup.
Manual USB package still verified23 files under
data/uefi-probe/windows3060-single-child-20261025-v3/manual-unlock-candidate/;
EFI61fa2b71d1332d4d6180610175955d3cad015420c41f393b7abea717507d09e1.
Private removal result data/uefi-probe/internal-startup/nvme-removal-result.private.json;
archive data/uefi-probe/3060-nvme-removal-20261025-181709-4e8c5f3c98cd45998a3725aa829d0cb5/.
Prior manual-platform evidence preserved there and invalidated as stale; future
checker can verify removal instead of requiring the old EFI.20 removal/41 staging
policy checks pass on PowerShell5.1/7.6;10 legacy policy checks pass; actual retired
restore refuses before UAC. Current USB remains3080Ti manual image c13c...fab4.
Older paragraphs below mentioning preservation/restoration are historical.

LATEST manual3080Ti RUN01 SUCCESS: [verified result](RTX3080TI-WINDOWS-UNLOCK-RESULT-20261025.md).
Current Windows boot18:02:44.5 America/New_York follows logged18:02:41 handoff.
MANUAL_U confirmed, fixed board/PROM/51144015+1 initial state matched. One FLR,
transaction result0/containment0/started1/quiesced1/fault0/retained0/maps0/safe1,
SS0=88888888/SS1=8 preserved through display recovery and output. FULL_FINAL0 /
touched1/restored1,9216-pixel readback zero mismatches, reboot0 Windows handoff.
Current same-executable GEMM FP32 25.700669/FP16 126.859854/BF16 129.957548TFLOPS;
versus saved3080Ti baseline +0.07%/+80.33%/+84.70%. Three reference checks pass.
GPU OK/error0,37C/10858MiB free, zero NVIDIA Error/Critical events this boot after
compute; driver610.88/350W unchanged. USB EFI remains c13c...fab4.
Raw log copy data/uefi-probe/3080ti-usb/captures-20261025-181102-fd129b01389b4e22837518c2e0e68593/RTX-UNLOCK/RUN01/;
compute data/uefi-probe/3080ti-usb/unlocked-compute-run01.private.json;
health manual-run01-health.private.json in same state directory. Original baseline
unchanged. No3080Ti automatic startup installed and no boot/driver/model/power
change during verification. Do not rerun unlock in current session. Repeated
boots/sleep/resume/updates/stability and post-unlock LLM speed unvalidated.

Historical manual3080Ti trial preparation: [first-trial workflow](RTX3080TI-WINDOWS-FIRST-UNLOCK-TRIAL-20261025.md).
Ownership RUN00 captured17:42 local, complete4 handles/5 roles/10 active edges,
no detach/touched. Copied/hash verified under
data/uefi-probe/3080ti-usb/captures-20261025-174554-1be0a845b90d45c889cfcd1653a49ef5/.
Its NVIDIA GOP differs:193248bytes/version0x6000d/startRVA0x774/stop0x698;
all five roles bind this actual capture. Fixed board PROM/SS0=51144015/SS1=1,
no zero-state exception. Builder scripts/prepare_uefi_3080ti_manual.py produces
data/uefi-probe/windows3080ti-manual-20261025-v3/single-child/manual-unlock-candidate/.
Shared3060 display builder now accepts an explicit separately guarded3080Ti target;
default3060 adaptation still reproduces saved validated C exactly. Transaction
sources unchanged, no mock/automatic/SSD flags in EFI. EFI SHA256
c13c39eb98bae5b836c80e1a4e5d7f84c05ad910f35b5b62f2ad97311052fab4.
Eight upstream suites,31 display/22 simulated transaction/26 metadata/19 actual
ColdCheck/eight manual-gate cases, nine synthetic ownership tests, seven setup
tests and39 PowerShell5.1/7.6 staging/prerequisite checks pass. Five pinned assets
and PE verified. Failed v1/v2 build folders preserved and never staged.
Fresh elevated checks in data/uefi-probe/3080ti-usb/manual-platform-prerequisites.private.json:
SecureBoot false, C FullyDecrypted/ProtectionOff, Windows first, original3060
EFI a57b...4394 hash preserved; U: removed. Staging timezone parsing fixed/tested.
Current USB is the MANUAL unlock candidate, all24 files independently verified;
both original capture RUN00 folders retained. Backup before-manual-* records
collisions; EFI copied last. User must full-shutdown/F8 ->UEFI Kingston, press U
once only after preflight; Esc/30sec cancels. After U allow10min for direct Windows
handoff. If stopped/no Windows, full power off, removeUSB, boot Windows normally;
do not replay in the same firmware session. Next read new GOP.TXT/UNLOCK.TXT and
same-executable compute/health before claiming success or configuring automatic
startup. No3080Ti unlock has executed; no internal boot/driver/power changes.

Historical capture preparation: new root Board/Ownership/Collect launchers
call scripts/Prepare-RTX3080TiProbeUsb.ps1. Exact current Windows identity2208 /
10de:1535 /BDF01:00.0 /VBIOS94.02.71.00.01 /12288MiB is checked before USB work.
USB must be FAT32, non-system, busUSB; ambiguous/missing drives refused. Paths,
hashes and reparse tags checked, all collisions backed up before staging,
disk/partition identity rechecked before writes; old capture directories retained.
22 PowerShell5.1/7.6 policy tests pass;7 Python setup tests pass. Actual disconnected
USB refused without staging. Both package ZIPs independently verified13/11 files.
Registry Secure Boot0/off. Kingston D: was exFAT with recordings; user explicitly
authorized format without backup. Now FAT32/RTX3080TI. Physical board RUN00 passed
exact2208/10de:1535 identity,16 valid register reads and1MiB PROM. Four private
capture files match the USB; offline audit passes FWSEC fuse2/booter1 signatures,
DMA geometry, boot descriptor, layout and host-copy FRTS encoding plus negative
parser cases. Audit output data/uefi-probe/3080ti-board-audit-20261025-run00/;
raw copy data/uefi-probe/3080ti-usb/captures-20261025-170200-5156551ec31e4c2d80848e60b4258684/.
Ownership probe now staged; all12 package files independently hash verified;
board RUN00 retained on USB. OneDrive cloud-tag handling and existing drive-root parent
creation fixed after real staging refusals; symbolic links/junctions/unknown tags
remain refused. Next user manually boots F8 ->UEFI Kingston, lets ownership probe
finish, then Windows Boot Manager. Collect/review RTX-UNLOCK/RUNnn/GOP.TXT before
building the unlock. GPU OK/error0, zero NVIDIA Error/Critical events this boot.
Audit now binds subsystem10de:1535/address0000:01:00.0 and ownership
config_before[2c]=153510de, refusing other3080Ti boards/slots. No unlock firmware
executed or built, no internal partition/BCD change or automatic reboot. Backups/copies stay under
ignored data/uefi-probe/3080ti-usb/. Follow [USB workflow](RTX3080TI-WINDOWS-UNLOCK-SETUP-20261025.md).

LATEST installed3080Ti: [four-model comparison](RTX3080TI-VS-3060-20261025.md).
PCI2208/subsystem10de:1535, VBIOS94.02.71.00.01,12288MiB, driver610.88,350W.
No project3080Ti unlock attempted; selector state not independently captured.
Capture RTX3080Ti Baseline.cmd passed actual hardware and all three compute
reference checks: FP32 25.683/FP16 70.350/BF16 70.363TFLOPS. Private baseline
is under data/uefi-probe/3080ti-baseline-20261025-*/. Exact-command four-profile
chat/streaming/two128-token checks passed, temperature0.1/seed42/cacheoff.
Ornith30.72/LFM78.35/Empero30.00/Qwen27B6.21t/s; versus historical unlocked3060
+8.4%/+20.0%/+1.9%/-5.8%. Auto fit differs:150–205MiB more CPU weights and
Qwen49/66 GPU layers versus51/66 previously. Contexts/options/guards unchanged;
no full-window/tool retest. Raw results data/state/rtx3080ti-bench-20261025/.
Workers exited, no router initially running/restored. GPU OK/error0, zero NVIDIA
Error/Critical events found this boot after tests. No app termination, power,
driver, firmware or boot changes. Windows-first and exact3060 restore remain.
Next collect this board's read-only PROM/register and GOP ownership captures,
audit offline, then review its own topology before building a guarded manual EFI.
Earlier paragraphs below describe preparation while3060 was still installed.


Historical3080Ti unlock preparation: [toolkit workflow](RTX3080TI-WINDOWS-UNLOCK-SETUP-20261025.md).
rtx3080ti_setup.py prepare produced data/uefi-probe/rtx3080ti-unlock-setup/
with01-board-probe.zip and02-ownership-probe.zip; these are distinct USB fallback
images, never merge them. Hashes: board ae7b5cdd1cc579fc516ebda68c9d438d433697fb78d151304d56a2cbca41785a;
ownership58f4d6beb444d423a8509dd4d1cdbb7a2e10a425e51ae2e65f2cceaa011342b8.
Ownership has no unlock linked and no firmware assets; grouped tree/entry and
2208 fixture tests pass. Six setup guard tests pass. Real3060 inventory/capture
refused before baseline compute/profile output. Capture RTX3080Ti Baseline.cmd
is ready for the card's first Windows boot; it records identity and pre-attempt
GEMM without power changes or app termination. audit mode imports strict2208/GA102
REPORT/PROM and optional read-only ownership log; generates a private exact-board
header and calls pure offline FWSEC/signature/DMA/layout checks. It never installs
or executes firmware and keeps approval/compatibility flags false. Review this
new board's display topology/driver roles before building its separate guarded
manual unlock. Current3060 is still installed; no USB connected, no3080Ti data
available and no3080Ti unlock image built. Windows-first boot unchanged; original
3060 EFI/restore and separate Linux AMD system preserved.

Historical GPU SWAP PREPARATION: Windows Boot Manager first;3060 unlock retained but
bypassed by default. [Swap instructions](WINDOWS-3060-3080TI-SWAP-20261025.md).
The next user shutdown/swap installs an unknown-board3080Ti. Verify Windows/driver,
PCI/subsystem/VBIOS/VRAM and CUDA, then collect a stock compute baseline. No3080Ti
unlock profile is prepared or authorized by the3060 evidence. Separate read-only
package/ZIP are under data/uefi-probe/rtx3080ti-readonly; no USB attached/staged.
Need its physical PROM/register and display-ownership evidence before a new unlock.
LLM hardware guard accepts exactly one3060 or3080Ti with>=12000MiB; UUID maps that
card to CUDA0. Eight guard/7 router tests pass; current3060 hardware-only preflight
passes. Four model contexts/options/thresholds unchanged, no weights reloaded.
Restore RTX3060 Unlock.cmd -> Set-GpuBootMode.ps1 -Mode3060 -Elevate requires the
original Gigabyte2503/407b1458/REV_A1, BDF01:00.0, VBIOS94.06.14.40.b2,12GB,
Secure Boot off, saved internal disk/GUID/hash. Actual guard passed on current
card;10 policy tests pass on Windows PowerShell5.1 and7.6. It reenables the existing
entry and leaves Windows second; no reboot. ModeStock restores Windows-first.
Private swap state/backups remain under data/uefi-probe/internal-startup/. Existing
paired3060 verification remains historical, while BootUnlockEnabled=false records
its effective bypass. Keep Linux AMD and credentials unrelated settings intact.

LATEST: paired automatic payload verified successful in RUN0004:
[physical paired-profile result](RTX3060-AUTOMATIC-PAIRED-STARTUP-20261025.md).
It accepted initial70520074/5, passed complete preflight/live PROM, AUTO_START,
one transaction/FLR with result0/quiesced1/maps0/retained0/fault0/safe1, display
restored and9216-pixel zero-mismatch readback; Windows handoff without another reset.
FP16 50.459/BF16 50.792TFLOPS (+88.0%/+89.6% stock), FP32 8.778TFLOPS.
Driver610.88/170W unchanged, GPU OK/error0, zero NVIDIA Error/Critical events found
since boot after compute; post-test42C. Logs copied/hash-verified; U: removed.
EFI SHA256 a57b0621ea87dd53c0a50aceca8de2467f2f4c3da1580f1fee230af6b8844394.
Private status automatic-paired-startup-verified, AutoInternalBootVerified=true,
VerifiedAutomaticRun=RUN0004. Capture metadata automatic-paired-boot-capture.private.json
under data/uefi-probe/internal-startup/. Keep prior RUN0000/RUN0001/RUN0003
metadata immutable for reproducible builds. No payload/boot/partition changes or
second runtime unlock during verification. Do not rerun unlock in this session.
One paired-payload nonzero-branch boot is validated; paired-binary zero-branch
physical execution, repeated starts, sleep/resume and updates remain untested.
Earlier zero-only RUN0001 and manual RUN01 successes remain valid for those boots;
RUN0003 failed under the superseded zero-only binary. F8 Windows fallback and
six-second Esc gate retained. Earlier notes below are historical.

Original automatic-build first verification FAILED to apply the unlock:
[logs, compute results and diagnosis](RTX3060-AUTOMATIC-FIRST-BOOT-20261025.md).
The internal EFI executed RUN0000 but refused unlock-preflight with EFI_NOT_READY,
touched0, before automatic start/transaction/FLR. Captured initial SS0/SS1 were
zero/zero, while the fixed profile expects the earlier nonzero pair. Do not skip
ColdCheck or mark the unlock successful. Later layout/PROM checks were not reached.
Current Windows FP16/BF16 are 26.786/26.806TFLOPS; device OK/error0, no NVIDIA
Error/Critical events found. Logs copied/hash-verified, U: removed. Same dedicated
ESP GUID is now partition4 after reboot; private bookkeeping corrected from5.
Firmware order/payload/guards were not changed. A reviewed startup-profile
correction and another physical boot test remain necessary. Prior LLM samples
below belong to the successful manual-unlock boot, not the current stock state.

Latest October 25 LLM tests: [results and model research](RTX3060-UNLOCKED-LLM-20261025.md).
Unchanged profiles passed short chat/streaming and two 128-token temperature 0.1
speed samples. Means: Ornith 28.34, LFM 65.29, Empero 29.45, Qwen27B 6.59 tok/s.
Historical differences from October 23 locked results are +6.4%, +1.1%, +10.8%, -2.1%.
All model placements match saved baselines. These are not controlled causal unlock
gains; LFM speed is reasoning-only. No full-window, tool or long-prompt rerun.
Curated JSON is public-safe; raw outputs remain ignored. Workers exited; no
nvlddmkm Error/Critical events found this boot. No profile/runtime/boot changes.
Recommended future experiment: full-GPU LFM2.5-2.6B BF16 or Qwen3.5-4B 16-bit,
separately measuring prefill and decode; candidates are not installed.

Automatic internal boot is installed; first boot refused preflight, as recorded above:
[installation, recovery and OS-update behavior](RTX3060-AUTOMATIC-INTERNAL-BOOT-20261025.md).
The user explicitly approved the 512 MiB C: shrink and dedicated FAT32 ESP.
Exactly 536870912 bytes were released once; original partition identities and
unrelated sizes are preserved. The actual-GUID automatic EFI and all 27 payload
files pass hash checks; unlock first, original Windows Boot Manager second.
Original Windows entry is unchanged; Secure Boot/Fast Startup off; U: removed.
Private state and BCD/partition backups remain under
`data/uefi-probe/internal-startup/`. The first attempt stopped on a PowerShell
null-to-empty-path state-write bug after shrinking C. A read-only audit confirmed
no new partition/entry; corrected state writes and guarded Mode Resume completed
the installation without another shrink. Installer now passes 20 policy/state/
resume checks; actual EFI build passes 14 automatic/internal-source cases.
The installer initiated no reboot or second unlock. The subsequent user restart
ran the entry but refused preflight. Physical automatic unlock remains unsuccessful. F8 -> Windows Boot Manager bypasses the
application; six-second Esc cancellation is retained. Preview must not be used.

**Latest October25 result: first physical unlock succeeded in Windows.**
[Execution and identical-executable comparison](RTX3060-WINDOWS-UNLOCK-RESULT-20261025.md).
RUN01 logs are hash-verified in ignored `data/uefi-probe/captures/20261025-UNLOCK-RUN01/`.
One FLR, maps0/retained0/fault0/safe1, SS0=88888888/SS1=8, display restoration,
resolution cycle and9216-pixel zero-mismatch readback pass; Windows Boot Manager
starts without a reset. Driver610.88 recognizes the3060 with StatusOK/error0;
no nvlddmkm Error/Critical events since this boot were found at inspection.
At unchanged170W, the same short CUDA GEMM executable measures FP16
26.835->50.724TFLOPS (+89.0%), BF16 26.788->50.591 (+88.9%), FP32 8.643->8.540.
This is one boot and one short sample per arm; no INT8, broad numerical,
long-run, repeat-boot or sleep/resume validation. That manual trial made no ESP/BCD/boot-order/driver/VBIOS change;
the later internal installation is recorded above. Do not rerun unlock in this boot. Preserve
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
