# NVIDIA 主机原生 Linux 解锁交接 — 2026-10-25

**准备完成，尚未安装或启用解锁。** 用户选择另加 SSD 安装 Linux，保留 Windows。新盘尚未在当前系统检测到；没有改分区、引导项、Secure Boot、Windows 驱动或推理配置。另一台双 AMD Linux 主机不属于本次任务。

## 硬件、源码与限制

本机 i5-13600KF、16 GB DDR5-6000、RTX 3060 12 GB，Windows NVIDIA 610.88。3060 PCI ID 为 `10de:2503`；计划增加标准零售 RTX 3080 Ti 12 GB，预期 `10de:2208`，到货后以实际 ID 为准。Linux 的 PCI 地址可能与 Windows 不同，安装第二张卡后也可能改变。

WSL 实测内核 `6.18.33.2-microsoft-standard-WSL2`，有 `/dev/dxg`，没有物理 NVIDIA PCI 设备。解锁模块必须在 NVIDIA 驱动绑定物理显卡之前运行，不能通过 WSL 完成。[NVIDIA WSL 驱动说明](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)。

[固定上游源码](https://github.com/Zagitta/gpu-unlock/tree/af28cbbfd3d922a659227ecfb7369adfd924cf03) 已下载到忽略目录 `runtimes/gpu-unlock-native/`，HEAD 为 `af28cbbfd3d922a659227ecfb7369adfd924cf03`。本工具只放行 `2503`、`2208`，不使用 `targets=all`。这不是 VBIOS 刷写，也不增加显存。

自动化范围：**Ubuntu/Debian + GRUB + initramfs-tools + x86_64**。工具不安装操作系统、分区、安装 NVIDIA 驱动或重启。Secure Boot 开启或状态未知时拒绝安装/启用；尚未实现模块签名/MOK 注册，不自动关闭 Secure Boot。如需保留 Secure Boot，先另行完成签名验证，再扩展工具支持。

## 新 SSD 安装

1. 新盘到货后确认目标盘型号、容量。保留 Windows 恢复密钥，避免固件变更触发 BitLocker 恢复时无法解锁。本次未读取或改变加密设置。
2. 建议安装时暂时断开 Windows SSD，使用 UEFI 安装 Ubuntu LTS 到新盘，让 Linux 的 EFI 分区也位于新盘。之后接回 Windows SSD，用固件启动菜单选系统。KF CPU 没有核显，需要独立显卡输出。
3. 在原生 Ubuntu 的 Additional Drivers 安装推荐 NVIDIA 驱动，重启后先确认 `nvidia-smi` 正常。[Ubuntu 驱动文档](https://documentation.ubuntu.com/server/how-to/graphics/install-nvidia-drivers/)。不要复制 Windows CUDA DLL 或修改 AMD 主机。
4. 将 `scripts/native_linux_gpu_unlock.py`、本文档和可选的 `runtimes/gpu-unlock-native/` 复制到新 Linux ext4 的 `~/Local-LLM/`，保持结构。无需复制 Windows runtime/models；源码未复制时工具会下载相同固定提交。

## 原生 Linux 检查与基线

下面在新盘的原生 Linux 中运行：

```bash
cd ~/Local-LLM
sudo apt-get update
sudo apt-get install python3 git mokutil initramfs-tools
python3 scripts/native_linux_gpu_unlock.py check
```

`check` 只读，列出实际 PCI 地址、型号和 Secure Boot 状态；驱动或引导器不符合要求时先修复环境。启用前保留相同 Linux 内核/驱动、功耗限制、模型、上下文、batch、预热和输出长度的基线。若已安装 CUDA PyTorch，可测 FP16/BF16 输入、FP32 累加的 GEMM，并校验数值误差；同时测真实推理、记录温度。Windows 测量不能当 Linux 对照。

## 安装与启用

```bash
# 普通用户运行，上游在必要步骤调用 sudo。
python3 scripts/native_linux_gpu_unlock.py source
python3 scripts/native_linux_gpu_unlock.py install
```

`install` 安装构建依赖及当前内核 headers，调用固定源码 `make install-deb`。上游下载 SHA256 固定输入、生成固件、运行其测试、构建 DKMS 软件包和更新 initramfs，需要网络和磁盘空间。源码/下载缓存位于项目 `runtimes/`、`data/cache/`，不进入 Git。安装本身不添加解锁启动参数。

从 `check` 复制本次 Linux 地址明确选择显卡；下例地址仅示意：

```bash
sudo python3 scripts/native_linux_gpu_unlock.py enable --targets 0000:01:00.0
# 3080 Ti 到货后重新 check，按新地址选择两张卡，例如：
# sudo python3 scripts/native_linux_gpu_unlock.py enable --targets 0000:01:00.0,0000:02:00.0
```

工具通过独立 GRUB drop-in 保留已有参数，添加 initramfs hook/init-top 提前加载脚本，兼容不读取上游 `modules.d` 的版本。生成后检查当前内核镜像含模块、声明固件和提前加载脚本。失败会恢复原文件并尝试重建原镜像；恢复也失败时先修复，不要重启。涉及三个独立文件：

- `/etc/default/grub.d/99-local-llm-gpu-unlock.cfg`
- `/etc/initramfs-tools/hooks/local-llm-gpu-unlock`
- `/etc/initramfs-tools/scripts/init-top/00-local-llm-gpu-unlock`

成功后自行完整关机再开机；工具不执行关机。随后检查：

```bash
cat /proc/cmdline
sudo journalctl -k -b | grep -Ei 'gpu.unlock|NVRM|Xid'
nvidia-smi
lspci -nnk -d 10de:
```

确认所选显卡解锁步骤成功、之后正常绑定 NVIDIA 驱动、无 Xid，再按原参数重复 GEMM/数值校验和推理测试。仅有 unlocked 日志不等于性能提升。两张卡分别测量；双卡 P2P、TP、Strata/Maya 还需另行配置验证。内核更新后重新确认 DKMS 构建及启动日志。

## 撤销

```bash
cd ~/Local-LLM
sudo python3 scripts/native_linux_gpu_unlock.py disable
```

仅移除本工具管理的三个文件并重建 initramfs/GRUB；软件包和源码保留。即使卡移除或 Secure Boot 重新开启也可撤销。完整关机再开机后检查，不会立即恢复已运行显卡状态。

启动失败时，在 GRUB 按 `e` 临时删掉 Linux 行里的 `gpu_unlock.targets=...` 再启动，进入后执行 `disable`。需要彻底卸载时先禁用，再 `sudo apt-get remove gpu-unlock-dkms gpu-unlock-firmware`，确认镜像生成成功后完整关机。Windows 的独立 SSD/固件启动入口应保留。

## 证据与性能预期

- [3060 PR #13](https://github.com/Zagitta/gpu-unlock/pull/13)：实测 `2504`，FP16/BF16 GEMM 约 1.85 倍，同报告 llama.cpp Q4 生成几乎不变。不是本机 `2503` 已通过。
- [3060 Strata #31](https://github.com/Zagitta/gpu-unlock/issues/31)：四卡报告预填充 450→600 t/s、生成变化小；不是单卡本机测量，未给准确 PCI ID。
- [标准 3080 Ti 报告](https://github.com/Zagitta/gpu-unlock/issues/2#issuecomment-6329404759)：315 W 下 BF16 71.59→113.98 TFLOPS、TF32 35.65→65.28；只对应作者的硬件/软件。
- [20 GB 工程 3080 Ti #28](https://github.com/Zagitta/gpu-unlock/issues/28)：`2205` 写入选择器后 BF16 未提升，本工具拒绝该 ID；不能当作标准 `2208`。

本机目前 GGUF 混合 GPU/RAM、CPU KV，生成还受带宽和 RAM 访问限制，不承诺翻倍。准备工具通过 10 项主机端测试，包括防护/回滚、生成 shell 语法和保留 GRUB 原参数；Windows 实际 `check` 正确拒绝执行。**原生 Linux 安装、DKMS 构建、真实启动/解锁、温度及性能 A/B 均未完成。**
