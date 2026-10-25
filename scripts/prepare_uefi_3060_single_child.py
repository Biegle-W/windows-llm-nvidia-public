#!/usr/bin/env python3
"""Adapt the pinned manual candidate to the captured one-child AMI display tree.

Builds and tests privately; never selects a physical drive or executes an EFI.
The unchanged upstream checkout and earlier two-child candidate are preserved.
"""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

from prepare_windows_3060_unlock import ROOT, PIN, FULL_DEFINES, FULL_SOURCES, build_efi, execute, sha


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError("Pinned source fragment differs: " + old[:75])
    return text.replace(old, new, 1)


def board_pair(identity, subsystem):
    if (identity,subsystem) not in (('250310de','407b1458'),('220810de','153510de')):
        raise RuntimeError('Only the separately captured original 3060 or installed 3080 Ti is supported.')


def read_tree(path, identity='250310de', subsystem='407b1458'):
    board_pair(identity,subsystem)
    text = path.read_text(encoding="ascii")
    if ("TREE_END status=0 complete=1 visited=4 queued=4 drivers=5" not in text or
            not text.endswith("TREE_RESULT status=0 touched=0\n") or
            f"config_before[00]={identity}" not in text or f"config_before[2c]={subsystem}" not in text):
        raise RuntimeError("Incomplete or unexpected physical ownership capture.")
    edges = []
    for h, protocol, attr, count, agent, child in re.findall(
            r"TREE_OPEN handle=(0x[0-9a-f]+) protocol=([0-9a-f]+) attr=(0x[0-9a-f]+) count=(\d+) agent=(0x[0-9a-f]+) controller=(0x[0-9a-f]+|0)", text):
        if int(attr, 16) in (1, 2, 4):
            continue
        if int(count) != 1:
            raise RuntimeError("An active ownership edge has an unexpected open count.")
        edges.append((h, protocol, int(attr, 16), agent, child))
    roots = re.findall(r"TREE_BEGIN root=(0x[0-9a-f]+)", text)
    if len(roots) != 1:
        raise RuntimeError("Ambiguous ownership root.")
    root = roots[0]

    def edge(handle, protocol, attr):
        found = [e for e in edges if e[:3] == (handle, protocol, attr)]
        if len(found) != 1:
            raise RuntimeError("Missing/ambiguous display ownership role.")
        return found[0][3:]

    nv, physical = edge(root, "09576e91", 8)
    if edge(root, "4cf5b200", 16) != (nv, root):
        raise RuntimeError("NVIDIA driver owner differs from its display-child owner.")
    combo, aggregate = edge(physical, "9042a9de", 8)
    if edge(physical, "9042a9de", 16) != (combo, physical):
        raise RuntimeError("GOP bridge ownership differs from its child owner.")
    member, shared = edge(aggregate, "387477c2", 8)
    if edge(aggregate, "387477c2", 16) != (member, aggregate):
        raise RuntimeError("Text member ownership differs from its shared-console edge.")
    gfx, controller = edge(aggregate, "9042a9de", 16)
    edid, edid_controller = edge(physical, "1c0c34f6", 16)
    if controller != aggregate or edid_controller != physical:
        raise RuntimeError("Unexpected aggregate or EDID controller.")
    if len(set((root, physical, aggregate, shared))) != 4 or len(set((nv, combo, gfx, member, edid))) != 5:
        raise RuntimeError("Display handles or driver roles alias unexpectedly.")
    expected = {(root,"09576e91",8,nv,physical),(root,"4cf5b200",16,nv,root),
                (physical,"9042a9de",8,combo,aggregate),(physical,"9042a9de",16,combo,physical),
                (physical,"1c0c34f6",16,edid,physical),(aggregate,"387477c2",8,member,shared),
                (aggregate,"387477c2",16,member,aggregate),(aggregate,"9042a9de",16,gfx,aggregate),
                (shared,"8d59d32b",16,edid,shared),(shared,"31878c87",16,edid,shared)}
    if len(edges) != 10 or set(edges) != expected:
        raise RuntimeError("Extra/missing ownership consumer; this tree is not the scoped port.")
    if f"TREE_NODE handle={shared} depth=3 console_out=1 console_in=1 stderr=1" not in text:
        raise RuntimeError("Shared input/output/error handles differ from the captured design.")
    bindings = {a: dict(version=int(v,16),start=int(start,16),stop=int(stop,16))
                for a,v,start,stop in re.findall(r"TREE_BINDING agent=(0x[0-9a-f]+).*? version=(0x[0-9a-f]+) start=(0x[0-9a-f]+) stop=(0x[0-9a-f]+)",text)}
    for a,base,size,kind in re.findall(r"TREE_IMAGE_INFO agent=(0x[0-9a-f]+) base=(0x[0-9a-f]+) bytes=(\d+) code_type=(\d+)",text):
        d=bindings[a]
        d.update(bytes=int(size),code_type=int(kind),start_offset=d.pop("start")-int(base,16),
                 stop_offset=d.pop("stop")-int(base,16))
    drivers = [bindings[a] for a in (nv,combo,gfx,member,edid)]
    for i,d in enumerate(drivers):
        if d["code_type"] != (5 if i==4 else 3) or not all(0 < d[k] < d["bytes"] for k in ("start_offset","stop_offset")):
            raise RuntimeError("Invalid driver image type or method offsets.")
    return drivers


def adapt_full(text, drivers, identity='250310de', subsystem='407b1458'):
    board_pair(identity,subsystem)
    # This is a separate exact-board implementation, not a relaxation of the
    # upstream two-child path. Every unexpected second child remains a refusal.
    text=replace_once(text,'#include "full.h"','#include "full.h"\n#include "single-driver-policy.h"')
    text=replace_once(text,'return *a && *b ? EFI_SUCCESS : EFI_UNSUPPORTED;',
                      'return *a && !*b ? EFI_SUCCESS : EFI_UNSUPPORTED;')
    text=replace_once(text,'for (UINTN i = 0; i < 4; i++) {','for (UINTN i = 0; i < 3; i++) {')
    text=replace_once(text,'  memset(p, 0, sizeof(*p));\n  EFI_STATUS s = GcLeafPrepare',
        f'  if (c->identity != 0x{identity}U || c->subsystem != 0x{subsystem}U ||\n'
        '      c->location[0] || c->location[1] != 1 || c->location[2] || c->location[3])\n'
        '    return EFI_UNSUPPORTED;\n  memset(p, 0, sizeof(*p));\n  EFI_STATUS s = GcLeafPrepare')
    text=replace_once(text,'  if (a != p->leaf.physical && b != p->leaf.physical) return EFI_UNSUPPORTED;\n  p->sibling = a == p->leaf.physical ? b : a;',
                      '  if (a != p->leaf.physical || b) return EFI_UNSUPPORTED;\n  p->sibling = NULL;')
    text=replace_once(text,'  agents[5] = Owner(&p->leaf.guard, p->sibling, &EdidGuid);\n  for (UINTN i = 0; i < 6; i++) {',
                      '  agents[5] = NULL;\n  for (UINTN i = 0; i < 5; i++) {')
    needle='    if (EFI_ERROR(s)) return s;\n    if (!c->log("FULL_DRIVER role='
    insert='''    if (EFI_ERROR(s)) return s;
#ifndef GU_TOPOLOGY_HOST_MOCK
    if (!GuSingleDriver(i, p->drivers[i].driver.bytes, p->drivers[i].driver.version,
         (UINTN)p->drivers[i].driver.start - (UINTN)p->drivers[i].driver.base,
         (UINTN)p->drivers[i].driver.stop - (UINTN)p->drivers[i].driver.base))
      return EFI_UNSUPPORTED;
#endif
    if (!c->log("FULL_DRIVER role='''
    text=replace_once(text,needle,insert)
    text=replace_once(text,'/* Only the observed two-output EDID/GOP topology is authorized for this experiment. */',
                      '/* Only the captured single-child AMI EDID/GOP topology is authorized. */')
    text=replace_once(text,'FULL_READY: two vendor children; all six roles verified; one FLR after full ',
                      'FULL_READY: one vendor child; all five captured roles verified; one FLR after full ')
    text=replace_once(text,'  s = StopAll(c, p, 5, p->sibling, 0, NULL);\n  if (EFI_ERROR(s)) goto finish;\n  EFI_HANDLE children[] = {p->leaf.physical, p->sibling};\n  s = StopAll(c, p, 0, c->target, 2, children);',
                      '  EFI_HANDLE children[] = {p->leaf.physical};\n  s = StopAll(c, p, 0, c->target, 1, children);')
    start=text.index('  EFI_HANDLE physical = NULL, sibling = NULL;')
    end=text.index('  s = Start(c, p, 4, physical);',start)
    text=text[:start]+'''  if (!a || b) { s = EFI_UNSUPPORTED; goto finish; }
  EFI_HANDLE physical = a, sibling = NULL;
  EFI_GRAPHICS_OUTPUT_PROTOCOL *gop = NULL;
  s = bs->HandleProtocol(physical, &GopGuid, (VOID **)&gop);
  if (!c->log("FULL_CHILD_GOP candidate=0 handle=%#llx status=%#llx interface=%#llx\\n",
       (unsigned long long)(UINTN)physical, (unsigned long long)s,
       (unsigned long long)(UINTN)gop)) { s = EFI_DEVICE_ERROR; goto finish; }
  if (EFI_ERROR(s) || !gop) { s = EFI_NOT_FOUND; goto finish; }
'''+text[end:]
    text=replace_once(text,'  s = Start(c, p, 5, sibling);\n  if (EFI_ERROR(s)) goto finish;\n','')
    return text


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tree',type=Path,required=True)
    parser.add_argument('--prepared',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--target',choices=('rtx3060','rtx3080ti'),default='rtx3060')
    parser.add_argument('--capture',type=Path,help='Required exact-board diagnostic profile for the 3080 Ti; never defaults to 3060 evidence')
    args=parser.parse_args()
    source=ROOT/'runtimes/rtx30-uefi-probe-source'
    llvm=ROOT/'runtimes/uefi-probe-tools/llvm-20.1.8/bin'
    bun=ROOT/'runtimes/uefi-probe-tools/bun-1.4.4/bun-windows-x64/bun.exe'
    output=args.output.resolve(); prepared=args.prepared.resolve()
    if not output.is_relative_to(ROOT/'data') or output.exists():
        raise RuntimeError('Choose a new ignored output directory.')
    env=dict(os.environ); env['LLVM_BIN']=str(llvm)
    env['PATH']=os.pathsep.join((str(llvm),str(bun.parent),str(Path(sys.executable).parent),env['PATH']))
    if execute(['git','rev-parse','HEAD'],source,env).strip()!=PIN or execute(['git','status','--porcelain'],source,env).strip():
        raise RuntimeError('Pinned upstream source is not unchanged.')
    metadata=json.loads((prepared/'BUILD-INFO.private.json').read_text())
    if metadata['source_commit']!=PIN or metadata['automatic_execution'] or metadata['physical_unlock_tested']:
        raise RuntimeError('Unexpected prerequisite candidate metadata.')
    # Revalidate original capture and profile header rather than trusting build metadata.
    sys.path.insert(0,str(source/'tools'))
    from check_profile import check,header
    if args.target=='rtx3080ti':
        if args.capture is None:raise RuntimeError('3080 Ti requires its own explicit diagnostic profile.')
        from rtx3080ti_setup import require_installed_board
        profile=check(args.capture,experimental=True);require_installed_board(profile)
        identity,subsystem='220810de','153510de'
        instructions=ROOT/'reports/RTX3080TI-WINDOWS-FIRST-UNLOCK-TRIAL-20261025.md'
    else:
        if args.capture is not None:raise RuntimeError('The original 3060 build uses its preserved capture only.')
        profile=check(ROOT/'data/uefi-probe/captures/20261025-RUN00/diagnostic-profile.json',experimental=True)
        identity,subsystem='250310de','407b1458'
        instructions=ROOT/'reports/RTX3060-WINDOWS-FIRST-UNLOCK-TRIAL.md'
    if (prepared/'private-board-profile.h').read_text()!=header(profile):
        raise RuntimeError('Prerequisite fixed profile header changed.')
    for row in (prepared/'manual-unlock-candidate/SHA256SUMS.txt').read_text().splitlines():
        digest,name=row.split('  ',1)
        if sha(prepared/'manual-unlock-candidate'/name)!=digest:
            raise RuntimeError('Prerequisite package changed.')
    drivers=read_tree(args.tree,identity,subsystem)
    output.mkdir(parents=True); logs=output/'checks'; logs.mkdir()
    policy='''/* GPL-2.0-only. Fixed metadata from the physical ownership capture. */
#pragma once
#include <Uefi.h>
static BOOLEAN GuSingleDriver(UINTN role, UINTN size, UINT32 version, UINTN start, UINTN stop) {
  const UINTN sizes[] = {%s};
  const UINT32 versions[] = {%s};
  const UINTN starts[] = {%s}, stops[] = {%s};
  return role < 5 && size == sizes[role] && version == versions[role] &&
         start == starts[role] && stop == stops[role];
}
''' % tuple(','.join(str(d[k]) for d in drivers) for k in ('bytes','version','start_offset','stop_offset'))
    (output/'single-driver-policy.h').write_text(policy)
    original=(source/'src/gop/full.c').read_text()
    full=adapt_full(original,drivers,identity,subsystem); patched=output/'full-single.c'; patched.write_text(full)
    (output/'single-child.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),full.splitlines(True),fromfile='upstream/src/gop/full.c',tofile='local/full-single.c')))
    fixture=(source/'src/gop/test_full.c').read_text()
    fixture=replace_once(fixture,'    Add(e, n, VENDOR, Current(EDID), EFI_OPEN_PROTOCOL_BY_CHILD_CONTROLLER);\n','')
    fixture=replace_once(fixture,'static EFI_STATUS EFIAPI FOpens(',
                        'static BOOLEAN InjectSecondChild;\nstatic EFI_STATUS EFIAPI FOpens(')
    fixture=replace_once(fixture,'    Add(e, n, VENDOR, Current(PHYS), EFI_OPEN_PROTOCOL_BY_CHILD_CONTROLLER);',
                        '    Add(e, n, VENDOR, Current(PHYS), EFI_OPEN_PROTOCOL_BY_CHILD_CONTROLLER);\n'
                        '    if (InjectSecondChild) Add(e, n, VENDOR, Current(EDID), EFI_OPEN_PROTOCOL_BY_CHILD_CONTROLLER);')
    fixture=replace_once(fixture,'assert(n == 2 && children[0] == PHYS && children[1] == EDID);','assert(n == 1 && children[0] == PHYS);')
    fixture=replace_once(fixture,'  Exclusive = NewHandles = Recreate = Quiet = FailResetWrite',
                        '  EdidS = InjectSecondChild = FALSE;\n  Context.location[1] = 1;\n  Exclusive = NewHandles = Recreate = Quiet = FailResetWrite')
    fixture=fixture.replace('0x220310deU','0x'+identity+'U').replace('0x20007377U','0x'+subsystem+'U')
    fixture=fixture.replace('role=sibling_edid','role=intermediate_text')
    (output/'test_full_single.c').write_text(fixture)
    patch_fixture=(source/'src/gop/test_patch.c').read_text().replace('#include "test_full.c"','#include "test_full_single.c"')
    patch_fixture=replace_once(patch_fixture,'    if (ChildCase == 2) *n = 1;\n','')
    patch_fixture=replace_once(patch_fixture,'if (ChildCase == 3) {','if (ChildCase == 2 || ChildCase == 3) {')
    patch_fixture=patch_fixture.replace('unique=2','unique=1')
    patch_fixture=replace_once(patch_fixture,'count ? "unique=1" : "unique=0"','count ? "unique=2" : "unique=0"')
    patch_fixture=replace_once(patch_fixture,'post-start status=0 unique=3','post-start status=0 unique=2')
    patch_fixture=replace_once(patch_fixture,'assert(strstr(FullLog, "FULL_CHILD_GOP candidate=0") &&\n         strstr(FullLog, "FULL_CHILD_GOP candidate=1"));',
                              'assert(strstr(FullLog, "FULL_CHILD_GOP candidate=0") &&\n         !strstr(FullLog, "FULL_CHILD_GOP candidate=1"));')
    (output/'test_patch_single.c').write_text(patch_fixture)
    host=['-std=c11','-O1','-Wall','-Wextra','-Werror','-Wno-unused-function',
          '-D_CRT_SECURE_NO_WARNINGS','-DGU_TOPOLOGY_HOST_MOCK','-I',output,'-I','src/gop',
          '-I','deps/edk2/MdePkg/Include','-I','deps/edk2/MdePkg/Include/X64']
    for name,extra in (('full',[]),('patch',['-DGC_FULL_UNLOCK'])):
        exe=logs/(name+'.exe')
        execute([llvm/'clang.exe',*host,*extra,output/('test_'+name+'_single.c'),patched,
                 'src/gop/reset.c','src/gop/leaf.c','-o',exe],source,env,logs/(name+'-build.log'))
        result=execute([exe],source,env,logs/(name+'.log'))
        print(result.strip(),flush=True)
    # Exercise the exact driver metadata policy separately; mock callbacks cannot
    # live at real UEFI image offsets. The EFI build never defines the mock flag.
    policy_test='#include "single-driver-policy.h"\n#include <assert.h>\nint main(void) {\n'
    for i,d in enumerate(drivers):
        values=[i,d['bytes'],d['version'],d['start_offset'],d['stop_offset']]
        policy_test+='assert(GuSingleDriver('+','.join(map(str,values))+'));\n'
        for j in range(1,5):
            bad=values.copy(); bad[j]+=1
            policy_test+='assert(!GuSingleDriver('+','.join(map(str,bad))+'));\n'
    policy_test+='assert(!GuSingleDriver(5,0,0,0,0));return 0;}\n'
    (output/'test_driver_policy.c').write_text(policy_test)
    execute([llvm/'clang.exe',*host,output/'test_driver_policy.c','-o',logs/'driver-policy.exe'],source,env)
    execute([logs/'driver-policy.exe'],source,env)
    # Additional preflight replays retain an unexpected second child and wrong BDF.
    rejected=fixture.replace('int main(void) {','int OriginalFullChecks(void) {',1)
    rejected+='''\nint main(void) { GF_PLAN plan; FReset(); Context.location[1]=2;
      assert(EFI_ERROR(GfPrepare(&Context,&plan)) && !FullStops);
      FReset(); InjectSecondChild=TRUE;
      assert(EFI_ERROR(GfPrepare(&Context,&plan)) && !FullStops);
      return 0; }\n'''
    (output/'test_scope.c').write_text(rejected)
    execute([llvm/'clang.exe',*host,output/'test_scope.c',patched,'src/gop/reset.c','src/gop/leaf.c','-o',logs/'scope.exe'],source,env)
    execute([logs/'scope.exe'],source,env)
    header_path=prepared/'private-board-profile.h'
    hardware_flags=['-target','x86_64-pc-windows-msvc','-std=c11','-fshort-wchar',
                    '-I','src/unlock/compat','-I','deps/edk2/MdePkg/Include',
                    '-I','deps/edk2/MdePkg/Include/X64','-I','src/gop',
                    '-include',header_path]+['-D'+d for d in FULL_DEFINES]
    expanded=execute([llvm/'clang.exe',*hardware_flags,'-E','-P',patched],source,env)
    if not re.search(r'if\s*\(!GuSingleDriver\(i,',expanded):
        raise RuntimeError('Driver method-offset checks are missing from the EFI compilation path.')
    (logs/'hardware-preprocessed.c').write_text(expanded)
    # Resolve a private source override without changing the upstream source tree.
    sources=[str(patched) if s=='src/gop/full.c' else s for s in FULL_SOURCES]
    build_env=env.copy()
    # The compiler searches the patched source directory for its policy header;
    # the pinned gop headers are provided via a local compiler wrapper directory.
    for name in ('full.h','leaf.h','reset.h','cycle.h','patch.h','visual.h'):
        shutil.copy2(source/'src/gop'/name,output/name)
    # Relative ../unlock includes in these headers need the original tree layout.
    # build_efi adds common includes; patched full.c's local headers reference
    # only these peers. No source override is used for the transaction itself.
    image,pe=build_efi(source,output/'build',llvm,build_env,sources,FULL_DEFINES,header_path,bun)
    package=output/'manual-unlock-candidate'
    shutil.copytree(prepared/'manual-unlock-candidate',package)
    (package/'EFI/BOOT').mkdir(parents=True,exist_ok=True)
    shutil.copy2(image,package/'EFI/BOOT/BOOTX64.EFI')
    local=package/'LOCAL-PORT'; local.mkdir()
    for name in ('full-single.c','single-driver-policy.h','single-child.patch'):
        shutil.copy2(output/name,local/name)
    shutil.copy2(Path(__file__),local/Path(__file__).name)
    shutil.copy2(instructions,package/'START-HERE.md')
    info={'source_commit':PIN,'mode':'fixed '+args.target+' single-child AMI manual experiment',
          'upstream_checkout_changed':False,'display_source_override':True,'transaction_source_changed':False,
          'ownership_tree_complete':True,'display_children':1,'driver_roles':5,'driver_metadata':drivers,
          'driver_code_hashes_captured':False,'driver_method_offsets_checked_in_efi':True,
          'mock_flag_in_efi':False,'manual_u_required':True,'automatic_execution':False,
          'firmware_assets_verified':5,'physical_unlock_tested':False,'efi':pe,
          'tests':{'single_child_full_replay':'passed','single_child_patch_replay':'passed',
                   'driver_policy_26_cases':'passed','wrong_bdf_and_extra_child_preflight':'passed',
                   'hardware_preprocessed_driver_checks_present':'passed'},
          'note':'Host replay is not proof of real GOP Stop/Start behavior; first hardware trial remains experimental.'}
    (output/'BUILD-INFO.json').write_text(json.dumps(info,indent=2)+'\n')
    (package/'BUILD-INFO.json').write_text(json.dumps(info,indent=2)+'\n')
    (package/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(package).as_posix()+'\n' for p in sorted(package.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt'))
    print('Single-child candidate built and tested; no physical drive changed.',flush=True)


if __name__=='__main__':
    try:
        main()
    except (OSError,RuntimeError,ValueError,KeyError) as error:
        print('Single-child preparation stopped: '+str(error),file=sys.stderr)
        sys.exit(1)
