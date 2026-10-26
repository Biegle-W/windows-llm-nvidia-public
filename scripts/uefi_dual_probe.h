#pragma once
#include <Uefi.h>
#include <Protocol/PciIo.h>

/* Exact subsystem values are supplied by an ignored, capture-derived header. */
#if !defined(DUAL_TI_SUBSYSTEM) || !defined(DUAL_3080_SUBSYSTEM)
#error Build with the private capture-derived dual-board policy header.
#endif
extern UINT32 DualSelectedIdentity;
BOOLEAN DualMatches(const UINT32 *config);
EFI_STATUS DualInventory(EFI_SYSTEM_TABLE *table);
EFI_STATUS EFIAPI DualBoardMain(EFI_HANDLE image, EFI_SYSTEM_TABLE *table);
EFI_STATUS EFIAPI DualTreeMain(EFI_HANDLE image, EFI_SYSTEM_TABLE *table);
