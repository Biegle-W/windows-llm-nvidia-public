# RTX 3080 Ti dedicated-USB refusal and v4 retry — October 25, 2026

The original RTX3080Ti is installed again. Its dedicated4GB USB booted the
previous manual image, but RUN00 refused at unlock preflight with EFI_NOT_READY
and touched0. Both initial selectors differed from the earlier successful Ti
boot. The manual U gate was not reached; no unlock transaction or FLR occurred.
The current Windows session is not unlocked. The earlier Ti RUN01 success and
its126.86/129.96TFLOPS measurements remain historical, not current-boot results.

Current same-executable compute: FP32 25.899118, FP16 69.966565 and BF16
69.997918TFLOPS. All three reference checks pass; tensor rates are stock-like
against the saved70.35/70.36TFLOPS baseline. GPU OK/error0, no NVIDIA Error/Critical
events found since this boot after compute. Driver610.88 and350W cap unchanged.

**Corrected v4 is staged on the4GB General USB Flash Disk / RTX3080TI (F:).**
All24 package files and both refusal capture files independently verify. The
previous image and colliding files are backed up; no formatting or boot-order
change occurred. EFI SHA256:
`4649c0ed12800ce5c8f6988f637bf5319809c4153d2f1249e0107abc7571f632`.

The original Ti board/ownership diagnostics are preserved unchanged. A derived
header binds only the exact new tuple from the untouched refusal and paired GOP
log. Only its expected initial pair changes. The actual ColdCheck and firmware
transaction remain unchanged, and live PROM/layout/GFW/PCI/driver metadata checks
remain enforced. Unknown, zero, original, mixed and already-unlocked states refuse.
Further boot-state variation is not established by these observations.

29 Python policy tests pass, including six new Ti refusal-evidence methods.
22 actual ColdCheck scenarios include rejection of the old pair and both mixed
pairs. Eight upstream host suites, eight manual-gate flows,31 display-rejoin,
22 simulated-unlock and26 driver-policy scenarios pass. Host tests are not proof
of a successful physical v4 transaction or display recovery.

Fresh administrator checks confirm Secure Boot off, C: FullyDecrypted/protection
Off, Windows-first boot and the removed3060 NVMe payload/entry. The3060 and3080
USBs, driver, power cap, model settings and12GB admission guards are unchanged.

Next fully shut down, F8 ->**4GB General USB / RTX3080TI**, wait for preflight,
then **U once only if it passes**. Esc/30sec cancels. Allow up to10 minutes for
Windows to start directly; do not repeat in the same firmware session. If Windows
never appears, fully power off, remove USB and boot Windows normally. Leave this
USB connected when reporting back. No automatic/internal Ti startup is installed.
[Curated verification](verification/rtx3080ti-dedicated-refusal-v4-20261025.json).
