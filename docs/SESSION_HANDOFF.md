# Session handoff

## Resume point

Read the owner's `SAYLACIAN_MASTER_DEVELOPMENT_DIRECTIVE.md`, `docs/IMPLEMENTATION_PROGRESS.md`, and this file first. Keep the approved black-and-white Kivy interface, prioritize verified functionality, and preserve unrelated user edits. Do not use mouse/keyboard control. Do not push, publish, tag, or release.

Repository: the current checkout of `zealousvec/Saylacian`
Branch: `main`
Starting local commit: `c4f2f87270c22a05e772816ce98e57a99b871b18`
Latest local implementation commit: `63eca70f473c962663e00e8e82071cb3e405c8c3`
Starting public CI: run `40087020450`, passed on the starting commit.
Remote state: no push requested; verify before any future approved push.

## This session

Implemented concise route labels and mode-specific picker choices. Removed a stale call to deleted `_choice_note`, which otherwise broke conversion. Added safe Borama/Kaddare copy menu actions named **Copy text**, **Copy image**, and **Copy Latin** on Windows; generic routes show only **Copy text**. The text action uses the existing versioned Saylacian Text package. Private-use text is not auto-detected; users can select Borama/Kaddare explicitly or paste the tagged package. Unknown/unlabelled input and invalid packages clear stale output. Tagged packages import, select the correct font and reconvert.

Updated user-visible pack/conversion wording and documentation for clipboard limitations, current chart-mapping support, and Unicode proposal status. Added regression tests and wrote the directive's task board, handoff, script interoperability, Old Nubian source ledger/reader plan, Nubian research register, translation evaluation plan, update architecture and UI copy register.

Live Kivy evidence: `%TEMP%\Saylacian-Master-Directive-20261024-final4`. `result.json` reports pass; screenshots are `chart-borama0001.png`, `chart-kaddare0001.png`, and `packaged-meaning0001.png`. No mouse or keyboard automation was used. The KivyMD runtime logs a deprecation notice for installed KivyMD 1.2.0; no framework upgrade was attempted. The real Windows clipboard test was not run: its read-only preflight found non-text clipboard formats, so the script would refuse before changing clipboard contents.

## Next three tasks

1. Re-run `tools/test_windows_clipboard.ps1` only when the clipboard safety preflight sees empty or text-only data. Use a new temp evidence path; then test Notepad, browser, Word/equivalent, VS Code and a messaging-style field.
2. Finish the visible-string inventory across dialogs, packs, history, website templates and GitHub-facing docs. Keep limitations clear and the approved UI intact.
3. Continue the Old Nubian source audit, source-linked fixtures and reader work. Do not add guessed mappings or enable modern Nubian routes.

## Final verification results

- `pytest`: `87 passed, 66 subtests passed`.
- Live Kivy `main.py --self-test`: passed on Windows; screenshot and JSON evidence are in `%TEMP%\Saylacian-Master-Directive-20261024-final4`.
- `compileall`, `ruff format --check .`, `pip check`, release-safety scan, local Markdown links, `git diff --check`: passed.
- Targeted Ruff check for `presentation.py` and its test: passed. Full repository Ruff check reports 35 findings; see command output for file/line list. These were not broadly auto-fixed.
- Real clipboard matrix: deferred because safety preflight found non-text clipboard data; no data was overwritten.

## Files changed this session

`main.py`; `app/main.kv`; `app/acceptance.py`; `saylacian/core/presentation.py`; `saylacian/core/interchange.py`; `saylacian/core/transliteration.py`; `tests/test_presentation.py`; `tests/test_core.py`; `tests/test_historical_chart_scripts.py`; `tests/test_clipboard_interchange.py`; `docs/IMPLEMENTATION_PROGRESS.md`; `docs/SESSION_HANDOFF.md`; `docs/SOMALI_SCRIPT_INTEROPERABILITY.md`; `docs/OLD_NUBIAN_SOURCE_LEDGER.md`; `docs/OLD_NUBIAN_READER_PLAN.md`; `docs/NUBIAN_RESEARCH_REGISTER.md`; `docs/TRANSLATION_EVALUATION_PLAN.md`; `docs/UPDATE_ARCHITECTURE.md`; `docs/UI_COPY_REGISTER.md`; `docs/SAYLACIAN_TEXT_FORMAT.md`; `docs/SCRIPT_FEASIBILITY.md`; `docs/SCRIPT_RESEARCH.md`; `docs/SUPPORT_MATRIX.md`; `models/en_fr/README.md`; `models/fr_en/README.md`.

The pre-existing `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` edits remain separate and must not be included in the commit.

## Local work and approvals

Implementation is committed locally as `63eca70f473c962663e00e8e82071cb3e405c8c3`. The pre-existing changes in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` remain uncommitted and untouched. No remote changes were made. Explicit approval remains required before any push or public release action.
