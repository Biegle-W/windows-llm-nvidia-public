# Windows GPU 解锁补充调查 — 2026-10-25

**结论：Windows 已有实际成功的 UEFI 解锁，包括桌面 RTX 3060；本机仍需要适配和首次启动验证。无需为了这项技术先安装 Linux。** 本次只调查源码和读取硬件信息，没有安装 EFI、挂载系统 EFI 分区、修改 BCD/NVRAM、解密磁盘、改变驱动或运行解锁。

## 本机匹配情况

| 项目 | 本机读取结果 |
|---|---|
| 主板 / BIOS | ASUS TX GAMING B760M WIFI / 1836，固件日期 2026-04-16 |
| CPU / RAM | i5-13600KF，无核显 / 16 GB DDR5-6000 |
| GPU | Gigabyte RTX 3060 12 GB，`10de:2503`，subsystem `1458:407b` |
| VBIOS / Windows NVIDIA | `94.06.14.40.b2` / `610.88` |
| Secure Boot | 注册表 `UEFISecureBootEnabled=0`；特权确认命令权限不足 |
| Windows 快速启动 | 注册表 `HiberbootEnabled=0` |
| 系统盘 BitLocker | 未确认；只读查询需要当前进程没有的管理员权限 |
| 未来 3080 Ti | 尚未安装，不能提前假定具体板卡、PROM、PCI 地址和显示拓扑 |

没有核显不再能作为否定 Windows 解锁的理由：已有 i7-12700F、单张 3070 Ti、所有显示器接独显的成功报告。但不同主板/BIOS 的 GOP 和 AMI 聚合控制台结构可能不同，不能把那个配置直接套用。

## 找到的实际 Windows 证据

| 案例 | 原始证据与测量 | 与本机的差别 |
|---|---|---|
| 桌面 RTX 3060 12 GB | [predator0321 实验记录](https://github.com/predator0321/rtx3060-ga106-uefi-experiment/tree/ca3041b77eb933c594bfd637bb6c71107bef94d2)：FP16 25.74→47.58、BF16 25.94→47.98 TFLOPS；USB 执行及内部独立 ESP 执行有记录 | ASUS `2504 / 1043:881d`，VBIOS `94.06.25.00.b6`；驱动也是 610.88，但本机是 Gigabyte `2503` |
| 无核显 Intel + RTX 3070 Ti | [Windows 项目 issue #4](https://github.com/impacifist/Windows-GPU-UNLOCK/issues/4)，2026-10-24 更新；ASUS B660M-E D4/BIOS4003、i7-12700F、MSI2482，FP16/BF16 约43.7→89 TFLOPS | 证明单卡无核显可行，不证明 B760M/3060 的控制台释放流程一致 |
| RTX 3060 Laptop 6 GB | [Zagitta issue #58](https://github.com/Zagitta/gpu-unlock/issues/58)，2026-10-24；ASUS FA506QM、2520，FP16 +35.24%、BF16 +48.89%，同次启动接续 Windows | AMD 核显保持 GOP，6GB 移动版，SS1 保留为4，不能直接套用 |
| RTX 3090 FE | [兼容说明](https://github.com/impacifist/Windows-GPU-UNLOCK/blob/e3f03cd9389195adcabda4743d8fc2922b32498c/docs/COMPATIBILITY.en.md)：特定 B650M/BIOS3057，已验证 headless 启动 | 专用板卡/固件配置，不是通用安装器 |
| RTX 3090 Ti | [craftingmod 项目](https://github.com/craftingmod/rtx30-unlock/tree/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8) 声明验证 Colorful2203、VBIOS94.02.A0.00.08、Windows驱动615.56 | GA102 的另一个 Windows 案例；不是3080 Ti的本机验证 |

3060 的 ComfyUI Anima 在同一组选项下报告 68.53→47.40 秒，时间减少30.8%；若与原先更快的另一组选项57.63秒相比，则减少17.8%。使用 `fp16_accumulation` 的那组解锁前后几乎不变。报告没有完整模型哈希/精度、同一随机种子集合和长时间温度控制，不能推广成所有绘图任务或本机 LLM 的收益。

本次没有找到与 **Gigabyte2503 + B760M1836** 相匹配的 Windows 实测，也未找到可直接用于未来特定3080Ti的 Windows 适配证据。[3080 Ti 的 Linux 测量](https://github.com/Zagitta/gpu-unlock/issues/2#issuecomment-6329404759) 不等同 Windows 引导验证。

## 逐项核对源码后的区别

### predator0321：最接近本机型号的实测，但明确拒绝2503

[entry.c](https://github.com/predator0321/rtx3060-ga106-uefi-experiment/blob/ca3041b77eb933c594bfd637bb6c71107bef94d2/uefi/entry.c#L36)、[runtime.c](https://github.com/predator0321/rtx3060-ga106-uefi-experiment/blob/ca3041b77eb933c594bfd637bb6c71107bef94d2/uefi/runtime.c#L154) 与 [prepare_usb.py](https://github.com/predator0321/rtx3060-ga106-uefi-experiment/blob/ca3041b77eb933c594bfd637bb6c71107bef94d2/uefi/prepare_usb.py#L52) 均限定 `2504`。所以现成工具不能原样支持本机2503，修改配置中的 subsystem 也不够。

它保留 SS1，实测桌面卡保持 `0x2`；只改 SS0。构建使用 GNU-EFI/GCC，可在 Linux 构建，生成 EFI 后在 Windows 主机启动，不要求最终使用 Linux 推理。旧子目录文档仍有“未验证”横幅，根 README 解释了之后一台2504的真实结果；两者需区分时间和范围。

### craftingmod：值得进一步适配的通用实验框架

[GA10x 设计说明](https://github.com/craftingmod/rtx30-unlock/blob/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8/docs/agent/GA10X-EXPERIMENTAL.md) 和 [gpu_family.py](https://github.com/craftingmod/rtx30-unlock/blob/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8/tools/gpu_family.py) 接受 GA102/103/104/106/107 芯片；PCI `22xx/24xx/25xx` 只是候选，之后读取真实芯片字段。这使2503和标准2208成为可研究目标，不构成已验证支持。

[当前 build.ts](https://github.com/craftingmod/rtx30-unlock/blob/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8/tools/build.ts) 默认构建 v20 外部/自动配置、GOP释放与恢复、Windows接续启动路径；Bun + clang/lld-link 可在 Windows 构建。单独的 [build-probe.ts](https://github.com/craftingmod/rtx30-unlock/blob/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8/tools/build-probe.ts) 构建只读探针，不能把默认解锁镜像当作只读探针。

[外部配置说明](https://github.com/craftingmod/rtx30-unlock/blob/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8/docs/agent/EXTERNAL-PROFILE.md) 包含176字节 PROFILE.BIN、实际 PROM/芯片/显存/WPR校验，以及 DEBUG.ON 首次收集和 U 确认流程；关闭 DEBUG 后的自动路径不能当作首次调查工具。部分文档还引用旧 PowerShell 路径，当前仓库已改为 TypeScript/Bun，不能照抄旧命令。

核心仍有实际 GOP 驱动/子节点/共享控制台检查，不是“识别到GA106即可解锁”。[app.c](https://github.com/craftingmod/rtx30-unlock/blob/5c076dc4ee7fa369639669fa591ac74d8f6dfcd8/src/unlock/app.c#L563) 的完成检查要求 SS0=`88888888`、SS1=`8`；与上述3060的 SS1保留策略不同。需要基于本机状态审阅这一差别，不能把别人的SS1值写死或删掉检查来强行运行。

### impacifist 与 EVGA3090 fork：显示处理和验证方法可参考

[impacifist 兼容说明](https://github.com/impacifist/Windows-GPU-UNLOCK/blob/e3f03cd9389195adcabda4743d8fc2922b32498c/docs/COMPATIBILITY.en.md) 的两个编译配置是 B650M/3090FE、B660M/3070Ti，均不是本机。无核显主机的 AMI GOP 聚合链处理值得参考，不能只替换 ID/PROM 哈希。

[EVGA3090 fork](https://github.com/bjrasmussen-jpg/windows_rtx3090_unlock/tree/48394d77fcec8bef979a8e45dbe194e2004b7964) 先做只读 UEFI 采集、主机模拟故障验证，再由人工单次启动测试；另一张5070Ti负责显示。该方法可借鉴，但不是2503单卡解锁包，自动启动仅通过模拟测试。

## 本机接下来的具体路线

1. 优先审阅 craftingmod 的独立只读探针，先构建/检查 PE 和写入路径，再用独立 FAT32 USB 的一次性启动菜单采集本机 PCI、BAR、芯片、显存/WPR、PROM 与 GOP 拓扑。保留现有 Windows Boot Manager；不直接运行 release 解锁镜像。
2. 确认磁盘加密状态和恢复手段，保存正常 Windows 的同环境基线。当前注册表显示 Secure Boot/快速启动均关闭，但 BitLocker 状态仍未确认，不自动解密系统盘。
3. 结合本机采集结果决定使用通用实验框架，还是将3060 transaction与无核显GOP处理做有检查的移植。保留固件哈希、cold-state、DMA/FLR和失败隔离检查；先验证主机模拟，再做一次手动启动。当前没有为本机构建或部署解锁 EFI。
4. 启动成功后在同一开机周期接续 Windows，不通过重启回 Windows；校验正常驱动、数值结果、FP16/BF16及真实推理。没有游戏帧数、额外CUDA核心、显存容量或INT8翻倍的承诺。
5. 3080Ti到货后重新采集其ID/PROM/拓扑；双卡时可研究将另一张卡用于显示，但不要把已有单NVIDIA探针、单卡GOP流程当成双卡支持。

因此，原生 Linux 新SSD方案继续保留；如果目标只是继续使用 Windows 推理，**现在值得先做 Windows 的只读探针与适配，而不必先迁移操作系统**。本次没有运行基准测试或改变任何推理配置。

## 调查版本与搜索范围

源码核对固定提交：craftingmod `5c076dc4ee7fa369639669fa591ac74d8f6dfcd8`；predator0321 `ca3041b77eb933c594bfd637bb6c71107bef94d2`；impacifist `e3f03cd9389195adcabda4743d8fc2922b32498c`；EVGA fork `48394d77fcec8bef979a8e45dbe194e2004b7964`；原MSI3080项目 `a08254d269af30ace9e57237abd3d8e6c261e8f5`。

也检索了 lcz.me 和 Level1Techs，没有找到本机组合的独立 Windows 解锁证据；本结论依赖上述原作者源码与报告。未将 Linux/CMP/LHR挖矿/ReBAR/P2P 的结果混作 Windows Tensor解锁证明。
