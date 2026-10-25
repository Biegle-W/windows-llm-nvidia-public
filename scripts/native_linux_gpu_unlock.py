#!/usr/bin/env python3
"""Pinned native-Linux preparation for this host's RTX 3060 / retail 3080 Ti.

No action reboots, partitions disks, flashes VBIOS or installs an NVIDIA driver.
Ubuntu/Debian + GRUB + initramfs-tools only. Run check first; see the handoff.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

PIN = "af28cbbfd3d922a659227ecfb7369adfd924cf03"
UPSTREAM = "https://github.com/Zagitta/gpu-unlock.git"
PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT / "runtimes/gpu-unlock-native"
SUPPORTED = {"2503": "RTX 3060 12GB (GA106)", "2208": "RTX 3080 Ti 12GB (GA102)"}
MARKER = "# Managed by Local-LLM native_linux_gpu_unlock.py\n"
GRUB = Path("/etc/default/grub.d/99-local-llm-gpu-unlock.cfg")
HOOK = Path("/etc/initramfs-tools/hooks/local-llm-gpu-unlock")
EARLY = Path("/etc/initramfs-tools/scripts/init-top/00-local-llm-gpu-unlock")
BDF = re.compile(r"[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]\Z")


def run(*args, capture=False, cwd=None):
    result = subprocess.run(args, check=True, text=True, cwd=cwd,
                            stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else ""


def read(path):
    try:
        return Path(path).read_text().strip()
    except FileNotFoundError:
        return ""


def native_only():
    if (platform.system() != "Linux" or
            re.search(r"microsoft|wsl", platform.release(), re.I) or
            Path("/dev/dxg").exists()):
        raise RuntimeError("需要原生 Linux；Windows/WSL 不支持物理显卡解锁。")
    if platform.machine() not in ("x86_64", "amd64"):
        raise RuntimeError("此准备工具只支持 x86_64。")


def devices(base=Path("/sys/bus/pci/devices")):
    found = []
    for path in sorted(base.glob("*")):
        if read(path / "vendor") != "0x10de":
            continue
        if not read(path / "class").startswith("0x03"):
            continue  # Exclude the GPU's audio/USB functions.
        device = read(path / "device").removeprefix("0x")
        found.append({"bdf": path.name, "device": device,
                      "supported_by_helper": device in SUPPORTED,
                      "model": SUPPORTED.get(device, "需要单独审阅的 NVIDIA 型号")})
    return found


def targets(value, cards):
    selected = value.lower().split(",")
    by_bdf = {card["bdf"]: card for card in cards}
    if len(selected) != len(set(selected)) or not selected:
        raise RuntimeError("PCI 地址为空或重复。")
    for address in selected:
        if not BDF.fullmatch(address) or address not in by_bdf:
            raise RuntimeError(f"不是当前机器上的 NVIDIA 显卡 PCI 地址：{address}")
        if by_bdf[address]["device"] not in SUPPORTED:
            raise RuntimeError(f"该型号未获本工具放行：{address}；只接受 2503/2208。")
    return ",".join(selected)


def secure_boot():
    if not Path("/sys/firmware/efi").exists():
        return "not-applicable-legacy-boot"
    if not shutil.which("mokutil"):
        return "unknown (install mokutil)"
    try:
        state = run("mokutil", "--sb-state", capture=True)
    except subprocess.CalledProcessError:
        return "unknown (mokutil failed)"
    if "SecureBoot disabled" in state:
        return "disabled"
    if "SecureBoot enabled" in state:
        return "enabled"
    return "unknown"


def prerequisites():
    native_only()
    distro = dict(line.split("=", 1) for line in read("/etc/os-release").splitlines()
                  if "=" in line and not line.startswith("#"))
    if distro.get("ID", "").strip('"') not in ("ubuntu", "debian"):
        raise RuntimeError("自动安装仅限 Ubuntu/Debian；其他发行版请按上游文档操作。")
    if not Path("/etc/default/grub").is_file():
        raise RuntimeError("未发现 GRUB 配置；不自动修改其他引导器。")
    for tool in ("update-grub", "update-initramfs", "nvidia-smi"):
        if not shutil.which(tool):
            raise RuntimeError(f"缺少 {tool}；先完成原生 Linux 和 NVIDIA 驱动安装。")
    if not devices():
        raise RuntimeError("没有物理 NVIDIA PCI 显卡。")
    run("nvidia-smi", "--query-gpu=name,pci.bus_id,driver_version", "--format=csv", capture=True)


def mutation_gate():
    prerequisites()
    if secure_boot() not in ("disabled", "not-applicable-legacy-boot"):
        raise RuntimeError("Secure Boot 已开启或状态未知；本工具不自动签名、注册 MOK 或关闭 Secure Boot。")


def verify_source():
    # enable runs as root against the ordinary user's checkout. Trust only this
    # exact path for these read-only Git calls, without editing global config.
    git = ("git", "-c", f"safe.directory={SOURCE}", "-C", str(SOURCE))
    if run(*git, "rev-parse", "HEAD", capture=True) != PIN:
        raise RuntimeError("上游源码未固定到审阅版本。")
    if run(*git, "status", "--porcelain", capture=True):
        raise RuntimeError("上游源码存在改动；不自动覆盖或安装。")


def prepare_source():
    native_only()
    if os.geteuid() == 0:
        raise RuntimeError("请用普通用户运行 source/install，让上游按需调用 sudo。")
    if not SOURCE.exists():
        SOURCE.parent.mkdir(parents=True, exist_ok=True)
        run("git", "clone", "--no-checkout", UPSTREAM, str(SOURCE))
        run("git", "-C", str(SOURCE), "checkout", "--detach", PIN)
    verify_source()
    print(f"固定源码：{SOURCE}\nHEAD={PIN}")


def check():
    native_only()
    print(json.dumps({"kernel": platform.release(), "gpus": devices(),
                      "secure_boot": secure_boot(), "reviewed_commit": PIN,
                      "running_kernel_arguments": read("/proc/cmdline"),
                      "owned_grub_dropin": GRUB.exists()}, ensure_ascii=False, indent=2))
    prerequisites()
    print(run("nvidia-smi", "--query-gpu=name,pci.bus_id,driver_version", "--format=csv", capture=True))
    print("检查完成；尚未安装/启用解锁。")


def install():
    mutation_gate()
    prepare_source()
    run("sudo", "apt-get", "install", "-y", "--no-install-recommends",
        "build-essential", "git", "python3", "dkms", "debhelper", "dh-sequence-dkms",
        "zstd", "mokutil", f"linux-headers-{platform.release()}")
    run("make", "install-deb", f"CACHE={PROJECT / 'data/cache/gpu-unlock'}", cwd=SOURCE)
    print("安装完成；尚未添加解锁启动参数。先记录未解锁基线，再 enable。")


def owned(path):
    if path.exists() and MARKER not in path.read_text().splitlines(keepends=True)[:2]:
        raise RuntimeError(f"已有非本工具管理的文件，停止：{path}")


def transactional_update(files, verify_image=False):
    """Restore our drop-ins if either boot-image generator fails."""
    for path in files:
        owned(path)
    old = {path: (path.read_bytes(), path.stat().st_mode & 0o777) if path.exists() else None
           for path in files}
    try:
        for path, content in files.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, newline="\n")
                path.chmod(0o644 if path == GRUB else 0o755)
        run("update-initramfs", "-u", "-k", "all")
        if verify_image:
            listing = run("lsinitramfs", f"/boot/initrd.img-{platform.release()}", capture=True)
            if not re.search(r"(?:^|/)gpu_unlock\.ko(?:\.(?:xz|gz|zst))?$", listing, re.M):
                raise RuntimeError("当前启动镜像未包含 gpu_unlock 模块。")
            if "scripts/init-top/00-local-llm-gpu-unlock" not in listing.splitlines():
                raise RuntimeError("当前启动镜像未包含提前加载脚本。")
            for firmware in run("modinfo", "-F", "firmware", "gpu_unlock", capture=True).splitlines():
                if not any(re.fullmatch(r"(?:usr/)?lib/firmware/" + re.escape(firmware) +
                                       r"(?:\.(?:xz|gz|zst))?", line)
                           for line in listing.splitlines()):
                    raise RuntimeError(f"启动镜像缺少固件：{firmware}")
        run("update-grub")
    except Exception:
        for path, previous in old.items():
            if previous is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(previous[0])
                path.chmod(previous[1])
        print("生成失败，已恢复原配置；尝试恢复启动镜像。不要立即重启。", file=sys.stderr)
        for command in (("update-initramfs", "-u", "-k", "all"), ("update-grub",)):
            try:
                run(*command)
            except subprocess.CalledProcessError:
                print(f"恢复仍失败，请先修复：{' '.join(command)}", file=sys.stderr)
        raise


def boot_files(selection):
    # Explicit early load, including on initramfs-tools versions without modules.d.
    hook = ("#!/bin/sh\n" + MARKER + 'set -e\nPREREQ=""\n'
            'case "$1" in prereqs) echo "$PREREQ"; exit 0 ;; esac\n'
            '. /usr/share/initramfs-tools/hook-functions\nmanual_add_modules gpu_unlock\n')
    early = ("#!/bin/sh\n" + MARKER + 'PREREQ=""\n'
             'case "$1" in prereqs) echo "$PREREQ"; exit 0 ;; esac\n'
             'case " $(cat /proc/cmdline) " in\n'
             '  *" gpu_unlock.targets="*) modprobe gpu_unlock || echo "gpu_unlock: early load failed" >&2 ;;\n'
             'esac\nexit 0\n')
    grub = (MARKER + 'GRUB_CMDLINE_LINUX_DEFAULT="${GRUB_CMDLINE_LINUX_DEFAULT}'
            f' gpu_unlock.targets={selection}"\n')
    return {GRUB: grub, HOOK: hook, EARLY: early}


def enable(value):
    mutation_gate()
    if os.geteuid() != 0:
        raise RuntimeError("enable 需要 sudo。")
    selection = targets(value, devices())
    # Check installed version and reviewed source; post-boot proof is still required.
    version = run("modinfo", "-F", "version", "gpu_unlock", capture=True)
    if version != "1.0.0":
        raise RuntimeError("当前内核没有预期的 gpu_unlock 1.0.0；先 install。")
    verify_source()
    for path in (Path("/etc/default/grub"), *Path("/etc/default/grub.d").glob("*.cfg")):
        if path != GRUB and "gpu_unlock.targets=" in path.read_text():
            raise RuntimeError(f"已有解锁参数，请先人工合并：{path}")
    transactional_update(boot_files(selection), verify_image=True)
    print("已为选定 PCI 地址生成下次启动配置。请自行完整关机再开机；当前运行状态未改变。")


def disable():
    # Recovery must still work with the card removed or Secure Boot re-enabled.
    native_only()
    if os.geteuid() != 0:
        raise RuntimeError("disable 需要 sudo。")
    transactional_update({GRUB: None, HOOK: None, EARLY: None})
    print("已移除本工具的解锁配置。请完整关机再开机恢复；软件包保留供复用。")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "source", "install", "enable", "disable"))
    parser.add_argument("--targets", help="从 check 复制原生 Linux 的准确 PCI 地址，以逗号分隔；不接受 all")
    args = parser.parse_args()
    if args.action == "enable" and not args.targets:
        parser.error("enable 必须明确指定 --targets")
    try:
        if args.action == "enable":
            enable(args.targets)
        else:
            {"check": check, "source": prepare_source, "install": install, "disable": disable}[args.action]()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"停止：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())
