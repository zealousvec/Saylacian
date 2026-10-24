# Session handoff

## Latest milestone — route and pack status usability (2026-10-24)

User-facing route warnings no longer expose internal terms such as “synthetic candidate,” “multilingual fallback,” or “human review pending.” Somali output retains a clear accuracy caution; Somali/French pivot warns meaning may change. Added unit and website regressions plus live Kivy assertion for the status label. Full suite: 127 passed, 2 skipped, 197 subtests. Ruff, format (105 files), compileall, `pip check`, release scan, `git diff --check`, and isolated Kivy self-test pass. Local UI acceptance output: `Bonjour, comment allez-vous ?`.

Completed visible chart and Old Nubian picker copy checks; users can distinguish missing artwork from limited conversion, and the Latin-reading picker does not imply scholarly validation. Pack download/removal errors now avoid local-path leakage, preserve integrity/security failures and give recovery steps. Missing offline translation routes direct users to Packs; the live Kivy check confirms the error and cleared output. Unit and isolated Kivy checks pass; failure cases used stubs only. Final full suite: 129 passed, 2 skipped, 197 subtests; Ruff/format, compileall, `pip check`, release scan and diff check pass. Short-input accuracy remains BLOCKED until a licensed, independently labelled natural short-phrase set or owner-approved review is available. DBMNT-derived expansion, Somali specialist quality review, screen-reader run, compact pixel capture, external-app clipboard and hosted workflow have their existing exact blockers in `docs/IMPLEMENTATION_PROGRESS.md`. Preserve owner changes to `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md`; no push.

## Resume point

Read the owner's `SAYLACIAN_MASTER_DEVELOPMENT_DIRECTIVE.md`, `docs/IMPLEMENTATION_PROGRESS.md`, and this file first. Keep the approved black-and-white Kivy interface, prioritize verified functionality, and preserve unrelated user edits. Do not use mouse/keyboard control. Do not push, publish, tag, or release.

Repository: the current checkout of `zealousvec/Saylacian`
Branch: `main`
Public `origin/main`: `c4f2f87270c22a05e772816ce98e57a99b871b18`
Public CI: run `40087020450` passed on that commit.
Recent local milestones include model-pack path containment, Old Nubian mark readability and short-text language detection. Public `main` remains at `c4f2f87270c22a05e772816ce98e57a99b871b18`; no push has occurred.
Preserve the pre-existing user edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md`; do not stage or rewrite them. Latest verified milestones improve Old Nubian mark readability and short-text Kivy routing. Expanded Tatoeba labels are noisy, so 0.80 remains unchanged and unvalidated. WiLI-2018 has no native phrase-length test rows; Lingua 2.2.0 adds a 170 MB Windows wheel. Next ACTIVE: find a suitable independently labelled, license-cleared short-text benchmark.

## Current milestone — memory recovery and rendering blocker (2026-10-24)

The translation worker catches `MemoryError` and shows an actionable shorter-passage/close-apps recovery message. Live Kivy worker injection displayed the expected status. App acceptance verifies missing-pack recovery, stale-output clearing, and fixture size/offline labels. Token-boundary tests cover standard models, Somali marker overhead, and synthetic EN→SO; over-limit input is rejected before inference.

The manual-only pack workflow and verifier were implemented. The full local suite is 104 passed / 148 subtests; Ruff, formatting, compileall, `pip check`, release-safety, live Kivy acceptance and YAML parsing passed. The actual French pack (174,530,568 bytes) and Somali pack (314,460,609 bytes) were downloaded into a temporary isolated store from pinned manifests, size/hash verified by `ModelPackManager`, then inferred in both directions with socket connections blocked. No weights were put in the repository. This verifies operation, not Somali linguistic quality. No hosted workflow run was triggered.

The compact SDL2 screenshot task is BLOCKED: `Window.screenshot` generated an all-black 450×800 px frame for a 360×640 dp viewport. Widget geometry at 200% font scale remains verified, but pixel review is not. Exact resolution: run through a validated isolated virtual display or known-good OpenGL/SDL screenshot path and capture the compact viewport. Keep this in BLOCKED, not READY.

The previous milestone at `2db5bef` improved fixed-height layout at 200% font scale. Live label geometry passed for Home, Packs, Saved, Alphabet/Osmanya and Old Nubian at 360×640 dp and 900×700 dp. Osmanya's missing chart image now routes to its Unicode alphabet grid.

Clean clone of `2db5bef` launched all six screens with socket networking denied, app/Kivy/pack data isolated, and both pack manifests listed; no downloads. The pinned existing environment was reused; this was not a fresh dependency install.

### Current queues

- ACTIVE: no unblocked task remains in the current queue; do not invent filler work. Reconcile against the roadmap on the next session.
- BLOCKED: DBMNT reuse needs written rights and qualified review (owner approval before outreach); Somali translation needs owner-approved consent-based fluent-speaker review; screen-reader claims need a manual Narrator/NVDA run; compact pixel review needs a functioning isolated capture environment; hosted model-pack workflow needs owner-approved push followed by manual dispatch.
- READY: none currently queued. Do not copy blocked tasks here. Reevaluate the roadmap when the session resumes.

## Earlier session milestone — enlarged text and reference recovery (2026-10-24)

At 200% Kivy font scale, live label geometry checks found clipping in Packs, Saved, Alphabet and Old Nubian. Updated fixed text heights and made pack rows follow their wrapped text. The missing Osmanya JPG lookup now falls back to the real Unicode alphabet grid; missing Borama/Kaddare images receive a readable status. A separate live Kivy measurement run passed for Home, Packs, Saved, Alphabet/Osmanya and Old Nubian at compact 360×640 dp and wide 900×700 dp. This is programmatic widget geometry evidence, not a claim of pixel-perfect compact screenshot review.

`main.py --self-test` passed at `KIVY_METRICS_FONTSCALE=2.0`, including offline output `Bonjour, comment allez-vous ?`. Full suite: 97 passed / 148 subtests. Ruff check passes; formatting was applied to `main.py`; compileall passed. Screenshot: `%TEMP%\saylacian-large-ui-evidence\old-nubian-reading-studio0002.png`.

## Earlier implementation milestone

Completed the visible UI and GitHub wording review, corrected stale pre-publication documentation, and added a KivyMD 2.0.0 migration plan. No UI redesign or GitHub settings change was made.

Resolved all 30 repository Ruff findings. Reviewed auto-fixes; corrected `U+` private-use data parsing to preserve hexadecimal semantics, and verified test assertions were not weakened. Precomputed Old Nubian reverse tokens and Somali forward tokens to avoid sorting mapping keys for each input character.

Expanded Old Nubian reading conservatively: keep 34 source-backed lowercase readings; derive uppercase handling mechanically from Unicode case pairs with no new linguistic claim; preserve unknown letters/marks/punctuation; report unreviewed letters and warn when Coptic marks may not render beside Latin. Added font cmap and case regression coverage plus a live paired-panel Kivy acceptance case. Source and reader docs record limits.

Fixed Kivy minimum-size initialization warning by setting width/height in graphics config before creating Window. KivyMD 1.2.0 deprecation and internal `padding_x` deprecation warning remain; no migration was attempted.

Hardened the real Windows clipboard test: disposable VM opt-in required, any nonempty clipboard refused, no `Clear` or restore operation, evidence goes to temp. PowerShell syntax passes. The external-consumer test was not run because no isolated VM is configured; everyday clipboard was untouched.

Live screenshot: `%TEMP%\Saylacian-goal-final\old-nubian-reading0001.png`; acceptance JSON reports pass. Full local suite: `88 passed, 148 subtests`. Ruff check/format, compileall, `pip check`, release-safety scan, PowerShell parse, and `git diff --check` passed.

## Prior session work

Implemented concise route labels and mode-specific picker choices. Removed a stale call to deleted `_choice_note`, which otherwise broke conversion. Added safe Borama/Kaddare copy menu actions named **Copy text**, **Copy image**, and **Copy Latin** on Windows; generic routes show only **Copy text**. The text action uses the existing versioned Saylacian Text package. Private-use text is not auto-detected; users can select Borama/Kaddare explicitly or paste the tagged package. Unknown/unlabelled input and invalid packages clear stale output. Tagged packages import, select the correct font and reconvert.

Updated pack/conversion wording and documentation for clipboard limits, chart mappings, and Unicode proposal status. Added the directive's task board, handoff, script interoperability note, Old Nubian source ledger/reader plan, Nubian research register, translation evaluation plan, update architecture, and UI copy register. A follow-up made the detection picker say **Detect** with a mode-accurate note. Added a direct regression for the RTF PUA glyph encoding, and removed unused imports; full-repository Ruff findings decreased from 35 to 30. Updated contributor and security guidance to match the public experimental-alpha status and avoid promising an unverified private reporting channel. Corrected stale roadmap entries for public Windows CI and the current Ruff count.

Live Kivy evidence: `%TEMP%\Saylacian-Autonomous-20261024-final`. `result.json` reports pass; screenshots cover Borama, Kaddare and packaged meaning output. No mouse or keyboard automation was used. KivyMD logs a deprecation notice for installed version 1.2.0; no framework upgrade was attempted. The real Windows clipboard test was not run: its read-only preflight found non-text clipboard formats, so the script would refuse before changing clipboard contents.

## Next three tasks

1. Do not run the hosted workflow until the owner approves pushing this source-only change; after approval, dispatch it manually and inspect the logs.
2. Use a validated isolated SDL/OpenGL viewport to resume compact pixel acceptance; the last 360×640 capture was black.
3. Continue only with an independent roadmap task that is READY; preserve the exact blockers and do not invent work to stay busy.

## Verification for latest milestone

- `pytest -q`: `88 passed, 148 subtests passed`.
- Live Kivy acceptance: pass; Old Nubian paired-reading screenshot is at `%TEMP%\Saylacian-goal-final\old-nubian-reading0001.png`.
- `ruff check .`: all checks passed; `ruff format --check .`: 98 files already formatted.
- `compileall`, `pip check`, release-safety scan, PowerShell parser and `git diff --check`: passed.
- Physical Windows clipboard test: intentionally deferred; no isolated VM. The script refuses populated clipboard and never clears/restores data.

Files changed in latest milestone: `app/acceptance.py`, `app/main.kv`, `cloud/oci/service.py`, `docs/CLIPBOARD_TESTING.md`, `docs/GITHUB_RELEASE_CHECKLIST.md`, `docs/IMPLEMENTATION_PROGRESS.md`, `docs/KIVYMD_MIGRATION.md`, `docs/OLD_NUBIAN_READER_PLAN.md`, `docs/OLD_NUBIAN_SOURCE_LEDGER.md`, `docs/SESSION_HANDOFF.md`, `docs/SOURCE_RELEASE_READINESS.md`, `docs/UI_COPY_REGISTER.md`, `main.py`, `saylacian/core/history.py`, `saylacian/core/translation.py`, `saylacian/core/transliteration.py`, `saylacian/website/templates/index.html`, tests for core/history/model packs/translation/website/chart-font coverage, and Ruff-cleaned tools. The two pre-existing owner edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` remain separate.

## Files changed during preceding, already committed session

`CONTRIBUTING.md`; `SECURITY.md`; `app/acceptance.py`; `app/main.kv`; `docs/DEVELOPMENT_ROADMAP.md`; `docs/IMPLEMENTATION_PROGRESS.md`; `docs/NUBIAN_RESEARCH_REGISTER.md`; `docs/OLD_NUBIAN_READER_PLAN.md`; `docs/OLD_NUBIAN_SOURCE_LEDGER.md`; `docs/SAYLACIAN_TEXT_FORMAT.md`; `docs/SCRIPT_FEASIBILITY.md`; `docs/SCRIPT_RESEARCH.md`; `docs/SESSION_HANDOFF.md`; `docs/SOMALI_SCRIPT_INTEROPERABILITY.md`; `docs/SUPPORT_MATRIX.md`; `docs/TRANSLATION_EVALUATION_PLAN.md`; `docs/UI_COPY_REGISTER.md`; `docs/UPDATE_ARCHITECTURE.md`; `main.py`; `saylacian/core/interchange.py`; `saylacian/core/model_packs.py`; `saylacian/core/presentation.py`; `saylacian/core/transliteration.py`; `tests/test_clipboard_interchange.py`; `tests/test_core.py`; `tests/test_historical_chart_scripts.py`; `tests/test_presentation.py`.

The pre-existing `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` edits remain separate and must not be included in the commit.

## Local work and approvals

All implementation/documentation commits listed above are local only. The pre-existing changes in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` remain uncommitted and untouched. Public `main` still points to `c4f2f87270c22a05e772816ce98e57a99b871b18`; no push occurred. Explicit approval remains required before any push or public release action.

## Phase 2 development update — Old Nubian Reading Studio

Implemented a dedicated Reading Studio within the existing Kivy app. On the Old Nubian route, **Read** opens the existing black-and-white screen family with an editable Coptic-derived passage, line-preserving limited Latin reading, warnings, searchable 34-entry table, selectable glyph details (code point, Unicode name, cited convention and “not independently reviewed” confidence), and insert-letter action. Users can copy either side. **Export record** writes a versioned JSON file beneath the app's user-data directory; **Import record** reads a user-selected clipboard payload, validates its schema/checksum/source/convention/warnings, and recomputes the Latin reading. The record contains the original and computed reading plus reference metadata. The checksum detects accidental corruption; it does not authenticate records. The live test used a mocked clipboard fixture and left the system clipboard alone.

Added `saylacian/core/old_nubian_reader.py` and `tests/test_old_nubian_reader.py`; updated `main.py`, `app/main.kv`, `app/acceptance.py`, `README.md`, `docs/OLD_NUBIAN_READER_PLAN.md`, `docs/THIRD_PARTY_NOTICES.md`, this handoff and the progress board. Read-through used the master directive, current board/handoff, mapping source ledger, reader plan and Nubian research register. Resumed branch/status verified: `main`, seven commits ahead of `origin/main`, plus only the two owner edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` as uncommitted modifications before this milestone. Those two files were left unchanged and excluded from the planned commit.

Research found the DBMNT transliteration table (p. 1) as the current linked mapping reference; its data-reuse licence remains unconfirmed. The openly accessible Smagina / Alonso de la Fuente *Old Nubian Language* book page declares CC BY-NC-SA 4.0. Its example text, transliteration and lexicon were not copied. The new UI is limited character reading, not meaning translation or a scholarly edition. No specialist review, manuscript text collection, word lexicon, OCR, or meaning translation was added.

Verification: focused reader/core tests `24 passed, 66 subtests`; full suite `92 passed, 148 subtests`; live Kivy `main.py --self-test` returned pass including studio search/letter detail/copy/import and existing script/translation paths; `ruff check .`, `ruff format --check .` (100 files), `compileall`, `pip check`, release-safety and `git diff --check` passed. The final populated studio screenshot was captured and inspected at `%TEMP%\Saylacian-phase2-reader-acceptance\old-nubian-reading-studio0001.png`; delaying navigation until after the frame capture resolved earlier black captures. KivyMD 1.2.0 deprecation and `padding_x` warnings remain. No system clipboard interaction or push occurred.

Next tasks: (1) confirm DBMNT data-reuse terms and record the decision; (2) seek qualified Old Nubian review before extending mappings or adding texts, while identifying legally reusable sample passages; (3) continue the held-out Somali evaluation and investigate measured model errors. The Phase 2 feature is committed locally as `603c79e90530fe4a855eff2203d09e4e6bbec2f9`; after the documentation checkpoint, local `main` is nine commits ahead. Public `origin/main` remains `c4f2f87270c22a05e772816ce98e57a99b871b18`, and nothing was pushed.

## Permanent mission initialization and Somali benchmark checkpoint

Created the dedicated Saylacian section in the owner-specified Obsidian vault after confirming the section did not already exist. Added 12 linked notes across dashboard, architecture, Old Nubian and Somali research, testing, backlog, licensing, session index and reusable lessons. Only the Saylacian root and its new files were accessed/written; unrelated notes were not read. All vault wiki-links resolve within that section.

Confirmed `origin/main` live with `git ls-remote`: still `c4f2f87270c22a05e772816ce98e57a99b871b18`; local main was nine commits ahead before this task. Re-ran the pre-change test baseline: `92 passed, 148 subtests`.

Added a caller-selected `--output` option and atomic JSON save helper to `tools/benchmark_somali_quality.py` so a repeat benchmark can avoid overwriting the ignored report. Added output-save tests and a reproduction entry in `docs/SOMALI_TRANSLATION_QUALITY.md`. Ran the full 150-pair current EN↔SO baseline offline, setting `LOCALAPPDATA` to a fresh temporary directory and results to `%TEMP%\Saylacian-somali-eval-20261024-152639\baseline-results.json`. Dataset SHA-256 `be58b2d350badb7e03b73906471453311a8843534e4a2a572a772c60c394c7f7`; EN→SO BLEU/chrF++ `7.057/28.996`, SO→EN `6.300/24.680`, exactly matching the existing report. Synthetic candidate selected 143/150; length-guard fallback 7/150. These are automatic comparative scores, not human review. The run's raw report remains in temp; default ignored output and ordinary app-data checkpoint were not touched.

Validation after the benchmark tooling change: `94 passed, 148 subtests`; `ruff check .`; `ruff format --check .` (101 files); `compileall`; `pip check`; release-safety scan and `git diff --check` pass. One release-scan finding was a local profile path recorded in this handoff; it was removed, and the scan now passes. The 12-note vault section has no broken wiki-links or local profile paths. Focused local commits: `3d59e05` (atomic caller-selected Somali benchmark output, tests, reproduction doc), `d4804d4` (DBMNT reuse-rights finding in three docs), and `41090b9` (progress/handoff checkpoint). Local `main` is 12 commits ahead; remote `origin/main` remains `c4f2f87270c22a05e772816ce98e57a99b871b18`. Preserve `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` unstaged; these were pre-existing owner edits. No push or publication.

## Autonomous queues and usability milestone (2026-10-24)

The workflow now maintains separate `ACTIVE`, `BLOCKED` and `READY` queues in `docs/IMPLEMENTATION_PROGRESS.md` and the Obsidian Feature Backlog. Every blocked item names the exact permission, rights or reviewer action needed. The permanent mission note instructs the next session to continue with the highest-impact independent READY task rather than stop at blockers.

Completed the offline pack-download cancellation UI. The Packs screen shows Cancel only during a download, disables repeat cancellation, passes an event to the existing installer, and explains that cancellation did not install a partial pack. The installer cleans staging. Live Kivy `main.py --self-test` checked the actual button state and request handling without mouse/keyboard input, network download or system clipboard access. A streamed cancellation regression cancels after receiving a chunk and checks there is no active pack or leftover staging directory. Saved-history atomic clear is now the next ACTIVE reliability task.

Full tests: `96 passed, 148 subtests`. Ruff and formatting pass for the touched code, `compileall`, `pip check`, and `git diff --check` pass. KivyMD 1.2.0 deprecation warnings remain. Keep the pre-existing owner changes in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` untouched/unstaged. No push.

## Keyboard usability milestone and next queue (2026-10-24)

Added Ctrl+Shift+M to switch mode, Ctrl+P to open packs, Ctrl+K to open target selection, Ctrl+Shift+K to open source selection, Up/Down and Enter for filtered route/pack choices, Ctrl+L to return to the editor, and Esc to go back or cancel an active pack download. `RUN.md` documents these keys. Live Kivy acceptance verified a mode change, pack selection with download invocation stubbed, changed route, editor focus, download cancellation request and return. The first run found an SDL key-name API mismatch; using `Keyboard.keycodes` fixed it and the rerun passed. This provides useful keyboard access but is not a full screen-reader/accessibility audit.

Saved-history `save` and `clear` now share a same-directory temporary JSON write plus atomic replace. Failure injection verifies the old history bytes survive failed replace and no temp file remains. Local commit `66581de`.

Latest full tests: `96 passed, 148 subtests`; Ruff and formatting (101 files), compileall, `pip check`, `git diff --check` and live Kivy `main.py --self-test` pass. The UI result JSON confirms keyboard picker navigation, download cancellation, Old Nubian reader actions and local English→French. No physical keyboard/mouse input or system clipboard was used. Next ACTIVE: reproduce startup from a clean checkout using isolated `APPDATA`/pack storage and a network-denied, time-bounded run. Then continue the READY focus/accessibility audit. BLOCKED: (1) DBMNT reuse remains unclear and no qualified Old Nubian reviewer; obtain written permission and qualified review, with owner approval before outreach. (2) Somali quality validation needs owner-approved, consent-based fluent review on a suitable sample. Preserve the pre-existing `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` edits; no push.

The clean-checkout test at `274d566` cloned the committed source to a new `%TEMP%` directory, isolated `APPDATA`, `LOCALAPPDATA`, Kivy home and pack storage, replaced socket connects with a failure, and ran the actual Kivy app for two seconds. It started all six screens, confirmed the app-data paths stayed under the temporary state folder, and left the clone clean. It reused the project's existing pinned interpreter; a fresh dependency installation remains untested. Current follow-up adds keyboard pack selection and download activation (the acceptance stubs the downloader), plus Esc cancellation. Verify, update the queue and commit this follow-up before repeating the clean startup test on the new HEAD.

Repeated the clean-clone startup probe on current HEAD `55b3736`. The actual Kivy app started all six screens with networking denied. APPDATA, LOCALAPPDATA, Kivy home and model-pack storage pointed inside a fresh temporary state folder; the cloned checkout remained clean. This verifies source startup only and reused the pinned project `.venv`; runtime dependencies still need a fresh isolated install. ACTIVE is now that disposable pinned-runtime install and launch. Full test suite remains `96 passed, 148 subtests`; Ruff, formatting, compilation, pip check and release-safety pass. Preserve pre-existing `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md`; no push.

## Fresh runtime installation complete; continue keyboard usability (2026-10-24)

Installed every package from `requirements-runtime-lock.txt` into a new disposable Python 3.12 venv under `%TEMP%`; no system Python was changed and no model packs were downloaded. `pip check` passed. Used that new interpreter to launch the clean checkout at source commit `55b3736` for two seconds with network connects forced to fail, all six screens present, and APPDATA/LOCALAPPDATA/Kivy/pack storage redirected to a temporary state folder. Startup passed and the checkout stayed clean. The venv and checkout are retained in `%TEMP%` as test evidence.

The next ACTIVE task is keyboard operation of the existing installed-pack removal confirmation. The pack list can be traversed by key, but Enter on an installed pack currently prompts for pointer use. Implement selection between KEEP/REMOVE with a safe default, test only through a removal stub, and never delete a real pack during acceptance. Later READY work: remaining Old Nubian/history keyboard flow and measured startup/picker performance. BLOCKED rights and fluent Somali review remain unchanged; use their exact resolution actions in the queue and continue independent work. Full suite remains `96 passed, 148 subtests`; Ruff, format, compileall, pip check, release-safety and live Kivy pass. Preserve the pre-existing two owner doc edits; no push.

## Keyboard pack removal confirmation complete (2026-10-24)

Installed-pack rows now open their existing confirmation on Enter. KEEP is selected by default; Right/Tab toggles to REMOVE; Enter activates the chosen action; Esc dismisses and keeps the pack. Live Kivy acceptance used an installed-pack fixture and a stubbed remover to ensure the explicit REMOVE path was invoked without deleting model data. Full suite remains `96 passed, 148 subtests`; Ruff, format, `compileall`, `pip check`, release scan and live UI test pass. Next ACTIVE: test and improve keyboard operation for history and Old Nubian reader. Do not claim full accessibility conformance.
## Keyboard usability milestone: pack removal and Old Nubian reading (2026-10-24)

Installed-pack removal now works from the keyboard through the existing confirmation: Enter opens it; KEEP is the default; Right/Tab selects REMOVE; Enter confirms; Esc keeps. Live Kivy acceptance uses an installed-pack fixture and stubbed remover, so no model pack was deleted. Old Nubian Reading Studio now accepts Enter to recompute the character-level reading and Escape to return; acceptance verified `ⲁ\nⲃ` produces `a\nb`. This is limited keyboard access, not a screen-reader or full accessibility claim.

Verification: full suite `96 passed, 148 subtests`; live `main.py --self-test` passed with local English-to-French output `Bonjour, comment allez-vous ?`; Ruff check and format passed; compileall, `pip check`, release-safety scan and `git diff --check` passed. KivyMD 1.2.0 deprecation warnings remain. No clipboard interaction, physical input, network model download or real pack removal.

Queue update: ACTIVE is remaining keyboard/focus audit on history and reader. BLOCKED remains Old Nubian data reuse pending written rights and qualified review (owner approval before outreach), and Somali quality pending owner-approved consent-based fluent-speaker review. READY: isolated startup/picker performance measurement, then contrast/screen-reader affordance inspection with appropriate test setup. Continue only with evidence-backed useful work.

## Keyboard navigation for history (2026-10-24)

Saved-history screen now supports Up/Down selection and Enter restore. The selected row has a visible `›` cursor. Live Kivy acceptance used two mocked history entries and a stub restore handler; it verified selection and dispatch without writing history. Full suite: `96 passed, 148 subtests`; Ruff check/format, compileall, `pip check`, release-safety and `git diff --check` pass. Next ACTIVE task is measured startup/picker responsiveness; remaining contrast/screen-reader checks require suitable tooling. Blockers and owner edits unchanged.

## Isolated responsiveness baseline (2026-10-24)

Three subprocess runs measured import plus Kivy `build()` at 1.32–1.46 s (median 1.39 s) and confirmed all six screens; this does not include main-loop first frame. Twenty-five language-picker filter rebuilds had 10.7 ms median with occasional 49–99 ms outliers, likely coupled to widget/render initialization; repeat before attributing cause. No code optimization made because measurements do not show a stable bottleneck. Raw data: `%TEMP%\saylacian_perf_baseline_20261024.json`. Full tests 96/148; Ruff and format (101 files), compileall, `pip check`, release scan, live UI and diff checks pass. Next ACTIVE: inspect contrast ratios from source color pairs; screen-reader claims still need an appropriate assistive-technology setup.


## Contrast and KivyMD API audit (2026-10-24)

Explicit app color pairs were computed in linearized sRGB: input/card 16.44:1; action/card 13.50:1; card icon/card 11.31:1; pack caption/black 9.40:1; white/black 21:1. All listed pairs pass WCAG AA normal text contrast. This does not cover theme-derived focus/disabled states or assistive technology.

Reviewed active KivyMD usage against official 2.0 component API comparisons. Buttons (`MDFlatButton`, `MDFillRoundFlatIconButton`), dialogs (`title`/`text`/`buttons`) and text fields (`mode="rectangle"` and inline hints) all require structural porting. `MDIconButton` remains, but needs state/style testing; labels/cards/theme need visual comparison. KivyMD's `padding_x` warning is internal; project search found no direct use. Updated `docs/KIVYMD_MIGRATION.md` with component inventory, acceptance gates and official docs links. Kept lock unchanged.

Screen-reader acceptance is BLOCKED until a manual Narrator/NVDA session can be run. Resolution: exercise the keyboard flows and record actual labels, focus and announcement behavior; no conformance claims until then. Next ACTIVE: inspect theme-derived contrast states programmatically. READY: responsive layout acceptance. Full suite `96 passed, 148 subtests`; Ruff/format, compileall, `pip check`, release safety, live Kivy and diff checks pass.


## Translator hint contrast correction (2026-10-24)

Rendered-state review found the input/output placeholders were Kivy gray (#787878) on #F2F2F2 cards, only 3.94:1. Set just those two `hint_text_color` values to #595959 for 6.25:1. Live acceptance asserts both widget values; actual post-fix screenshot: `%TEMP%\Saylacian-theme-state-capture-20261024\disabled-after-fix0001.png`. This is the only source UI visual adjustment; approved palette remains intact. Full tests/format/Ruff and live Kivy passed before final doc edits; rerun after changes.

ACTIVE: verify compact/wide/short-landscape breakpoints programmatically. BLOCKED: screen-reader behavior requires manual Windows Narrator/NVDA keyboard session; exact action is to exercise flows and record actual speech/focus behavior. DBMNT and Somali blockers unchanged.


## Responsive breakpoint check (2026-10-24)

Live Kivy harness verified `wide_layout` policy for 320×700 dp compact, 800×700 dp wide, and 500×500 dp short-landscape inputs, then restored the real window size. This checks policy branches; not physical resize or device-level layout. Full suite 96 passed/148 subtests; live acceptance, Ruff/format, compileall, `pip check`, release scan and diff check pass. Next ACTIVE: clean local clone startup with network blocked and isolated user data, checking all six screens and pack manifest. Screen-reader test is blocked until manual Narrator/NVDA session can be performed; exact resolution action is recorded above.


## Clean clone and responsive UI limits (2026-10-24)

A fresh local clone of `044cbf2` launched the app with socket connects denied and app/Kivy data isolated inside the clone. All six screens loaded and `ModelPackManager` listed two pack definitions; no pack/model was downloaded. Source checkout stayed clean; only the intentionally isolated `.test-state` runtime directory is untracked.

Live Kivy acceptance verifies panel orientation: vertical at compact 320×700 dp; horizontal at wide 800×700 and short-landscape 500×500 dp. A separate 360×640 `Window.screenshot` capture was black/warped at launch and after resize; treat pixel-level compact rendering as unresolved. Next ACTIVE: get valid compact rendering evidence in a suitable isolated viewport. BLOCKED: screen-reader behavior requires manual Narrator/NVDA acceptance; Old Nubian rights/review and Somali fluent review blockers unchanged. Full tests 96/148; Ruff, format, compileall, `pip check`, release scan and live acceptance pass.


## Workflow checkpoint — blocked work does not stop development (2026-10-24)

The active goal remains to improve Saylacian usability while maintaining separate ACTIVE, BLOCKED and READY queues. The Obsidian Permanent Mission now makes the required handoff explicit: record each blocked task and its exact resolution action, leave it in BLOCKED, select the highest-impact independent READY task, and continue implementation/testing. Do not invent filler tasks or bypass approval requirements.

Current local HEAD is `565ad37` (`test: cover responsive Saylacian layouts`), 24 commits ahead of public `origin/main` at `c4f2f87270c22a05e772816ce98e57a99b871b18`; nothing was pushed. Full suite: 96 passed, 148 subtests; Ruff, formatting, compileall, `pip check`, release-safety and diff checks passed. Live Kivy acceptance passed. Clean source launch was verified from clone `044cbf2` with network blocked and isolated data; the later `565ad37` change adds tests only.

ACTIVE: verify theme-derived focus/disabled/selected colors and contrast. READY: obtain valid compact rendering evidence, test text scaling/overflow, and rerun clean source setup after runtime-affecting edits. BLOCKED: Old Nubian DBMNT-derived data requires written reuse terms plus qualified review (owner approval before outreach); Somali quality requires owner-approved consent-based fluent-speaker review; screen-reader behavior requires manual Narrator/NVDA acceptance. Preserve the existing uncommitted owner edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md`.


## Accessibility milestone — visible translator keyboard focus (2026-10-24)

Live widget inspection showed the translator fields have blank normal/active backgrounds and no visible focus cue. Added a 2dp black outline that follows each `SaylacianTextInput.focus` state; its inset rectangle adapts on position and size changes. The black outline against the #F2F2F2 field surface has approximately 18.8:1 contrast. Live acceptance toggles focus programmatically and asserts outline visibility/color/width. Captured and inspected `%TEMP%\saylacian-focus-acceptance\evidence\keyboard-focus0001.png`; no physical mouse/keyboard or system clipboard was used.

Full verification after this change: `96 passed, 148 subtests`; Ruff check, Ruff formatting (101 files), compileall and release-safety scan passed. Live `main.py --self-test` passed including translation output `Bonjour, comment allez-vous ?`, keyboard focus and layout checks. KivyMD 1.2.0 deprecation and internal `padding_x` warnings remain.

Next ACTIVE task: test text scaling and layout overflow at compact and wide sizes. READY: valid compact pixel-render capture, then clean-start regression if runtime-affecting files change. BLOCKED remains exact: DBMNT reuse requires written terms and qualified review (owner approval before outreach); Somali quality requires owner-approved consent-based fluent review; screen-reader behavior requires manual Narrator/NVDA observation. Current `main` is 25 commits ahead of `origin/main`; do not push. Preserve the two pre-existing owner edits.

## 2026-10-24 — saved-history recovery and blocked-work continuation

Permanent workflow updated in the master directive and Obsidian mission: maintain separate ACTIVE/BLOCKED/READY queues; every blocked task names the exact action needed; when an external dependency blocks the top item, choose the highest-impact independent READY task. If READY is empty, reconcile the roadmap and acceptance criteria before concluding no safe task remains. Do not invent filler tasks or bypass approvals. At verified milestones update Obsidian and repository handoff, commit locally, and continue while session is active. No push or publication.

### Verified product change

`History.read()` now validates JSON decoding, top-level version/schema, list shape and required record fields before the Saved screen consumes records. Damaged JSON and malformed entries raise actionable `ValueError`s. `read`, `save` and `clear` do not modify invalid or unknown-version history. `app/acceptance.py` verifies the live Saved flow reports a damaged file, leaves its bytes unchanged, and stays on Home.

Tests: `107 passed, 154 subtests`; Ruff check and format pass (103 files); `compileall`, `pip check`, `git diff --check` pass. Isolated live `main.py --self-test` passes with network denied; app/Kivy/evidence data redirected under `%TEMP%\saylacian-history-recovery-check`. No mouse/keyboard automation, clipboard operations, user-data writes, model downloads or remote writes.

### Queue

- ACTIVE: make focused local commit for saved-history resilience, then implement the READY Osmanya warning.
- READY: warn on Somali `ii`/`uu` converting to U+10495/U+10493, which also represent `y`/`w`; preserve mapping, explain reverse ambiguity, and add regression coverage using the Unicode Standard. After that, test a disposable clean checkout.
- BLOCKED: Old Nubian DBMNT-derived data requires written reuse terms and qualified review; owner approval before outreach. Somali quality needs owner-approved consent-based fluent-speaker review. Screen-reader claims need manual Narrator/NVDA observation. Compact screenshot needs a validated display because current 360×640 SDL capture was black. Hosted pack workflow needs explicit push approval before dispatch.

Previous user changes in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` remain untouched and excluded from staging. Current committed HEAD before this milestone: `f6a604f`; public origin was last verified at `c4f2f87270c22a05e772816ce98e57a99b871b18`. No remote action taken. KivyMD 1.2.0 and its `padding_x` deprecation warnings remain.

## 2026-10-24 — Osmanya conversion warns about irreversible vowel ambiguity

`docs/DEVELOPMENT_ROADMAP.md` and the Unicode 16.0 Core Specification §19.2.1 show that long `ii` and `uu` use Osmanya YA and WAW, which the reverse converter also reads as `y` and `w`. Forward conversion now keeps the existing Unicode output and adds an explicit warning that reverse conversion may read `ii`/`uu` as `y`/`w`. No orthography or mapping changed; no linguistic quality claim made.

Regression tests cover each digraph's unchanged code point plus warning. Live Kivy self-test confirms the warning reaches the visible status. Full suite: 108 passed, 156 subtests; Ruff check/format (103 files), compileall, `pip check`, isolated self-test and diff checks pass. Evidence source: https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-19/ .

- ACTIVE: stage reviewed Osmanya files and focused local commit; then validate clean checkout.
- READY: fresh disposable source checkout with isolated app/Kivy paths; run `main.py --self-test`, check history recovery + ambiguity warning, and verify source checkout remains clean.
- BLOCKED: Old Nubian DBMNT reuse needs written terms and specialist review (owner approval before outreach); Somali linguistic quality needs owner-approved consent-based fluent-speaker review; screen-reader claims need manual Narrator/NVDA observation; compact pixel review needs validated isolated OpenGL/SDL capture; hosted pack workflow needs explicit push approval before dispatch.

History resilience remains in local commit `b86bdb1`. Current pre-commit branch checkpoint was `b86bdb1`; no push/publish occurred. Preserve owner edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md`. No OS clipboard or physical input used.

## 2026-10-24 — Osmanya character assignment and digit detection

Audited every supported Somali-to-Osmanya output code point against Python Unicode character names: all 32 spelling entries name assigned `OSMANYA LETTER` characters. Added a regression guard; this verifies assignment only, not Somali orthographic accuracy. `detect_script()` now recognizes digit-only and letter-plus-digit Osmanya using Unicode U+10480–U+1049D and digit U+104A0–U+104A9 ranges. It still abstains on ASCII numerals and mixed scripts. Live Kivy acceptance confirms number-only input is labeled as Osmanya script, never meaning translation.

Full suite: 109 passed, 188 subtests. Ruff check/format (103 files), compileall, pip check, and `git diff --check` passed. Clean source clone of `be0e422` launched all six screens with socket connections denied and isolated APPDATA/LOCALAPPDATA/Kivy/pack paths; saved-history damage and forward `ii`/`uu` warning checks passed, source checkout stayed clean, and the two manifest packs enumerated as not installed. This clone uses the existing pinned Python environment; it was not a fresh dependency installation and no model pack was downloaded.

- ACTIVE: make a local commit for the Osmanya assignment/detection tests and Kivy acceptance.
- READY: after commit, re-run clean-checkout smoke against committed source; then reconcile roadmap for another independent, evidence-backed task.
- BLOCKED: Old Nubian DBMNT reuse needs written terms and specialist review (owner approval before outreach); Somali linguistic quality needs owner-approved consent-based fluent-speaker review; screen-reader claims need manual Narrator/NVDA observation; compact pixel review needs validated isolated OpenGL/SDL capture; hosted pack workflow needs explicit push approval before dispatch.

Local commits: `b86bdb1` (damaged saved-history safety), `be0e422` (Osmanya reverse-ambiguity warning). Existing user edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` remain untouched and excluded. No remote writes.

## Final checkpoint — 2026-10-24

Committed and verified locally:
- `b86bdb1` — preserve malformed saved-history bytes and report schema errors safely.
- `be0e422` — warn that Osmanya long `ii`/`uu` shares letters with `y`/`w` and cannot be reversed with certainty.
- `3bdc380` — guard all 32 Osmanya mapping outputs as assigned Unicode letters; recognize Osmanya digit-only text without inferring ASCII/mixed scripts.

Verification: `109 passed, 188 subtests`; `ruff check .`; `ruff format --check .` (103 files); compileall; `pip check`; `git diff --check`; isolated live Kivy self-test. Clean clone at `3bdc380` launched six screens with network denied, listed French/Somali manifests as not installed, and passed history/Osmanya checks; clone remained clean. Existing pinned venv reused; no model weights downloaded.

Queue reconciliation against `docs/DEVELOPMENT_ROADMAP.md`: ACTIVE none; READY none currently meets acceptance without an external permission, specialist evidence, or validated isolated graphics capture resource. This is after completing independent code tasks while blockers remained; do not treat the blocker itself as a reason to stop when a suitable READY task exists.

BLOCKED, exact resolution: Old Nubian DBMNT-derived expansion needs written reuse terms plus qualified specialist review; owner approval before outreach. Somali quality needs owner-approved consent-based fluent-speaker review. Screen-reader claims need manual Windows Narrator/NVDA interaction and observed announcements. Compact pixels need a validated isolated virtual display/OpenGL/SDL capture. Hosted pack integration needs owner approval to push the workflow commit, then manually dispatch and inspect Actions.

Current HEAD `1a07540` (progress-board sync), latest code checkpoint `3bdc380`, branch `main`. No remote writes/push. User edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` remain untouched and uncommitted. The active Codex goal remains active for future READY work.

## 2026-10-24 — saved-history recovery made actionable

Damaged saved history now offers two explicit choices: KEEP FILE (default, Escape-safe) and BACK UP & START FRESH. The second choice writes a unique backup using exclusive creation, flushes it, then atomically resets the original file. If reset fails, the original and backup both remain and the visible error includes the backup name. Unknown future versions are not eligible for recovery. After success, the user sees the backup filename and instruction to reopen Saved.

Tests: 9 history tests, including malformed JSON, invalid schemas, unknown version, valid-file refusal, backup integrity and simulated reset failure. Full suite `112 passed, 188 subtests`; Ruff check/format, compileall, `pip check`, `git diff --check`, and isolated `main.py --self-test` passed. The Kivy acceptance verifies default KEEP, keyboard-selected recovery, backup bytes, blank new history, and user-visible next step. No actual app user data or physical input was used.

- ACTIVE: stage reviewed recovery implementation/tests/progress and make focused local commit.
- READY: clone that commit into a disposable clean checkout, deny network, and confirm six-screen launch, backup-preserving recovery, and refusal to reset unknown versions.
- BLOCKED: Old Nubian DBMNT expansion needs written reuse terms and qualified specialist review (owner approval before outreach); Somali quality needs owner-approved consent-based fluent review; screen-reader claims need manual Narrator/NVDA run; compact pixels need a validated isolated capture environment; hosted pack workflow needs owner approval to push then dispatch.

Preserve user edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md`; do not stage them. Nothing pushed or published. Existing source branch base before this milestone: `97e356a`.


## 2026-10-24 — reject SentencePiece unknown-token output in EN→SO candidate route

The pinned pre-guard 150-pair benchmark contained U+2047 in 46/150 English→Somali candidate outputs (81 occurrences). Official SentencePiece documentation defines U+2047 as its default decoded surface for unknown tokens. Added a narrow check: if the experimental synthetic EN→SO candidate emits that marker, use the already-supported multilingual EN→SO route and tell the user why. Tests assert both marker detection and selected fallback output; no model mapping or Somali linguistic rule changed.

Added `sacrebleu==2.5.1` to developer-only requirements because the benchmark imports it. Installed `requirements-dev.txt` into a fresh Python 3.12 venv and verified `pip check`. Launched Kivy with isolated APPDATA/LOCALAPPDATA/Kivy/pack paths, installed and hash-verified the pinned Somali pack in temporary storage, and passed both offline smoke directions. The post-guard 150-pair benchmark ran with network blocked during inference: synthetic candidate selected 97 times; unknown-token fallback 47 times; output-length fallback 6 times. No U+2047 remained in final EN→SO output. BLEU/chrF++ changed from 7.057/28.996 to 5.287/25.282; SO→EN stayed 6.300/24.680. This removes a decode artifact but does not prove better meaning or Somali quality.

Full test suite: 114 passed. Ruff check/format (103 files), compileall, `pip check`, isolated Kivy startup and `git diff --check` passed. Benchmark output and model pack remain in `%TEMP%`; none is committed. Existing user edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` are untouched. No physical input, clipboard access or push. Local code/evidence commit: `1f97472`.

- ACTIVE: none after screening remaining roadmap items for safe, measurable implementation.
- BLOCKED: Somali semantic quality requires owner-approved consent-based fluent-speaker review; DBMNT-derived expansion requires written reuse terms and qualified review, with owner approval before outreach; screen-reader behavior needs observed Narrator/NVDA announcements; compact pixels need validated isolated graphics capture; hosted pack workflow needs push approval before dispatch.
- READY: none currently. Numeric-token and possible-negation counters are automatic cues, not verified errors; no linguistic fix is safe without review. Reconcile the roadmap again when evidence/permissions change or a new independent acceptance task is found.


## 2026-10-24 — close pack-version path escapes (M6-1)

A reproducible traversal test showed `ModelPackManager.active_model_roots()` accepted `current.json` version `../outside` and exposed a model directory outside its pack version folder. Pack IDs and versions now must be single safe ASCII path components. Pointer, version folder, installed manifest and every manifest-listed model file are resolved and checked under their expected storage directory before status reporting, verification or inference. Install rejects path-like version values before any download. Added regression coverage for POSIX and Windows traversal spellings; a directory-symlink escape test skips when the host denies symlink creation.

`docs/UPDATE_ARCHITECTURE.md` now records the trust boundary and keeps app self-updates separate and disabled. Full suite: 116 passed, 2 symlink tests skipped because Windows denied symlink creation. Ruff check/format (103 files), compileall, `pip check`, release safety scan, `git diff --check`, pinned Somali pack integrity recheck, both offline smoke directions, and isolated fresh-environment Kivy launch passed. No remote writes or real user pack/data changes.

- ACTIVE: audit short-text language detection using labeled test data and current roadmap acceptance; preserve abstention when evidence does not support a language label.
- BLOCKED: Old Nubian table expansion still needs DBMNT reuse terms and qualified review (owner approval before outreach); Somali linguistic quality needs owner-approved, consent-based fluent-speaker assessment; screen-reader behavior needs observed Narrator/NVDA announcements; compact pixels need validated isolated graphics capture; hosted pack workflow needs push approval.
- READY: none additional until the short-text detection audit identifies a concrete independent acceptance task.

## 2026-10-24 — Old Nubian combining-mark readability

The Old Nubian forward route no longer normalizes to NFC, preserving combining-mark order. Both translator output and Reading Studio Latin output use the bundled Noto Sans Coptic font. Reading Studio adds a display-only note with Unicode names and one-based code-point positions; it assigns no linguistic reading. Tests verify converted text, mark order, metadata and font selection. Live Kivy self-test passed; screenshot is `%TEMP%\saylacian-oldnubian-mark-20261024\evidence-final\old-nubian-reading-studio0001.png`. The screenshot shows the reading and mark note, but SDL capture omits some widgets; correct mark attachment in Latin context remains unverified. Full suite: `121 passed, 2 skipped`; Ruff, format, compileall, `pip check`, release safety and diff checks pass.

Queue reconciliation: **ACTIVE** short-text language-detection audit, using existing roadmap acceptance and labeled tests; **BLOCKED** DBMNT reuse (written terms plus qualified review; owner approval before outreach), Somali quality (owner-approved consent-based fluent review), screen-reader behavior (manual Narrator/NVDA), compact pixels (validated isolated capture path), external clipboard interoperability (disposable VM with sharing disabled), hosted workflow (push approval then manual dispatch). **READY:** none additionally queued. Preserve owner's pre-existing edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md`; no push or external action.

## 2026-10-24 — Short-text language detection

Below 20 characters, offline detection initially required at least 12 characters, three words and model confidence ≥0.85; longer text kept the 0.70 floor and 20-character minimum. A small 40-prompt hand-authored probe increased accepted/explicitly unsupported cases from 5 to 17. This was an initial engineering smoke check only.

## 2026-10-24 — Tatoeba short-text calibration

Added `tools/evaluate_language_detection_corpus.py`. It verifies five Tatoeba compressed exports by SHA-256, filters 12–19 code-point sentences with at least three words, makes a deterministic every-fifth holdout per language, and reports aggregates without printing or bundling sentence text. English/French/German/Spanish files were CC0 exports; Somali used Tatoeba's standard CC BY 2.0 France export, attributed in the roadmap. All files are in an isolated temporary directory.

The pinned sample yielded 1,918 English, 252 French, 43 Somali, 4 German and 1 Spanish eligible sentences. At short confidence 0.80, 562 outputs matched source language labels (456 development, 106 holdout); at 0.85, 432 matched (346/86). Neither threshold produced a false supported label, but unsupported evidence was only five items, Somali only 43. Because thresholds were explored after inspecting the full sample, the split is reproducible but not blind or preregistered. Lowered code threshold to 0.80; added a French regression at confidence 0.824. Somali translation quality remains experimental; dataset labels do not substitute for fluent review.

Tatoeba is a community-supplied corpus, not a specialist-validated language-ID benchmark. This five-language snapshot is superseded by the expanded 15-language evaluation below. Current ACTIVE: identify a reusable independent short-text language-ID benchmark. BLOCKED: Tatoeba source tags conflict with some texts; WiLI-2018 test paragraphs are ≥140 characters and none meet the app gate; resolve with independently verified natural short examples under clear terms or owner-approved review. Keep threshold 0.80 and make no accuracy claim. READY: none additional after roadmap reconciliation.


## 2026-10-24 — Expanded short-input language evaluation

Pinned 15 Tatoeba per-language archives by SHA-256; English/French are CC0 exports and the other 13 are CC BY 2.0 France. No sentence text is stored in the repository. The evaluator strips rows, filters 12–19 code points/three words, uses every fifth sorted ID as holdout, classifies once per example, and aggregates threshold sweeps. Unit tests verify one inference per record and that outputs use source-label disagreement terminology.

There were 403,820 eligible rows: English 1,918, French 252, Somali 43 and 401,607 unsupported-language rows across German, Spanish, Italian, Portuguese, Dutch, Polish, Swedish, Russian, Arabic, Japanese, Chinese and Hindi. At 0.80: 562 source-label matches (456 development, 106 holdout), six label disagreements in development and none in holdout. At 0.85: 432 matches (346/86), four development disagreements and none in holdout. Spot checks found some sentence text inconsistent with its Tatoeba language label, so this cannot be called false-positive or accuracy measurement. The deterministic split is exploratory, not preregistered; Somali sample is insufficient for quality review. Kept 0.80.

Added an actual Kivy acceptance assertion for short French input `Ou est la gare`: it routes to French with visible 82% confidence; isolated self-test passed. Full suite: 125 passed, 2 skipped, 197 subtests; Ruff check/format (105 files), compileall, `pip check`, release-safety and diff checks passed. Short detector warm-run latency was 0.019–0.033 ms median across five fixed samples, with maxima ≤0.080 ms in this one environment; no optimization indicated. WiLI-2018 test data contains no natural short examples within the app gate; it is not used as phrase evidence. Next ACTIVE is to find an independent, reusable short-text benchmark. READY: none separate after roadmap reconciliation.
