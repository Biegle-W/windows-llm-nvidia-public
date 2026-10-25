# Retired RTX 3060 NVMe startup launcher

The user requested removing the3060 firmware entry and all payload files from
the dedicated NVMe EFI partition on October25,2026, and using USB for future3060
unlocks. Removal and archive verification succeeded. The partition itself was
retained; no partition was resized or deleted.

The old root restore launcher is retained here as a disabled historical file.
Its old relative path is not a runnable installation workflow. Set-GpuBootMode
also refuses a removal-marked state. Do not recreate the3060 internal startup
without a new user request. The original manual USB package, diagnostic captures
and build sources remain in ignored private project storage.
