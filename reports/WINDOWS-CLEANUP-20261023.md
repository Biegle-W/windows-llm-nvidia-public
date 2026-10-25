# Windows directory consolidation — October 23, 2026

The Windows installation now keeps its four downloaded inference GGUFs together
in the project-root `models/` directory. All project-managed models, active
runtimes, configuration, state, logs, evidence and archives are under one
`Local-LLM` folder on C:. No D: drive is required. Credentials and frontend-owned
application data remain in their existing locations; unrelated applications are
outside this cleanup.

| Model file in `models/` | Role | Bytes |
|---|---|---:|
| Ornith-1.5-35B-A3B-IQ2_S.gguf | Selected production profile, 32K, GPU + RAM | 11,486,963,360 |
| Qwen3.8-35B-A3B-IQ2_M.gguf | Empero experimental weights, outside active catalog | 12,558,245,760 |
| LFM2.5-24B-A2B-UD-IQ3_XXS.gguf | Separate 8K test profile | 8,959,328,480 |
| Qwen3.8-27B-UD-IQ3_XXS.gguf | Separate 8K test profile | 10,934,860,704 |

The files were renamed on the same volume from Downloads, without retaining
duplicate model copies there. Each relocated file was rehashed against its prior
verified SHA256 receipt; see the [relocation manifest](verification/windows-model-relocation-20261023.json).
Small Strata tokenizer/vocabulary and experimental metadata fixtures remain with
their archived source; they are not runnable inference weights.

## Maintained layout

```text
Local-LLM/
  README.md
  Start Local LLM.cmd
  config/                  active registry, test profiles, catalogs, disabled Strata marker
  scripts/                 maintained CUDA/client/network helpers
  models/                  all four inference GGUFs; ignored by Git
  runtimes/                selected llama.cpp b11630 CUDA + Python; ignored by Git
  data/                    credentials, caches and private state; ignored by Git
  logs/                    runtime logs; ignored by Git
  reports/                 current and dated historical evidence
  retired/20261023/        tracked Strata source/config/launcher archive
  archive/                 private backups and inactive runtimes; ignored by Git
```

`config/selected-profiles.json` and
`config/test-profiles-lfm-qwen-20261023.json` use `models/<filename>` paths resolved
against the project root, independent of the caller's current directory.
`scripts/build_configuration.py` regenerates the absolute runtime paths in
`config/models.ini`; run it again after moving the whole installation.
Registration preserves project-relative paths for files inside the project.

The only active runtime directories are `llama.cpp-b11630-cuda-13.4` and `python`.
Unused CUDA builds b11065/b11155, Vulkan builds b11680/b11706, ROCm 10.1.0 and
the disabled Strata checkout were moved into
`archive/retired-windows-20261023/runtimes/`. Retired setup/tuning/test helpers,
`Start Strata.cmd` and full Strata configuration snapshots are in
`retired/20261023/`. Restore them only after reviewing that directory's README.

## Validation and unchanged behavior

All four files retain their byte counts and SHA256 hashes. Registry resolution,
generated catalogs and maintained Python/PowerShell/JavaScript syntax were
checked. Models and runtime binaries remain excluded from Git. No inference or
performance benchmark was rerun for this relocation. Saved measurements retain
their original paths and dates as historical evidence.

Ornith's default, 32K context, mixed GPU/RAM fitting and admission limits are
unchanged. Candidate models remain outside the active catalog. The owned backend
remains stopped following the previously documented memory-admission refusal;
this cleanup did not stop unrelated apps or change memory limits. Saved client
model IDs, credentials, app data and network settings are unchanged. Linux files
and hardware policies are separate.
