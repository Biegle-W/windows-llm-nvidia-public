#!/usr/bin/env python3
"""Build/test a manual-only EFI for the captured 2208/10de:1535 board; never stage or execute it."""
import argparse
import importlib
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile

from prepare_windows_3060_unlock import ROOT, PIN, FULL_DEFINES, execute, inspect_firmware, sha
from prepare_uefi_3060_single_child import read_tree
from rtx3080ti_setup import tools, require_installed_board

SOURCE=ROOT/'runtimes/rtx30-uefi-probe-source'
LLVM=ROOT/'runtimes/uefi-probe-tools/llvm-20.1.8/bin'
BUN=ROOT/'runtimes/uefi-probe-tools/bun-1.4.4/bun-windows-x64/bun.exe'


def validate_tree(path):
    text=path.read_text(encoding='ascii')
    if not re.search(r'^target=0x[0-9a-f]+ BDF=0:1:0\.0$',text,re.M):
        raise RuntimeError('Ownership capture PCI address differs from the installed board.')
    if 'STAGE secure-boot query=0 bytes=1 enabled=0' not in text or 'detach_attempted=0' not in text:
        raise RuntimeError('Read-only ownership/security capture is incomplete.')
    return read_tree(path,'220810de','153510de')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',type=Path,required=True)
    parser.add_argument('--tree',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    env=tools();out=args.output.resolve()
    if not out.is_relative_to(ROOT/'data') or out==ROOT/'data' or out.exists():
        raise RuntimeError('Choose a new private output directory below project data.')
    sys.path.insert(0,str(SOURCE/'tools'))
    checker=importlib.import_module('check_profile')
    profile=checker.check(args.profile,experimental=True);require_installed_board(profile)
    drivers=validate_tree(args.tree)
    specs=re.findall(r'L"ASSETS\\\\([^"\\]+)",\s*(\d+),\s*"([0-9a-f]{64})"',
                     (SOURCE/'src/unlock/app_io.c').read_text(encoding='utf-8'))
    if len(specs)!=5:raise RuntimeError('Pinned firmware asset table differs.')
    assets=SOURCE/'build/firmware-assets'
    for name,size,digest in specs:
        if (assets/name).stat().st_size!=int(size) or sha(assets/name)!=digest:
            raise RuntimeError('Pinned firmware asset mismatch: '+name)
    out.mkdir();checks=out/'checks';checks.mkdir()
    base=out/'base';base.mkdir()
    header=base/'private-board-profile.h';header.write_text(checker.header(profile),encoding='ascii')
    firmware=inspect_firmware(SOURCE,checks,LLVM,env,profile)
    (checks/'offline-firmware.private.json').write_text(json.dumps(firmware,indent=2)+'\n',encoding='utf-8')
    print('Exact board/PROM/topology and all five firmware asset hashes verified.',flush=True)
    for suite in ('gop-cycle','gop-patch-state','gop-windows','gop-visual','port','checks','profile-runtime','probe-profile'):
        execute([BUN,'tools/test.ts',suite],SOURCE,env,checks/(suite+'.log'))
        print(suite+': host checks passed',flush=True)
    host=['-std=c11','-O1','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter',
          '-D_CRT_SECURE_NO_WARNINGS','-I','src/gop','-I','deps/edk2/MdePkg/Include',
          '-I','deps/edk2/MdePkg/Include/X64','-include',header]+['-D'+d for d in FULL_DEFINES]
    gate=(ROOT/'scripts/uefi_manual_gate_test.c').read_text(encoding='utf-8')
    assert gate.count('DeviceIdentity = 0x250310de;')==1 and gate.count('DeviceSubsystem = 0x407b1458;')==1
    gate=gate.replace('DeviceIdentity = 0x250310de;','DeviceIdentity = GU_BOARD_ID;').replace('DeviceSubsystem = 0x407b1458;','DeviceSubsystem = GU_BOARD_SUBSYSTEM;')
    gate_path=checks/'manual-gate-3080ti.c';gate_path.write_text(gate,encoding='utf-8')
    execute([LLVM/'clang.exe',*host,gate_path,'src/unlock/format.c','-o',checks/'manual-gate.exe'],SOURCE,env,checks/'manual-gate-build.log')
    print(execute([checks/'manual-gate.exe'],SOURCE,env,checks/'manual-gate.log').strip(),flush=True)
    app=(SOURCE/'src/unlock/app.c').read_text(encoding='utf-8')
    start=app.index('static EFI_STATUS ColdCheck(VOID) {');end=app.index('static EFI_STATUS PromCheck(VOID) {',start)
    (checks/'cold-check-under-test.h').write_text(app[start:end],encoding='utf-8')
    cold_host=['-std=c11','-O1','-Wall','-Wextra','-Werror','-Wno-unused-function',
        '-D_CRT_SECURE_NO_WARNINGS','-I',SOURCE,'-I',checks,'-I','deps/edk2/MdePkg/Include',
        '-I','deps/edk2/MdePkg/Include/X64','-include',header]
    execute([LLVM/'clang.exe',*cold_host,ROOT/'scripts/uefi_fixed_cold_profile_test.c',
             'src/unlock/vendor/gfw_eval.c','-o',checks/'cold-check.exe'],SOURCE,env,checks/'cold-check-build.log')
    print(execute([checks/'cold-check.exe'],SOURCE,env,checks/'cold-check.log').strip(),flush=True)
    package=base/'manual-unlock-candidate'
    payload=package/'RTX-UNLOCK';(payload/'ASSETS').mkdir(parents=True)
    (payload/'README.txt').write_text('Fixed installed 3080 Ti only. Manual U is required after preflight. Preserve capture runs.\n',encoding='utf-8')
    (payload/'DEBUG.ON').write_bytes(b'')
    for name,_,_ in specs:shutil.copy2(assets/name,payload/'ASSETS'/name)
    for license_name in ('NVIDIA-LICENSE','NVIDIA-LICENSE.txt'):
        if (assets/license_name).is_file():shutil.copy2(assets/license_name,payload/license_name)
    for name in ('LICENSE','THIRD_PARTY_NOTICES.md'):shutil.copy2(SOURCE/name,package/name)
    shutil.copytree(SOURCE/'LICENSES',package/'LICENSES')
    execute(['git','archive','--format=tar.gz','--output='+str(package/'SOURCE.tar.gz'),PIN],SOURCE,env)
    with zipfile.ZipFile(package/'BUILD-HELPERS.zip','x',zipfile.ZIP_DEFLATED) as archive:
        for name in ('prepare_uefi_3080ti_manual.py','prepare_uefi_3060_single_child.py',
                     'prepare_windows_3060_unlock.py','rtx3080ti_setup.py','uefi_manual_gate_test.c','uefi_fixed_cold_profile_test.c'):
            archive.write(ROOT/'scripts'/name,name)
        archive.write(header,'private-board-profile.h');archive.write(gate_path,'manual-gate-3080ti.c')
    (package/'SHA256SUMS.txt').write_text(''.join(sha(f)+'  '+f.relative_to(package).as_posix()+'\n' for f in sorted(package.rglob('*')) if f.is_file()),encoding='ascii')
    (base/'BUILD-INFO.private.json').write_text(json.dumps({'source_commit':PIN,'automatic_execution':False,'physical_unlock_tested':False})+'\n',encoding='utf-8')
    execute([sys.executable,ROOT/'scripts/prepare_uefi_3060_single_child.py','--target','rtx3080ti',
             '--capture',args.profile.resolve(),'--tree',args.tree.resolve(),'--prepared',base,
             '--output',out/'single-child'],ROOT,env,checks/'single-child-build.log')
    print((checks/'single-child-build.log').read_text(encoding='utf-8').strip(),flush=True)
    info=json.loads((out/'single-child/BUILD-INFO.json').read_text(encoding='utf-8'))
    assert info['manual_u_required'] and not info['automatic_execution'] and not info['physical_unlock_tested']
    # Only the display adaptation changes. The actual transaction and cold check retain the pinned sources.
    info.update(board_profile_input_sha256=sha(args.profile),ownership_input_sha256=sha(args.tree),
        generated_header_sha256=sha(header),fixed_target=profile['target'],
        original_validation_flags=profile['validation'],firmware_cpu_validation=firmware,
        unchanged_actual_cold_check_tested=True,manual_gate_cases=8,
        upstream_host_suites=8,usb_staged=False,unlock_executed=False)
    (out/'BUILD-INFO.private.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'manual_candidate_built':True,'efi_sha256':info['efi']['sha256'],
        'manual_u_required':True,'automatic':False,'usb_staged':False,'firmware_executed':False}),flush=True)


if __name__=='__main__':
    try:main()
    except (OSError,RuntimeError,ValueError,KeyError,AssertionError) as error:
        print('3080 Ti manual build stopped: '+str(error),file=sys.stderr);sys.exit(1)
