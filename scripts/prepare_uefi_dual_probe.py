#!/usr/bin/env python3
"""Build a read-only two-card capture EFI. Never stage, unlock, reset or reboot a GPU.

Both board selectors come from private, previously audited diagnostic profiles.
Fresh dual-card captures are required before developing a coordinated unlock.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import zipfile

from prepare_windows_3060_unlock import ROOT, PIN, execute, sha
from prepare_uefi_probe import FORBIDDEN

SOURCE = ROOT / 'runtimes/rtx30-uefi-probe-source'
LLVM = ROOT / 'runtimes/uefi-probe-tools/llvm-20.1.8/bin'
BUN = ROOT / 'runtimes/uefi-probe-tools/bun-1.4.4/bun-windows-x64/bun.exe'


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError('Pinned source fragment differs: ' + old[:70])
    return text.replace(old, new, 1)


def subsystem(profile_path, device):
    sys.path.insert(0, str(SOURCE / 'tools'))
    from check_profile import check
    profile = check(profile_path.resolve(), experimental=True)
    t = profile['target']
    if (t['vendorId'], t['deviceId'], t['architecture']) != ('10de', device, 'GA102'):
        raise RuntimeError('Use independent, complete GA102 profiles for the specified cards.')
    if not profile['validation']['probeComplete'] or any(
            profile['validation'][k] for k in ('unlockApproved', 'firmwareCompatible', 'hardwareTested')):
        raise RuntimeError('Preserve the original diagnostic validation flags.')
    values = [t[k] for k in ('subsystemDeviceId', 'subsystemVendorId')]
    if not all(re.fullmatch('[0-9a-f]{4}', v) for v in values):
        raise RuntimeError('Missing subsystem identity.')
    return ''.join(values)


def patched_sources(out):
    board = (SOURCE / 'src/probe/probe_app.c').read_text()
    board = '#define efi_main DualBoardMain\n#include "uefi_dual_probe.h"\n' + board
    board = replace_once(board, '      if (!ProbeMatches(Config)) continue;',
        '      if (!ProbeMatches(Config) || !DualMatches(Config) ||\n'
        '          Config[0] != DualSelectedIdentity) continue;')
    board = replace_once(board, 'One NVIDIA display device found. Checking read-only allowlist...',
                         'One selected board found. Checking read-only allowlist...')
    board = replace_once(board, '  return EFI_SUCCESS;\n}\n\nEFI_STATUS ProbeCaptureProfile',
        '  return EFI_ERROR(Status) ? Status : EFI_ERROR(Evidence) ? Evidence :\n'
        '         Matches == 1 && PromSaved ? EFI_SUCCESS : EFI_NOT_READY;\n}\n\nEFI_STATUS ProbeCaptureProfile')
    tree = (SOURCE / 'src/gop/app.c').read_text()
    tree = '#define efi_main DualTreeMain\n#include "uefi_dual_probe.h"\n' + tree
    tree = replace_once(tree,
        '    if ((cfg[0] & 0xffff) != 0x10de || (cfg[2] >> 24) != 3) continue;',
        '    if (!DualMatches(cfg) || cfg[0] != DualSelectedIdentity) continue;')
    for name, text in (('board-dual.c', board), ('tree-dual.c', tree)):
        (out / name).write_text(text, encoding='utf-8')
    return board, tree


def compile_host(out, env, header, name, sources, extra=()):
    target = out / (name + '.exe')
    flags = ['-std=c11', '-O1', '-Wall', '-Wextra', '-Werror', '-Wno-unused-function',
             '-Wno-unused-parameter', '-D_CRT_SECURE_NO_WARNINGS',
             '-I', ROOT / 'scripts', '-I', out, '-I', SOURCE / 'src/probe',
             '-I', SOURCE / 'src/gop', '-I', SOURCE / 'src/unlock',
             '-I', SOURCE / 'deps/edk2/MdePkg/Include',
             '-I', SOURCE / 'deps/edk2/MdePkg/Include/X64', '-include', header]
    execute([LLVM / 'clang.exe', *flags, *extra, *sources, '-o', target], SOURCE, env,
            out / (name + '-build.log'))
    result = execute([target], SOURCE, env, out / (name + '.log')).strip()
    print(result, flush=True)
    return result


def entry_fixtures(out):
    # Reuse the upstream filesystem/MMIO mocks, but run the actual modified entry.
    fixture = (SOURCE / 'src/probe/test_core.c').read_text().split('int main(void) {')[0]
    fixture = fixture.replace('extern EFI_STATUS EFIAPI efi_main(',
                              'extern EFI_STATUS EFIAPI DualBoardMain(')
    (out / 'board-entry-fixture.c').write_text(fixture + '\n#include "uefi_dual_probe.h"\n' + r'''
UINT32 DualSelectedIdentity;
BOOLEAN DualMatches(const UINT32 *c) {
  return (c[0] == 0x220810deU && c[11] == DUAL_TI_SUBSYSTEM) ||
         (c[0] == 0x220610deU && c[11] == DUAL_3080_SUBSYSTEM);
}
static EFI_PCI_IO_PROTOCOL second;
static BOOLEAN WrongSubsystem;
static EFI_STATUS EFIAPI PairRead(EFI_PCI_IO_PROTOCOL *p, EFI_PCI_IO_PROTOCOL_WIDTH w,
                                  UINT32 off, UINTN n, VOID *data) {
  EFI_STATUS s = read_config(&pci,w,off,n,data);
  if (!EFI_ERROR(s)) {
    ((UINT32 *)data)[0] = p == &pci ? 0x220810deU : 0x220610deU;
    ((UINT32 *)data)[11] = p == &pci ? DUAL_TI_SUBSYSTEM : DUAL_3080_SUBSYSTEM;
    if (WrongSubsystem) ((UINT32 *)data)[11] ^= 1;
  }
  return s;
}
static EFI_STATUS EFIAPI PairBar(EFI_PCI_IO_PROTOCOL *p, UINT8 i, UINT64 *s, VOID **out) {
  (void)p; return get_bar(&pci,i,s,out);
}
static EFI_STATUS EFIAPI PairMem(EFI_PCI_IO_PROTOCOL *p, EFI_PCI_IO_PROTOCOL_WIDTH w, UINT8 i,
                                 UINT64 off, UINTN n, VOID *out) {
  (void)p; return read_mem(&pci,w,i,off,n,out);
}
static EFI_STATUS EFIAPI PairLocation(EFI_PCI_IO_PROTOCOL *p, UINTN *s, UINTN *b, UINTN *d, UINTN *f) {
  *s=0; *b=p == &pci ? 1 : 5; *d=*f=0; return EFI_SUCCESS;
}
static EFI_STATUS EFIAPI PairHandle(EFI_HANDLE h, EFI_GUID *g, VOID **out) {
  if (h == &second && !memcmp(g,&pci_guid,sizeof(*g))) { *out=&second; return EFI_SUCCESS; }
  return handle_protocol(h,g,out);
}
static EFI_STATUS EFIAPI PairHandles(EFI_LOCATE_SEARCH_TYPE t, EFI_GUID *g, VOID *k,
                                     UINTN *n, EFI_HANDLE **out) {
  if (!memcmp(g,&pci_guid,sizeof(*g))) {
    *n=2; *out=calloc(2,sizeof(**out)); (*out)[0]=&pci; (*out)[1]=&second; return EFI_SUCCESS;
  }
  return locate_handles(t,g,k,n,out);
}
static void PairSetup(void) {
  reset(); usb_output=TRUE; enumerate_target=TRUE; WrongSubsystem=FALSE;
  pci.Pci.Read=PairRead; pci.Mem.Read=PairMem; pci.GetBarAttributes=PairBar;
  pci.GetLocation=PairLocation; second=pci;
  bs.HandleProtocol=PairHandle; bs.LocateHandleBuffer=PairHandles;
}
int main(void) {
  unsigned cases=0;
  for (unsigned i=0;i<2;i++) {
    PairSetup(); DualSelectedIdentity=i ? 0x220610deU : 0x220810deU;
    CHECK(DualBoardMain((EFI_HANDLE)1,&system_table) == EFI_SUCCESS);
    CHECK(reads == 16+PROBE_PROM_SIZE/1024 && prom_writes && report_writes && !writes);
    CHECK(strstr(saved_report,i ? "identity=0x00000000220610de" : "identity=0x00000000220810de"));
    CHECK(!strstr(saved_report,i ? "identity=0x00000000220810de" : "identity=0x00000000220610de"));
    cases++;
  }
  PairSetup(); DualSelectedIdentity=0x220810deU; WrongSubsystem=TRUE;
  CHECK(EFI_ERROR(DualBoardMain((EFI_HANDLE)1,&system_table)) && !reads && !writes); cases++;
  PairSetup(); DualSelectedIdentity=0x220810deU; fail_log=TRUE;
  CHECK(EFI_ERROR(DualBoardMain((EFI_HANDLE)1,&system_table)) && !reads && !writes); cases++;
  PairSetup(); DualSelectedIdentity=0x220810deU; sentinel=TRUE;
  CHECK(EFI_ERROR(DualBoardMain((EFI_HANDLE)1,&system_table)) && !prom_writes && !writes); cases++;
  PairSetup(); DualSelectedIdentity=0x220810deU; usb_output=FALSE;
  CHECK(EFI_ERROR(DualBoardMain((EFI_HANDLE)1,&system_table)) && !reads && !writes); cases++;
  printf("PASS %u actual dual-board capture scenarios (%d failures); no GPU writes\n",cases,failures);
  return failures ? 1 : 0;
}
''', encoding='utf-8')
    fixture = (SOURCE / 'src/gop/test_io.c').read_text().split('int main(void) {')[0]
    fixture = replace_once(fixture, '#include "app.c"', '#include "tree-dual.c"')
    (out / 'tree-entry-fixture.c').write_text(fixture + r'''
UINT32 DualSelectedIdentity;
BOOLEAN DualMatches(const UINT32 *c) {
  return (c[0] == 0x220810deU && c[11] == DUAL_TI_SUBSYSTEM) ||
         (c[0] == 0x220610deU && c[11] == DUAL_3080_SUBSYSTEM);
}
static EFI_PCI_IO_PROTOCOL Other;
static BOOLEAN WrongSubsystem;
static EFI_STATUS EFIAPI PairRead(EFI_PCI_IO_PROTOCOL *p, EFI_PCI_IO_PROTOCOL_WIDTH w,
                                  UINT32 off, UINTN n, VOID *out) {
  assert(w==EfiPciIoWidthUint32 && off==0 && n==64);
  memset(out,0,256); ((UINT32 *)out)[0]=p==&TestPci ? 0x220810deU : 0x220610deU;
  ((UINT32 *)out)[2]=0x030000a1;
  ((UINT32 *)out)[11]=p==&TestPci ? DUAL_TI_SUBSYSTEM : DUAL_3080_SUBSYSTEM;
  if (WrongSubsystem) ((UINT32 *)out)[11]^=1;
  return EFI_SUCCESS;
}
static EFI_STATUS EFIAPI PairHandle(EFI_HANDLE h, EFI_GUID *g, VOID **out) {
  if (!memcmp(g,&PciGuid,sizeof(*g)) && ((UINTN)h==1 || (UINTN)h==2)) {
    *out=(UINTN)h==1 ? &TestPci : &Other; return EFI_SUCCESS;
  }
  return StartupHandle(h,g,out);
}
static void PairSetup(void) {
  Startup(); SecureEnabled=0; DeviceCount=2; WrongSubsystem=FALSE;
  TestPci.Pci.Read=PairRead; Other=TestPci; Services.HandleProtocol=PairHandle;
  Services.ProtocolsPerHandle=TreeProtocols; Services.OpenProtocolInformation=TreeOpens;
}
int main(void) {
  unsigned cases=0;
  for (unsigned i=0;i<2;i++) {
    PairSetup(); DualSelectedIdentity=i ? 0x220610deU : 0x220810deU;
    assert(DualTreeMain((EFI_HANDLE)77,&System)==EFI_SUCCESS && !Polls);
    assert(strstr(SavedLog,"TREE_RESULT status=0 touched=0"));
    assert(strstr(SavedLog,i ? "config_before[00]=220610de" : "config_before[00]=220810de"));
    assert(!strstr(SavedLog,i ? "config_before[00]=220810de" : "config_before[00]=220610de"));
    cases++;
  }
  PairSetup(); DualSelectedIdentity=0x220810deU; WrongSubsystem=TRUE;
  assert(EFI_ERROR(DualTreeMain((EFI_HANDLE)77,&System)) && !Polls); cases++;
  printf("PASS %u actual dual-tree entry scenarios; no GPU mutation services provided\n",cases);
  return 0;
}
''', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ti-profile', type=Path, required=True)
    parser.add_argument('--other-profile', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / 'data') or out.exists():
        raise RuntimeError('Choose a new ignored project data directory.')
    env = dict(os.environ)
    env['PATH'] = os.pathsep.join((str(LLVM), str(BUN.parent), env['PATH']))
    if execute(['git', 'rev-parse', 'HEAD'], SOURCE, env).strip() != PIN or execute(
            ['git', 'status', '--porcelain'], SOURCE, env).strip():
        raise RuntimeError('Pinned upstream source changed.')
    ti = subsystem(args.ti_profile, '2208')
    other = subsystem(args.other_profile, '2206')
    out.mkdir(parents=True)
    header = out / 'dual-board-policy.private.h'
    header.write_text(f'#define DUAL_TI_SUBSYSTEM 0x{ti}U\n'
                      f'#define DUAL_3080_SUBSYSTEM 0x{other}U\n', encoding='ascii')
    board, tree = patched_sources(out)
    files = [out / 'board-dual.c', out / 'tree-dual.c', ROOT / 'scripts/uefi_dual_probe.c',
             SOURCE / 'src/probe/probe_core.c', SOURCE / 'src/probe/probe_profile.c',
             SOURCE / 'src/unlock/sha256.c', SOURCE / 'src/gop/tree.c',
             SOURCE / 'src/unlock/format.c', SOURCE / 'src/unlock/runtime.c']
    for file in files:
        text = file.read_text()
        if any(re.search(p, text) for p in FORBIDDEN):
            raise RuntimeError('Unexpected mutating operation: ' + file.name)
    tests = {}
    for suite in ('probe', 'probe-profile', 'gop-cycle'):
        execute([BUN, 'tools/test.ts', suite], SOURCE, env, out / (suite + '.log'))
        tests['upstream_' + suite] = 'passed'
        print('upstream ' + suite + ': passed', flush=True)
    entry_fixtures(out)
    tests['controller'] = compile_host(out, env, header, 'controller',
        [ROOT / 'scripts/test_uefi_dual_probe.c', ROOT / 'scripts/uefi_dual_probe.c'])
    tests['board_entry'] = compile_host(out, env, header, 'board-entry',
        [out / 'board-entry-fixture.c', out / 'board-dual.c',
         SOURCE / 'src/probe/probe_core.c', SOURCE / 'src/probe/probe_profile.c',
         SOURCE / 'src/unlock/sha256.c'])
    tests['tree_entry'] = compile_host(out, env, header, 'tree-entry',
        [out / 'tree-entry-fixture.c', SOURCE / 'src/gop/tree.c', SOURCE / 'src/unlock/format.c'],
        ['-DGC_TREE_ONLY'])
    build = out / 'build'; build.mkdir()
    flags = ['-target', 'x86_64-pc-windows-msvc', '-std=c11', '-ffreestanding',
             '-fno-builtin', '-fno-stack-protector', '-mno-red-zone', '-fshort-wchar',
             '-Os', '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter', '-Wno-unused-function',
             '-DGC_TREE_ONLY', '-I', ROOT / 'scripts', '-I', out,
             '-I', SOURCE / 'src/probe', '-I', SOURCE / 'src/gop', '-I', SOURCE / 'src/unlock',
             '-I', SOURCE / 'src/unlock/compat', '-I', SOURCE / 'deps/edk2/MdePkg/Include',
             '-I', SOURCE / 'deps/edk2/MdePkg/Include/X64', '-include', header]
    objects = []
    for i, file in enumerate(files):
        obj = build / f'{i}.obj'
        execute([LLVM / 'clang.exe', *flags, '-c', file, '-o', obj], SOURCE, env)
        objects.append(obj)
    image = build / 'BOOTX64.EFI'; mapfile = build / 'BOOTX64.map'
    execute([LLVM / 'lld-link.exe', '/nologo', '/nodefaultlib', '/subsystem:efi_application',
             '/entry:efi_main', '/machine:x64', '/base:0', '/dynamicbase', '/nxcompat',
             '/timestamp:0', '/opt:ref', '/opt:icf', f'/map:{mapfile}', f'/out:{image}',
             *objects], SOURCE, env)
    execute([BUN, 'tools/verify_pe.ts', image, mapfile, '--output', build / 'pe.json'], SOURCE, env)
    linked = mapfile.read_text()
    for symbol in ('DualInventory', 'DualBoardMain', 'DualTreeMain', 'ProbeCollect', 'GcReadTree'):
        if not re.search(r'\b' + symbol + r'\b', linked):
            raise RuntimeError('Missing diagnostic symbol: ' + symbol)
    for symbol in ('GfRun', 'GxPatch', 'GuWrite32', 'GuDmaAllocate', 'GwStart', 'GuProfileCreate'):
        if re.search(r'\b' + symbol + r'\b', linked):
            raise RuntimeError('Unexpected mutation code linked: ' + symbol)
    package = out / 'usb-package'; (package / 'EFI/BOOT').mkdir(parents=True)
    shutil.copy2(image, package / 'EFI/BOOT/BOOTX64.EFI')
    for folder in ('RTX30-PROBE', 'RTX-UNLOCK'):
        (package / folder).mkdir()
        (package / folder / 'README.txt').write_text(
            'Read-only pair preparation. Preserve every RUNnn directory; captures are private.\n', encoding='ascii')
    for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md'):
        shutil.copy2(SOURCE / name, package / name)
    shutil.copytree(SOURCE / 'LICENSES', package / 'LICENSES')
    execute(['git', 'archive', '--format=tar.gz', '--output=' + str(package / 'SOURCE.tar.gz'), PIN], SOURCE, env)
    helpers = package / 'LOCAL-SOURCE'; helpers.mkdir()
    for name in ('uefi_dual_probe.h', 'uefi_dual_probe.c', 'test_uefi_dual_probe.c',
                 'prepare_uefi_dual_probe.py', 'prepare_windows_3060_unlock.py', 'prepare_uefi_probe.py'):
        shutil.copy2(ROOT / 'scripts' / name, helpers / name)
    for name in ('board-dual.c', 'tree-dual.c', header.name):
        shutil.copy2(out / name, helpers / name)
    guide = ROOT / 'reports/RTX3080-DUAL-WINDOWS-PREPARATION-20261025.md'
    shutil.copy2(guide, package / 'START-HERE.md')
    info = dict(source_commit=PIN, mode='read-only dual-card preparation',
                unlock_code_linked=False, firmware_assets_included=False,
                gpu_writes=False, gpu_resets=False, driver_detach=False,
                automatic_unlock=False, internal_boot_changes=False, physical_pair_tested=False,
                tests=tests, efi=json.loads((build / 'pe.json').read_text()),
                input_profiles_sha256=[sha(args.ti_profile), sha(args.other_profile)],
                next_step='Install both cards, capture actual topology, then review before building any dual unlock.')
    (package / 'BUILD-INFO.json').write_text(json.dumps(info, indent=2) + '\n')
    (package / 'SHA256SUMS.txt').write_text(''.join(
        sha(f) + '  ' + f.relative_to(package).as_posix() + '\n'
        for f in sorted(package.rglob('*')) if f.is_file()), encoding='ascii')
    with zipfile.ZipFile(out / 'dual-readonly-usb.zip', 'x', zipfile.ZIP_DEFLATED) as bundle:
        for f in sorted(package.rglob('*')):
            if f.is_file(): bundle.write(f, f.relative_to(package).as_posix())
    print(json.dumps({'package': str(package), 'efi_sha256': sha(image), 'unlock_ready': False}))


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        print('Dual preparation stopped: ' + str(error), file=sys.stderr)
        sys.exit(1)
