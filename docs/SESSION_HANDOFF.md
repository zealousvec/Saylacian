# Session handoff

## Resume point

Read the owner's `SAYLACIAN_MASTER_DEVELOPMENT_DIRECTIVE.md`, `docs/IMPLEMENTATION_PROGRESS.md`, and this file first. Keep the approved black-and-white Kivy interface, prioritize verified functionality, and preserve unrelated user edits. Do not use mouse/keyboard control. Do not push, publish, tag, or release.

Repository: the current checkout of `zealousvec/Saylacian`
Branch: `main`
Public `origin/main`: `c4f2f87270c22a05e772816ce98e57a99b871b18`
Public CI: run `40087020450` passed on that commit.
Local HEAD at start of the current milestone: `998ade1` (`fix: support enlarged text on compact layouts`); public `main` remains `c4f2f87270c22a05e772816ce98e57a99b871b18`. No push has occurred.
Preserve the pre-existing user edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md`; do not stage or rewrite them. The ongoing pack-update UI/acceptance/test changes and current text-fit fix are implementation work; stage only reviewed project files.

## Current milestone — enlarged-text fit and Osmanya reference recovery (2026-10-24)

At 200% Kivy font scale, live label geometry checks found clipping in Packs, Saved, Alphabet and Old Nubian. Updated fixed text heights and made pack rows follow their wrapped text. The missing Osmanya JPG lookup now falls back to the real Unicode alphabet grid; missing Borama/Kaddare images receive a readable status. A separate live Kivy measurement run passed for Home, Packs, Saved, Alphabet/Osmanya and Old Nubian at compact 360×640 dp and wide 900×700 dp. This is programmatic widget geometry evidence, not a claim of pixel-perfect compact screenshot review.

`main.py --self-test` passed at `KIVY_METRICS_FONTSCALE=2.0`, including offline output `Bonjour, comment allez-vous ?`. Full suite: 97 passed / 148 subtests. Ruff check passes; formatting was applied to `main.py`; compileall passed. Screenshot: `%TEMP%\saylacian-large-ui-evidence\old-nubian-reading-studio0002.png`.

### Current queues

- ACTIVE: run a clean-clone startup check after the runtime UI changes; isolate app data and deny network connections.
- BLOCKED: DBMNT reuse needs written rights and qualified review (owner approval before outreach); Somali translation needs owner-approved consent-based fluent-speaker review; screen-reader claims need a manual Narrator/NVDA run.
- READY: get valid 360×640 pixel-render evidence in a suitable isolated Kivy viewport. The previous Kivy window screenshot had black/warped pixels; do not claim visual validation based on it.

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

1. Run a clean local clone of the committed revision with networking denied, isolated app/Kivy data and no model download.
2. Obtain valid compact pixel-render evidence using an isolated Kivy viewport; preserve the current pixel-level validation limitation until then.
3. Continue the next highest-impact READY product task; keep DBMNT, Somali human review, screen reader and external clipboard checks BLOCKED with their exact resolution actions.

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
