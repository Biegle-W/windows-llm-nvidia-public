#!/usr/bin/env python3
"""Build a logged automatic internal-ESP variant of the hardware-tested 3060 port.

No partition, boot variable or installed file is changed. The installer supplies
the unique GUID of its newly created dedicated ESP. A preview GUID is test-only.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import uuid
import zipfile

from prepare_windows_3060_unlock import ROOT, PIN, FULL_SOURCES, FULL_DEFINES, build_efi, execute, sha
from prepare_uefi_3060_single_child import replace_once


def guid_c(value):
    g=uuid.UUID(value.strip('{}'))
    b=g.bytes
    return '{0x%x,0x%x,0x%x,{%s}}' % (g.time_low,g.time_mid,g.time_hi_version,','.join('0x%02x'%x for x in b[8:]))


def boot_header(guid):
    return '''/* GPL-2.0-only. Only the dedicated internal GPT ESP may supply this build. */
#pragma once
#include <Uefi.h>
#include <Protocol/DevicePath.h>
#include <Protocol/PartitionInfo.h>
#include <Guid/Gpt.h>
#include <string.h>
static const EFI_GUID GuInternalPartition = %s;
static inline BOOLEAN GuBootSourceAllowed(EFI_SYSTEM_TABLE *table, EFI_HANDLE device) {
  EFI_GUID pathGuid=EFI_DEVICE_PATH_PROTOCOL_GUID, partGuid=EFI_PARTITION_INFO_PROTOCOL_GUID;
  EFI_GUID espGuid=EFI_PART_TYPE_EFI_SYSTEM_PART_GUID;
  EFI_DEVICE_PATH_PROTOCOL *path=NULL;
  EFI_PARTITION_INFO_PROTOCOL *part=NULL;
  if (!table || !table->BootServices ||
      EFI_ERROR(table->BootServices->HandleProtocol(device,&partGuid,(VOID **)&part)) ||
      !part || part->Revision!=EFI_PARTITION_INFO_PROTOCOL_REVISION || part->Type!=PARTITION_TYPE_GPT ||
      memcmp(&part->Info.Gpt.PartitionTypeGUID,&espGuid,sizeof(espGuid)) ||
      memcmp(&part->Info.Gpt.UniquePartitionGUID,&GuInternalPartition,sizeof(GuInternalPartition)) ||
      EFI_ERROR(table->BootServices->HandleProtocol(device,&pathGuid,(VOID **)&path)) || !path)
    return FALSE;
  UINTN total=0; BOOLEAN disk=FALSE;
  for (UINTN i=0;i<64 && total+4<=4096;i++) {
    UINTN n=path->Length[0]+((UINTN)path->Length[1]<<8);
    if (n<4 || n>4096-total) return FALSE;
    if (path->Type==MESSAGING_DEVICE_PATH && (path->SubType==MSG_USB_DP ||
        path->SubType==MSG_USB_CLASS_DP || path->SubType==MSG_USB_WWID_DP)) return FALSE;
    if (path->Type==MEDIA_DEVICE_PATH && path->SubType==MEDIA_HARDDRIVE_DP) {
      HARDDRIVE_DEVICE_PATH *hd=(VOID *)path;
      if (disk || n!=sizeof(*hd) || hd->SignatureType!=SIGNATURE_TYPE_GUID ||
          memcmp(hd->Signature,&GuInternalPartition,sizeof(GuInternalPartition))) return FALSE;
      disk=TRUE;
    }
    if (path->Type==END_DEVICE_PATH_TYPE)
      return disk && n==4 && path->SubType==END_ENTIRE_DEVICE_PATH_SUBTYPE;
    total+=n; path=(VOID *)((UINT8 *)path+n);
  }
  return FALSE;
}
''' % guid_c(guid)


def automatic_app(text):
    begin=text.index('static EFI_STATUS Approve(VOID) {')
    end=text.index('\nstatic VOID Halt(VOID)',begin)
    text=text[:begin]+'''static EFI_STATUS Approve(VOID) {
  if (!Table->ConIn || !Table->ConIn->Reset || !Table->ConIn->ReadKeyStroke)
    return EFI_UNSUPPORTED;
  EFI_STATUS status=Table->ConIn->Reset(Table->ConIn,FALSE);
  if (EFI_ERROR(status)) return status;
  status=Say(L"Automatic RTX 3060 unlock after preflight. Esc cancels within 6 seconds.\\r\\n"
             L"F8 > Windows Boot Manager always bypasses this application.\\r\\n");
  if (EFI_ERROR(status)) return status;
  for (UINTN i=0;i<60;i++) {
    EFI_INPUT_KEY key;
    status=Table->ConIn->ReadKeyStroke(Table->ConIn,&key);
    if (!EFI_ERROR(status)) {
      if (key.ScanCode==0x17 || key.UnicodeChar==0x1b) return EFI_ABORTED;
    } else if (status!=EFI_NOT_READY) return status;
    Table->BootServices->Stall(100000);
  }
  return EFI_SUCCESS;
}'''+text[end:]
    text=replace_once(text,'  BOOLEAN manual = TRUE;','  BOOLEAN manual = FALSE;')
    return log_names(text,True)


def log_names(text,app=False):
    text=text.replace('L"RUN00"','L"RUN0000"')
    old="    name[3] = (CHAR16)('0' + slot / 10);\n    name[4] = (CHAR16)('0' + slot % 10);"
    new="    name[3] = (CHAR16)('0' + slot / 1000);\n    name[4] = (CHAR16)('0' + slot / 100 % 10);\n    name[5] = (CHAR16)('0' + slot / 10 % 10);\n    name[6] = (CHAR16)('0' + slot % 10);"
    text=replace_once(text,old,new)
    text=text.replace('slot < 100;', 'slot < 10000;')
    text=text.replace('Selected >= 100','Selected >= 10000').replace('Selected + 1 : 100)', 'Selected + 1 : 10000)')
    if app:
        text=text.replace('RunSlot = 100;', 'RunSlot = 10000;')
    else:
        text=text.replace('RUN%02u','RUN%04u').replace('one manual attempt per launch','one automatic attempt per launch')
    return text


def observed_zero_profile(capture_path, original_header):
    """Change only the two fixed initial selectors using hash-verified board evidence."""
    capture_path=capture_path.resolve()
    if not capture_path.is_relative_to(ROOT/'data'):
        raise RuntimeError('Startup evidence must remain in private project data.')
    capture=json.loads(capture_path.read_text(encoding='utf-8-sig'))
    if not capture.get('Success') or not capture.get('EfiHashVerified') or capture.get('LogRun')!='RUN0000' or capture.get('EfiSha256')!='7adcaa078172121a39861bf388596f161aec50ec336af57dd9f9821834cb77d8':
        raise RuntimeError('Expected the verified first automatic-boot capture.')
    folder=Path(capture['CaptureDirectory']).resolve()
    if not folder.is_relative_to(ROOT/'data/uefi-probe/captures'):
        raise RuntimeError('Boot-log evidence escapes private captures.')
    evidence={row['Name']:row for row in capture['Logs']}
    texts={}
    for name in ('GOP.TXT','UNLOCK.TXT'):
        path=folder/name
        if sha(path)!=evidence[name]['Sha256'] or path.stat().st_size!=evidence[name]['Bytes']:
            raise RuntimeError('Captured boot-log hash or length changed.')
        texts[name]=path.read_text(encoding='utf-8-sig')
    if 'CANCELLED_OR_REFUSED stage=unlock-preflight status=0x8000000000000006 touched=0' not in texts['GOP.TXT'] or 'AUTO_START' in texts['GOP.TXT']:
        raise RuntimeError('Expected an untouched startup preflight refusal.')
    cold='cold state: chip=0xb76000a1 plm=0xffffff8f gfw=0x8b8f/0x3ff/0x10 WPR2_HI=0 SS0=0 SS1=0'
    if texts['UNLOCK.TXT'].splitlines().count(cold)!=1 or 'PATCH_PREFLIGHT status=0x8000000000000006 profile=1 pci=0x250310de subsystem=0x407b1458' not in texts['UNLOCK.TXT']:
        raise RuntimeError('Observed board/startup state differs from the reviewed zero-selector capture.')
    text=replace_once(original_header,'#define GU_INITIAL_SS0 0x70520074U','#define GU_INITIAL_SS0 0x00000000U')
    text=replace_once(text,'#define GU_INITIAL_SS1 0x00000005U','#define GU_INITIAL_SS1 0x00000000U')
    return text,{'capture_sha256':sha(capture_path),'gop_sha256':evidence['GOP.TXT']['Sha256'],
                 'unlock_sha256':evidence['UNLOCK.TXT']['Sha256'],'fixed_initial_ss0':'00000000','fixed_initial_ss1':'00000000'}


ORIGINAL_SELECTOR_CHECK = '''      ss0 != GU_INITIAL_SS0 ||
      (GU_PROFILE_BUILD ? ss1 != GU_INITIAL_SS1 : (ss1 != 2 && ss1 != 3)) ||'''
PAIRED_SELECTOR_CHECK = '      !GuCapturedStartupSelectorsMatch(ss0, ss1) ||'


def verified_capture_logs(path, run, image_hash):
    path=path.resolve()
    if not path.is_relative_to(ROOT/'data'):
        raise RuntimeError('Paired startup evidence escapes private data.')
    capture=json.loads(path.read_text(encoding='utf-8-sig'))
    if not capture.get('Success') or not capture.get('EfiHashVerified') or capture.get('LogRun')!=run or capture.get('EfiSha256')!=image_hash:
        raise RuntimeError('Unexpected paired startup capture identity.')
    folder=Path(capture['CaptureDirectory']).resolve()
    if not folder.is_relative_to(ROOT/'data/uefi-probe/captures'):
        raise RuntimeError('Paired startup logs escape private captures.')
    rows={x['Name']:x for x in capture['Logs']};texts={}
    for name in ('GOP.TXT','UNLOCK.TXT'):
        file=folder/name
        if sha(file)!=rows[name]['Sha256'] or file.stat().st_size!=rows[name]['Bytes']:
            raise RuntimeError('Paired startup log hash/length differs.')
        texts[name]=file.read_text(encoding='utf-8-sig')
    return texts


def observed_paired_profile(zero_header, repeat_path):
    image='f837ed1db52138125fe530460a546f9f9fdda122d76b13ef862a7036524516ca'
    repeat=verified_capture_logs(repeat_path,'RUN0003',image)
    good_path=ROOT/'data/uefi-probe/internal-startup/automatic-corrected-boot-capture.private.json'
    good=verified_capture_logs(good_path,'RUN0001',image)
    prefix='cold state: chip=0xb76000a1 plm=0xffffff8f gfw=0x8b8f/0x3ff/0x10 WPR2_HI=0 '
    if prefix+'SS0=0x70520074 SS1=0x5' not in repeat['UNLOCK.TXT'] or 'CANCELLED_OR_REFUSED stage=unlock-preflight status=0x8000000000000006 touched=0' not in repeat['GOP.TXT']:
        raise RuntimeError('Expected the untouched RUN0003 refusal on the original startup pair.')
    transaction='PATCH_TRANSACTION result=0 containment=0 started=1 quiesced=1 fault=0 retained=0 maps=0 FLR=1 safe=1'
    if prefix+'SS0=0 SS1=0' not in good['UNLOCK.TXT'] or transaction not in good['UNLOCK.TXT'] or 'AUTO_START: all preflight checks passed' not in good['GOP.TXT']:
        raise RuntimeError('Missing successful zero-pair automatic execution evidence.')
    manual_path=ROOT/'data/uefi-probe/captures/20261025-UNLOCK-RUN01/UNLOCK.TXT'
    manual=manual_path.read_text(encoding='utf-8-sig')
    success=json.loads((ROOT/'reports/verification/rtx3060-windows-unlock-success-20261025.json').read_text(encoding='utf-8'))
    if success['transaction_result']!=0 or not success['compute_improvement_observed_in_windows'] or prefix+'SS0=0x70520074 SS1=0x5' not in manual or transaction not in manual:
        raise RuntimeError('Missing successful original-pair manual execution evidence.')
    header=zero_header+'''\n/* Two complete, physically observed pre-unlock pairs; never mix their components. */
static inline int GuCapturedStartupSelectorsMatch(unsigned int ss0, unsigned int ss1) {
  return (ss0 == 0U && ss1 == 0U) || (ss0 == 0x70520074U && ss1 == 5U);
}
'''
    return header,{'allowed_initial_pairs':[['00000000','00000000'],['70520074','00000005']],
                   'repeat_capture_sha256':sha(repeat_path),'successful_zero_capture_sha256':sha(good_path),
                   'successful_original_pair_log_sha256':sha(manual_path)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--partition-guid',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--preview',action='store_true')
    parser.add_argument('--observed-zero-startup',type=Path,
                        default=ROOT/'data/uefi-probe/internal-startup/automatic-first-boot-capture.private.json',
                        help='Verified private first-boot capture (default: saved RUN0000 evidence); fixes both initial selectors to zero without bypassing checks')
    parser.add_argument('--observed-repeat-startup',type=Path,
                        default=ROOT/'data/uefi-probe/internal-startup/paired-startup-repeat-evidence.private.json',
                        help='Immutable RUN0003 evidence; requires successful execution evidence for each of two exact startup pairs')
    args=parser.parse_args()
    guid=str(uuid.UUID(args.partition_guid.strip('{}')))
    output=args.output.resolve()
    if not output.is_relative_to(ROOT/'data') or output.exists():
        raise RuntimeError('Choose a new project-local ignored output directory.')
    original=ROOT/'runtimes/rtx30-uefi-probe-source'
    tested=ROOT/'data/uefi-probe/windows3060-single-child-20261025-v3'
    llvm=ROOT/'runtimes/uefi-probe-tools/llvm-20.1.8/bin'
    bun=ROOT/'runtimes/uefi-probe-tools/bun-1.4.4/bun-windows-x64/bun.exe'
    env=dict(os.environ);env['LLVM_BIN']=str(llvm)
    env['PATH']=os.pathsep.join((str(llvm),str(bun.parent),str(Path(sys.executable).parent),env['PATH']))
    if execute(['git','rev-parse','HEAD'],original,env).strip()!=PIN or execute(['git','status','--porcelain'],original,env).strip():
        raise RuntimeError('Reviewed upstream checkout changed.')
    if sha(tested/'manual-unlock-candidate/EFI/BOOT/BOOTX64.EFI')!='61fa2b71d1332d4d6180610175955d3cad015420c41f393b7abea717507d09e1':
        raise RuntimeError('Hardware-tested candidate changed.')
    for row in (tested/'manual-unlock-candidate/SHA256SUMS.txt').read_text().splitlines():
        digest,name=row.split('  ',1)
        if sha(tested/'manual-unlock-candidate'/name)!=digest: raise RuntimeError('Tested package changed.')
    success=json.loads((ROOT/'reports/verification/rtx3060-windows-unlock-success-20261025.json').read_text())
    if not success['compute_improvement_observed_in_windows'] or success['transaction_result']!=0:
        raise RuntimeError('Expected the recorded successful physical manual trial.')
    output.mkdir(parents=True); source=output/'source';source.mkdir()
    archive=output/'upstream-source.zip'
    execute(['git','archive','--format=zip','--output='+str(archive),PIN],original,env)
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            if not (source/item.filename).resolve().is_relative_to(source): raise RuntimeError('Invalid archive path.')
        z.extractall(source)
    shutil.copy2(tested/'full-single.c',source/'src/gop/full.c')
    shutil.copy2(tested/'single-driver-policy.h',source/'src/gop/single-driver-policy.h')
    app=source/'src/gop/app.c';app.write_text(automatic_app(app.read_text()),encoding='utf-8')
    io=source/'src/unlock/app_io.c';io.write_text(log_names(io.read_text()),encoding='utf-8')
    (source/'src/unlock/boot_source.h').write_text(boot_header(guid))
    header=ROOT/'data/uefi-probe/windows3060-unlock-20261025-v2/private-board-profile.h'
    startup_evidence=None
    if args.observed_zero_startup:
        profile,startup_evidence=observed_zero_profile(args.observed_zero_startup,header.read_text(encoding='utf-8'))
        profile,paired_evidence=observed_paired_profile(profile,args.observed_repeat_startup)
        startup_evidence.update(paired_evidence)
        header=output/'paired-startup-board-profile.private.h'
        header.write_text(profile,encoding='utf-8')
        unlock_app=source/'src/unlock/app.c'
        unlock_app.write_text(replace_once(unlock_app.read_text(encoding='utf-8'),ORIGINAL_SELECTOR_CHECK,PAIRED_SELECTOR_CHECK),encoding='utf-8')
    # Adapt only the CPU-host fixture to an internal disk path and four-digit logs.
    fixture=source/'src/gop/test_io.c'; text=fixture.read_text()
    text=text.replace('USB_DEVICE_PATH usb;','HARDDRIVE_DEVICE_PATH usb;')
    text=replace_once(text,"name[2] == 'N' && !name[5]","name[2] == 'N' && !name[7]")
    text=replace_once(text,"UINTN slot = (name[3] - '0') * 10 + name[4] - '0';",
                      "UINTN slot = (name[3]-'0')*1000+(name[4]-'0')*100+(name[5]-'0')*10+name[6]-'0';")
    text=replace_once(text,'static EFI_STATUS EFIAPI StartupHandle(',
        'static EFI_PARTITION_INFO_PROTOCOL InternalPart;\n'
        'static EFI_GUID InternalPartGuid = EFI_PARTITION_INFO_PROTOCOL_GUID;\n'
        'static EFI_STATUS EFIAPI StartupHandle(')
    needle='  else if (!memcmp(guid, &PciGuid, sizeof(*guid)))'
    text=replace_once(text,needle,
        '  else if (!memcmp(guid, &InternalPartGuid, sizeof(*guid)))\n'
        '    *out = &InternalPart;\n'+needle)
    text=text.replace('UsbPath.usb.Header.Type = MESSAGING_DEVICE_PATH;','UsbPath.usb.Header.Type = MEDIA_DEVICE_PATH;')
    text=text.replace('UsbPath.usb.Header.SubType = MSG_USB_DP;','UsbPath.usb.Header.SubType = MEDIA_HARDDRIVE_DP;')
    text=text.replace('sizeof(USB_DEVICE_PATH);','sizeof(HARDDRIVE_DEVICE_PATH);')
    text=replace_once(text,'  UsbPath.end.Type = END_DEVICE_PATH_TYPE;',
        '  UsbPath.usb.SignatureType = SIGNATURE_TYPE_GUID;\n'
        '  memcpy(UsbPath.usb.Signature,&GuInternalPartition,sizeof(GuInternalPartition));\n'
        '  memset(&InternalPart,0,sizeof(InternalPart));\n'
        '  InternalPart.Revision=EFI_PARTITION_INFO_PROTOCOL_REVISION;\n'
        '  InternalPart.Type=PARTITION_TYPE_GPT;\n'
        '  InternalPart.Info.Gpt.PartitionTypeGUID=(EFI_GUID)EFI_PART_TYPE_EFI_SYSTEM_PART_GUID;\n'
        '  InternalPart.Info.Gpt.UniquePartitionGUID=GuInternalPartition;\n'
        '  UsbPath.end.Type = END_DEVICE_PATH_TYPE;')
    fixture.write_text(text)
    logs=output/'checks';logs.mkdir()
    if startup_evidence:
        # Compile the actual unchanged ColdCheck body, not a reimplementation of its conditions.
        app_text=(source/'src/unlock/app.c').read_text(encoding='utf-8')
        begin=app_text.index('static EFI_STATUS ColdCheck(VOID) {')
        end=app_text.index('\nstatic EFI_STATUS PromCheck(VOID)',begin)
        (logs/'cold-check-under-test.h').write_text(app_text[begin:end]+'\n',encoding='utf-8')
        cold_flags=['-std=c11','-O1','-Wall','-Wextra','-Werror','-Wno-unused-function',
                    '-I',str(source),'-I',str(logs),'-I','deps/edk2/MdePkg/Include',
                    '-I','deps/edk2/MdePkg/Include/X64','-include',str(header)]
        execute([llvm/'clang.exe',*cold_flags,ROOT/'scripts/uefi_cold_profile_test.c',
                 'src/unlock/vendor/gfw_eval.c','-o',logs/'cold-test.exe'],source,env,logs/'cold-build.log')
        print(execute([logs/'cold-test.exe'],source,env,logs/'cold.log').strip(),flush=True)
    test='''/* GPL-2.0-only. Real automatic entry and gate, mocked device/OS actions. */
#define SSD_FLOW_MAIN UnusedSsdTests
#include "test_ssd_flow.c"
int main(void) {
  SetupFlow(); InputStatus=EFI_NOT_READY;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77,&System);
  assert(Runs==1 && Starts==1 && Polls==60 && strstr(SavedLog,"AUTO_START") && !strstr(SavedLog,"MANUAL_U"));
  SetupFlow(); Key=0x1b;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77,&System);
  assert(!Runs && !Starts && Polls==1);
  SetupFlow(); System.ConIn=NULL;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77,&System);
  assert(!Runs && !Starts);
  SetupFlow(); InputStatus=EFI_DEVICE_ERROR;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77,&System);
  assert(!Runs && !Starts && Polls==1);
  SetupFlow(); PreflightStatus=EFI_NOT_READY;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77,&System);
  assert(!Runs && !Starts && !Polls);
  SetupFlow(); SecureEnabled=1;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77,&System);
  assert(!Runs && !Starts && !Polls);
  SetupFlow(); FailFlush=TRUE;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77,&System);
  assert(!Runs && !Starts && !Polls);
  SetupFlow(); RunStatus=EFI_DEVICE_ERROR;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77,&System);
  assert(Runs==1 && !Starts);
  SetupFlow(); OccupiedRuns=101; InputStatus=EFI_NOT_READY;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77,&System);
  assert(Runs==1 && Starts==1 && RunSlot==101);
  SetupFlow(); assert(GuBootSourceAllowed(&System,LoadedImage.DeviceHandle));
  InternalPart.Info.Gpt.UniquePartitionGUID.Data1^=1;
  assert(!GuBootSourceAllowed(&System,LoadedImage.DeviceHandle));
  SetupFlow(); UsbPath.usb.Header.Type=MESSAGING_DEVICE_PATH; UsbPath.usb.Header.SubType=MSG_USB_DP;
  assert(!GuBootSourceAllowed(&System,LoadedImage.DeviceHandle));
  SetupFlow(); UsbPath.usb.Signature[0]^=1;
  assert(!GuBootSourceAllowed(&System,LoadedImage.DeviceHandle));
  SetupFlow(); InternalPart.Info.Gpt.PartitionTypeGUID.Data1^=1;
  assert(!GuBootSourceAllowed(&System,LoadedImage.DeviceHandle));
  SetupFlow(); UsbPath.usb.Header.Length[0]=0;
  assert(!GuBootSourceAllowed(&System,LoadedImage.DeviceHandle));
  puts("PASS 14 automatic/internal-source scenarios; no physical hardware access");
  return 0;
}
'''
    (logs/'auto-test.c').write_text(test)
    flags=['-std=c11','-O1','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter',
           '-D_CRT_SECURE_NO_WARNINGS','-I','src/gop','-I','deps/edk2/MdePkg/Include',
           '-I','deps/edk2/MdePkg/Include/X64','-include',header]+['-D'+x for x in FULL_DEFINES]
    execute([llvm/'clang.exe',*flags,logs/'auto-test.c','src/unlock/format.c','-o',logs/'auto-test.exe'],source,env,logs/'auto-build.log')
    print(execute([logs/'auto-test.exe'],source,env,logs/'auto.log').strip(),flush=True)
    image,pe=build_efi(source,output/'build',llvm,env,FULL_SOURCES,FULL_DEFINES,header,bun)
    for name in ('src/unlock/vendor/unlock_610.c','src/unlock/port.c','src/gop/leaf.c','src/gop/reset.c'):
        if sha(source/name)!=sha(original/name): raise RuntimeError('A transaction/safety source changed: '+name)
    restored=replace_once((source/'src/unlock/app.c').read_text(encoding='utf-8'),PAIRED_SELECTOR_CHECK,ORIGINAL_SELECTOR_CHECK)
    if restored!=(original/'src/unlock/app.c').read_text(encoding='utf-8'):
        raise RuntimeError('Unlock app changed beyond the reviewed coupled-pair predicate.')
    if sha(source/'src/gop/full.c')!=sha(tested/'full-single.c'):
        raise RuntimeError('The hardware-tested display adaptation changed.')
    package=output/'package';package.mkdir()
    for file in (tested/'manual-unlock-candidate').iterdir():
        if file.name in ('EFI','SHA256SUMS.txt','START-HERE.md','BUILD-INFO.json'):continue
        if file.is_dir():shutil.copytree(file,package/file.name)
        else:shutil.copy2(file,package/file.name)
    boot=package/'EFI/LLMUnlock';boot.mkdir(parents=True)
    shutil.copy2(image,boot/'Auto3060.efi')
    correspondence=package/'AUTOMATIC-SOURCE';correspondence.mkdir()
    for name in ('src/gop/app.c','src/unlock/app.c','src/unlock/app_io.c','src/unlock/boot_source.h'):
        dst=correspondence/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/name,dst)
    shutil.copy2(header,correspondence/'board-profile.private.h')
    shutil.copy2(Path(__file__),correspondence/Path(__file__).name)
    shutil.copy2(ROOT/'reports/RTX3060-AUTOMATIC-INTERNAL-BOOT-20261025.md',package/'START-HERE.md')
    meta={'source_commit':PIN,'efi':pe,'internal_partition_guid':guid,'preview_only':args.preview,
          'automatic':True,'escape_cancel_seconds':6,'always_logs':True,'log_slots':10000,
          'firmware_transaction_unchanged':True,'hardware_tested_display_source_unchanged':True,
          'automatic_profile_changes':False,'source_volume_bound_to_exact_internal_esp':True,
          'host_auto_and_source_tests':14,'host_tests_passed':True,'physical_internal_boot_tested':False}
    if startup_evidence:
        meta.update(startup_profile_evidence=startup_evidence,host_actual_cold_check_tests=23,
                    coldcheck_only_initial_pair_predicate_changed=True,
                    startup_profile='exactly two observed complete startup pairs; mixed/unknown/unlocked pairs rejected')
    (output/'BUILD-INFO.private.json').write_text(json.dumps(meta,indent=2)+'\n')
    (package/'BUILD-INFO.private.json').write_text(json.dumps(meta,indent=2)+'\n')
    (package/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(package).as_posix()+'\n' for p in sorted(package.rglob('*')) if p.is_file()))
    print('Prepared automatic internal-ESP package; no installed boot files or partitions changed.',flush=True)


if __name__=='__main__':
    try:main()
    except (OSError,RuntimeError,ValueError,KeyError) as error:
        print('Automatic preparation stopped: '+str(error),file=sys.stderr);sys.exit(1)
