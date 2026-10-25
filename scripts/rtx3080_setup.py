"""Separate2206 RTX3080 10GB diagnostics/baseline/audit; never build or execute an unlock."""
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

from prepare_windows_3060_unlock import ROOT,PIN,TREE_SOURCES,build_efi,execute,inspect_firmware,sha
from rtx3080ti_setup import tools,new_output,manifest

SOURCE=ROOT/'runtimes/rtx30-uefi-probe-source'
LLVM=ROOT/'runtimes/uefi-probe-tools/llvm-20.1.8/bin'
BUN=ROOT/'runtimes/uefi-probe-tools/bun-1.4.4/bun-windows-x64/bun.exe'


def inventory(text):
    rows=list(csv.reader(text.splitlines()))
    if len(rows)!=1 or len(rows[0])!=9:raise RuntimeError('Exactly one physical NVIDIA card is required.')
    name,bdf,pci,subsystem,vbios,total,power,driver,uuid=(x.strip() for x in rows[0])
    if name!='NVIDIA GeForce RTX 3080' or pci.lower()!='0x220610de' or int(total)!=10240:
        raise RuntimeError('This separate setup requires2206 RTX3080 with10240MiB;3060/3080Ti/other variants are refused.')
    if not re.fullmatch(r'(?:[0-9a-fA-F]{4}|[0-9a-fA-F]{8}):[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7]',bdf) or not re.fullmatch(r'0x[0-9a-fA-F]{8}',subsystem) or not vbios or not uuid:
        raise RuntimeError('Incomplete physical card identity.')
    domain,bus,device=bdf.split(':')
    return {'name':name,'bdf':f'{int(domain,16):04x}:{bus.lower()}:{device.lower()}',
        'pci':pci,'subsystem':subsystem,'vbios':vbios,'total_mib':int(total),
        'power_limit_w':float(power),'driver':driver,'uuid':uuid}


def require_profile(profile,card):
    t=profile['target'];sub=int(card['subsystem'],16)
    expected=('10de','2206','GA102',f'{sub&65535:04x}',f'{sub>>16:04x}',card['bdf'])
    actual=tuple(t.get(k) for k in ('vendorId','deviceId','architecture','subsystemVendorId','subsystemDeviceId','pciAddress'))
    if actual!=expected or not profile['validation']['probeComplete']:
        raise RuntimeError('Capture does not match the actual3080 baseline identity.')
    if any(profile['validation'][x] for x in ('unlockApproved','firmwareCompatible','hardwareTested')):
        raise RuntimeError('Diagnostic approval/compatibility flags must remain false.')


def ownership(path):
    env=tools();out=new_output(path);checks=out/'checks';checks.mkdir()
    execute([BUN,'tools/test.ts','gop-cycle'],SOURCE,env,checks/'gop-cycle.log')
    fixture=(SOURCE/'src/gop/test_io.c').read_text(encoding='utf-8')
    if fixture.count('0x220410deU')!=1:raise RuntimeError('Reviewed target fixture changed.')
    file=checks/'entry-2206.c';file.write_text(fixture.replace('0x220410deU','0x220610deU'),encoding='utf-8')
    flags=['-std=c11','-O1','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter',
        '-D_CRT_SECURE_NO_WARNINGS','-DGC_TREE_ONLY','-I','src/gop','-I','deps/edk2/MdePkg/Include','-I','deps/edk2/MdePkg/Include/X64']
    execute([LLVM/'clang.exe',*flags,file,'src/gop/tree.c','src/unlock/format.c','-o',checks/'entry-2206.exe'],SOURCE,env)
    execute([checks/'entry-2206.exe'],SOURCE,env,checks/'entry-2206.log')
    image,pe=build_efi(SOURCE,out/'build',LLVM,env,TREE_SOURCES,('GC_TREE_ONLY',),None,BUN)
    package=out/'package';(package/'EFI/BOOT').mkdir(parents=True);(package/'RTX-UNLOCK').mkdir()
    shutil.copy2(image,package/'EFI/BOOT/BOOTX64.EFI')
    (package/'RTX-UNLOCK/README.txt').write_text('Read-only2206 ownership capture. No unlock linked. Preserve new RUNnn/GOP.TXT.\n',encoding='utf-8')
    for name in ('LICENSE','THIRD_PARTY_NOTICES.md'):shutil.copy2(SOURCE/name,package/name)
    shutil.copytree(SOURCE/'LICENSES',package/'LICENSES')
    execute(['git','archive','--format=tar.gz','--output='+str(package/'SOURCE.tar.gz'),PIN],SOURCE,env)
    shutil.copy2(ROOT/'reports/RTX3080-10GB-UNLOCK-SETUP-20261025.md',package/'START-HERE.md')
    info={'source_commit':PIN,'expected_pci_id':'10de:2206','mode':'GC_TREE_ONLY','efi':pe,
        'unlock_code_linked':False,'firmware_assets_included':False,'physical_3080_tested':False,
        'host_tests':['gop-cycle','2206 target-selection entry fixture']}
    (package/'BUILD-INFO.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8');manifest(package)
    with zipfile.ZipFile(out.with_suffix('.zip'),'x',zipfile.ZIP_DEFLATED) as z:
        for f in package.rglob('*'):
            if f.is_file():z.write(f,f.relative_to(package).as_posix())
    print(json.dumps({'ownership_package_prepared':True,'efi_sha256':pe['sha256'],'unlock_built':False}))


def baseline(path):
    fields='name,pci.bus_id,pci.device_id,pci.sub_device_id,vbios_version,memory.total,power.limit,driver_version,uuid'
    card=inventory(subprocess.check_output(['nvidia-smi','--query-gpu='+fields,'--format=csv,noheader,nounits'],text=True,creationflags=subprocess.CREATE_NO_WINDOW))
    free=subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True,creationflags=subprocess.CREATE_NO_WINDOW)
    if int(free.strip())<2048:raise RuntimeError('At least2GiB actual free VRAM required; no apps will be stopped.')
    exe=ROOT/'data/uefi-probe/rtx3060-compute-baseline.exe'
    if sha(exe)!='aa8cca683335ee33ab000829b0aa47eceb7de04281eec39d3d36103b2338916e':raise RuntimeError('Comparison executable differs.')
    env=dict(os.environ);env['CUDA_VISIBLE_DEVICES']=card['uuid']
    cuda=Path(os.environ.get('CUDA_PATH_V13_3',r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3'))
    env['PATH']=str(cuda/'bin')+os.pathsep+str(cuda/'bin/x64')+os.pathsep+env['PATH']
    data=json.loads(execute([exe],ROOT,env))
    if len(data['benchmarks'])!=3 or not all(x['reference_checked'] for x in data['benchmarks']):raise RuntimeError('Compute reference checks failed.')
    out=new_output(path);(out/'baseline.private.json').write_text(json.dumps({'label':'Before project3080 unlock; lock state not independently asserted','card':card,'compute':data},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'3080_baseline_recorded':True,'measurements':[{'mode':x['name'],'tflops':x['gflops']/1000} for x in data['benchmarks']]}))


def audit(capture,baseline_path,path,tree):
    env=tools();sys.path.insert(0,str(SOURCE/'tools'))
    parser=importlib.import_module('probe_profile');checker=importlib.import_module('check_profile')
    saved=json.loads(baseline_path.read_text(encoding='utf-8'));card=saved['card']
    if card['name']!='NVIDIA GeForce RTX 3080' or card['total_mib']!=10240 or card['pci'].lower()!='0x220610de':raise RuntimeError('An actual2206/10GB baseline is required.')
    profile=parser.generate(capture/'REPORT.TXT',capture/'PROM.BIN');require_profile(profile,card)
    if tree:
        text=tree.read_text(encoding='utf-8-sig');sub=f"{int(card['subsystem'],16):08x}"
        if 'config_before[00]=220610de' not in text or f'config_before[2c]={sub}' not in text or 'TREE_RESULT status=0 touched=0' not in text or not re.search(r'TREE_END status=0 complete=1 .*detach_attempted=0',text):raise RuntimeError('Ownership log is wrong-card/incomplete or not read-only.')
    out=new_output(path);raw=out/'capture';raw.mkdir()
    for name in ('REPORT.TXT','PROM.BIN','ROMIMAGE.BIN','INVENTORY.TXT'):
        if (capture/name).is_file():shutil.copy2(capture/name,raw/name)
    profile=parser.generate(raw/'REPORT.TXT',raw/'PROM.BIN');require_profile(profile,card)
    file=out/'diagnostic-profile.private.json';file.write_text(json.dumps(profile,indent=2)+'\n',encoding='utf-8')
    require_profile(checker.check(file,experimental=True),card)
    (out/'board-profile.private.h').write_text(checker.header(profile),encoding='ascii')
    fw=inspect_firmware(SOURCE,out,LLVM,env,profile)
    (out/'offline-firmware.private.json').write_text(json.dumps(fw,indent=2)+'\n',encoding='utf-8')
    if tree:shutil.copy2(tree,out/'ownership-GOP.private.txt')
    result={'board_capture_valid':True,'offline_checks_passed':True,'ownership_capture_present':bool(tree),
        'display_policy_reviewed':False,'unlock_built':False,'firmware_executed':False,'unlockApproved':False}
    (out/'AUDIT-STATUS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))


def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='mode',required=True)
    for mode in ('ownership','baseline','audit'):
        command=s.add_parser(mode);command.add_argument('--output',type=Path,required=True)
        if mode=='audit':
            command.add_argument('--capture-dir',type=Path,required=True);command.add_argument('--baseline',type=Path,required=True);command.add_argument('--ownership-log',type=Path)
    a=p.parse_args()
    if a.mode=='ownership':ownership(a.output)
    elif a.mode=='baseline':baseline(a.output)
    else:audit(a.capture_dir,a.baseline,a.output,a.ownership_log)


if __name__=='__main__':
    try:main()
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.CalledProcessError) as error:
        print('3080 setup stopped: '+str(error),file=sys.stderr);sys.exit(1)
