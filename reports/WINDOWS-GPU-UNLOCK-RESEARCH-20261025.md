# Further Windows GPU unlock research - October 25, 2026

**Windows UEFI unlocks have succeeded on real hardware, including a desktop RTX 3060. This host still needs adaptation and its first validated boot; installing Linux is not a prerequisite for the technique.** This investigation reviewed source and read inventory only. No EFI was installed, system ESP mounted, BCD/NVRAM changed, disk decrypted, driver changed or unlock attempted.

## Host compatibility

| Item | Observed configuration |
|---|---|
| Motherboard / BIOS | ASUS TX GAMING B760M WIFI / 1836, firmware date April 16, 2026 |
| CPU / RAM | i5-13600KF, no iGPU / 16 GB DDR5-6000 |
| GPU | Gigabyte RTX 3060 12 GB, `10de:2503`, subsystem `1458:407b` |
| VBIOS / Windows NVIDIA driver | `94.06.14.40.b2` / `610.88` |
| Secure Boot | Registry `UEFISecureBootEnabled=0`; privileged confirmation lacked permission |
| Windows Fast Startup | Registry `HiberbootEnabled=0` |
| System-drive BitLocker | Unknown; the read-only query required administrator privileges unavailable to this process |
| Future 3080 Ti | Not installed; exact board, PROM, PCI address and display topology are not yet known |

Lack of an iGPU does not rule out the Windows route: an i7-12700F with one 3070 Ti and all monitors connected to it has succeeded. GOP and AMI aggregate-console topology can differ by motherboard/BIOS, so that profile cannot simply be reused.

## Actual Windows evidence

| Case | Original evidence and measurements | Difference from this host |
|---|---|---|
| Desktop RTX 3060 12 GB | [predator0321 experiment](https://github.com/predator0321/rtx3060-ga106-uefi-experiment/tree/ca3041b77eb933c594bfd637bb6c71107bef94d2): FP16 25.74 to 47.58 and BF16 25.94 to 47.98 TFLOPS; USB and separate internal ESP execution recorded | ASUS `2504 / 1043:881d`, VBIOS `94.06.25.00.b6`; same driver610.88, but this host is Gigabyte2503 |
| Intel without iGPU + RTX 3070 Ti | [Windows issue #4](https://github.com/impacifist/Windows-GPU-UNLOCK/issues/4), updated October24: ASUS B660M-E D4/BIOS4003, i7-12700F, MSI2482; FP16/BF16 roughly43.7 to89 TFLOPS | Establishes single-GPU/no-iGPU feasibility, not matching B760M/3060 console release |
| RTX 3060 Laptop 6 GB | [Zagitta issue #58](https://github.com/Zagitta/gpu-unlock/issues/58), October24: ASUS FA506QM,2520, FP16 +35.24%, BF16 +48.89%, same-boot Windows handoff | AMD iGPU retained GOP; mobile6GB card, SS1 preserved at4 |
| RTX 3090 FE | [Compatibility documentation](https://github.com/impacifist/Windows-GPU-UNLOCK/blob/e3f03cd9389195adcabda4743d8fc2922b32498c/docs/COMPATIBILITY.en.md): specific B650M/BIOS3057 headless boot validated | Exact board/firmware profile, not a general installer |
| RTX 3090 Ti | [craftingmod project](https://github.com/craftingmod/rtx30-unlock/tree/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8) lists Colorful2203, VBIOS94.02.A0.00.08, Windows driver615.56 as tested | Another GA102 Windows case, not validation of this host's future3080Ti |

The 3060 ComfyUI Anima report measured 68.53 to47.40 seconds with matching options, a30.8% time reduction. Against the previously faster alternative option set at57.63 seconds, the reduction was17.8%. With `fp16_accumulation`, locked/unlocked times were almost unchanged. Missing complete model hashes/precision, matched seed sets and controlled sustained temperatures prevent extrapolating these results to all image workloads or local LLMs.

No matching Windows measurement was found for **Gigabyte2503 + B760M1836**, nor a Windows profile directly applicable to a specific future3080Ti. The [3080 Ti Linux measurement](https://github.com/Zagitta/gpu-unlock/issues/2#issuecomment-6329404759) does not validate Windows booting.

## Source-level differences

### predator0321: closest measured GPU family, but explicitly rejects2503

[entry.c](https://github.com/predator0321/rtx3060-ga106-uefi-experiment/blob/ca3041b77eb933c594bfd637bb6c71107bef94d2/uefi/entry.c#L36), [runtime.c](https://github.com/predator0321/rtx3060-ga106-uefi-experiment/blob/ca3041b77eb933c594bfd637bb6c71107bef94d2/uefi/runtime.c#L154) and [prepare_usb.py](https://github.com/predator0321/rtx3060-ga106-uefi-experiment/blob/ca3041b77eb933c594bfd637bb6c71107bef94d2/uefi/prepare_usb.py#L52) all require `2504`. The unmodified tool cannot support this2503; changing subsystem configuration alone is insufficient.

It changes SS0 while preserving SS1, observed at `0x2` on the tested desktop card. GNU-EFI/GCC builds can run on Linux and produce EFI for a Windows host; Linux inference is not required. Older subdirectory documentation retains unvalidated banners, while the root README documents the later real2504 results. Keep their dates and scopes distinct.

### craftingmod: a general experimental framework worth adapting

The [GA10x design](https://github.com/craftingmod/rtx30-unlock/blob/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8/docs/agent/GA10X-EXPERIMENTAL.md) and [gpu_family.py](https://github.com/craftingmod/rtx30-unlock/blob/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8/tools/gpu_family.py) accept GA102/103/104/106/107 chip identities. PCI22xx/24xx/25xx is only an initial candidate filter, followed by actual chip reads. That makes2503 and standard2208 research candidates rather than validated support.

Current [build.ts](https://github.com/craftingmod/rtx30-unlock/blob/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8/tools/build.ts) defaults to v20 external/automatic profiling, GOP release/restoration and Windows handoff. Bun plus clang/lld-link can build on Windows. Separate [build-probe.ts](https://github.com/craftingmod/rtx30-unlock/blob/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8/tools/build-probe.ts) builds the read-only probe; the default unlock image must not be used as a diagnostic probe.

The [external-profile design](https://github.com/craftingmod/rtx30-unlock/blob/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8/docs/agent/EXTERNAL-PROFILE.md) includes a176-byte PROFILE.BIN, actual PROM/chip/VRAM/WPR validation, DEBUG.ON capture and U confirmation. The automatic path with DEBUG disabled is unsuitable for an initial investigation. Some documentation still references old PowerShell paths; the current tree uses TypeScript/Bun, so those commands cannot be copied blindly.

Actual GOP driver/child/shared-console checks remain; recognizing GA106 is insufficient. The [app.c completion check](https://github.com/craftingmod/rtx30-unlock/blob/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8/src/unlock/app.c#L563) requires SS0=`88888888` and SS1=`8`, differing from the3060 SS1-preserve experiment. Review that difference against this host's captured state rather than hardcoding someone else's SS1 or deleting checks.

### impacifist and EVGA3090 fork: display handling and validation references

The two [impacifist profiles](https://github.com/impacifist/Windows-GPU-UNLOCK/blob/e3f03cd9389195adcabda4743d8fc2922b32498c/docs/COMPATIBILITY.en.md) target B650M/3090FE and B660M/3070Ti, neither matching this host. The no-iGPU AMI GOP aggregate-chain handling is useful reference material, but replacing IDs/PROM hashes is not a validated port.

The [EVGA3090 fork](https://github.com/bjrasmussen-jpg/windows_rtx3090_unlock/tree/48394d77fcec8bef979a8e45dbe194e2004b7964) used read-only UEFI capture, host fault-injection tests and an operator's manual boot trial; a5070Ti provided display output. Its method is useful, but it is not a2503 single-card package, and automatic boot passed mocks only.

## Concrete next steps for this host

1. Review the separate craftingmod read-only probe, build/check its PE image and file-write paths, then use a separate FAT32 USB and the one-time boot menu to capture PCI, BAR, chip, VRAM/WPR, PROM and GOP topology. Preserve Windows Boot Manager; do not run a release unlock image directly.
2. Confirm encryption state/recovery access and retain a normal-Windows baseline with matching settings. Registry readings indicate Secure Boot/Fast Startup are off, but BitLocker remains unknown. Do not automatically decrypt the system drive.
3. Use the capture to choose the general framework or a checked port combining the3060 transaction with no-iGPU GOP handling. Keep firmware hashes, cold-state, DMA/FLR and failure containment checks. Validate host mocks before one manual hardware boot. No host-specific unlock EFI was built or deployed during this investigation.
4. After successful execution, chain into Windows in the same power cycle without rebooting. Check normal driver operation, numerical outputs, FP16/BF16 and real inference. No game-FPS, extra-core, VRAM-capacity or2x INT8 claim is made.
5. Capture the3080Ti's ID/PROM/topology after arrival. A second card may provide display output, but existing single-NVIDIA probes and single-card GOP flows do not establish multi-GPU support.

The additional-SSD native Linux plan remains available. For continued Windows inference, **read-only Windows UEFI capture and adaptation are worth pursuing before an OS migration**. No benchmark or inference configuration changed during this investigation.

## Reviewed revisions and search scope

Pinned source: craftingmod `5c076dc4ee7fa369639669fa591ac74d8f6dfcd8`; predator0321 `ca3041b77eb933c594bfd637bb6c71107bef94d2`; impacifist `e3f03cd9389195adcabda4743d8fc2922b32498c`; EVGA fork `48394d77fcec8bef979a8e45dbe194e2004b7964`; original MSI3080 project `a08254d269af30ace9e57237abd3d8e6c261e8f5`.

lcz.me and Level1Techs were also searched; no independent matching-host Windows unlock evidence was found. Conclusions rely on the original authors' source and reports above. Linux/CMP/LHR-mining/ReBAR/P2P results were not treated as Windows Tensor-unlock proof.
