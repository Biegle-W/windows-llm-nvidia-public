#!/usr/bin/env python3
"""Prepare a fixed-evidence, manual-only experimental EFI and read-only GOP tree probe.

Never installs an EFI, selects a drive, changes boot variables or runs GPU firmware.
Firmware assets must already be extracted by the pinned upstream tools.
Raw captures, generated headers, binaries and full manifests stay in ignored data.
"""
import argparse
import ctypes as ct
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PIN = "5c076dc4ee7fa369639669fa591ac74d8f6dfcd8"
FULL_SOURCES = (
    "src/gop/app.c", "src/gop/full.c", "src/unlock/runtime.c", "src/unlock/format.c",
    "src/gop/leaf.c", "src/gop/reset.c", "src/gop/visual.c", "src/unlock/app.c",
    "src/unlock/app_io.c", "src/unlock/ownership.c", "src/unlock/sha256.c",
    "src/unlock/checks.c", "src/unlock/port.c", "src/unlock/compat.c",
    "src/unlock/vendor/unlock_610.c", "src/unlock/vendor/prep_610.c",
    "src/unlock/vendor/layout_610.c", "src/unlock/vendor/vbios_610.c",
    "src/unlock/vendor/gfw_eval.c", "src/gop/windows.c")
TREE_SOURCES = ("src/gop/app.c", "src/gop/tree.c", "src/unlock/runtime.c", "src/unlock/format.c")
FULL_DEFINES = ("GC_FULL_FLR", "GC_FULL_UNLOCK", "GU_GOP_EXPERIMENT", "__KERNEL__",
                "GU_UEFI_PORT", "GC_WINDOWS_HANDOFF")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def execute(args, source, env, log=None):
    result = subprocess.run([str(a) for a in args], cwd=source, env=env,
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    if log:
        Path(log).write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{Path(str(args[0])).name} failed:\n{result.stdout[-2000:]}{result.stderr[-3000:]}")
    return result.stdout


def inspect_firmware(source, work, llvm, env, profile):
    """Call only the upstream byte parsers on CPU-owned captured bytes."""
    dll = work / "offline-parsers.dll"
    execute([llvm / "clang.exe", "-shared", "-O2", "-std=c11",
             "src/unlock/vendor/vbios_610.c", "src/unlock/vendor/layout_610.c",
             "src/unlock/vendor/prep_610.c", "-Wl,/export:gpu_unlock_vbios_fwsec",
             "-Wl,/export:gpu_unlock_fwsec_sig_offset", "-Wl,/export:gpu_unlock_fwsec_patch_frts",
             "-Wl,/export:gpu_unlock_fuse_version", "-Wl,/export:gpu_unlock_layout",
             "-Wl,/export:gpu_unlock_boot_desc_parse", "-Wl,/export:gpu_unlock_elf_section",
             "-o", dll], source, env)
    lib = ct.CDLL(str(dll))
    names = ("image_off image_size imem_pa imem_size imem_va dmem_pa data_off dmem_size "
             "pkc_off interface_off ucode_id engine_mask sig_count sig_versions sig_off sig_bytes").split()

    class Fwsec(ct.Structure):
        _fields_ = [(name, ct.c_uint32) for name in names]

    raw = Path(profile["inputs"]["prom"]["path"]).read_bytes()
    buffer = ct.create_string_buffer(raw)
    fw = Fwsec()
    parse = lib.gpu_unlock_vbios_fwsec
    parse.argtypes = [ct.c_void_p, ct.c_size_t, ct.POINTER(Fwsec)]
    if parse(buffer, len(raw), ct.byref(fw)):
        raise RuntimeError("Captured PROM failed the actual upstream FWSEC parser.")
    # The current launch path loads exactly the recorded DMEM size in 256-byte blocks.
    # Refuse an unaligned image rather than silently backporting a transaction change.
    if fw.engine_mask != 0x400 or fw.ucode_id != 9 or fw.dmem_size % 256 or fw.imem_size % 256:
        raise RuntimeError("FWSEC engine/ucode/DMA geometry needs additional porting.")
    regs = profile["preboot"]["registers"]
    fuse = lib.gpu_unlock_fuse_version
    fuse.argtypes = [ct.c_uint32]
    fuse.restype = ct.c_uint32
    version = fuse(int(regs["8241e0"]["value"], 16))
    offset = ct.c_uint32()
    select = lib.gpu_unlock_fwsec_sig_offset
    select.argtypes = [ct.c_uint32, ct.c_uint32, ct.c_uint32, ct.POINTER(ct.c_uint32)]
    if select(fw.sig_versions, version, 384, ct.byref(offset)):
        raise RuntimeError("Captured FWSEC fuse has no matching firmware signature.")
    if offset.value + 384 > fw.sig_bytes:
        raise RuntimeError("Selected FWSEC signature exceeds the descriptor.")
    if fuse(int(regs["824148"]["value"], 16)) != 1:
        raise RuntimeError("Booter signature index differs from the pinned implementation.")
    class Span(ct.Structure):
        _fields_ = [("offset", ct.c_uint64), ("size", ct.c_uint64)]

    class Boot(ct.Structure):
        _fields_ = [(name, ct.c_uint32) for name in
                    ("code_offset", "data_offset", "manifest_offset", "image_size")]

    class LayoutIn(ct.Structure):
        _fields_ = [("usable_fb", ct.c_uint64), ("vga_base", ct.c_uint64),
                    ("mmu_lock_valid", ct.c_bool)] + [(name, ct.c_uint64) for name in
                    ("mmu_lock_low", "frts_size", "boot_size", "image_size", "nonwpr_size", "heap_request")]

    class LayoutOut(ct.Structure):
        _fields_ = [(name, ct.c_uint64) for name in
                    ("reserved_top", "wpr_end", "frts_offset", "boot_offset", "gsp_offset",
                     "heap_offset", "heap_size", "wpr_start", "nonwpr_start")]

    assets = source / "build/firmware-assets"
    gsp_bytes = (assets / "gsp_ga10x.bin").read_bytes()
    gsp = ct.create_string_buffer(gsp_bytes)
    image_span = Span()
    section = lib.gpu_unlock_elf_section
    section.argtypes = [ct.c_void_p, ct.c_size_t, ct.c_char_p, ct.POINTER(Span)]
    if section(gsp, len(gsp_bytes), b".fwimage", ct.byref(image_span)):
        raise RuntimeError("Pinned GSP firmware has no supported .fwimage section.")
    desc_bytes = (assets / "gsp_boot_desc_ga102.bin").read_bytes()
    desc = ct.create_string_buffer(desc_bytes)
    boot = Boot()
    boot_parse = lib.gpu_unlock_boot_desc_parse
    boot_parse.argtypes = [ct.c_void_p, ct.c_size_t, ct.c_uint32, ct.POINTER(Boot)]
    if boot_parse(desc, len(desc_bytes), (assets / "gsp_boot_ga102.bin").stat().st_size, ct.byref(boot)):
        raise RuntimeError("Pinned GSP boot descriptor failed the upstream parser.")
    reg = lambda name: int(regs[name]["value"], 16)
    fb = reg("1183a4") << 20
    vga = fb - (1 << 20)
    if reg("625f04") & 8:
        vga = (reg("625f04") >> 8) << 16
        if vga < fb - (1 << 20):
            vga = fb - 0x20000
    low, high = (reg(name) >> 4 << 12 for name in ("1fa82c", "1fa830"))
    top = (high + 0xffff) & ~0xffff
    layout_in = LayoutIn(fb, vga, high >= low and top >> 20 == fb >> 20,
                         low, 1 << 20, boot.image_size, image_span.size, 1 << 20, 88 << 20)
    layout = LayoutOut()
    calculate = lib.gpu_unlock_layout
    calculate.argtypes = [ct.POINTER(LayoutIn), ct.POINTER(LayoutOut)]
    if calculate(ct.byref(layout_in), ct.byref(layout)):
        raise RuntimeError("Captured memory registers fail the upstream WPR layout calculation.")
    image = ct.create_string_buffer(raw[fw.image_off:fw.image_off + fw.image_size])
    patch = lib.gpu_unlock_fwsec_patch_frts
    patch.argtypes = [ct.c_void_p, ct.POINTER(Fwsec), ct.c_uint64]
    if patch(image, ct.byref(fw), layout.frts_offset):
        raise RuntimeError("Captured FWSEC command interface cannot encode the calculated FRTS.")
    # Negative checks exercise the same pure parsers; no firmware is executed.
    if parse(buffer, 1, ct.byref(Fwsec())) == 0:
        raise RuntimeError("FWSEC parser accepted a truncated ROM.")
    if select(fw.sig_versions, 15, 384, ct.byref(ct.c_uint32())) == 0:
        raise RuntimeError("FWSEC signature parser accepted an absent fuse version.")
    return {"descriptor": {name: getattr(fw, name) for name in names},
            "fwsec_fuse_version": version, "fwsec_signature_offset": offset.value,
            "booter_fuse_version": 1, "dmem_dma_aligned": True,
            "gsp_fwimage_bytes": image_span.size,
            "memory_layout": {name: getattr(layout, name) for name, _ in LayoutOut._fields_},
            "fwsec_frts_command_encoded_in_host_copy": True,
            "negative_truncated_rom_and_missing_signature_rejected": True,
            "scope": "CPU byte-parser validation only; firmware has not executed"}


def build_efi(source, work, llvm, env, sources, defines, header, bun):
    work.mkdir()
    flags = ["-target", "x86_64-pc-windows-msvc", "-std=c11", "-ffreestanding",
             "-fno-builtin", "-fno-stack-protector", "-mno-red-zone", "-fshort-wchar",
             "-Os", "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter", "-Wno-unused-function",
             "-I", "src/unlock/compat", "-I", "deps/edk2/MdePkg/Include",
             "-I", "deps/edk2/MdePkg/Include/X64"] + ["-D" + d for d in defines]
    if header:
        flags += ["-include", str(header)]
    objects = []
    for name in sources:
        obj = work / (name.replace("/", "_") + ".obj")
        execute([llvm / "clang.exe", *flags, "-c", name, "-o", obj], source, env)
        objects.append(obj)
    image, mapfile = work / "BOOTX64.EFI", work / "BOOTX64.map"
    execute([llvm / "lld-link.exe", "/nologo", "/nodefaultlib", "/subsystem:efi_application",
             "/entry:efi_main", "/machine:x64", "/base:0", "/dynamicbase", "/nxcompat",
             "/timestamp:0", "/opt:ref", "/opt:icf", f"/map:{mapfile}", f"/out:{image}",
             *objects], source, env)
    execute([bun, "tools/verify_pe.ts", image, mapfile, "--output", work / "pe.json"], source, env)
    text = mapfile.read_text(encoding="utf-8")
    if header:
        for symbol in ("GfRun", "GxPatch", "GwStart"):
            if not re.search(r"\b" + symbol + r"\b", text):
                raise RuntimeError("Missing manual unlock symbol: " + symbol)
        for symbol in ("GuProfileCreate", "GuProfileRefresh", "GuProfileLoad"):
            if re.search(r"\b" + symbol + r"\b", text):
                raise RuntimeError("Unexpected automatic/external profile code.")
    else:
        if not re.search(r"\bGcReadTree\b", text):
            raise RuntimeError("Missing read-only ownership-tree code.")
        for symbol in ("GfRun", "GxPatch", "GuWrite32", "GuDmaAllocate", "GwStart"):
            if re.search(r"\b" + symbol + r"\b", text):
                raise RuntimeError("Mutating operation linked into ownership capture: " + symbol)
    return image, json.loads((work / "pe.json").read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True,
                        help="Private diagnostic-profile.json generated from the physical capture")
    parser.add_argument("--output", type=Path, required=True,
                        help="New folder below this project's ignored data directory")
    args = parser.parse_args()
    source = ROOT / "runtimes/rtx30-uefi-probe-source"
    llvm = ROOT / "runtimes/uefi-probe-tools/llvm-20.1.8/bin"
    bun = ROOT / "runtimes/uefi-probe-tools/bun-1.4.4/bun-windows-x64/bun.exe"
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "data") or output == ROOT / "data" or output.exists():
        raise RuntimeError("Choose a new output subdirectory below ignored data.")
    env = dict(os.environ)
    env["LLVM_BIN"] = str(llvm)
    env["PATH"] = os.pathsep.join((str(llvm), str(bun.parent), str(Path(sys.executable).parent), env["PATH"]))
    if execute(["git", "rev-parse", "HEAD"], source, env).strip() != PIN:
        raise RuntimeError("Upstream source pin differs from the reviewed revision.")
    if execute(["git", "status", "--porcelain"], source, env).strip():
        raise RuntimeError("Tracked or untracked upstream changes require review.")
    sys.path.insert(0, str(source / "tools"))
    check_profile = importlib.import_module("check_profile")
    profile = check_profile.check(args.capture, experimental=True)
    target = profile["target"]
    if (target["deviceId"], target["subsystemVendorId"], target["subsystemDeviceId"],
            target["architecture"]) != ("2503", "1458", "407b", "GA106"):
        raise RuntimeError("This helper is scoped to the captured Gigabyte RTX 3060.")
    # Preserve all generated profile validation flags: never claim approval or compatibility.
    if profile["validation"]["unlockApproved"] or profile["validation"]["firmwareCompatible"]:
        raise RuntimeError("Expected the original unapproved diagnostic profile.")
    specs_text = (source / "src/unlock/app_io.c").read_text(encoding="utf-8")
    specs = re.findall(r'L"ASSETS\\\\([^"\\]+)",\s*(\d+),\s*"([0-9a-f]{64})"', specs_text)
    if len(specs) != 5:
        raise RuntimeError("Firmware asset table has changed.")
    assets = source / "build/firmware-assets"
    for name, size, digest in specs:
        path = assets / name
        if path.stat().st_size != int(size) or sha(path) != digest:
            raise RuntimeError("Pinned firmware asset mismatch: " + name)
    output.mkdir(parents=True)
    logs = output / "checks"
    logs.mkdir()
    header = output / "private-board-profile.h"
    header.write_text(check_profile.header(profile), encoding="ascii")
    firmware = inspect_firmware(source, logs, llvm, env, profile)
    (logs / "offline-firmware.json").write_text(json.dumps(firmware, indent=2) + "\n")
    print("Actual captured PROM: FWSEC parser, DMA geometry and fuse signatures passed", flush=True)
    checks = {}
    for suite in ("gop-cycle", "gop-patch-state", "gop-windows", "gop-visual", "port", "checks",
                  "profile-runtime", "probe-profile"):
        execute([bun, "tools/test.ts", suite], source, env, logs / (suite + ".log"))
        checks[suite] = "passed"
        print(suite + ": passed (host mocks)", flush=True)
    host_flags = ["-std=c11", "-O1", "-Wall", "-Wextra", "-Werror", "-Wno-unused-function",
                  "-Wno-unused-parameter", "-D_CRT_SECURE_NO_WARNINGS", "-I", "src/gop",
                  "-I", "deps/edk2/MdePkg/Include", "-I", "deps/edk2/MdePkg/Include/X64",
                  "-include", str(header)] + ["-D" + d for d in FULL_DEFINES]
    gate = logs / "manual-gate-test.exe"
    execute([llvm / "clang.exe", *host_flags, ROOT / "scripts/uefi_manual_gate_test.c",
             "src/unlock/format.c", "-o", gate], source, env, logs / "manual-gate-build.log")
    execute([gate], source, env, logs / "manual-gate.log")
    checks["manual-only-8-flow-tests"] = "passed"
    print("Manual-only approval/failure paths: passed", flush=True)
    full, full_pe = build_efi(source, output / "build-unlock", llvm, env,
                              FULL_SOURCES, FULL_DEFINES, header, bun)
    tree, tree_pe = build_efi(source, output / "build-tree", llvm, env,
                              TREE_SOURCES, ("GC_TREE_ONLY",), None, bun)
    for name, image in (("manual-unlock-candidate", full), ("ownership-probe", tree)):
        boot = output / name / "EFI/BOOT"
        payload = output / name / "RTX-UNLOCK"
        boot.mkdir(parents=True)
        payload.mkdir()
        shutil.copy2(image, boot / "BOOTX64.EFI")
        (payload / "README.txt").write_text("Keep this directory beside EFI on the same FAT32 USB.\n")
        if name == "manual-unlock-candidate":
            (payload / "ASSETS").mkdir()
            for asset, _, _ in specs:
                shutil.copy2(assets / asset, payload / "ASSETS" / asset)
            # Not used by this non-production build: retain the marker as a visible safeguard.
            (payload / "DEBUG.ON").write_bytes(b"")
            license_file = assets / "NVIDIA-LICENSE"
            if not license_file.exists():
                license_file = assets / "NVIDIA-LICENSE.txt"
            if license_file.is_file():
                shutil.copy2(license_file, payload / license_file.name)
        notices = output / name / "LICENSES"
        shutil.copytree(source / "LICENSES", notices)
        shutil.copy2(source / "LICENSE", output / name / "LICENSE")
        shutil.copy2(source / "THIRD_PARTY_NOTICES.md", output / name / "THIRD_PARTY_NOTICES.md")
        source_archive = output / name / "SOURCE.tar.gz"
        execute(["git", "archive", "--format=tar.gz", "--output=" + str(source_archive), PIN], source, env)
        with zipfile.ZipFile(output / name / "BUILD-HELPERS.zip", "x", zipfile.ZIP_DEFLATED) as bundle:
            for helper in ("prepare_windows_3060_unlock.py", "uefi_manual_gate_test.c"):
                bundle.write(ROOT / "scripts" / helper, helper)
            if name == "manual-unlock-candidate":
                bundle.write(header, "private-board-profile.h")
        shutil.copy2(ROOT / "reports/RTX3060-WINDOWS-UNLOCK-PREPARATION.md",
                     output / name / "START-HERE.md")
    metadata = {"source_commit": PIN, "upstream_source_modified": False,
                "source_compiled_with_private_generated_header": True,
                "fixed_target": target, "profile_flags": profile["validation"],
                "full_defines": FULL_DEFINES, "automatic_execution": False,
                "automatic_profile_creation_or_refresh": False, "quiet_logging": False,
                "manual_u_required": True, "cancel_timeout_seconds": 30,
                "firmware_assets_verified": len(specs), "firmware_cpu_validation": firmware,
                "selector_policy": "Unmodified upstream SS0=88888888 and SS1=8; not hardware validated on this board",
                "host_checks": checks, "unlock_pe": full_pe, "tree_pe": tree_pe,
                "ownership_review_complete": False, "ready_for_unlock_boot": False,
                "physical_unlock_tested": False, "usb_changed_by_builder": False,
                "system_esp_or_boot_variables_changed": False,
                "next_boot": "Read-only ownership probe; review the graph before deploying the unlock candidate"}
    (output / "BUILD-INFO.private.json").write_text(json.dumps(metadata, indent=2) + "\n")
    for directory in (output / "manual-unlock-candidate", output / "ownership-probe"):
        files = sorted(p for p in directory.rglob("*") if p.is_file())
        (directory / "SHA256SUMS.txt").write_text("".join(
            sha(p) + "  " + p.relative_to(directory).as_posix() + "\n" for p in files), encoding="ascii")
    print("Prepared manual unlock candidate and read-only ownership probe; no physical drive changed.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print("Preparation stopped: " + str(error), file=sys.stderr)
        sys.exit(1)
