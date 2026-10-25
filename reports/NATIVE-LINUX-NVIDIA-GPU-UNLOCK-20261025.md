# Native Linux GPU unlock handoff for the NVIDIA host - October 25, 2026

**Preparation is complete; the unlock is not installed or enabled.** The user chose an additional SSD for native Linux while preserving Windows. That SSD has not yet been detected. No partition, boot entry, Secure Boot setting, Windows driver or inference configuration was changed. The separate dual-AMD Linux machine is outside this task.

Update: [Further Windows research](WINDOWS-GPU-UNLOCK-RESEARCH-20261025.md) found real desktop RTX 3060/2504 and single-GPU Intel-without-iGPU UEFI successes, plus a general GA106 experimental framework. This 2503/B760M host still needs read-only capture and adaptation. Native Linux remains an option rather than the only possible route.

## Hardware, pinned source and limitations

This host has an i5-13600KF, 16 GB DDR5-6000, RTX 3060 12 GB and Windows NVIDIA driver 610.88. The installed card is `10de:2503`. A standard retail RTX 3080 Ti 12 GB is planned, normally `10de:2208`; verify its actual ID after arrival. Linux PCI addresses can differ from Windows and can change after adding another card.

The observed WSL kernel was `6.18.33.2-microsoft-standard-WSL2`, with `/dev/dxg` and no physical NVIDIA PCI device exposed. The unlock module must run before the NVIDIA driver binds the physical GPU, so this cannot be done inside WSL. See [NVIDIA's WSL driver documentation](https://docs.nvidia.com/cuda/wsl-user-guide/index.html).

[Pinned upstream source](https://github.com/Zagitta/gpu-unlock/tree/af28cbbfd3d922a659227ecfb7369adfd924cf03) is cached in ignored `runtimes/gpu-unlock-native/`, at HEAD `af28cbbfd3d922a659227ecfb7369adfd924cf03`. The helper allows only `2503` and `2208`, using explicit PCI addresses rather than `targets=all`. This does not flash VBIOS or increase VRAM.

Automation covers **Ubuntu/Debian + GRUB + initramfs-tools + x86_64**. The helper does not install an OS, partition disks, install the NVIDIA driver or reboot. It refuses installation/enabling when Secure Boot is enabled or unknown. Module signing and MOK enrollment are not implemented, and Secure Boot is never disabled automatically. Keeping Secure Boot requires a separately verified signing workflow and corresponding helper support.

## Installing Linux on the additional SSD

1. Identify the new SSD by model and capacity. Retain the Windows recovery key in case firmware changes trigger BitLocker recovery. This task did not read or change encryption settings.
2. Prefer temporarily disconnecting the Windows SSD during installation. Install Ubuntu LTS in UEFI mode on the new SSD, including its own EFI partition. Reconnect Windows afterward and choose the OS through the firmware boot menu. The KF processor has no iGPU, so a discrete GPU must provide display output.
3. Install Ubuntu's recommended NVIDIA driver through Additional Drivers, reboot and confirm normal `nvidia-smi` operation before unlocking. See [Ubuntu's driver documentation](https://documentation.ubuntu.com/server/how-to/graphics/install-nvidia-drivers/). Do not copy Windows CUDA DLLs or change the AMD machine.
4. Copy `scripts/native_linux_gpu_unlock.py`, this handoff and optionally `runtimes/gpu-unlock-native/` to `~/Local-LLM/` on Linux ext4, preserving the directory structure. Windows runtimes/models are not needed. Without the cached source, the helper downloads the same pinned commit.

## Native Linux checks and baseline

Run these commands in native Linux on the new SSD:

```bash
cd ~/Local-LLM
sudo apt-get update
sudo apt-get install python3 git mokutil initramfs-tools
python3 scripts/native_linux_gpu_unlock.py check
```

`check` is read-only and lists current PCI addresses, models and Secure Boot state. Resolve driver or bootloader prerequisites first. Before enabling, retain a baseline with the same Linux kernel/driver, power limit, model, context, batch, warmup and output length. If CUDA PyTorch is installed, measure FP16/BF16-input GEMM with FP32 accumulation and check numerical error; also measure real inference and temperatures. Windows measurements are not a Linux control.

## Installation and enabling

```bash
# Run as a regular user; upstream invokes sudo where needed.
python3 scripts/native_linux_gpu_unlock.py source
python3 scripts/native_linux_gpu_unlock.py install
```

`install` installs build dependencies and current-kernel headers, then runs pinned upstream `make install-deb`. Upstream downloads SHA256-pinned inputs, generates firmware, runs its tests, builds DKMS packages and updates initramfs. Network access and disk space are required. Source/download caches stay in ignored project `runtimes/` and `data/cache/`. Installation itself does not add the unlock kernel argument.

Explicitly select addresses copied from the current Linux `check` output. These addresses are examples:

```bash
sudo python3 scripts/native_linux_gpu_unlock.py enable --targets 0000:01:00.0
# After adding the 3080 Ti, run check again and select current addresses, e.g.:
# sudo python3 scripts/native_linux_gpu_unlock.py enable --targets 0000:01:00.0,0000:02:00.0
```

The helper preserves existing arguments through a separate GRUB drop-in and adds an initramfs hook/init-top early loader, including for versions that do not read upstream `modules.d`. It checks that the current-kernel image contains the module, declared firmware and early loader. Generation failure restores the original files and attempts to rebuild the original images. If recovery also fails, repair the error before rebooting. Three independent files are managed:

- `/etc/default/grub.d/99-local-llm-gpu-unlock.cfg`
- `/etc/initramfs-tools/hooks/local-llm-gpu-unlock`
- `/etc/initramfs-tools/scripts/init-top/00-local-llm-gpu-unlock`

After successful enabling, fully power off and start the machine yourself. The helper never initiates shutdown. Then inspect:

```bash
cat /proc/cmdline
sudo journalctl -k -b | grep -Ei 'gpu.unlock|NVRM|Xid'
nvidia-smi
lspci -nnk -d 10de:
```

Confirm the selected GPU's unlock steps succeeded, normal NVIDIA binding followed and there are no Xid errors. Repeat numerical/GEMM and inference checks with the original parameters. An unlocked log alone does not prove improved performance. Measure each GPU separately; dual-GPU P2P, TP and Strata/Maya require separate configuration/validation. Recheck DKMS and boot logs after kernel updates.

## Disabling and recovery

```bash
cd ~/Local-LLM
sudo python3 scripts/native_linux_gpu_unlock.py disable
```

This removes only the helper's three managed files and rebuilds initramfs/GRUB, retaining packages and source. It remains available after removing a card or re-enabling Secure Boot. Fully power off and start again before checking; it does not immediately restore the state of an already running GPU.

If Linux fails to boot, press `e` in GRUB and temporarily remove `gpu_unlock.targets=...` from the Linux line. Boot and run `disable`. For complete package removal, disable first, then run `sudo apt-get remove gpu-unlock-dkms gpu-unlock-firmware`; confirm image generation succeeded before powering off. Preserve the independent Windows SSD and firmware boot entry.

## Evidence and performance expectations

- [3060 PR #13](https://github.com/Zagitta/gpu-unlock/pull/13): tested `2504`, roughly 1.85x FP16/BF16 GEMM, almost unchanged llama.cpp Q4 decode. This does not validate this host's `2503`.
- [3060 Strata #31](https://github.com/Zagitta/gpu-unlock/issues/31): four-card report of prefill 450 to 600 t/s, little decode change. Neither a local single-card measurement nor an exact PCI-ID report.
- [Retail 3080 Ti report](https://github.com/Zagitta/gpu-unlock/issues/2#issuecomment-6329404759): at 315 W, BF16 71.59 to 113.98 TFLOPS and TF32 35.65 to 65.28, for the author's hardware/software only.
- [Engineering 20 GB 3080 Ti #28](https://github.com/Zagitta/gpu-unlock/issues/28): `2205` showed no BF16 gain after selector writes. The helper rejects that ID; it is not the standard `2208`.

Current local GGUF profiles mix GPU/RAM weights and CPU KV; bandwidth and RAM access can limit decode, so no 2x inference claim is made. Ten host-only tests passed, covering guards/rollback, generated shell syntax and preservation of existing GRUB arguments. An actual Windows `check` was correctly refused. **Native Linux installation, DKMS build, real boot/unlock, temperatures and performance A/B remain untested.**
