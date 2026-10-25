# RTX 3060 Windows unlock preparation — October 25, 2026

The fixed-board **manual unlock candidate is built**, with all five pinned
firmware assets verified. It has not run on the GPU and is **not yet cleared
for an unlock boot**. The next USB boot captures the display ownership tree
without detaching drivers or unlocking. This is necessary because the first
[physical probe](RTX3060-READONLY-UEFI-PROBE.md) recorded GOP paths and modes,
but not the driver/child relationships used by the display-release code.

## Review findings

- The upstream revisions are unchanged as of this review: craftingmod
  `5c076dc4ee7fa369639669fa591ac74d8f6dfcd8`, predator0321 `ca3041b` and
  impacifist `e3f03cd`.
- The actual captured PROM passes craftingmod's CPU byte parser. FWSEC image
  offset/size are `0x434e0` / `0xe700`; IMEM/DMEM sizes are `0xdf00` / `0x800`.
  Engine mask `0x400`, ucode9, three signatures and version mask7 are supported.
  Captured fuse raw3 selects FWSEC version2/signature offset `0x300`; Booter
  fuse raw1 selects version1. Both signatures are available.
- DMEM is already a multiple of256 bytes. The Linux
  [DMA-rounding fix](https://github.com/Zagitta/gpu-unlock/pull/35) is not needed
  for this captured descriptor. No transaction backport or guard removal was made.
- The pinned GSP ELF/boot descriptor and captured memory registers pass the
  upstream layout calculation: FRTS=`0x2ffe00000`, WPR end=`0x2fff00000`.
  The actual FWSEC command interface accepts that address in a **CPU-owned
  image copy**. No firmware was executed. Truncated-ROM and absent-signature
  negative cases are rejected.
- An administrator **query only** confirmed Secure Boot=false, system-volume
  FullyDecrypted, BitLocker ProtectionStatus=Off and encryption0%. No encryption
  or firmware settings were changed, and no recovery key was read.
- The framework's display plan requires a particular two-child GOP/EDID tree
  and six driver roles. The first probe cannot establish that match. The
  ownership capture is required before deploying the unlock candidate.

## Selector policy and scope

The candidate retains the unmodified upstream full-selector transaction:
SS0=`88888888`, SS1=`8`. It embeds the observed cold SS0=`70520074`, SS1=`5`,
Gigabyte `2503 / 1458:407b`, GA106 chip, PROM hash, revision and memory registers
through a private generated header. Initial-state and post-FLR comparisons remain
enabled. The source profile's approval/compatibility flags remain false.

The [desktop2504 Windows example](https://github.com/predator0321/rtx3060-ga106-uefi-experiment/tree/ca3041b77eb933c594bfd637bb6c71107bef94d2)
preserved SS1=2. That value is not copied to this board. A
[Linux3060 report](https://github.com/Zagitta/gpu-unlock/issues/78) demonstrates
SS1=8 on2504, but cannot validate Windows display recovery on this2503. The
candidate is an experimental full-selector build, not a claim that its policy
is hardware validated. Review the ownership capture before deciding the first
transaction. Do not suppress a failed check to proceed.

## Build and validation

The maintained builder is `scripts/prepare_windows_3060_unlock.py`, using the
same pinned source and LLVM20.1.8/Bun1.4.4 as the first probe. It checks the
unchanged source revision and the original evidence, and refuses changed or
different-board captures and existing output directories.

The unlock image has **no production, SSD, automatic-profile or runtime-profile
build flags**. It has a compiled fixed profile, always logs, and requires a
physical U key after preflight. Esc or30 seconds cancels. Removing DEBUG.ON
cannot enable automatic execution. It cannot silently accept a new PROM or
replace its own profile. The existing Secure Boot, PCI/BAR, cold-state, PROM,
asset, ownership, DMA, one-FLR, recovery and selector checks remain enabled.
Same-boot Windows handoff occurs only after successful transaction, restoration,
display and log checks. Uncertain recovery halts instead of continuing boot.

Host checks passed for ownership/cycle/leaf/full-plan failure paths, selector
readback, Windows handoff, visual recovery, DMA/port, PCI configuration, profile
families and report parsing. An additional eight-flow test exercises the actual
app's manual-only U/Esc/timeout/missing-input path, preflight failure, Secure
Boot refusal, log failure and transaction failure. GPU and Windows actions in
those tests are mocked; they do not establish hardware compatibility.

Both images pass AMD64 EFI subsystem10/entrypoint/relocation/NX/ASLR checks with
no imports, IAT or delay imports. The ownership image links `GcReadTree` and
does not link the transaction, DMA, GPU-write or Windows-handoff functions.

| Image | Bytes | SHA256 |
|---|---:|---|
| Manual unlock candidate, local only | 93,696 | `ee2df12dfe01f5352e9c4b8760aa2603de794a4c25d37b8c6957ae50b42e8fea` |
| Read-only ownership capture, next USB boot | 12,288 | `58f4d6beb444d423a8509dd4d1cdbb7a2e10a425e51ae2e65f2cceaa011342b8` |

Local build: ignored `data/uefi-probe/windows3060-unlock-20261025-v2/`.
It contains `manual-unlock-candidate/` and `ownership-probe/`, full private build
metadata, logs, source archives, corresponding build helpers, generated header
and licenses. Binary packages, board-specific evidence and firmware are not
published to GitHub.

For a future rebuild with the existing private evidence and extracted assets:

```powershell
python scripts/prepare_windows_3060_unlock.py `
  --capture data/uefi-probe/captures/20261025-RUN00/diagnostic-profile.json `
  --output data/uefi-probe/windows3060-unlock-rebuild-01
```

The builder never formats/selects a USB, mounts an ESP, writes a boot variable,
installs a driver or executes GPU firmware. The source remains unchanged;
build modes are selected explicitly instead of using upstream's automatic default.

## Next physical step: ownership capture

The Kingston FAT32 USB is staged with the **read-only ownership image** as
`EFI/BOOT/BOOTX64.EFI`. Original files and RUN00 are backed up privately and
preserved; only the fallback EFI is replaced. `OWNERSHIP-PROBE/` retains the
source/package and instructions. The marker `RTX-UNLOCK/` collects new logs.
The actual unlock candidate and firmware assets remain local, off the USB.

1. Save work, fully shut down with Shift + Shut down, then start and press F8.
2. Choose the Kingston **UEFI USB** entry in the one-time boot menu.
3. Expect a read-only ownership-tree diagnostic, **no U confirmation** and no
   driver detachment. It saves `RTX-UNLOCK/RUN00/GOP.TXT` and returns to firmware
   after20 seconds. If a previous ownership run exists, it selects the next number.
4. Boot the existing Windows Boot Manager normally and leave the USB connected.
5. Review GOP.TXT before replacing the USB fallback with an unlock image.

This capture may disable the firmware watchdog for its own run, writes only new
USB logs and does not write boot variables. Do not select or install a different
unlock EFI, change boot order or run a second experiment in that firmware session.
If the capture stalls, power off, remove the USB and boot Windows normally.

## Stock compute baseline

A short ordinary CUDA13.3/cuBLAS13.6 baseline was saved before any unlock:
4096-square all-ones GEMM, FP32 accumulation,2 seconds warm-up and30 timed samples.

| Mode | Median time | TFLOPS |
|---|---:|---:|
| FP32 pedantic | 15.902496 ms | 8.643 |
| FP16 Tensor / FP32 accumulation | 5.121536 ms | 26.835 |
| BF16 Tensor / FP32 accumulation | 5.130560 ms | 26.788 |

This uses the pinned upstream `src/gop/compute-benchmark.cu`, built with local
nvcc13.3 forsm86. Its arithmetic check examines the first/last output elements;
it is not a broad numerical accuracy test. This is one short desktop sample,
not a sustained or isolated benchmark and not an LLM decode measurement.
The identical executable is retained privately for a same-settings comparison.
No unlocked performance or quantized-inference improvement is claimed.

[Sanitized preparation evidence](verification/rtx3060-windows-unlock-preparation-20261025.json).
