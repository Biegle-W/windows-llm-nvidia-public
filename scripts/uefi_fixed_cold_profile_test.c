/* GPL-2.0-only. Test the unchanged fixed-board ColdCheck using CPU memory only. */
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
  memset(Registers,0,sizeof(Registers)); Gu.fault=false;
  Registers[0]=GU_BOARD_CHIP;
  Registers[GU_GFW_PLM_OFFSET/4]=0x8b8f;
  Registers[GU_GFW_BOOT_OFFSET/4]=0x3ff;
  Registers[GU_GFW_CPUCTL_OFFSET/4]=0x10;
  Registers[GU_FEAT_PLM_OFFSET/4]=GU_INITIAL_PLM;
  Registers[GU_FEAT_SS0_OFFSET/4]=GU_INITIAL_SS0;
  Registers[GU_FEAT_SS1_OFFSET/4]=GU_INITIAL_SS1;
  Registers[0x1183a4/4]=GU_FB_MIB;
  const UINT32 offsets[]=GU_LAYOUT_OFFSETS, values[]=GU_LAYOUT_VALUES;
  for(size_t i=0;i<sizeof(offsets)/sizeof(offsets[0]);i++) Registers[offsets[i]/4]=values[i];
}
int main(void) {
  unsigned cases=0;
  Setup(); assert(ColdCheck()==EFI_SUCCESS); cases++;
  const UINT32 offsets[]={0,GU_GFW_PLM_OFFSET,GU_GFW_BOOT_OFFSET,GU_GFW_CPUCTL_OFFSET,
    0x1fa828,GU_FEAT_PLM_OFFSET,GU_FEAT_SS0_OFFSET,GU_FEAT_SS1_OFFSET,0x1183a4};
  for(size_t i=0;i<sizeof(offsets)/sizeof(offsets[0]);i++) {
    Setup(); Registers[offsets[i]/4]^=((offsets[i]==0x1fa828 || offsets[i]==GU_GFW_CPUCTL_OFFSET)?0x10:1);
    assert(EFI_ERROR(ColdCheck())); cases++;
  }
  Setup(); Gu.fault=true; assert(EFI_ERROR(ColdCheck())); cases++;
  Setup(); Registers[GU_FEAT_SS0_OFFSET/4]=0x88888888;
  Registers[GU_FEAT_SS1_OFFSET/4]=8; assert(EFI_ERROR(ColdCheck())); cases++;
  Setup(); Registers[GU_FEAT_SS0_OFFSET/4]=0;
  Registers[GU_FEAT_SS1_OFFSET/4]=0; assert(EFI_ERROR(ColdCheck())); cases++;
  const UINT32 layout[]=GU_LAYOUT_OFFSETS;
  for(size_t i=0;i<sizeof(layout)/sizeof(layout[0]);i++) {
    Setup(); Registers[layout[i]/4]^=1; assert(EFI_ERROR(ColdCheck())); cases++;
  }
  printf("PASS %u actual fixed-board ColdCheck scenarios; no physical GPU access\n",cases);
  return 0;
}
