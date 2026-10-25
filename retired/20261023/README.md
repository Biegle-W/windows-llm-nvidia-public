# Retired Windows setup — October 23, 2026

These Strata launchers, setup/tuning/test helpers and configuration snapshots are
archived source, outside the maintained `scripts/` and `config/` directories.
Strata is disabled on the current RTX 3060 / 16 GB Windows build. This archive does
not change the separate Linux AMD installation.

Do not launch these files from this directory: their original relative paths and
runtime assumptions are historical. A deliberate restoration would require
reviewing the dated reports, restoring the original project layout and validating
hardware, model assets, resource guards and clients again.

The private installation also preserves inactive binaries and the complete Strata
checkout (including its Git history) under
`archive/retired-windows-20261023/runtimes/`. Archived virtual environments may
contain original absolute paths; restore their original location or rebuild them
before reuse. They are not portable executables from the archive directory.

All previous reports, failed trials and benchmark evidence remain under
`reports/`; no historical result was rerun or reassigned to the current hardware.
The small `config/strata.json` disabled marker remains in the maintained layout
because current network/client helpers read it.

The dated LFM/Qwen8K test-profile list is also archived under `config/` here. It is historical evidence, outside the active model catalog. The maintained test helper can accept that file explicitly to reproduce the dated trial.
