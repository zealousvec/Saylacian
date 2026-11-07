# Independent local Python runner

The runner executes Python directly; it does not require Codex or Hermes.
Production app models remain separate from private research adapters.

From a checkout with app/development dependencies installed:

```powershell
$lab = Join-Path $env:LOCALAPPDATA 'SaylacianResearchLab'
$py = '.\.venv\Scripts\python.exe'
& $py tools/local_translation_lab.py --workspace $lab init
.\tools\run_saylacian_lab.ps1 -Action doctor
.\tools\run_saylacian_lab.ps1 -Action scripts -RunId overnight-scripts -Target 10000
# After Ctrl+C or an interrupted process, retain the original target and run ID:
.\tools\run_saylacian_lab.ps1 -Action scripts -RunId overnight-scripts -Target 10000 -Resume
.\tools\run_saylacian_lab.ps1 -Action report -RunId overnight-scripts
```

SQLite case commits and `progress.jsonl` live under `$lab\runs\<RunId>`;
reports contain committed counts, failures and recovery state. Invariant passes
measure converter robustness, not linguistic correctness. The command never
defaults to a million-case run. Use a new run ID for a new seed or target.

## Training and evaluation

Training requires an existing, approved private source registry, prepared
train/validation data and the pinned M2M100 base model. `init` does not download
data or grant training rights. The separate CUDA runtime can be installed using
`tools/setup_translation_training.cmd`; this downloads dependencies only when
explicitly invoked. The app environment is not changed by that setup.

```powershell
# Start a NEW private shared-adapter experiment; this is real GPU training.
.\tools\run_saylacian_lab.ps1 -Action train -RunId my-shared-adapter
# Resume with the SAME epochs, learning rate, source fingerprints and run ID:
.\tools\run_saylacian_lab.ps1 -Action train -RunId my-shared-adapter -Resume
# Evaluate the finished frozen adapter (may take time on the full held-out set):
.\tools\run_saylacian_lab.ps1 -Action evaluate -RunId my-shared-adapter
```

Do not resume completed training just to repeat an epoch. Trainer checkpoints
include adapter/optimizer/scheduler/RNG state. Resource and rights guards fail
closed. Model files, data, checkpoints and predictions belong outside Git.
No command automatically promotes or redistributes a candidate.

For a short checkpoint plumbing demonstration without a large model:

```powershell
& $py tools/local_translation_lab.py --workspace $lab train-smoke --run-id checkpoint-demo --steps 40 --stop-after 10
& $py tools/local_translation_lab.py --workspace $lab train-smoke --run-id checkpoint-demo --steps 40 --resume
```

This smoke is synthetic linear regression, not translation-model training.

## One fixed app-versus-adapter comparison

Use a private JSON array with `route`, `source` and `reference` fields; supported
routes are en-so, so-en, fr-so and so-fr. Freeze the sample before evaluation.
This compares identical examples, isolates models in separate processes, saves
each prediction durably, and writes `report.json` / `report.md` with BLEU,
chrF++, paired uncertainty, per-route time and process/GPU memory. Re-running
the same command resumes predictions only if sample and model identity match.
Timing includes first-use route initialization; it is not a steady-state
hardware-normalized performance comparison. Working-set peaks are per process;
an interrupted/resumed invocation's resource peaks cover that invocation only.

```powershell
& $py tools/compare_offline_models.py `
  --sample "$lab\reports\quality-corrected-20261107\sample.json" `
  --output "$lab\reports\my-fixed-model-comparison" --workspace $lab `
  --python-app $py `
  --python-training "$lab\runtime\training-venv\Scripts\python.exe" `
  --experiments m2m100-en-fr-so-shared-lora-recovery-20261105 m2m100-shared-lora-continuation-1e-05-20261106
```

The example refers to the owner's existing private artifacts; they are not
included in Git. Other users must provide their own rights-cleared sample and
completed adapters. The comparison blocks network connections during inference.
It does not establish general accuracy, Google Translate parity or deployment
compatibility. Evaluate the actual installed app route before promotion.

The corrected multilingual evaluator treats rows without language metadata as
canonical English→Somali, reverses them only for Somali→English, and rejects
partial/mismatched metadata. Older reports made with the faulty direction helper
must not be used as release evidence. Eighteen focused regression tests cover the
multilingual module; full model inference is optional and runs separately.
