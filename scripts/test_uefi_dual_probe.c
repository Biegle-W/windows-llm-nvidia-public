#include "uefi_dual_probe.h"
#include <Protocol/LoadedImage.h>
#include <Protocol/DevicePath.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern EFI_STATUS EFIAPI efi_main(EFI_HANDLE, EFI_SYSTEM_TABLE *);
static EFI_PCI_IO_PROTOCOL Cards[4];
static UINT32 Ids[4], Subs[4];
static UINTN Buses[4], Count, Calls, FailChild;
static BOOLEAN ReadFailure, BadLocation, Secure, Usb, BadUsbPath;
static UINT32 Order[4];
static EFI_SYSTEM_TABLE System;
static EFI_BOOT_SERVICES Bs;
static EFI_RUNTIME_SERVICES Rs;
static EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL Console;
static EFI_LOADED_IMAGE_PROTOCOL Loaded;
static struct { USB_DEVICE_PATH usb; EFI_DEVICE_PATH_PROTOCOL end; } Path;
static EFI_STATUS EFIAPI Read(EFI_PCI_IO_PROTOCOL *p, EFI_PCI_IO_PROTOCOL_WIDTH w,
                              UINT32 off, UINTN n, VOID *out) {
  assert(w == EfiPciIoWidthUint32 && off == 0 && n == 64);
  if (ReadFailure) return EFI_DEVICE_ERROR;
  UINTN i = (UINTN)(p - Cards);
  assert(i < Count);
  memset(out, 0, 256);
  ((UINT32 *)out)[0] = Ids[i];
  ((UINT32 *)out)[2] = 0x030000a1;
  ((UINT32 *)out)[11] = Subs[i];
  return EFI_SUCCESS;
}
static EFI_STATUS EFIAPI Location(EFI_PCI_IO_PROTOCOL *p, UINTN *s, UINTN *b, UINTN *d, UINTN *f) {
  *s = 0; *b = BadLocation ? 256 : Buses[p - Cards]; *d = *f = 0;
  return EFI_SUCCESS;
}
static EFI_STATUS EFIAPI Handles(EFI_LOCATE_SEARCH_TYPE t, EFI_GUID *g, VOID *k,
                                 UINTN *n, EFI_HANDLE **out) {
  (void)g; assert(t == ByProtocol && !k);
  *n = Count;
  *out = calloc(Count ? Count : 1, sizeof(**out));
  for (UINTN i = 0; i < Count; i++) (*out)[i] = &Cards[i];
  return EFI_SUCCESS;
}
static EFI_STATUS EFIAPI Handle(EFI_HANDLE h, EFI_GUID *g, VOID **out) {
  EFI_GUID pci = EFI_PCI_IO_PROTOCOL_GUID, loaded = EFI_LOADED_IMAGE_PROTOCOL_GUID;
  EFI_GUID path = EFI_DEVICE_PATH_PROTOCOL_GUID;
  if (!memcmp(g, &loaded, sizeof(*g))) { *out = &Loaded; return EFI_SUCCESS; }
  if (!memcmp(g, &path, sizeof(*g))) {
    if (!Usb) return EFI_NOT_FOUND;
    *out = &Path; return EFI_SUCCESS;
  }
  assert(!memcmp(g, &pci, sizeof(*g)));
  *out = h; return EFI_SUCCESS;
}
static EFI_STATUS EFIAPI Free(VOID *p) { free(p); return EFI_SUCCESS; }
static EFI_STATUS EFIAPI Variable(CHAR16 *n, EFI_GUID *g, UINT32 *a, UINTN *s, VOID *v) {
  (void)n; (void)g; assert(!a && *s == 1); *(UINT8 *)v = Secure; return EFI_SUCCESS;
}
static EFI_STATUS EFIAPI Output(EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL *c, CHAR16 *s) {
  assert(c == &Console && s); return EFI_SUCCESS;
}
static EFI_STATUS EFIAPI Stall(UINTN us) { assert(us == 10000000); return EFI_SUCCESS; }
EFI_STATUS EFIAPI DualBoardMain(EFI_HANDLE i, EFI_SYSTEM_TABLE *t) {
  (void)i; assert(t == &System && Calls < 4 && Calls % 2 == 0);
  Order[Calls++] = DualSelectedIdentity;
  return Calls == FailChild ? EFI_DEVICE_ERROR : EFI_SUCCESS;
}
EFI_STATUS EFIAPI DualTreeMain(EFI_HANDLE i, EFI_SYSTEM_TABLE *t) {
  (void)i; assert(t == &System && Calls < 4 && Calls % 2 == 1);
  Order[Calls++] = DualSelectedIdentity;
  return Calls == FailChild ? EFI_DEVICE_ERROR : EFI_SUCCESS;
}
static VOID Reset(VOID) {
  memset(Cards, 0, sizeof(Cards)); memset(&Bs, 0, sizeof(Bs));
  memset(&System, 0, sizeof(System)); memset(&Rs, 0, sizeof(Rs));
  memset(&Console, 0, sizeof(Console)); memset(&Path, 0, sizeof(Path));
  Ids[0] = 0x220810deU; Ids[1] = 0x220610deU; Ids[2] = 0x250310deU;
  Subs[0] = DUAL_TI_SUBSYSTEM; Subs[1] = DUAL_3080_SUBSYSTEM; Subs[2] = 0;
  for (UINTN i = 0; i < 4; i++) {
    Cards[i].Pci.Read = Read; Cards[i].GetLocation = Location; Buses[i] = 1 + i * 4;
  }
  Count = 2; Calls = FailChild = 0; ReadFailure = BadLocation = Secure = BadUsbPath = FALSE;
  Usb = TRUE;
  Bs.LocateHandleBuffer = Handles; Bs.HandleProtocol = Handle; Bs.FreePool = Free;
  Bs.Stall = Stall; Rs.GetVariable = Variable; Console.OutputString = Output;
  System.BootServices = &Bs; System.RuntimeServices = &Rs; System.ConOut = &Console;
  Loaded.DeviceHandle = (EFI_HANDLE)(UINTN)99;
  Path.usb.Header.Type = MESSAGING_DEVICE_PATH; Path.usb.Header.SubType = MSG_USB_DP;
  Path.usb.Header.Length[0] = sizeof(USB_DEVICE_PATH);
  Path.end.Type = END_DEVICE_PATH_TYPE; Path.end.SubType = END_ENTIRE_DEVICE_PATH_SUBTYPE;
  Path.end.Length[0] = 4;
}
int main(void) {
  unsigned cases = 0;
  Reset(); assert(efi_main((EFI_HANDLE)1, &System) == EFI_SUCCESS && Calls == 4);
  assert(Order[0] == Ids[0] && Order[1] == Ids[0] && Order[2] == Ids[1] && Order[3] == Ids[1]);
  assert(DualSelectedIdentity == 0); cases++;
  Reset(); Ids[0] = 0x220610de; Ids[1] = 0x220810de;
  Subs[0] = DUAL_3080_SUBSYSTEM; Subs[1] = DUAL_TI_SUBSYSTEM;
  assert(efi_main((EFI_HANDLE)1, &System) == EFI_SUCCESS && Calls == 4); cases++;
  for (UINTN n = 0; n <= 3; n++) if (n != 2) {
    Reset(); Count = n; assert(EFI_ERROR(efi_main((EFI_HANDLE)1, &System)) && !Calls); cases++;
  }
  Reset(); Ids[1] = Ids[0]; Subs[1] = Subs[0];
  assert(EFI_ERROR(efi_main((EFI_HANDLE)1, &System)) && !Calls); cases++;
  Reset(); Subs[1] ^= 1; assert(EFI_ERROR(efi_main((EFI_HANDLE)1, &System)) && !Calls); cases++;
  Reset(); Buses[1] = Buses[0]; assert(EFI_ERROR(efi_main((EFI_HANDLE)1, &System)) && !Calls); cases++;
  Reset(); BadLocation = TRUE; assert(EFI_ERROR(efi_main((EFI_HANDLE)1, &System)) && !Calls); cases++;
  Reset(); ReadFailure = TRUE; assert(EFI_ERROR(efi_main((EFI_HANDLE)1, &System)) && !Calls); cases++;
  Reset(); Secure = TRUE; assert(EFI_ERROR(efi_main((EFI_HANDLE)1, &System)) && !Calls); cases++;
  Reset(); Usb = FALSE; assert(EFI_ERROR(efi_main((EFI_HANDLE)1, &System)) && !Calls); cases++;
  Reset(); Path.end.Length[0] = 0; assert(EFI_ERROR(efi_main((EFI_HANDLE)1, &System)) && !Calls); cases++;
  for (UINTN n = 1; n <= 4; n++) {
    Reset(); FailChild = n;
    assert(efi_main((EFI_HANDLE)1, &System) == EFI_DEVICE_ERROR && Calls == n);
    assert(DualSelectedIdentity == 0); cases++;
  }
  Reset(); assert(efi_main(NULL, NULL) == EFI_INVALID_PARAMETER); cases++;
  printf("PASS %u dual-probe controller scenarios; no GPU mutation services provided\n", cases);
  return 0;
}
