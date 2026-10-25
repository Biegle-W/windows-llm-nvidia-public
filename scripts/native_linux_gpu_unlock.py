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
        raise RuntimeError("Native Linux is required; Windows/WSL cannot unlock the physical GPU.")
    if platform.machine() not in ("x86_64", "amd64"):
        raise RuntimeError("This preparation helper supports x86_64 only.")


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
                      "model": SUPPORTED.get(device, "NVIDIA model requiring separate review")})
    return found


def targets(value, cards):
    selected = value.lower().split(",")
    by_bdf = {card["bdf"]: card for card in cards}
    if len(selected) != len(set(selected)) or not selected:
        raise RuntimeError("PCI addresses are empty or duplicated.")
    for address in selected:
        if not BDF.fullmatch(address) or address not in by_bdf:
            raise RuntimeError(f"Not a current NVIDIA display-device PCI address: {address}")
        if by_bdf[address]["device"] not in SUPPORTED:
            raise RuntimeError(f"This helper does not allow this model: {address}; only 2503/2208 are allowed.")
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
        raise RuntimeError("Automatic installation supports Ubuntu/Debian only; follow upstream for other distributions.")
    if not Path("/etc/default/grub").is_file():
        raise RuntimeError("GRUB configuration was not found; other bootloaders are not modified automatically.")
    for tool in ("update-grub", "update-initramfs", "nvidia-smi"):
        if not shutil.which(tool):
            raise RuntimeError(f"Missing {tool}; finish native Linux and NVIDIA driver installation first.")
    if not devices():
        raise RuntimeError("No physical NVIDIA PCI display device was found.")
    run("nvidia-smi", "--query-gpu=name,pci.bus_id,driver_version", "--format=csv", capture=True)


def mutation_gate():
    prerequisites()
    if secure_boot() not in ("disabled", "not-applicable-legacy-boot"):
        raise RuntimeError("Secure Boot is enabled or unknown; this helper does not sign modules, enroll MOKs or disable Secure Boot.")


def verify_source():
    # enable runs as root against the ordinary user's checkout. Trust only this
    # exact path for these read-only Git calls, without editing global config.
    git = ("git", "-c", f"safe.directory={SOURCE}", "-C", str(SOURCE))
    if run(*git, "rev-parse", "HEAD", capture=True) != PIN:
        raise RuntimeError("Upstream source is not pinned to the reviewed revision.")
    if run(*git, "status", "--porcelain", capture=True):
        raise RuntimeError("Upstream source has changes; refusing automatic overwrite or installation.")


def prepare_source():
    native_only()
    if os.geteuid() == 0:
        raise RuntimeError("Run source/install as a regular user; upstream invokes sudo where needed.")
    if not SOURCE.exists():
        SOURCE.parent.mkdir(parents=True, exist_ok=True)
        run("git", "clone", "--no-checkout", UPSTREAM, str(SOURCE))
        run("git", "-C", str(SOURCE), "checkout", "--detach", PIN)
    verify_source()
    print(f"Pinned source: {SOURCE}\nHEAD={PIN}")


def check():
    native_only()
    print(json.dumps({"kernel": platform.release(), "gpus": devices(),
                      "secure_boot": secure_boot(), "reviewed_commit": PIN,
                      "running_kernel_arguments": read("/proc/cmdline"),
                      "owned_grub_dropin": GRUB.exists()}, ensure_ascii=False, indent=2))
    prerequisites()
    print(run("nvidia-smi", "--query-gpu=name,pci.bus_id,driver_version", "--format=csv", capture=True))
    print("Checks complete; the unlock has not been installed/enabled by this check.")


def install():
    mutation_gate()
    prepare_source()
    run("sudo", "apt-get", "install", "-y", "--no-install-recommends",
        "build-essential", "git", "python3", "dkms", "debhelper", "dh-sequence-dkms",
        "zstd", "mokutil", f"linux-headers-{platform.release()}")
    run("make", "install-deb", f"CACHE={PROJECT / 'data/cache/gpu-unlock'}", cwd=SOURCE)
    print("Installation complete; no unlock boot argument was added. Record the locked baseline before enable.")


def owned(path):
    if path.exists() and MARKER not in path.read_text().splitlines(keepends=True)[:2]:
        raise RuntimeError(f"An existing file is not managed by this helper; stopping: {path}")


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
                raise RuntimeError("The current boot image does not contain the gpu_unlock module.")
            if "scripts/init-top/00-local-llm-gpu-unlock" not in listing.splitlines():
                raise RuntimeError("The current boot image does not contain the early loader.")
            for firmware in run("modinfo", "-F", "firmware", "gpu_unlock", capture=True).splitlines():
                if not any(re.fullmatch(r"(?:usr/)?lib/firmware/" + re.escape(firmware) +
                                       r"(?:\.(?:xz|gz|zst))?", line)
                           for line in listing.splitlines()):
                    raise RuntimeError(f"Boot image is missing firmware: {firmware}")
        run("update-grub")
    except Exception:
        for path, previous in old.items():
            if previous is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(previous[0])
                path.chmod(previous[1])
        print("Generation failed; original configuration restored. Attempting image recovery. Do not reboot yet.", file=sys.stderr)
        for command in (("update-initramfs", "-u", "-k", "all"), ("update-grub",)):
            try:
                run(*command)
            except subprocess.CalledProcessError:
                print(f"Recovery still failed; repair this first: {' '.join(command)}", file=sys.stderr)
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
        raise RuntimeError("enable requires sudo.")
    selection = targets(value, devices())
    # Check installed version and reviewed source; post-boot proof is still required.
    version = run("modinfo", "-F", "version", "gpu_unlock", capture=True)
    if version != "1.0.0":
        raise RuntimeError("The current kernel lacks the expected gpu_unlock 1.0.0; run install first.")
    verify_source()
    for path in (Path("/etc/default/grub"), *Path("/etc/default/grub.d").glob("*.cfg")):
        if path != GRUB and "gpu_unlock.targets=" in path.read_text():
            raise RuntimeError(f"An unlock argument already exists; reconcile it manually first: {path}")
    transactional_update(boot_files(selection), verify_image=True)
    print("Next-boot configuration generated for the selected PCI addresses. Fully power off and start again yourself; current runtime state is unchanged.")


def disable():
    # Recovery must still work with the card removed or Secure Boot re-enabled.
    native_only()
    if os.geteuid() != 0:
        raise RuntimeError("disable requires sudo.")
    transactional_update({GRUB: None, HOOK: None, EARLY: None})
    print("Removed this helper's unlock configuration. Fully power off and start again to restore state; packages remain installed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "source", "install", "enable", "disable"))
    parser.add_argument("--targets", help="Exact native Linux PCI addresses from check, comma-separated; all is not accepted")
    args = parser.parse_args()
    if args.action == "enable" and not args.targets:
        parser.error("enable requires an explicit --targets argument")
    try:
        if args.action == "enable":
            enable(args.targets)
        else:
            {"check": check, "source": prepare_source, "install": install, "disable": disable}[args.action]()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"Stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())
