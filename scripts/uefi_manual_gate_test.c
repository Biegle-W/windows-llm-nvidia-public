/* SPDX-License-Identifier: GPL-2.0-only */
/* Exercise the real upstream entry/approval path; all GPU and OS actions are mocks. */
#define SSD_FLOW_MAIN UnusedUpstreamSsdChecks
#include "test_ssd_flow.c"

int main(void) {
  SetupFlow();
  DeviceIdentity = 0x250310de;
  DeviceSubsystem = 0x407b1458;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77, &System);
  assert(Plans == 1 && Runs == 1 && Starts == 1 && Polls == 1);
  assert(strstr(SavedLog, "MANUAL_U") && !strstr(SavedLog, "AUTO_START"));
  SetupFlow();
  DebugMarker = FALSE;
  Key = 0x1b;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77, &System);
  assert(!Runs && !Starts && Polls == 1);
  SetupFlow();
  InputStatus = EFI_NOT_READY;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77, &System);
  assert(!Runs && !Starts && Polls == 300);
  SetupFlow();
  System.ConIn = NULL;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77, &System);
  assert(!Runs && !Starts && !Polls);
  SetupFlow();
  PreflightStatus = EFI_NOT_READY;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77, &System);
  assert(!Runs && !Starts && !Polls);
  SetupFlow();
  SecureEnabled = 1;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77, &System);
  assert(!Plans && !Runs && !Starts && !Polls);
  SetupFlow();
  FailFlush = TRUE;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77, &System);
  assert(!Runs && !Starts && !Polls);
  SetupFlow();
  RunStatus = EFI_DEVICE_ERROR;
  if (!setjmp(ExitFlow)) efi_main((EFI_HANDLE)(UINTN)77, &System);
  assert(Runs == 1 && !Starts);
  puts("PASS 8 manual-only flows: U, Esc, timeout, missing input, preflight failure, Secure Boot, log failure, transaction failure");
  return 0;
}
