/* Read-only preparation for a two-board Windows unlock. No unlock code is linked. */
#include "uefi_dual_probe.h"
#include "boot_source.h"
#include <Protocol/LoadedImage.h>
#include <Guid/GlobalVariable.h>

UINT32 DualSelectedIdentity;
static CHAR16 *volatile Banner = L"\r\nRTX 3080 Ti + RTX 3080: READ-ONLY dual-card preparation\r\n";

BOOLEAN DualMatches(const UINT32 *config) {
  if (!config || (config[2] >> 24) != 3) return FALSE;
  return (config[0] == 0x220810deU && config[11] == DUAL_TI_SUBSYSTEM) ||
         (config[0] == 0x220610deU && config[11] == DUAL_3080_SUBSYSTEM);
}

/* Require exactly the captured pair, with distinct, valid addresses. Do not guess slots. */
EFI_STATUS DualInventory(EFI_SYSTEM_TABLE *table) {
  if (!table || !table->BootServices) return EFI_INVALID_PARAMETER;
  EFI_BOOT_SERVICES *bs = table->BootServices;
  EFI_GUID pciGuid = EFI_PCI_IO_PROTOCOL_GUID;
  EFI_HANDLE *handles = NULL;
  UINTN count = 0, nvidia = 0, seen = 0, previous[4] = {0};
  EFI_STATUS status = bs->LocateHandleBuffer(ByProtocol, &pciGuid, NULL, &count, &handles);
  if (EFI_ERROR(status)) return status;
  if (!handles || !count || count > 1024) status = EFI_UNSUPPORTED;
  for (UINTN i = 0; !EFI_ERROR(status) && i < count; i++) {
    EFI_PCI_IO_PROTOCOL *pci = NULL;
    UINT32 config[64];
    status = bs->HandleProtocol(handles[i], &pciGuid, (VOID **)&pci);
    if (EFI_ERROR(status)) break;
    if (!pci || !pci->Pci.Read || !pci->GetLocation) { status = EFI_UNSUPPORTED; break; }
    status = pci->Pci.Read(pci, EfiPciIoWidthUint32, 0, 64, config);
    if (EFI_ERROR(status)) break;
    if ((config[0] & 0xffffU) != 0x10deU || (config[2] >> 24) != 3) continue;
    nvidia++;
    if (!DualMatches(config)) { status = EFI_UNSUPPORTED; break; }
    UINTN bit = config[0] == 0x220810deU ? 1 : 2;
    if (seen & bit) { status = EFI_UNSUPPORTED; break; }
    UINTN location[4];
    status = pci->GetLocation(pci, &location[0], &location[1], &location[2], &location[3]);
    if (EFI_ERROR(status)) break;
    if (location[0] > 65535 || location[1] > 255 || location[2] > 31 || location[3] > 7 ||
        (seen && !memcmp(previous, location, sizeof(location)))) {
      status = EFI_UNSUPPORTED; break;
    }
    memcpy(previous, location, sizeof(location));
    seen |= bit;
  }
  if (handles && EFI_ERROR(bs->FreePool(handles))) return EFI_DEVICE_ERROR;
  return !EFI_ERROR(status) && (nvidia != 2 || seen != 3) ? EFI_UNSUPPORTED : status;
}

EFI_STATUS EFIAPI efi_main(EFI_HANDLE image, EFI_SYSTEM_TABLE *table) {
  DualSelectedIdentity = 0;
  if (!table || !table->BootServices || !table->RuntimeServices || !table->ConOut ||
      !table->ConOut->OutputString) return EFI_INVALID_PARAMETER;
  EFI_STATUS status = table->ConOut->OutputString(table->ConOut, Banner);
  if (EFI_ERROR(status)) return status;
  EFI_GUID loadedGuid = EFI_LOADED_IMAGE_PROTOCOL_GUID, globalGuid = EFI_GLOBAL_VARIABLE;
  EFI_LOADED_IMAGE_PROTOCOL *loaded = NULL;
  status = table->BootServices->HandleProtocol(image, &loadedGuid, (VOID **)&loaded);
  if (EFI_ERROR(status) || !loaded || !GuBootSourceAllowed(table, loaded->DeviceHandle))
    return EFI_UNSUPPORTED;
  UINT8 secure = 0xff;
  UINTN size = 1;
  status = table->RuntimeServices->GetVariable(L"SecureBoot", &globalGuid, NULL, &size, &secure);
  if (EFI_ERROR(status) || size != 1 || secure) return EFI_SECURITY_VIOLATION;
  status = DualInventory(table);
  if (EFI_ERROR(status)) {
    table->ConOut->OutputString(table->ConOut,
        L"Capture stopped: install BOTH captured cards. No GPU changes were made.\r\n");
    table->BootServices->Stall(10000000);
    return status;
  }
  const UINT32 targets[2] = {0x220810deU, 0x220610deU};
  for (UINTN i = 0; i < 2; i++) {
    DualSelectedIdentity = targets[i];
    status = DualBoardMain(image, table);
    if (!EFI_ERROR(status)) status = DualTreeMain(image, table);
    if (EFI_ERROR(status)) break;
  }
  DualSelectedIdentity = 0;
  if (!EFI_ERROR(status))
    table->ConOut->OutputString(table->ConOut,
        L"BOTH captures completed. No unlock, GPU reset or driver detach occurred.\r\n"
        L"Choose Windows Boot Manager, then collect this USB's capture files.\r\n");
  else
    table->ConOut->OutputString(table->ConOut,
        L"Capture incomplete. Preserve all logs for review. No unlock was attempted.\r\n");
  table->BootServices->Stall(10000000);
  return status;
}
