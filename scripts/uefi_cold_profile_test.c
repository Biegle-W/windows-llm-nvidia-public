/* GPL-2.0-only. Exercise the extracted, unchanged production ColdCheck on CPU memory. */
#include <Uefi.h>
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "src/probe/gpu_family.h"
#include "src/unlock/vendor/gfw_eval.h"

static struct { bool fault; } Gu;
static UINT32 Registers[0x1000000 / 4];
static UINT32 GuRead32(UINT32 offset) {
  assert(offset < sizeof(Registers) && !(offset & 3));
  return Registers[offset / 4];
}
#define GuLog(...) ((void)0)
#include "cold-check-under-test.h"

static void Setup(void) {
  memset(Registers, 0, sizeof(Registers));
  Gu.fault = false;
  Registers[0] = GU_BOARD_CHIP;
  Registers[GU_GFW_PLM_OFFSET / 4] = 0x8b8f;
  Registers[GU_GFW_BOOT_OFFSET / 4] = 0x3ff;
  Registers[GU_GFW_CPUCTL_OFFSET / 4] = 0x10;
  Registers[GU_FEAT_PLM_OFFSET / 4] = GU_INITIAL_PLM;
  Registers[GU_FEAT_SS0_OFFSET / 4] = GU_INITIAL_SS0;
  Registers[GU_FEAT_SS1_OFFSET / 4] = GU_INITIAL_SS1;
  Registers[0x1183a4 / 4] = GU_FB_MIB;
  const UINT32 offsets[] = GU_LAYOUT_OFFSETS, values[] = GU_LAYOUT_VALUES;
  for (size_t i = 0; i < sizeof(offsets) / sizeof(offsets[0]); i++)
    Registers[offsets[i] / 4] = values[i];
}
int main(void) {
  assert(GU_INITIAL_SS0 == 0 && GU_INITIAL_SS1 == 0);
  Setup(); assert(ColdCheck() == EFI_SUCCESS);
  Setup(); Registers[GU_FEAT_SS0_OFFSET / 4] = 0x70520074;
  Registers[GU_FEAT_SS1_OFFSET / 4] = 5; assert(ColdCheck() == EFI_SUCCESS);
  Setup(); Registers[GU_FEAT_SS0_OFFSET / 4] = 0x70520074; assert(EFI_ERROR(ColdCheck()));
  Setup(); Registers[GU_FEAT_SS1_OFFSET / 4] = 5; assert(EFI_ERROR(ColdCheck()));
  Setup(); Registers[GU_FEAT_SS0_OFFSET / 4] = 0x70520074;
  Registers[GU_FEAT_SS1_OFFSET / 4] = 5; Registers[0x1183a4 / 4]--; assert(EFI_ERROR(ColdCheck()));
  Setup(); Registers[GU_FEAT_SS0_OFFSET / 4] = 0x70520074;
  Registers[GU_FEAT_SS1_OFFSET / 4] = 5; Registers[GU_GFW_CPUCTL_OFFSET / 4] = 0; assert(EFI_ERROR(ColdCheck()));
  Setup(); Registers[GU_FEAT_SS0_OFFSET / 4] = 1; assert(EFI_ERROR(ColdCheck()));
  Setup(); Registers[GU_FEAT_SS1_OFFSET / 4] = 1; assert(EFI_ERROR(ColdCheck()));
  Setup(); Registers[GU_FEAT_SS0_OFFSET / 4] = 0x88888888;
  Registers[GU_FEAT_SS1_OFFSET / 4] = 8; assert(EFI_ERROR(ColdCheck()));
  Setup(); Gu.fault = true; assert(EFI_ERROR(ColdCheck()));
  Setup(); Registers[0] ^= 1; assert(EFI_ERROR(ColdCheck()));
  Setup(); Registers[GU_GFW_PLM_OFFSET / 4] = 0xffffffff; assert(EFI_ERROR(ColdCheck()));
  Setup(); Registers[GU_GFW_BOOT_OFFSET / 4] = 0; assert(EFI_ERROR(ColdCheck()));
  Setup(); Registers[GU_GFW_CPUCTL_OFFSET / 4] = 0; assert(EFI_ERROR(ColdCheck()));
  Setup(); Registers[0x1fa828 / 4] = 0x10; assert(EFI_ERROR(ColdCheck()));
  Setup(); Registers[GU_FEAT_PLM_OFFSET / 4] ^= 1; assert(EFI_ERROR(ColdCheck()));
  Setup(); Registers[0x1183a4 / 4]--; assert(EFI_ERROR(ColdCheck()));
  const UINT32 offsets[] = GU_LAYOUT_OFFSETS;
  for (size_t i = 0; i < sizeof(offsets) / sizeof(offsets[0]); i++) {
    Setup(); Registers[offsets[i] / 4] ^= 1; assert(EFI_ERROR(ColdCheck()));
  }
  puts("PASS 23 actual ColdCheck scenarios; no physical GPU access");
  return 0;
}
