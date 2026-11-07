# Alpha source completion — 2026-11-07

The independent Python runner and corrected M2M100 evaluator are now part of
the source tree. See [working PowerShell commands](../research/README.md).
Private source approvals, samples, datasets, checkpoints, weights and detailed
research results are not distributed with this repository.

## Verified source work

- Multilingual direction-handling module: 18 focused tests pass, including
  canonical English/Somali rows without metadata and invalid metadata rejection.
- Independent runner: a 1,000-case converter run was interrupted after 500
  committed cases and resumed to 1,000 unique passes, zero failures. Batch
  boundaries explain why `--stop-after 400` committed 500 cases. The full suite
  also tests abrupt child-process termination and recovery.
- Tiny synthetic training checkpoint resumed from 10 to 40 steps. This is
  checkpoint plumbing evidence, not translation-model improvement.
- PowerShell wrapper ran 64 bounded converter checks and printed the report.
- Fixed comparison executed the installed app routes and two saved adapters
  on identical private examples (160 directed tasks; 480 outputs). Independent
  rescoring matched all metrics and prediction hashes. Production models are
  retained: adapters lose on three routes, require substantially more memory,
  and are not verified portable-runtime replacements. French→Somali sample gains
  do not justify general promotion or distribution of private weights.
- Headless Edge passed nine website checks, including actual offline French
  inference, Old Nubian alternatives, mobile layout and clipboard-double checks.
- Source Kivy self-test exits 0 and reports script/font rendering, isolated
  session restore, UI controls and offline French inference. Metrics initialize
  before canvas rules; hidden self-tests omit physical pen/touch hooks only.
- Six installed source-app translation routes returned output with network
  connections blocked. Some Somali outputs are poor; this is not a quality pass.

## Windows binary disposition: NOT RELEASED

The existing portable recipe built a clean candidate from commit
`c8df7f7f662228c39036ea0c5a1e790b9d92b883`: 673 manifest-listed files;
71,036,354-byte ZIP; SHA-256
`0269f64bcdcc2cac50a3748b5dff3228af633513f4e3b6901253ed9c0761bd85`.
All manifest hashes, ZIP contents and bundled font hashes/cmaps verify.

The first candidate exposed a canvas startup failure. A display probe completed
its functional self-test but failed while restoring hidden-window pen hooks.
Source initialization and self-test input were corrected; Windows Application
Control then blocked the rebuilt EXE with WinError 4551. No policy was bypassed.
The rebuilt package therefore remains runtime-unverified. Source self-tests do
not substitute for packaged execution or a clean-machine test.

Binary redistribution evidence remains unresolved for VC runtime coverage,
Intel OpenMP, exact GLEW binary provenance and Material Design Icons provenance.
Existing notices and script/font attribution remain bundled; their presence
does not resolve those separate questions. Real external-app clipboard testing
requires the existing disposable-VM harness. No such VM was available.

No GitHub binary release is published until these execution and distribution
gates clear. The source PR can ship independently. No new translation-model
training, model promotion, private-data upload or security-policy change occurred.
