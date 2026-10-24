# Session handoff

## Resume point

Read the owner's `SAYLACIAN_MASTER_DEVELOPMENT_DIRECTIVE.md`, `docs/IMPLEMENTATION_PROGRESS.md`, and this file first. Keep the approved black-and-white Kivy interface, prioritize verified functionality, and preserve unrelated user edits. Do not use mouse/keyboard control. Do not push, publish, tag, or release.

Repository: the current checkout of `zealousvec/Saylacian`
Branch: `main`
Public `origin/main`: `c4f2f87270c22a05e772816ce98e57a99b871b18`
Public CI: run `40087020450` passed on that commit.
Five implementation/progress commits were ahead of public main at session start. This session's implementation is committed locally as `5a5b54f` (`fix: improve readings and reliability`); it is unpushed. Public `main` remains `c4f2f87270c22a05e772816ce98e57a99b871b18`.
No push has occurred. The only pre-existing user edits were `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md`; both remain unstaged and outside this commit. Preserve them.

## Latest session milestone

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

1. Continue Old Nubian work only with cited scholarly evidence or a specialist reviewer; improve mark display only if raw copy remains unchanged.
2. Run external clipboard acceptance in a disposable Windows VM with host clipboard sharing disabled. Never run it on the everyday desktop.
3. Continue Somali-speaker evaluation and investigate remaining KivyMD warnings; migrate only in an isolated branch after UI acceptance.

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

Added Ctrl+Shift+M to switch mode, Ctrl+P to open packs, Ctrl+K to open target selection, Ctrl+Shift+K to open source selection, Up/Down to traverse filtered results, Enter to choose, Ctrl+L to return to the editor and Esc to go back. `RUN.md` documents these keys. Live Kivy acceptance verified a mode change, pack navigation, changed target selection, editor focus and return from the pack screen. The first run found an SDL key-name API mismatch; using `Keyboard.keycodes` fixed it and the rerun passed. This provides useful keyboard access but is not a full screen-reader/accessibility audit.

Saved-history `save` and `clear` now share a same-directory temporary JSON write plus atomic replace. Failure injection verifies the old history bytes survive failed replace and no temp file remains. Local commit `66581de`.

Latest full tests: `96 passed, 148 subtests`; Ruff and formatting (101 files), compileall, `pip check`, `git diff --check` and live Kivy `main.py --self-test` pass. The UI result JSON confirms keyboard picker navigation, download cancellation, Old Nubian reader actions and local English→French. No physical keyboard/mouse input or system clipboard was used. Next ACTIVE: reproduce startup from a clean checkout using isolated `APPDATA`/pack storage and a network-denied, time-bounded run. Then continue the READY focus/accessibility audit. BLOCKED: (1) DBMNT reuse remains unclear and no qualified Old Nubian reviewer; obtain written permission and qualified review, with owner approval before outreach. (2) Somali quality validation needs owner-approved, consent-based fluent review on a suitable sample. Preserve the pre-existing `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` edits; no push.
