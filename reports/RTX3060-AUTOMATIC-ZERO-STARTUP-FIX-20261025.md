# Automatic RTX 3060 zero-startup profile correction — October 25, 2026

**The corrected automatic EFI is installed and hash-verified. Its physical boot
test is pending.** The observed Windows compute state remains stock until a
successful subsequent unlock; no runtime unlock or reboot was initiated here.

The [original automatic boot](RTX3060-AUTOMATIC-FIRST-BOOT-20261025.md) ran from
the internal partition but refused at the exact initial-selector check. Its
observed SS0/SS1 pair was zero/zero, whereas the earlier manual profile captured
`70520074/00000005`.

## Correction and checks retained

`prepare_uefi_3060_automatic.py` now defaults to the private, hash-verified RUN0000
evidence and generates a separate automatic profile with exactly two changes:
`GU_INITIAL_SS0=0` and `GU_INITIAL_SS1=0`. The original manual profile and package
remain intact. The build refuses missing, modified or mismatched evidence.

The actual ColdCheck function and firmware transaction source are unchanged.
It still requires the exact initial pair and rejects mixed, prior nonzero and
already-unlocked values. Board/chip/PROM checks, firmware state, memory layout,
single-child display checks, one-FLR containment/recovery, internal partition
GUID restriction, six-second Esc cancellation and logging remain in place.
No SSD experiment, automatic profile refresh or generic bypass was enabled.
Later PROM/layout checks were not reached by the failed physical run; only the
next boot can establish that the complete preflight passes on this startup path.

Validation completed:

- 10 provenance tests reject tampered logs, wrong board/run/EFI, touched or
  nonzero captures, an altered original header and paths outside private captures.
- 19 CPU-memory scenarios exercise the actual extracted ColdCheck with the
  corrected header, including firmware, chip and memory-layout rejection cases.
- 14 automatic-entry/internal-source scenarios and EFI PE checks pass.
- 8 updater path checks accept owned files and reject traversal, Windows EFI
  targets and run-log overwrites.

## Installed payload

New EFI SHA256:
`f837ed1db52138125fe530460a546f9f9fdda122d76b13ef862a7036524516ca`.
All 28 manifest files were verified on the same exact-GUID dedicated FAT32 ESP.
The updater verifies disk identity, partition extent/size, current EFI hash and
corrected build contract before writing. It backs up the previous package,
stages the replacement EFI, checks every installed hash, preserves RUN0000 logs,
and confirms partition inventory and firmware entries are unchanged. U: is removed.

The first update attempt rolled back because BCDEdit renders a mounted volume
as U: instead of HarddiskVolumeN. The corrected updater compares before/after
readings under the same mount state, then checks the unmounted view too. The
second attempt completed with a separate retained backup. No partition resize,
formatting, boot-entry change, driver change or GPU operation was performed.

Private backup/state/build paths are under `data/uefi-probe/internal-startup/`.
The previous EFI is also retained as `EFI/LLMUnlock/Auto3060.previous.efi` on the
dedicated ESP. Raw profiles, logs and boot identifiers remain ignored by Git.

Next: restart without USB, inspect the next internal run (normally RUN0001), and
repeat the same compute check. Do not mark automatic unlock successful before
that evidence. If startup stalls, power off and use F8 -> Windows Boot Manager.
Do not execute another unlock in the current Windows session.

[Sanitized update evidence](verification/rtx3060-automatic-zero-startup-fix-20261025.json).
