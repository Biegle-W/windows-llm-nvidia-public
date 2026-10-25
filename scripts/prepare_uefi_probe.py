#!/usr/bin/env python3
"""Build/test/package the pinned standalone read-only RTX30 UEFI probe.

Creates a NEW project-local folder and ZIP. Never selects/formats a drive,
mounts an ESP, changes boot variables, downloads firmware or runs an EFI image.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
PIN = "5c076dc4ee7fa369639669fa591ac74d8f6dfcd8"
UPSTREAM = "https://github.com/craftingmod/rtx30-unlock"
SOURCES = ("src/probe/probe_app.c", "src/probe/probe_core.c",
           "src/probe/probe_profile.c", "src/probe/efi_runtime.c", "src/unlock/sha256.c")
FORBIDDEN = (r"\b(?:Mem|Pci|Io)\s*\.\s*Write\s*\(",
             r"->\s*(?:Attributes|SetBarAttributes|SetVariable|ResetSystem|DisconnectController|"
             r"ConnectController|LoadImage|StartImage|AllocateBuffer|Map|Unmap)\s*\(")


def run(args, cwd, env, allowed_failure=False):
    result = subprocess.run([str(x) for x in args], cwd=cwd, env=env,
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode and not allowed_failure:
        raise RuntimeError(f"Command failed: {Path(str(args[0])).name}\n{result.stdout}{result.stderr}")
    return result


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=('rtx3060','rtx3080ti','rtx3080'), default='rtx3060',
                        help='Packaging label and additional host fixture; does not change the read-only EFI')
    parser.add_argument("--source", type=Path, default=PROJECT/"runtimes/rtx30-uefi-probe-source")
    parser.add_argument("--llvm-bin", type=Path,
                        default=PROJECT/"runtimes/uefi-probe-tools/llvm-20.1.8/bin")
    parser.add_argument("--bun", type=Path,
                        default=PROJECT/"runtimes/uefi-probe-tools/bun-1.4.4/bun-windows-x64/bun.exe")
    parser.add_argument("--output", type=Path, default=PROJECT/"data/uefi-probe/rtx3060-readonly")
    args = parser.parse_args()
    source, llvm, bun, output = (path.resolve() for path in
                                 (args.source, args.llvm_bin, args.bun, args.output))
    if not output.is_relative_to(PROJECT/"data") or output == PROJECT/"data":
        raise RuntimeError("Output must be a new subdirectory of this project's ignored data folder.")
    archive = output.with_suffix(".zip")
    if output.exists() or archive.exists():
        raise RuntimeError("Output folder/ZIP already exists; select a new --output rather than overwrite it.")
    env = dict(os.environ)
    env["LLVM_BIN"] = str(llvm)
    env["PATH"] = os.pathsep.join((str(llvm), str(bun.parent), str(Path(sys.executable).parent), env["PATH"]))
    clang = llvm/"clang.exe"
    for path in (clang, llvm/"lld-link.exe", bun):
        if not path.is_file():
            raise RuntimeError(f"Build tool missing: {path}")
    if run(["git", "rev-parse", "HEAD"], source, env).stdout.strip() != PIN:
        raise RuntimeError("Source is not pinned to the reviewed commit.")
    if run(["git", "status", "--porcelain"], source, env).stdout.strip():
        raise RuntimeError("Upstream source has changes; refusing this build.")
    for name in SOURCES:
        text = (source/name).read_text(encoding="utf-8")
        if any(re.search(pattern, text) for pattern in FORBIDDEN):
            raise RuntimeError(f"Unexpected mutating GPU/boot API call in {name}")
    build_script = (source/"tools/build-probe.ts").read_text(encoding="utf-8")
    built_sources = tuple(name+".c" for name in re.findall(r'"(src/[^"\n]+)"', build_script))
    if built_sources != SOURCES or "-DGU_AUTO_PROFILE" in build_script:
        raise RuntimeError("Standalone build source list/flags differ from the reviewed probe.")
    results = {}
    for name, command in (
            ("probe_build", [bun, "tools/build-probe.ts"]),
            ("upstream_probe_mocks", [bun, "tools/test.ts", "probe"]),
            ("report_parser_11_tests", [bun, "tools/test.ts", "probe-profile"])):
        result = run(command, source, env)
        results[name] = "passed"
        print(f"{name}: passed")

    build = source/"build/probe"
    # Only the mocked test fixture changes; the EFI's five source files stay intact.
    fixture = (source/"src/probe/test_core.c").read_text(encoding="utf-8")
    original = "0x248410de, 0x250410de, 0x25a210de"
    if fixture.count(original) != 1 or fixture.count("config[0] = Ids[i];") != 2:
        raise RuntimeError("Unexpected upstream mock fixture layout.")
    fixture = fixture.replace(original, "0x248410de, 0x250310de, 0x25a210de")
    if args.target in ('rtx3080ti','rtx3080'):
        if fixture.count('0x220310de') != 1:
            raise RuntimeError('Expected one GA102 fixture identity.')
        fixture = fixture.replace('0x220310de','0x220810de' if args.target=='rtx3080ti' else '0x220610de')
    fixture = fixture.replace("config[0] = Ids[i];", "config[0] = Ids[i];\n"
                              "      if (Ids[i] == 0x250310de) config[11] = 0x407b1458;")
    fixture = fixture.replace("config[11] = 0x12345678;",
                              "config[11] = Ids[i] == 0x250310de ? 0x407b1458 : 0x12345678;")
    targeted = build/"test_core_gigabyte2503.c"
    targeted.write_text(fixture, encoding="utf-8", newline="\n")
    mock = build/"probe-gigabyte2503-mock.exe"
    run([clang, "-std=c11", "-Wall", "-Wextra", "-Werror", "-D_CRT_SECURE_NO_WARNINGS",
         "-I", "deps/edk2/MdePkg/Include", "-I", "deps/edk2/MdePkg/Include/X64",
         "-I", "src/probe", targeted, "src/probe/probe_core.c", "src/probe/probe_app.c",
         "src/probe/probe_profile.c", "src/unlock/sha256.c", "-o", mock], source, env)
    targeted_result = run([mock], source, env)
    if "Core tests: PASS (0 failures)" not in targeted_result.stdout:
        raise RuntimeError("Exact-card mock did not report a clean pass.")
    results["gigabyte_2503_407b1458_capture_mocks"] = "passed"
    print("gigabyte_2503_407b1458_capture_mocks: passed (simulated)")
    if args.target == 'rtx3080ti':
        results['rtx3080ti_2208_ga102_capture_mocks'] = 'passed'
        print('rtx3080ti_2208_ga102_capture_mocks: passed (simulated; subsystem not yet known)')
    elif args.target == 'rtx3080':
        results['rtx3080_2206_ga102_capture_mocks']='passed'
        print('rtx3080_2206_ga102_capture_mocks: passed (simulated; subsystem not yet known)')

    image = build/"BOOTX64.EFI"
    mapfile = build/"BOOTX64.map"
    image_bytes = image.read_bytes()
    pe = struct.unpack_from("<I", image_bytes, 0x3c)[0]
    for name, offset, value in (("wrong_machine", pe+4, b"\0\0"),
                                ("wrong_subsystem", pe+24+68, b"\3\0"),
                                ("unexpected_import", pe+24+112+8, b"\1\0\0\0")):
        changed = bytearray(image_bytes)
        changed[offset:offset+len(value)] = value
        negative = build/f"negative-{name}.efi"
        negative.write_bytes(changed)
        result = run([bun, "tools/verify_pe.ts", negative, mapfile], source, env, allowed_failure=True)
        if result.returncode == 0:
            raise RuntimeError(f"PE verifier accepted negative case {name}")
        results[f"pe_rejects_{name}"] = "passed"

    output.parent.mkdir(parents=True, exist_ok=True)
    run([sys.executable, "tools/package_probe_usb.py", "--output", output], source, env)
    correspondence = output/"SOURCE"
    correspondence.mkdir()
    run(["git", "archive", "--format=tar.gz",
         f"--output={correspondence/'read-only-probe-source.tar.gz'}", PIN,
         "src/probe", "src/unlock/sha256.c", "src/unlock/sha256.h", "deps/edk2/MdePkg/Include",
         "tools/build-probe.ts", "tools/test_support.ts", "tools/verify_pe.ts", "LICENSE",
         "THIRD_PARTY_NOTICES.md", "LICENSES"], source, env)
    shutil.copy2(PROJECT/"scripts/prepare_uefi_probe.py", correspondence/"prepare_uefi_probe.py")
    instructions = PROJECT/({'rtx3080ti':'reports/WINDOWS-3060-3080TI-SWAP-20261025.md',
        'rtx3080':'reports/RTX3080-10GB-UNLOCK-SETUP-20261025.md',
        'rtx3060':'reports/RTX3060-READONLY-UEFI-PROBE.md'}[args.target])
    shutil.copy2(instructions, output/"START-HERE.md")
    (output/"RTX30-PROBE/README.txt").write_text(
        "Keep this directory on the same FAT32 USB as EFI/BOOT/BOOTX64.EFI.\n"
        "The probe creates a new RUN00..RUN99 directory here without overwriting old runs.\n"
        "Captures can identify the machine; keep REPORT/PROM/ROMIMAGE files private.\n", encoding="utf-8")
    metadata = {"upstream": UPSTREAM, "source_commit": PIN, "source_modified_for_efi": False,
                "expected_pci_id": {'rtx3080ti':'10de:2208','rtx3080':'10de:2206','rtx3060':'10de:2503'}[args.target],
                "expected_subsystem": '1458:407b' if args.target=='rtx3060' else None,
                "compiler": run([clang, "--version"], source, env).stdout.splitlines()[0],
                "linker": run([llvm/"lld-link.exe", "--version"], source, env).stdout.strip(),
                "bun": run([bun, "--version"], source, env).stdout.strip(),
                "pe": json.loads((build/"pe-verification.json").read_text()),
                "host_validation": results, "physical_uefi_boot_tested": False,
                "gpu_unlock_performed": False, "persistent_writes": "new USB capture files only"}
    (output/"BUILD-INFO.json").write_text(json.dumps(metadata, indent=2)+"\n", encoding="utf-8")
    files = sorted(path for path in output.rglob("*") if path.is_file())
    sums = "".join(f"{digest(path)}  {path.relative_to(output).as_posix()}\n" for path in files)
    (output/"SHA256SUMS.txt").write_text(sums, encoding="ascii")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(output).as_posix())
    if digest(output/"EFI/BOOT/BOOTX64.EFI") != metadata["pe"]["sha256"]:
        raise RuntimeError("Staged EFI differs from the verified image.")
    print(json.dumps({"prepared_folder": str(output), "zip": str(archive),
                      "efi_sha256": metadata["pe"]["sha256"], "hardware_boot_tested": False}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Probe preparation stopped: {error}", file=sys.stderr)
        sys.exit(1)
