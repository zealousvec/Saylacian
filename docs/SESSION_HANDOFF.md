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
