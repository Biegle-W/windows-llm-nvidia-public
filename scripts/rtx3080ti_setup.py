"""Prepare read-only 3080 Ti evidence and offline firmware checks; never install an unlock."""
import argparse
import csv
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

from prepare_windows_3060_unlock import ROOT, PIN, TREE_SOURCES, build_efi, execute, inspect_firmware, sha

SOURCE=ROOT/'runtimes/rtx30-uefi-probe-source'
LLVM=ROOT/'runtimes/uefi-probe-tools/llvm-20.1.8/bin'
BUN=ROOT/'runtimes/uefi-probe-tools/bun-1.4.4/bun-windows-x64/bun.exe'


def tools():
    env=dict(os.environ)
    env['LLVM_BIN']=str(LLVM)
    env['PATH']=os.pathsep.join((str(LLVM),str(BUN.parent),str(Path(sys.executable).parent),env['PATH']))
    if execute(['git','rev-parse','HEAD'],SOURCE,env).strip()!=PIN or execute(['git','status','--porcelain'],SOURCE,env).strip():
        raise RuntimeError('Reviewed upstream source changed.')
    return env


def new_output(path):
    path=path.resolve()
    if not path.is_relative_to(ROOT/'data') or path==ROOT/'data' or path.exists():
        raise RuntimeError('Choose a new directory under ignored project data.')
    path.mkdir(parents=True)
    return path


def inventory(text):
    rows=list(csv.reader(text.splitlines()))
    if len(rows)!=1 or len(rows[0])!=9:
        raise RuntimeError('Exactly one unambiguous NVIDIA card is required.')
    name,bdf,pci,subsystem,vbios,total,power,driver,uuid=(v.strip() for v in rows[0])
    if name!='NVIDIA GeForce RTX 3080 Ti' or pci.lower() not in ('0x220810de','220810de') or int(total)<12000:
        raise RuntimeError('The retail 2208 RTX 3080 Ti must be physically installed; the 3060 is refused.')
    if not re.fullmatch(r'(?:[0-9a-fA-F]{4}|[0-9a-fA-F]{8}):[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7]',bdf) or not vbios or not uuid:
        raise RuntimeError('Incomplete physical card identity.')
    return dict(name=name,bdf=bdf,pci=pci,subsystem=subsystem,vbios=vbios,total_mib=int(total),power_limit_w=float(power),driver=driver,uuid=uuid)


def require_3080_profile(profile):
    t=profile['target']
    if (t['vendorId'],t['deviceId'],t['architecture'])!=('10de','2208','GA102') or not profile['validation']['probeComplete']:
        raise RuntimeError('A complete physical 2208/GA102 capture is required.')
    for flag in ('unlockApproved','firmwareCompatible','hardwareTested'):
        if profile['validation'][flag]:
            raise RuntimeError('Keep independent compatibility/approval flags false during diagnostic preparation.')


def manifest(package):
    files=[f for f in sorted(package.rglob('*')) if f.is_file() and f.name!='SHA256SUMS.txt']
    (package/'SHA256SUMS.txt').write_text(''.join(sha(f)+'  '+f.relative_to(package).as_posix()+'\n' for f in files),encoding='ascii')


def prepare(path):
    env=tools();out=new_output(path)
    board=ROOT/'data/uefi-probe/rtx3080ti-readonly'
    info=json.loads((board/'BUILD-INFO.json').read_text(encoding='utf-8'))
    if info['expected_pci_id']!='10de:2208' or info['source_modified_for_efi']:
        raise RuntimeError('Expected the reviewed 3080 Ti board-probe package.')
    for line in (board/'SHA256SUMS.txt').read_text().splitlines():
        digest,relative=line.split('  ',1)
        file=(board/relative).resolve()
        if not file.is_relative_to(board) or sha(file)!=digest:
            raise RuntimeError('Board-probe package hash differs.')
    shutil.copytree(board,out/'01-board-probe')
    checks=out/'checks';checks.mkdir()
    # The pinned runner groups the tree and tree-entry cases under gop-cycle.
    execute([BUN,'tools/test.ts','gop-cycle'],SOURCE,env,checks/'gop-cycle.log')
    # Exercise the actual entry's target selection with 2208 in a CPU-host fixture.
    fixture=(SOURCE/'src/gop/test_io.c').read_text(encoding='utf-8')
    if fixture.count('0x220410deU')!=1: raise RuntimeError('Unexpected ownership-entry fixture layout.')
    fixture=fixture.replace('0x220410deU','0x220810deU')
    fixture_path=checks/'test_tree_2208.c';fixture_path.write_text(fixture,encoding='utf-8')
    flags=['-std=c11','-O1','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter',
           '-D_CRT_SECURE_NO_WARNINGS','-DGC_TREE_ONLY','-I','src/gop','-I','deps/edk2/MdePkg/Include','-I','deps/edk2/MdePkg/Include/X64']
    execute([LLVM/'clang.exe',*flags,fixture_path,'src/gop/tree.c','src/unlock/format.c','-o',checks/'tree-2208.exe'],SOURCE,env,checks/'tree-2208-build.log')
    execute([checks/'tree-2208.exe'],SOURCE,env,checks/'tree-2208.log')
    image,pe=build_efi(SOURCE,out/'build-ownership',LLVM,env,TREE_SOURCES,('GC_TREE_ONLY',),None,BUN)
    ownership=out/'02-ownership-probe';(ownership/'EFI/BOOT').mkdir(parents=True);(ownership/'RTX-UNLOCK').mkdir()
    shutil.copy2(image,ownership/'EFI/BOOT/BOOTX64.EFI')
    (ownership/'RTX-UNLOCK/README.txt').write_text('Read-only ownership capture. Preserve new RUNnn/GOP.TXT; no unlock firmware is included.\n',encoding='utf-8')
    for name in ('LICENSE','THIRD_PARTY_NOTICES.md'):shutil.copy2(SOURCE/name,ownership/name)
    shutil.copytree(SOURCE/'LICENSES',ownership/'LICENSES')
    execute(['git','archive','--format=tar.gz','--output='+str(ownership/'SOURCE.tar.gz'),PIN],SOURCE,env)
    metadata={'source_commit':PIN,'efi':pe,'mode':'GC_TREE_ONLY','firmware_assets_included':False,'unlock_code_linked':False,
              'host_tests':['gop-cycle (includes tree and tree-entry)','2208 target-selection entry fixture'],'physical_3080ti_tested':False}
    (ownership/'BUILD-INFO.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    guide=ROOT/'reports/RTX3080TI-WINDOWS-UNLOCK-SETUP-20261025.md'
    for package in (out/'01-board-probe',ownership):
        shutil.copy2(guide,package/'START-HERE.md');manifest(package)
        with zipfile.ZipFile(out/(package.name+'.zip'),'x',zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(package.rglob('*')):
                if file.is_file():archive.write(file,file.relative_to(package).as_posix())
    shutil.copy2(guide,out/'START-HERE.md')
    result={'prepared':True,'source_commit':PIN,'board_probe_sha256':info['pe']['sha256'],'ownership_probe':metadata,
            'actual_3080ti_data_available':False,'3080ti_unlock_efi_built':False,'boot_or_partition_changes':False}
    (out/'SETUP-INFO.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'prepared':True,'packages':['01-board-probe.zip','02-ownership-probe.zip'],'ownership_efi_sha256':pe['sha256'],'unlock_built':False}))


def baseline(path):
    env=tools()
    fields='name,pci.bus_id,pci.device_id,pci.sub_device_id,vbios_version,memory.total,power.limit,driver_version,uuid'
    card=inventory(execute(['nvidia-smi','--query-gpu='+fields,'--format=csv,noheader,nounits'],ROOT,env))
    from hardware_guard import selected_gpu
    gpu=selected_gpu()
    if gpu['uuid']!=card['uuid'] or gpu['free_mib']<2048:
        raise RuntimeError('The same card must have at least 2GiB actually free; no apps will be stopped.')
    exe=ROOT/'data/uefi-probe/rtx3060-compute-baseline.exe'
    if sha(exe)!='aa8cca683335ee33ab000829b0aa47eceb7de04281eec39d3d36103b2338916e':
        raise RuntimeError('The retained comparison executable changed.')
    env['CUDA_VISIBLE_DEVICES']=card['uuid']
    cuda=Path(os.environ.get('CUDA_PATH_V13_3',r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3'))
    env['PATH']=str(cuda/'bin')+os.pathsep+str(cuda/'bin/x64')+os.pathsep+env['PATH']
    data=json.loads(execute([exe],ROOT,env))
    if len(data['benchmarks'])!=3 or not all(x['reference_checked'] for x in data['benchmarks']):
        raise RuntimeError('Compute reference checks failed.')
    out=new_output(path)
    (out/'baseline.private.json').write_text(json.dumps({'label':'Before this project attempts a 3080Ti unlock; hardware lock state not independently asserted','card':card,'compute':data},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'baseline_saved':True,'name':card['name'],'measurements':[{ 'mode':x['name'],'tflops':x['gflops']/1000} for x in data['benchmarks']]}))


def audit(capture,path,ownership_log):
    env=tools();capture=capture.resolve()
    sys.path.insert(0,str(SOURCE/'tools'))
    parser=importlib.import_module('probe_profile');checker=importlib.import_module('check_profile')
    # Parse and reject wrong-card input before copying or creating output.
    profile=parser.generate(capture/'REPORT.TXT',capture/'PROM.BIN');require_3080_profile(profile)
    out=new_output(path);raw=out/'capture';raw.mkdir()
    for name in ('REPORT.TXT','PROM.BIN','ROMIMAGE.BIN','INVENTORY.TXT'):
        if (capture/name).is_file():shutil.copy2(capture/name,raw/name)
    profile=parser.generate(raw/'REPORT.TXT',raw/'PROM.BIN');require_3080_profile(profile)
    file=out/'diagnostic-profile.private.json';file.write_text(json.dumps(profile,indent=2)+'\n',encoding='utf-8')
    checked=checker.check(file,experimental=True);require_3080_profile(checked)
    (out/'board-profile.private.h').write_text(checker.header(checked),encoding='ascii')
    fw=inspect_firmware(SOURCE,out,LLVM,env,checked)
    (out/'offline-firmware.private.json').write_text(json.dumps(fw,indent=2)+'\n',encoding='utf-8')
    tree_captured=False
    if ownership_log:
        text=ownership_log.read_text(encoding='utf-8-sig')
        if 'config_before[00]=220810de' not in text or 'TREE_RESULT status=0 touched=0' not in text or not re.search(r'TREE_END status=0 complete=1 .*detach_attempted=0',text):
            raise RuntimeError('Ownership capture is incomplete, wrong-card or not read-only.')
        shutil.copy2(ownership_log,out/'ownership-GOP.private.txt');tree_captured=True
    result={'board_capture_valid':True,'offline_firmware_checks_passed':True,'display_tree_captured':tree_captured,
            'display_policy_reviewed':False,'manual_unlock_build_ready':False,'unlock_efi_built':False,
            'firmware_executed':False,'unlockApproved':False,
            'next':'Review this board\'s display topology/driver roles and offline results before building its guarded manual unlock; preserve the 3060 profile.'}
    (out/'AUDIT-STATUS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='mode',required=True)
    for name in ('prepare','baseline','audit'):
        command=sub.add_parser(name);command.add_argument('--output',type=Path,required=True)
        if name=='audit':command.add_argument('--capture-dir',type=Path,required=True);command.add_argument('--ownership-log',type=Path)
    args=parser.parse_args()
    if args.mode=='prepare':prepare(args.output)
    elif args.mode=='baseline':baseline(args.output)
    else:audit(args.capture_dir,args.output,args.ownership_log)


if __name__=='__main__':
    try:main()
    except (OSError,RuntimeError,ValueError,KeyError) as error:
        print('3080 Ti setup stopped: '+str(error),file=sys.stderr);sys.exit(1)
