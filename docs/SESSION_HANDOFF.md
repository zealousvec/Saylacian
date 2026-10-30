# Session handoff

## 2026-10-25 — current feature changes

Added bounded whitespace segmentation for long offline model inputs with an explicit context-change warning; text within model limits still uses one inference. Old Nubian now exposes the cited `ⳣ` `w`/`ou` alternatives, including the alphabet and Reading Studio. Kaddare explains that its conversion emits one label glyph although the chart shows two forms; Borama/Kaddare duplicate case variants are deduplicated in unmapped-letter notices. No tests or UI automation were run. Preserve user edits to `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md`. Do not add chart-derived mappings or Old Nubian readings without the unresolved rights and specialist review; next useful task is review the diff and, when allowed, exercise chunked offline input with installed packs.

## Current changes — 2026-10-25

Removed the app-drawn text-field focus border, added local last-session persistence (restores the last completed output without rerunning translation), and wrote `docs/SCRIPT_LETTER_GUIDE.md` with the actual current script-table entries and limitations. Linked the guide from README and docs. No tests or UI automation were run per user instruction. Preserve the user's existing `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` changes. When checks are permitted, verify persistence and field focus behavior without OS input injection; no mouse/keyboard control is authorized.

## Current checkpoint — 2026-10-25

**Not finished: remaining work requires external review, resources or approval.** Local source/UI commits include `b7fbe45`, `8b748ab`, and `f452827c481ab8bfdd8261a7784582d321ae492c`. Full suite: 163 passed, 2 Windows symlink-permission skips, 208 subtests. Ruff, format, compilation, dependency/security checks and 41 modified-document links passed. Real Kivy: 19 checks across six window sizes, with exact home-control and text-panel positions asserted across mode switches; broader app self-test: 24 checks. Network blocked; clipboard was in-memory.

The unavailable Read action stays hidden. Picker now shows one-line route names with an ASCII `[x]` selection marker; long coverage/copy explanations moved to linked GitHub docs. Mode toggle has a reserved layout slot; compact spacing protects text entry. Latest compact screenshot: `%TEMP%\saylacian-final-ui-afeab47f12cb469daaf2ff6df6383c2a\evidence\previews\enhanced-compact-portrait.png`; picker: `%TEMP%\saylacian-final-ui-afeab47f12cb469daaf2ff6df6383c2a\evidence\previews\enhanced-picker-mobile.png`. No redesign or physical input occurred.

New docs: `docs/README.md`, `docs/USER_GUIDE.md`, and `docs/API_REFERENCE.md`. User guide explains Borama/Kaddare `Copy text`, `Copy image`, and `Copy Latin`, including PUA/font limits and unverified external-app behavior. No public translation API is claimed. KivyMD 1.2.0 deprecation warning remains; no framework migration was attempted.

Four benchmark CLIs now reject repository output paths, generate unique results in local app data and preserve baseline audits. Six legacy output/checkpoint files were hash-verified in a local archive before removal from the checkout. Aggregate evidence and model provenance remain tracked; older Git commits were not rewritten. Archive: `%LOCALAPPDATA%\Saylacian\benchmark\legacy-predictions-20261025-b676335650ff493dad0bab373b73145e`.

Use the ACTIVE/BLOCKED/READY queues in `IMPLEMENTATION_PROGRESS.md`. No independent READY task remains in this audit. Do not invent filler work. External actions: fluent Somali review; written Old Nubian reuse rights and specialist review; Narrator/NVDA; clipboard VM; hosted-run/push approval; clean-host signing/package tests; physical devices and documented evaluation resources. Keep owner edits in PROJECT_STATUS/TECHNICAL_AUDIT untouched. Nothing pushed or published. Dated sections below are historical.


## Unfinished recovery campaign — 2026-10-25

**Status: PARTIALLY COMPLETE — NOT FINISHED.** The earlier completion report was premature. This recovery completed the pinned Somali benchmark reproduction and fixed a vulnerable development dependency. No push or release occurred.

Clipboard acceptance correction: `tools/check_ui.py` had called the native Windows clipboard publisher during its older recorded round-trip, without proving existing clipboard contents were preserved. It now patches the app to an in-memory clipboard and publisher before app creation. Three focused helper tests pass; the full suite passes 149, 2 Windows symlink-permission skips and 200 subtests. Ruff, formatting, compileall, `pip check` and release-safety pass. The live Kivy script was not rerun, and its 2026-10-23 clipboard result is not accepted as preservation or external-app evidence. Real interoperability remains BLOCKED pending the guarded disposable-VM procedure in `docs/CLIPBOARD_TESTING.md`.

## Required benchmark re-run — 2026-10-25

Installed the pinned Somali pack in a fresh temporary store: version `1-bfd6cf52bd69`, 314,460,806 verified bytes, all 10 assets valid, both offline smoke directions passed. Re-ran all 150 TICO-19 pairs from fixture SHA-256 `be58b2d350badb7e03b73906471453311a8843534e4a2a572a772c60c394c7f7`; `socket.socket.connect` was blocked during inference. Output and checkpoint stayed outside the repository. EN→SO BLEU/chrF++ `5.287/25.282`; SO→EN `6.300/24.680`; 97 candidate selections, 53 fallbacks (47 unreadable marker, 6 output length); no U+2047 in final EN→SO. Runtime 115.26 s, peak working set 548,388,864 bytes. This is reproducibility evidence only, not Somali quality review. The candidate model SHA-256 matched its pinned manifest.

Benchmark: fresh 10/10-asset pack `1-bfd6cf52bd69` installed in unique temporary storage; socket connections were blocked during inference and predictions/checkpoints stayed outside the repository. The 150-pair results matched the recorded post-guard metrics: EN→SO BLEU/chrF++ 5.287/25.282 and SO→EN 6.300/24.680. This is reproducibility evidence, not linguistic quality. The route-audit parser now recognizes current fallback warnings; synthetic candidate accepted 97/150, 53 used fallback (47 unreadable-marker and 6 output-length), and final EN→SO contained no U+2047. The score is below the pre-guard EN→SO 7.057/28.996; do not call it an improvement.

Dependency audit: `requirements-dev.txt` now pins pytest 9.1.1, replacing vulnerable 8.4.2 (PYSEC-2026-1845). `pip-audit` found no known vulnerabilities in any `requirements*.txt` file after the fix. A fresh temporary Windows environment installed the dev requirements; `pip check` and the complete suite passed: 144 passed, 2 symlink-permission skips, 197 subtests. Ruff, format (113 files), compileall, release scan and diff checks also passed.

Recovery milestone is committed locally at `72a3e5ee8554401fd36d9901722bd64bcf1ed66b` (`fix: secure dev deps and audit routes`). It contains only seven reviewed paths; owner edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` remain untouched and unstaged. Do not push. No safe implementation task is currently READY; reassess if an external resource or new evidence changes the queue.

Follow-up security fix: `_safe_relative()` rejected POSIX traversal but accepted Windows backslashes and drive paths; on Windows those could resolve outside the model-pack staging folder. It now rejects backslashes and Windows drive paths before destination construction. Regression covers `..\` traversal, absolute drive paths, and drive-relative paths; each is rejected before the network fetch and creates no escaped file. Full suite: 145 passed, 2 Windows symlink-permission skips, 200 subtests. Ruff, format, compileall, `pip check`, release scan and diff check pass. Local code commit: `6f294db2bf8be75bfba88334325635784fd9631a`, containing only the validator and regression test. Nothing was pushed.

Latest implementation is committed locally as `b4904be9643dee1f8dfb2a5e484b4e731a8f06d6` (`fix: verify installed model hashes`), containing only `saylacian/core/model_packs.py`, `tests/test_model_packs.py`, `main.py` and `app/acceptance.py`. Active pack roots and the Packs screen validate installed file SHA-256 values from the installation receipt. Hash results are cached against path, size, timestamps, device and inode; a changed file causes revalidation without rescanning unchanged model files on every route. A same-size tamper regression first warms the cache, modifies model bytes, and proves the route is rejected and the pack is marked damaged. Reinstall leaves damaged files untouched; the user can confirm removal in the Packs screen and download the pinned pack again. Kivy acceptance verifies the damage message and both keyboard and button removal entry points with a stub, without deleting a real pack.

An isolated, freshly downloaded French pack passed hash verification and both offline directions with network connections blocked. Live Kivy `main.py --self-test` passed using isolated app, Kivy, pack and evidence paths. Latest full suite: 146 passed, 2 symlink-permission skips, 200 subtests. Ruff/format, compileall, `pip check`, release-safety and diff checks pass. **ACTIVE:** none. **READY:** none after this milestone; reassess when new evidence/resources arrive. Keep owner docs untouched and do not push.

**BLOCKED:** fluent Somali review; written DBMNT rights plus Old Nubian specialist review; Narrator/NVDA observation; validated compact-layout capture; real clipboard delivery/import in a disposable VM; hosted workflow run requiring an approved push; clean-host Windows signing/package validation; Maanka2 model data reuse terms because its linked dataset page requires authorization. M2M100 has since had a 30-pair dev screen and was rejected; short-text language-ID still lacks adjudicated labels. Exact unblock actions remain in `docs/IMPLEMENTATION_PROGRESS.md`.

The active goal remains unfinished even though this local milestone is committed. Start future work by checking `git status --short` and the queues, then continue any newly READY safe task. Preserve the benchmark temp outputs; no model weights or example predictions belong in Git.

## Latest milestone — diagnostic log path privacy (2026-10-24)

Source review found that `PrivateDiagnostics.record_exception()` stored full traceback filenames. This could disclose an account name or installation directory if a user shared a diagnostic log. It now stores only each filename's basename, line number and function name; exception messages and translation text remain excluded. `docs/RUN.md` explains the fields and says to review logs before sharing. Regression verifies that an actual traceback still includes `test_diagnostics.py` but omits its parent directory and private exception text.

Focused diagnostic test: `1 passed`. Full suite: `143 passed, 2 skipped, 197 subtests`; Ruff check, format (`112 files`), compileall, `pip check`, and diff checks pass. No user diagnostic file was read or changed. **ACTIVE:** none after this fix. **BLOCKED:** same external reviewer/rights/isolated-resource tasks remain in the progress board. **READY:** none currently; re-evaluate without inventing filler work. No push.

## Previous milestone — clipboard setup failure cleanup (2026-10-24)

Audited the Windows clipboard publisher's error paths after the HWND ownership fix. If allocation of a later format failed, earlier movable global-memory blocks escaped cleanup. Allocation and publish now share the existing `finally` cleanup; each handle is tracked immediately after allocation, so lock/allocation failures free all untransferred blocks. The regression forces the second allocation to fail and verifies the first is freed, no blocks remain, and `OpenClipboard` is never called.

Focused tests: `3 passed`. Full suite: `143 passed, 2 skipped, 197 subtests`; Ruff check, format (`112 files`), compileall, `pip check`, and diff checks pass. No real OS clipboard was touched. The fix is committed locally; no push. **ACTIVE:** none after this fix. **BLOCKED:** real clipboard delivery still needs a disposable Windows VM with host clipboard sharing disabled and a font-compatible external app. **READY:** none currently; reconcile roadmap without inventing filler work.

## Previous milestone — Windows clipboard publishing owner fix (2026-10-24)

Found a real Windows clipboard failure: Saylacian called `OpenClipboard(NULL)`, then `EmptyClipboard`; Microsoft documents that this sets clipboard ownership to NULL and makes subsequent `SetClipboardData` fail. See [OpenClipboard](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-openclipboard) and [EmptyClipboard](https://learn.microsoft.com/en-us/windows/win32/api/Winuser/nf-winuser-emptyclipboard). `main.py` now obtains Kivy's native `Window.get_window_info().window` handle and passes it as the owner. The publisher rejects a missing owner before allocating clipboard memory. Tests use isolated fake Win32 APIs to verify owner propagation, standard/custom format IDs, handle transfer and null-owner rejection; no OS clipboard was read or changed.

Focused clipboard suite: 16 passed, 4 subtests. Full suite: `142 passed, 2 skipped, 197 subtests`; Ruff check, format (`112 files`), compileall, `pip check`, and diff checks pass. This fixes the API owner defect but does not verify actual Windows clipboard delivery or import into external applications. **BLOCKED:** use a disposable Windows VM with host clipboard sharing disabled, then test Copy as Latin/Image/Saylacian Text and confirm formats in a font-compatible external app. **ACTIVE:** none after this code fix. **READY:** none currently; reconcile roadmap before selecting more work.

## Latest milestone — short-input language detection (2026-10-24)

Added an aggregate-only evaluator for Amazon MASSIVE 1.1. Official archive SHA-256: `4cba5faa11c71437928e17cb1b9b3d8b8e727e7ea363a3a9a8045e19c0491577`; licence: CC BY 4.0. The 40 MB archive was used from temporary storage and not bundled. Of 154,648 test rows, 12,729 meet Saylacian's 12–19-code-point/three-word input gate. A deterministic cap of 500 per locale sampled 11,386 across 52 locales. The dataset has locale labels but no per-row language-identification judgements; Somali is absent. At 0.75 confidence, 142/451 English/French samples matched their locale label and none of 10,935 unsupported-locale samples was sent to an app-supported language. At 0.80, 116/451 matched; at 0.70, two unsupported-locale samples were sent to a supported language. These are exploratory source-locale checks, not independently adjudicated language-ID accuracy.

Compared the same thresholds against pinned Qor Somali short text: at 0.75, 33/67 were detected Somali and 34 abstained, with no other-language predictions; at 0.80, 30/67 were detected Somali and 37 abstained; at 0.70, 37 were detected Somali, 29 abstained and one was predicted as another language. Lowered `MIN_SHORT_CONFIDENCE` from 0.80 to 0.75. This improved accepted short examples in both corpora without an observed wrong supported route in these samples. The samples are small or locale-labelled and do not establish general accuracy or translation quality. Production behavior has an exact boundary regression.

Full suite: `140 passed, 2 skipped, 197 subtests`. Ruff check, formatting (`111 files`), compileall, `pip check`, and `git diff --check` pass. Added `tools/evaluate_massive_lid.py` and three tests. Dataset/corpus text remains in temporary storage; evaluator prints aggregates only. No UI redesign, physical input or clipboard interaction.

**ACTIVE:** no independent short-text language-ID labels are currently available; reconcile the next product milestone against the roadmap without inventing filler work. **BLOCKED:** overall detector accuracy needs consented, independently adjudicated short examples across Somali, English/French and unsupported languages. Resolve by arranging appropriate reviewers and terms; Common Voice can add locale-labelled data after the owner obtains its official MDC TSV. CommonLID is eval-only, gated under Common Crawl Terms of Use, and its published 109-language table does not include Somali. **READY:** none after this milestone; reevaluate when external evidence or a concrete acceptance task becomes available.

## Latest milestone — route and pack status usability (2026-10-24)

User-facing route warnings no longer expose internal terms such as “synthetic candidate,” “multilingual fallback,” or “human review pending.” Somali output retains a clear accuracy caution; Somali/French pivot warns meaning may change. Added unit and website regressions plus live Kivy assertion for the status label. Full suite: 127 passed, 2 skipped, 197 subtests. Ruff, format (105 files), compileall, `pip check`, release scan, `git diff --check`, and isolated Kivy self-test pass. Local UI acceptance output: `Bonjour, comment allez-vous ?`.

Completed visible chart and Old Nubian picker copy checks; users can distinguish missing artwork from limited conversion, and the Latin-reading picker does not imply scholarly validation. Pack download/removal errors now avoid local-path leakage, preserve integrity/security failures and give recovery steps. Missing offline translation routes direct users to Packs; the live Kivy check confirms the error and cleared output. Unit and isolated Kivy checks pass; failure cases used stubs only. Final full suite: 129 passed, 2 skipped, 197 subtests; Ruff/format, compileall, `pip check`, release scan and diff check pass. Short-input accuracy remains BLOCKED until a licensed, independently labelled natural short-phrase set or owner-approved review is available. DBMNT-derived expansion, Somali specialist quality review, screen-reader run, compact pixel capture, external-app clipboard and hosted workflow have their existing exact blockers in `docs/IMPLEMENTATION_PROGRESS.md`. Preserve owner changes to `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md`; no push.

## Latest milestone — short-text benchmark tooling (2026-10-24)

Mozilla Common Voice Text LID is now recorded as a promising CC0, split-based source. Its official archive is gated through Mozilla Data Collective; this session has no authorized archive or API credentials. Added an aggregate-only evaluator that uses test rows, enforces the app’s 12–19-character/three-word gate, SHA-256-hashes the full archive and bounds a stable sample at 500 per language. It emits no text. Four fixture tests pass; this is tooling verification only, not benchmark evidence.

ACTIVE: find an authorized non-Somali short-text sample with independent labels to evaluate precision and supported/unsupported confusion. SomaliWeb v1’s benchmark CSV was checked at its cited GitHub repository/raw path; both returned 404. BLOCKED: Common Voice scoring until the owner provides an official MDC TSV or authorizes credentialed access. Full suite after Qor evaluator: 136 passed, 2 skipped, 197 subtests; Ruff/format (109 files), compileall, `pip check`, and diff check pass. Keep 0.80 until multilingual/negative short examples support a threshold decision.

### Qor Somali-only short-input evidence

Fetched the public Qor Af-Soomaali sentence export into an ephemeral temp directory and evaluated immutable HF revision `5234876e5019cc4b1c79096c9f046fe2f8113b1e` (CC BY-SA 4.0; SHA-256 `f53ec99fbbd620ac65412d0c26c62a80faa534b9a939e95a0da6c53d5b38c60c`). All 3,629 records are marked verified; 67 native records meet the 12–19-code-point / three-word gate. At 0.80: 30 Somali predictions, 37 below-threshold abstentions. At 0.70: 37 Somali predictions, 29 abstentions, one other-language prediction. No corpus data is retained in the repository; evaluator prints aggregates only. The source notes that longer passages were sometimes verified at passage level. This measures Somali-only recall-like detection share, not precision, overall accuracy, translation quality or expert adjudication of every short sentence. Keep the production threshold unchanged pending negative/multilingual evidence.

Added `tools/evaluate_qor_somali_lid.py` with a pinned hash and three fixture tests. The Common Voice evaluator remains in place; its archive is still gated through MDC. SomaliWeb’s source CSV is unavailable at the cited location. Next ACTIVE: identify authorized non-Somali short inputs; READY is empty after this milestone.

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

## 2026-10-25 — Safe isolated Kivy acceptance restored

Updated `tools/check_ui.py` to match current language-picker/status wording and the separately listed Borama chart reference. The harness now defaults all screenshots, failure traces and JSON results to a fresh temporary evidence directory (overridable with `SAYLACIAN_UI_EVIDENCE_DIR`) instead of overwriting tracked or ignored `docs/` artifacts. Clipboard actions remain replaced by an in-memory clipboard and stub publisher.

Ran the actual Kivy acceptance script with isolated APPDATA, LOCALAPPDATA, Kivy home, pack store and evidence output, with network connections blocked. All 19 checks passed, including the in-memory clipboard round trip, offline Somali routes, installed-pack screen, stale-worker handling, and layout geometry at 320x640, 390x780, 780x390, 768x1024 and 1366x768. Evidence is at `%TEMP%\Saylacian-safe-ui-a2d90f6ce6bd4b159781638269540aab\evidence`. The 320x640 PNG was visually inspected at 400x800 RGBA and is legible, with all primary controls and status visible. This clears the compact-capture-path blocker for this viewport; broad platform visual regression, screen-reader announcements and real system clipboard remain unverified.

Full verification after the harness fix: `149 passed, 2 skipped, 200 subtests passed`; Ruff check and format, compileall, `pip check` pass. The two skipped tests require Windows symlink privilege. Owner edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` remain untouched. No host clipboard access, push or publication.

ACTIVE: commit this focused harness correction and then reassess the next independently verifiable READY work. BLOCKED: fluent Somali review; Old Nubian rights/specialist review; Narrator/NVDA; external clipboard test in disposable VM; hosted CI workflow approval; clean-host Windows signing/packaging; full M2M100 development evaluation on suitable faster hardware. READY: none established beyond this verification/commit step; do not invent tasks.

## 2026-10-25 — Release matrix reconciled with current clipboard/UI evidence

Corrected stale Windows source claims in `docs/PACKAGING_MATRIX.md`: current live acceptance uses an in-memory clipboard, so actual system clipboard delivery remains unverified. Updated source test counts and Windows onedir wording to label historical unsigned artifacts accurately. Reconciled the roadmap queue: 320x640 compact capture is now verified from fresh isolated evidence; Narrator/NVDA, real clipboard VM, specialist/rights, hosted workflow approval and signed clean-host packaging remain blocked. No code runtime behavior or owner-owned project-status/audit files changed.

## 2026-10-25 — Release documentation links and current evidence

Fixed `docs/PACKAGING.md` to link to tracked `SUPPORT_MATRIX.md` and `WINDOWS_RELEASE_SECURITY.md` rather than the ignored, non-published `PACKAGING_MATRIX.md`; added a dated source/runtime gate summary distinguishing isolated in-memory clipboard checks from unverified system clipboard delivery. A repository-wide local-link scan checked 46 tracked Markdown files with no missing file targets. Full suite/Ruff/format were rerun before these Markdown-only edits and passed (149 passed, 2 symlink skips, 200 subtests); `git diff --check` passes. No source behavior changed. Roadmap re-screen found no new unblocked implementation item; keep goal active and reassess when evidence or a concrete acceptance task appears.

## 2026-10-25 — Fix landscape UI evidence capture

Reviewing fresh screenshots revealed the 780x390 `Window.screenshot` frame was sheared on this AMD Radeon 780M/high-DPI setup. A separate Kivy process started at that size reproduced the issue; the same live screen exported with `Widget.export_to_png` (FBO) rendered correctly, and measured home/panel/input/output geometry stayed within the window. This isolates the defect to framebuffer capture, not the approved app layout. Updated `tools/check_ui.py` to export the live root widget through FBO after frame presentation.

Reran live Kivy acceptance: all 19 checks pass with network connections blocked, isolated app/Kivy/pack/evidence directories, and in-memory clipboard. Visually reviewed five FBO captures: 320x640, 390x780, 780x390, 768x1024 and 1366x768; all are intact, including landscape. PNGs are valid and nonblank (256 colors each). Evidence: `%TEMP%\Saylacian-ui-fbo-95a9ffd1d7f34eee8ea84129ea6d9e70\evidence\previews`.

Full repo: `149 passed, 2 skipped, 200 subtests passed`; Ruff check and format (115 files), compileall, `pip check`, screenshot integrity check and diff check pass. The two skips require Windows symlink privilege. No app layout redesign, host clipboard, physical input or network calls. ACTIVE: commit this acceptance-harness fix, then reconcile remaining READY tasks. BLOCKED: Somali review, DBMNT rights/specialist, Narrator/NVDA, real clipboard VM, hosted workflow approval, signed clean-host package and full M2M100 evaluation on faster hardware. Goal remains active/not finished.

## 2026-10-25 — Bound retained translation models with measured tradeoff

`load_model` previously cached up to four CTranslate2 engines for the whole app session. A process-level profile loaded each real local route and measured 422 MiB working set after the four-route sequence. Reducing the cache to two lowered the settled working set to 220 MiB but caused route thrashing: the full Somali benchmark took 178.67 s and peaked at 583,114,752 bytes. Rejected that setting.

Set the LRU cap to three, enough for the EN→SO candidate, OPUS fallback and SO→EN engines used by the benchmark. A regression with mocked model loaders checks actual LRU eviction beyond three distinct routes. The four-route memory profile now settles at 318 MiB (about 104 MiB below the old four-entry cache); cache clear returned to 34 MiB.

Reinstalled Somali pack `1-bfd6cf52bd69` in a new isolated store, verified 10/10 assets (314,460,806 bytes), and passed both offline smoke directions. Re-ran all 150 pinned examples with socket connections blocked and output/checkpoint in temp. Exact metrics reproduced: EN→SO BLEU/chrF++ `5.287/25.282`; SO→EN `6.300/24.680`. Candidate 97, fallback 53 (47 unreadable marker, six output length), no U+2047. Runtime 108.06 s; peak RSS 547,704,832 bytes, effectively unchanged from the prior ~548 MiB run. The temporary two-entry experiment was slower with higher peak; cap three is the evidence-backed setting. This improves steady route-switch memory only; it does not claim Android/low-memory-device validation or Somali quality.

Verification: full suite `150 passed, 2 skipped, 200 subtests`; Ruff check/format (115 files), compileall, `pip check`, release-safety scan, and isolated live Kivy acceptance (19 checks, network blocked, five FBO viewport geometries) passed. ACTIVE: commit this code/test change, then re-screen. BLOCKED: fluent Somali review; DBMNT rights/specialist review; Narrator/NVDA; real clipboard VM; hosted workflow approval; clean-host signing/packaging; full M2M100 evaluation on faster hardware. Owner docs remain untouched; no push/publication.

## 2026-10-25 — Release cached engines when removing a pack

Pack removal previously deleted the installed folder but left its CTranslate2 engine referenced by the process LRU. Successful removal now clears cached engines immediately so users recover memory and a reinstall cannot reuse an object loaded from the removed installation. If removal fails, the cache remains unchanged. Implemented with a small core cache-clear function called from the existing Kivy removal flow; approved UI and pack storage behavior stay the same.

Added live acceptance for both outcomes: mocked successful removal confirms cache clear and success status; mocked deletion failure confirms cache is preserved and the existing privacy-safe error is shown. Translation cache unit test confirms clear empties the cache. Kivy `main.py --self-test` passed with isolated app/Kivy/pack/evidence directories and networking disabled; `result.json` reports 24 checks, including the new assertion. No physical input, OS clipboard use, real pack deletion, or network call.

Full suite: `150 passed, 2 skipped, 200 subtests`; Ruff check/format, compileall, `pip check`, and release-safety scan pass. ACTIVE: commit and re-screen remaining READY tasks. BLOCKED: fluent Somali review, Old Nubian rights/specialist review, Narrator/NVDA, external clipboard VM, hosted workflow approval, clean-host signing/packaging, and full M2M100 evaluation on faster hardware. Owner status/audit edits untouched; no push.

## Latest continuation — cache release after pack removal (2026-10-25)

**Goal status: ACTIVE — NOT FINISHED.** User explicitly asked to register the prior stopping point as unfinished and continue. The pack-removal memory-retention fix is complete locally at `3d2f694633a56aaaa13b7eebc7325f7bbe789292` (`fix: release models after pack removal`). Successful deletion clears the translation-engine LRU; failed deletion preserves it. Acceptance covers both paths and privacy-safe user feedback.

Verification: full suite `150 passed, 2 skipped, 200 subtests`; Ruff, format (115 files), compileall, `pip check`, release-safety scan and isolated Kivy self-test (`24` checks, networking blocked) pass. Owner edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` remain untouched and unstaged. No push, mouse/keyboard control, host clipboard use, real pack deletion, or network inference occurred.

Backlog re-audit found no additional safe, evidence-backed product implementation READY without external review, permission, isolated VM/device, or host approval. Keep those tasks BLOCKED with their resolution actions in `docs/IMPLEMENTATION_PROGRESS.md`; revisit the backlog when new evidence/resources arrive. Compact-layout desktop FBO captures are fixed and visually reviewed at five viewports; physical-device behavior remains unverified. Do not mark the mission complete or push.

## Fresh benchmark and next cache-lifecycle fix (2026-10-25)

Re-downloaded Somali pack `1-bfd6cf52bd69` into isolated temporary storage. All 10 installed receipt assets matched their recorded sizes and SHA-256. Installed payload size was 314,460,806 bytes; manifest download size was 314,460,609 bytes because its generated 197-byte config is created locally. Ran the full TICO-19 150-pair benchmark with `socket.socket.connect` blocked during inference and results/checkpoint outside the repository. Fixture SHA-256 `be58b2d350badb7e03b73906471453311a8843534e4a2a572a772c60c394c7f7`; EN→SO BLEU/chrF++ `5.287/25.282`; SO→EN `6.300/24.680`; candidate 97/150, fallback 53 (47 unreadable markers, six output length); 135.21 seconds, peak RSS 548,720,640 bytes. This is reproducibility only and does not validate Somali quality.

Implemented next fix: successful pack install/update clears loaded model engines; failed download leaves the cache alone. This prevents unused engines staying resident after an update. Live Kivy self-test passed all 24 checks including install success/failure cache behavior. Full suite is green (`150 passed, 2 skipped, 200 subtests`); Ruff, formatting, compileall, `pip check`, release-safety and diff checks pass. Committed locally as `2b42cef90dd1eeb7f2c267380d73814ce9a88fe2` (`fix: clear cached models after pack install`). Rechecked the backlog; no independent evidence-backed task is READY without external rights/review, permissions, VM/device or host approval. Obsidian handoff is updated. Goal remains active and unfinished; do not push.

## 2026-10-25 — Bound saved-history file handling

Source review found that `History.read()` decoded and parsed the entire file without a size bound. A malformed or externally enlarged local history could consume excessive memory and block the UI. Added a 16 MiB ceiling: reads consume at most limit + 1 byte, oversized files are reported as damaged without modification, and oversized saves are rejected before replacing the prior history. `backup_and_reset()` now streams the original file to an exclusive backup in 1 MiB chunks before atomic reset, preserving even oversized user data without loading it all into memory.

Regressions verify bounded read (with `Path.read_bytes` disabled), exact oversized backup/reset, and rejection of oversized saves with no change to the prior file or temporary-file residue. Full suite: `153 passed, 2 skipped, 200 subtests`; Ruff, format (115 files), compileall, `pip check`, release-safety and diff checks pass. Local code commit `2b5d9fa9bfca97cf8c9c8fdfdf5d3ea96fb4040f` (`fix: bound saved history reads`). No push. Existing owner edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` remain unstaged and untouched.

The development goal remains ACTIVE — NOT FINISHED. Re-screen the remaining READY queue next; specialist language review, rights, Narrator/NVDA, disposable VM/device validation, hosted-workflow approval and signed clean-host packaging remain external blockers.

## 2026-10-25 — Validate saved-history writes and screen a Somali model candidate

`History.save()` used to accept invalid field types, write them to disk, then make the next `read()` classify the file as damaged. It now checks each entry against the reader schema before any I/O; invalid values leave existing history bytes unchanged. Focused tests: 13 passed, 12 subtests. Full suite: `154 passed, 2 skipped, 206 subtests`; Ruff, format (115 files), compileall, `pip check`, release-safety and diff checks pass. Local code commit `9789f025d9a13922608e26e42c3d25f26bebfa9b` (`fix: reject invalid saved history entries`).

Model scan found a potentially relevant 243 MB English→Somali Marian candidate at a pinned Hugging Face revision. Its card declares Apache-2.0 and reports BLEU 11.60 / chrF 45.87 on FLORES-200 devtest and 7.45 / 33.07 on TICO-19 test; these scores are not independently reproduced and the candidate has already been evaluated on the Saylacian TICO test set. The same card identifies a Helsinki CC-BY-4.0 base and training on 14 datasets (including NLLB, CCAligned, CCMatrix and TED2020). Training-data reuse terms need audit, and this environment lacks Torch/Transformers for conversion to Saylacian's CTranslate2 runtime. Recorded as BLOCKED; do not integrate/download into a pack until provenance, licensing and unbiased evaluation path are established.

Goal remains ACTIVE — NOT FINISHED. No push. Owner edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` remain unstaged and untouched. Progress board: `docs/IMPLEMENTATION_PROGRESS.md`.

## 2026-10-25 — Compact portrait layout usability

The goal remains ACTIVE and unfinished; previous stopping point is recorded as NOT FINISHED. Re-screening revealed a 320 dp wide, 500 dp high window was treated as landscape solely because it was short. Two translation panels became too narrow. Updated the breakpoint: side-by-side panels require 760 dp width, or at least 480 dp width when height is 520 dp or less. At narrow compact height, source/swap/target controls use one row with tighter spacing and a smaller swap button, reclaiming space for both text panels. The viewport harness now asserts both text widgets remain at least 56 dp high at 320×500.

Added live viewport checks and a rendered 320×500 screenshot. Kivy capture visibly shows input and output panels and all language controls. Live UI acceptance passed with network blocked and in-memory clipboard. Full suite: `154 passed, 2 skipped, 206 subtests`; Ruff, format (115 files), compileall, `pip check`, release-safety and `git diff --check` pass. Screenshot/evidence is in the temp folder printed by `tools/check_ui.py`; it is not added to the source tree.

Changed files: `main.py`, `app/main.kv`, `app/acceptance.py`, `tools/check_ui.py`, and the handoff/progress board. Code commit `05d5608753c08980502f16fa352e76b5d074af8b` (`fix: keep compact portrait usable`) contains the four implementation/test files and `docs/IMPLEMENTATION_PROGRESS.md`; this handoff follow-up records the final commit and is committed separately. Existing owner changes in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` remain untouched and unstaged. Goal stays ACTIVE — NOT FINISHED. Remaining blockers/actions remain in the progress board: human Somali review; Old Nubian reuse permission and specialist review; manual Narrator/NVDA; external clipboard in disposable VM; hosted workflow approval; clean-host Windows signing/package; independent language-ID judgements; complete M2M100 evaluation on faster hardware; and candidate model data/runtime audit. No push or publication.

Acceptance hardening commit `5d8ee03b227cd7fb5a1913e1b36625c83db8f082` adds a live Kivy assertion that input and output fields each retain at least 56 dp height at 320×500. The UI suite was rerun successfully with the assertion; the repository suite remains `154 passed, 2 skipped, 206 subtests`, and Ruff/format, compileall, `pip check`, release-safety and diff checks pass. Goal remains ACTIVE — NOT FINISHED.

## 2026-10-25 — Bound optional online-provider responses

Source review found both optional online translation clients used unbounded `response.read()` and assumed the JSON root was an object. Responses now read at most 1 MiB + 1 byte and reject larger bodies with a recoverable `ValueError`. Non-object JSON roots are converted to each provider's safe invalid-response error rather than leaking `AttributeError` through the Kivy worker callback. Tests assert bounded reads and malformed-root recovery for Cloudflare and self-hosted clients. No request payload, credential, provider choice, or offline behavior changed.

Focused online-provider tests pass; full suite: `155 passed, 2 skipped, 208 subtests`. Ruff check/format, compileall, `pip check`, release-safety and `git diff --check` pass. Offline Kivy viewport acceptance from the prior milestone remains valid; no real network request or credential was used. Local code commit `93aa1484ed63f21b8074e598973555a0a63a8876` (`fix: bound online translation responses`); no push. Goal stays ACTIVE — NOT FINISHED.

Final live Kivy acceptance against this code passed 19 checks with network connections blocked and clipboard replaced in memory. Six FBO viewports passed, including 320×500 dp; I visually reviewed the compact screenshot at `%TEMP%\saylacian-ui-final-20261025\previews\enhanced-compact-portrait.png`. Full source re-screen found no additional safe, evidence-backed READY code task. Keep the goal ACTIVE and NOT FINISHED; exact unresolved external actions remain in `docs/IMPLEMENTATION_PROGRESS.md`. Owner edits remain unstaged; no push.
# 2026-10-25 continuation — self-hosted service memory failure

Current source adds a safe HTTP 503 response if local inference raises `MemoryError` in `cloud/oci/service.py`. The generic response avoids exposing exception details. The client already converts 503 into a retryable busy error; test verifies this end to end against an ephemeral loopback HTTP server, and verifies all translation semaphore slots are released after failure. Unauthorized requests are also checked not to invoke translation.

Validation: `157 passed, 2 skipped, 208 subtests`; Ruff check and format, compileall, `pip check`, and `git diff --check` passed. No external network, system clipboard, or UI was used for this service-only change. Owner changes in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` remain untouched. Goal remains ACTIVE — NOT FINISHED; see `docs/IMPLEMENTATION_PROGRESS.md` for blockers and next queue state. Keep changes local; no push or publication.

## 2026-10-25 continuation — idle service client timeout

Latest service code commit: `889dfc1ff15d6362d883c8963f87a6ba39092e59`. Each accepted connection now has a 15-second inactivity timeout so idle clients cannot occupy the bounded request workers indefinitely. The loopback test confirms socket closure and return of all request slots. The prior `MemoryError` → HTTP 503 behavior remains covered end-to-end; its semaphore test now waits for handler cleanup to avoid a scheduling race. Full suite: `158 passed, 2 skipped, 208 subtests`; Ruff, format, compileall, dependency, release-safety and diff checks passed. No external connections or OS clipboard access. Goal stays ACTIVE — NOT FINISHED; preserve existing owner edits and do not push.

## 2026-10-25 continuation — malformed nested request recovery

Latest service code commit: `d4c406e516dc056d2c38a090a110b2c598a88a0c`. A well-formed but deeply nested JSON array under the 20,000-byte body cap raised `RecursionError`; the API now returns HTTP 400, with a loopback test proving inference is not invoked. Full suite: `159 passed, 2 skipped, 208 subtests`; Ruff, format, compileall, dependency, release-safety and diff checks passed. Existing owner changes remain untouched; keep all work local and unpublished.

## 2026-10-25 continuation — fresh Somali benchmark

Latest pinned TICO-19 baseline rerun used current source `d4c406e516dc056d2c38a090a110b2c598a88a0c`. Before inference, the isolated Somali pack `1-bfd6cf52bd69` passed SHA-256 and byte-count checks for all 10 assets (314,460,806 bytes). The 150-pair fixture hash remained `be58b2d350badb7e03b73906471453311a8843534e4a2a572a772c60c394c7f7`; benchmark code blocked socket connects during inference and saved predictions/checkpoint under `%TEMP%\Saylacian-fresh-bench-...`, outside Git.

Reproduced EN→SO BLEU/chrF++ 5.287/25.282; SO→EN 6.300/24.680. Candidate accepted 97/150, fallback 53 (47 unreadable marker, 6 output length). Runtime 129.12 s; peak working set 548,409,344 bytes. These automatic scores do not validate Somali quality. No new READY task appeared; keep goal active and consult progress board for blocker actions. No push.
## 2026-10-25 continuation — translation segmentation and detection input quality

Validated the existing model-aware long-input chunking and added the missing direct regression for bounded chunks plus exact preserved whitespace. Existing unbroken 400-token-limit tests still pass. Automatic detection now requires at least five alphabetic characters in addition to its 12-character/three-word minimum and abstains before model initialization on punctuation-only input. Re-ran the pinned 15-export Tatoeba evaluator from `%TEMP%\saylacian-language-id-expanded-20261024`; 403,820 rows qualified. At 0.80 it reported 456 development supported/source-label matches and 6 disagreements, and 106/0 on deterministic holdout; at 0.85 it reported 346/4 development and 86/0 holdout. No threshold change: labels are noisy community source tags, not adjudicated ground truth.

Full suite after these changes: `165 passed, 2 skipped, 208 subtests`. Focused Ruff check/format and compileall pass. `docs/TRANSLATION_FEASIBILITY.md` was reconciled with the already documented AfriSLM benchmark (automatic metrics higher than the shipped route, but not human-rated and not integrated due to separate GGUF runtime/device and training-data licensing considerations). Preserve existing user changes, especially `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md`; no push. Next: continue investigating evidence-backed optional Somali model integration and obtain independent short-language-ID review data; do not make accuracy claims from Tatoeba tags alone. Goal remains ACTIVE and NOT FINISHED.

Additional real offline inference check: the installed EN→FR model translated a 405-token generated input while socket connections were blocked. It returned non-empty output and the chunk-context warning; direct code-point checks found `côté` intact and no U+FFFD. This confirms the new multi-batch path runs through the real CTranslate2 model, not just the helper fake. The synthetic repeated text is plumbing evidence, not a quality benchmark.

Local verified code/test/docs commit: `bfa92ae45d5754cbdec2d9e50b4ef99d783fb6c9` (`Improve translation input handling`). No push. Preserve the remaining modified and untracked files; they were not included in this commit.

## 2026-10-25 — optional AfriSLM Somali model

Current local code commit: `8a3a264` (`feat: add optional Somali AfriSLM pack`), exactly six paths: pinned 641 MiB model manifest, optional `llama-cpp-python==0.3.36` CPU runtime file, pack manager, translator, and regressions. Separate opt-in pack is preferred for English↔Somali only when downloaded and runtime is installed; otherwise existing offline route stays available. Verified upstream/local byte count and SHA-256, then exercised the real installer in isolated temporary storage and ran actual model inference both directions with network blocked. Example: `Waan ku jeclahay.` → `I love you`; English greeting output was mixed English/Somali, illustrating quality limits. Every candidate output warns that fluent review is needed. Model weights are Apache-2.0; CC-BY-NC-4.0 training data is not included. Do not infer user-facing accuracy from one domain-limited 150-pair test sample.

Checks after feature: full test suite `169 passed, 2 skipped, 208 subtests`; Ruff, formatting, compileall, `pip check`, and `git diff --check` pass. Isolated live Kivy acceptance did not finish: it stopped on the existing Old Nubian reader `read_button.width >= dp(72)` assertion. No UI-wide success claim. The paired separate TICO dev comparison is complete and recorded below; keep detector thresholds fixed until independently adjudicated short examples exist. User's other dirty files (including `main.py`, session persistence, Old Nubian changes, UI guide/docs, and owner edits in `docs/PROJECT_STATUS.md`/`docs/TECHNICAL_AUDIT.md`) remain uncommitted and must be preserved. No push or publication.

## 2026-10-25 — paired TICO-19 dev comparison completed

Official TICO-19 archive downloaded to temp and hash-verified (`0e82fc7ceaa877606c8934f32ead185716c9d2c54b3818f2a7ae655f5e7a08d8`); dev split has 971 EN-SO pairs. Deterministic length-stratified sample selected 150 pairs and evaluated both directions against the standard offline pack, same examples, socket connections blocked. AfriSLM BLEU/chrF++: EN→SO `5.634/25.730`; SO→EN `9.538/28.103`. Standard route: EN→SO `5.184/24.314`; SO→EN `4.407/21.213`. AfriSLM mean latency `1651/1110 ms`; standard `755/288 ms`. Detailed outputs and sample IDs: `%TEMP%\saylacian-afrislm-dev-eval-20261025\paired-afrislm-vs-baseline-dev-150.json`. Results favor AfriSLM on this small dev sample but remain automatic, single-reference, medical-domain; do not tune from this or infer broad quality. `docs/SOMALI_TRANSLATION_QUALITY.md` records provenance and limitations. Added tested evaluator `tools/benchmark_somali_dev.py`, commits `b0590a7` and `8ae0d99`. Four unit tests pass. It pins archive/model/runtime versions, verifies the standard pack, stores checkpoint and output outside Git, and its real 150-pair CLI run reproduced these metrics exactly in both directions. Full suite `173 passed, 2 skipped, 208 subtests`; Ruff, formatting, compileall, dependency and diff checks pass. Next: screen pinned Maanka2 EN→SO candidate snapshot and training-data provenance before adapting evaluator; do not distribute until terms are clear. Somali detection remains blocked on independently judged short examples; no thresholds changed.

## 2026-10-25 continuation — direction-specific Somali packs

Local change adds a 1.56 GB optional AfriSLM 2B Q4 pack, pinned at upstream revision `9bcceade...` and SHA-256 `fc2a80532e58e0655efd9e68c5b7cb2c4373222e736bcc88de648502a4e30361`. The model uses the existing `llama-cpp-python==0.3.36` optional CPU runtime. Model card declares Apache-2.0 weights; its synthetic training mix is CC-BY-NC-4.0 and is not included.

On 60 deterministically sampled FLORES-200 devtest pairs, metrics were EN→SO: 0.8B `12.001/41.925`, 2B `10.198/39.758`, standard `6.939/39.903` BLEU/chrF++; SO→EN: 0.8B `22.507/45.797`, 2B `28.594/51.662`, standard `10.106/32.321`. CPU latency averaged `1436/2746 ms` EN→SO and `904/1683 ms` SO→EN for 0.8B/2B. Keep 0.8B for EN→SO; use 2B only as optional first route for SO→EN, then fall back to the smaller installed model. This is preliminary automatic evidence, not fluent quality review.

Actual offline app-route smoke passed: `Waan ku jeclahay.` → `I love you`, with socket connects blocked. Full suite `176 passed, 2 skipped, 208 subtests`; Ruff, format, compileall, `pip check`, and diff checks pass. The attempt to copy the full 1.56 GB file through the pack installer was cut off by the runner at staging (`0x40010004`); generic installer integrity tests remain strict, but this exact asset's complete install was not verified. Preserve the staged temp evidence; do not put model weights or benchmark predictions in Git.

ACTIVE next: make the FLORES comparison reproducible in a repository benchmark tool and seek a separate licensed benchmark before any more model switching. BLOCKED: independent fluent Somali review; independently adjudicated language-ID examples; rights/specialist review for Old Nubian. READY: screen another open Somali model and any legally accessible benchmark. Preserve all unrelated dirty edits and keep the goal ACTIVE. No push.


## 2026-10-25 — latest detector/model evaluation

Latest detector checkpoint screened Lingua 2.2.0 outside the repository. It adds a 170.1 MB Windows wheel. On 2,585 eligible hash-pinned short Tatoeba rows, current py3langid at ≥0.75 matched 148/443 English/French/Somali source labels with 0/2,142 unsupported rows routed as supported. Lingua at ≥0.75 matched 121/443 with 0/2,142 unsupported routes; ≥0.70 also matched 121/443. These are noisy source-label agreement counts, not verified accuracy. Keep py3langid and 0.75 threshold. No dependency or production code change. CLD3 is not a practical immediate replacement: upstream code is archived and its old gcld3 release has no CPython 3.12 Windows wheel.

Next ACTIVE/READY: evaluate another light Somali translation candidate against the existing pinned held-out dev samples and check rights before any distribution. Maanka2's referenced training corpus page was not accessible without authorization in this session, so its training-data reuse terms remain unverified; do not bundle or route it into the app unless those terms are resolved. BLOCKED: independently adjudicated short-text LID labels, fluent Somali reviewer, and Old Nubian rights/specialist review. Preserve user edits; no push.


Current validation: `176 passed, 2 skipped, 208 subtests`; Ruff and format check pass, compileall and `pip check` pass, `git diff --check` passes. Lingua candidate rejected for app integration: on same 2,585 hash-pinned Tatoeba short rows, Lingua with ≥0.75 confidence matched 121/443 supported source labels vs current py3langid's 148/443; both had zero supported predictions in 2,142 unsupported rows. These are label-agreement data only. Maanka2 model is 124 MB and declares Apache-2.0 but has no reported metrics; its linked training dataset endpoint returned HTTP 401, leaving data-use terms unknown. No production changes made. User's dirty tree preserved.



## Latest milestone — optional AfriSLM 4B route

New model manifest pins QVAC AfriSLM 4B Q4 (revision `82df4b20772a4a46f38b421a569a90d53a93f657`, 3,066,385,344 bytes, SHA-256 `166226feb6144f6e416e4936706eb5f9183526a05141410156c578c48b4bd4f1`). It loaded through llama-cpp-python 0.3.36 and Saylacian's application translation helper. In a fresh 30-pair FLORES-200 devtest sample excluding the earlier 60 sample: EN→SO 4B 10.360/40.896 BLEU/chrF++ vs 0.8B 11.312/42.019; SO→EN 4B 36.660/58.507 vs 2B 30.074/52.851 and 0.8B 29.289/52.050. 4B averaged 6.10s / 4.32s per input on CPU and used about 5GB working set on this 32GB Windows machine. A separate TICO test comparison is exploratory and was not used for route selection because the 4B training notes mention TICO dev.

Routing change: optional 3.07GB 4B pack is tried first only for Somali→English, then 2B, 0.8B, and standard offline; English→Somali remains on 0.8B. The pack manager surfaces its memory/storage size and training-data terms. Weights declare Apache-2.0; CC-BY-NC-4.0 and ODC-By-1.0 training sources are not included. Targeted tests: `44 passed, 2 skipped, 8 subtests`. Next: full checks and isolated installer test; keep all pre-existing dirty UI/Nubian/docs untouched when staging/committing. No push.

Follow-up: complete 4B pack install/integrity verification passed through `ModelPackManager` in isolated temp storage, using the existing hash-verified 3.07GB artifact as the response stream (no new network transfer). Installed manifest/version and active-root discovery verified; final progress reached full bytes. Also added tested fallback for native `llama-cpp-python` `RuntimeError`/`OSError`; local installed runtime source confirms `RuntimeError` on native decode failure. Focused tests: `45 passed, 2 skipped, 8 subtests`. Full suite: `179 passed, 2 skipped, 208 subtests`; Ruff, format (`123 files`), compileall, `pip check`, release-safety scan and diff checks passed. Commit `6b90dc6` contains only 4B pack/routing/fallback, tests, manifest and candidate note. Goal remains active; next evidence-backed work needs an independently licensed benchmark or fluent Somali review rather than weakening detector thresholds on noisy labels. Preserve all other user changes; no push.

## 2026-10-25 — MASSIVE split validation and fastText candidate

Official Amazon MASSIVE 1.1 archive downloaded to `%TEMP%`, 40,251,390 bytes, expected SHA-256 verified. Short-gate sample: 8,268 dev and 11,386 test rows across 51 locale files (max 500/locale); Somali is not present. Evaluator now accepts `--partition dev|test`, default test; thresholds can be selected on dev and checked on held-out test. Synthetic tests exercise dev/test separation and reject train.

At production short threshold 0.75, py3langid yielded 89/311 supported English/French dev labels and 1 false-supported among 7,957 unsupported labels; test yielded 142/451 supported labels and 0 false-supported among 10,935 unsupported labels. Source locale is a proxy label, not per-utterance expert adjudication; no threshold was changed.

Screened fast-langdetect 1.1.0 externally: fastText lite (917 KB) had 74 false-supported test rows at threshold .75 and 25 at .95. Full 125 MB model had 10 at .98 and 1 at .999; coverage was lower than py3langid's 142 correct at .75. Candidate rejected, no app dependency added. Official fastText model weights are CC-BY-SA-3.0 (https://fasttext.cc/docs/en/language-identification.html). Next: keep detector conservative; look for independent Somali test labels or a newer licensed detector with held-out evidence. Keep unrelated dirty changes untouched; no push.

## 2026-10-25 — CUS-to-English OPUS candidate

Tested `Helsinki-NLP/opus-mt-cus-en` through pinned conversion `ooeoeo/opus-mt-cus-en-ct2-float16` (revisions recorded in `docs/SOMALI_MODEL_CANDIDATES.md`). Actual app route smoke passed; full fresh 30-pair FLORES devtest inference ran offline with network socket connections blocked and exact English reference alignment checked. Candidate SO→EN BLEU/chrF++ `3.767/23.166`; same-sample standard `13.163/35.254`; AfriSLM 4B `36.660/58.507`. CPU latency 251 ms. Reject route; no production model change. Temp model/predictions outside Git. Candidate assessment doc updated. Keep active goal, no push.


## 2026-10-25 — Short-text detector threshold and MADLAD candidate

Set the short-text confidence threshold to 0.70. Pinned MASSIVE locale-label agreement for English/French rises from 89/311 to 101/311 on dev and 142/451 to 168/451 on test. All four extra English/French predictions at 0.70 in other locale files were inspected and were English phrases; locale filename is only a proxy, not utterance truth. The pinned Qor sample has 67 Somali short sentences; at 0.70, 37 are classified Somali and one is classified as unsupported Oromo (the app returns no selectable language); at 0.75, 33 are classified Somali and none as another language. Treat these limited samples as detection-share evidence only, not accuracy claims. Somali short text now has a regression boundary at 0.70.

Screened Google MADLAD-400 3B via CTranslate2 conversion revision `c32ad0cf118807ea6258d14be137547155842723`; model hash `f3c87256a2c888100c179d7dcd7f41df17c767469546c59d32c7dde86c740a6b`. On 30 deterministic length-stratified TICO-19 test pairs EN→SO: installed route `3.271 BLEU / 22.200 chrF++`, MADLAD `2.779 / 25.097`; candidate CPU mean `10.507 s`, max `33.61 s`. Do not add or route it from this evidence. A Google-hosted 1.65 GB Q4 GGUF did not load in pinned `llama-cpp-python 0.3.36` (tensor name length limit); the CTranslate2 candidate loaded. Model details and source links in `docs/SOMALI_MODEL_CANDIDATES.md`; weights/raw predictions remain in `%TEMP%`.

No push. The goal stays active. Next: find other rights-clear Somali benchmarks/models and seek independently labeled language-identification examples; continue measurable, low-risk work meanwhile.

Verification after the final detector change: `181 passed, 2 skipped, 208 subtests`; detector tests `9 passed, 7 subtests`; Ruff, format check (123 files), compileall, `pip check` and diff check all pass. Local commit `8b7d025a51e7ce72229fd87c9fd34d7dd83b854e` contains only the detector/test/model-candidate milestone. Pre-existing dirty UI, Nubian, README and other documentation files remain uncommitted. No push.


## 2026-10-25 — M2M100 candidate and very-short-input review

Screened the pinned MIT M2M100 418M CTranslate2 model on 30 deterministic, length-stratified pairs from the TICO-19 English→Somali dev split (`20261025` seed; archive SHA-256 `0e82fc7ceaa877606c8934f32ead185716c9d2c54b3818f2a7ae655f5e7a08d8`). `model.bin` verified at 490,667,752 bytes and SHA-256 `a1826980fc5c037e69c7ac94fcb56c03001a66f380eb71863cc0a3879e71421b`; network connections were blocked during inference. Saylacian's installed route scored BLEU/chrF++ `3.539/20.980`. M2M100 with trigram blocking scored `1.608/12.272` (1.923 s mean, 4.41 s max); with default n-gram repetition it scored `0.142/7.171` (2.950 s mean, 7.65 s max). Reject for app routing; no 150-pair run or route change is justified from this dev result. Raw predictions/model remain in `%TEMP%`. Model card and exact revision/decision are linked in `docs/SOMALI_MODEL_CANDIDATES.md`.

Checked shorter auto-detection inputs against the same 15 SHA-pinned Tatoeba exports: 139,987 rows with 4–11 characters and one/two words produced only three supported-language predictions at confidence `0.70`, all matching their source locale label; those labels are not adjudicated truth. There were 109 English, 8 French and 4 Somali rows in this subset. The verified Qor Somali corpus contains no eligible 4–11-character, one/two-word entries. Keep the existing minimum input gate; this sparse evidence does not support reliable short-phrase routing. Current threshold remains `0.70` for the existing 12–19-character/three-word case.

Queues updated in `docs/IMPLEMENTATION_PROGRESS.md`: M2M100 moved to completed candidate screen, Maanka2 moved to BLOCKED pending accessible dataset provenance/terms, and the next ACTIVE task is finding another rights-clear candidate. Goal remains active; no source changes or push in this milestone.

## 2026-10-25 — Somali prompt and language-detection recheck

Discarded an earlier AfriSLM prompt screen because its slices overlapped. Reran with 60 unique, length-balanced TICO-19 dev examples excluded from prior prompt experiments, using the exact current app prompt against a concise Somali-Latin instruction. The first 30 were mixed (BLEU/chrF++ old `7.134/24.532`, concise `7.003/24.023`); next 30 also mixed (old `2.581/22.526`, concise `3.366/23.392`), with latency moving opposite directions across groups. No prompt/source code changes. Raw outputs stay in `%TEMP%\saylacian-afrislm-prompt-disjoint-20261025.json`.

Held-out MASSIVE long-input screen: 24,592 rows across 52 locale files, selected at most 500 per locale, 20–500 chars/four-plus words. At threshold .70, 881/1,000 English/French source-locale matches and 12 supported predictions from other locale files; at .75, 854 matches and 8 other-locale supported predictions. Labels are proxies, not adjudicated utterance truth; threshold unchanged. Archive hash `4cba5faa11c71437928e17cb1b9b3d8b8e727e7ea363a3a9a8045e19c0491577`.

New candidate evidence: Sunflower-Qwen3.5-9B has promising published Somali metrics but its 7.9 GB 4-bit checkpoint needs a compatible runtime/GPU; current 8 GB GPU and `llama-cpp-python 0.3.36` environment has no Transformers/PyTorch. Sunflower-Gemma4-E2B is gated with contact-sharing conditions and 10.2 GB BF16 weights; do not request access without owner direction. Somast's `som-en-mt` is listed in docs, but no downloadable translation repo appears in its public Hugging Face listing. GooboLabs `SomNLP-Translate` is only M1, with data downloaders planned. Details/URLs recorded in `docs/SOMALI_MODEL_CANDIDATES.md`.

No app code changed; no test rerun in this research-only milestone. Next ACTIVE: screen a rights-clear Somali model that runs in current or practical optional local runtime. BLOCKED: human Somali review and independently adjudicated detection labels; Sunflower runtime/host; gated model access choice; Somast release. Preserve pre-existing owner edits and keep goal ACTIVE. No push.

## 2026-10-25 continuation — optional-model fallback guard

Local working change applies existing candidate-output validation to optional AfriSLM. Degenerate outputs now fall back to the standard offline model with a visible warning; normal output and model ordering are unchanged. Regression test passes. A compact Windy EN→SO model was rejected on a 60-example TICO dev screen because both BLEU and chrF++ were lower despite improved CPU latency; training-corpus provenance is also missing. Focused translation tests: 33 passed. Full suite: 182 passed, 2 skipped, 208 subtests; Ruff, format, compileall, `pip check`, and diff checks pass. Preserve all other uncommitted user edits. No push.

## 2026-10-25 — detector margin and Somali-specific candidate screen

No detector change: adding a minimum top-1/top-2 score margin from 0.00 through 0.40 did not alter results on the sampled 5,937 short Tatoeba rows or 67 verified Qor Somali rows; current Somali detection share remained 37/67. These are source-label/source-only observations, not accuracy or independent review.

Rechecked the 131,266,198-byte FastText `lid.176.bin` candidate on the same data. On Qor it labeled only 1/67 Somali rows as Somali at confidence 0.70, 1/67 at 0.90, and none at 0.95+. On the separate hash-ranked 5,937-row Tatoeba sample, it showed more English/French label matches at moderate thresholds but also false-supported unsupported labels; at 0.98 it had fewer supported matches than the existing detector on the held-out subset. Reject for app integration. OpenLID-v3 officially includes Somali but its checkpoint is 1.23 GB and GPL-3.0; the paper notes Somali was itself highly confused with other languages. Keep as a possible isolated evaluation only after assessing the large download and source-data terms; do not route or redistribute on published claims alone.
## 2026-10-30 handoff — Windows source release campaign

**Checkout:** the authoritative Saylacian repository, branch `main`. Public `origin/main` was read-only checked at `c4f2f87270c22a05e772816ce98e57a99b871b18`; local `main` was `527df1569da68a5dadb758eafd9f0693aff983db`, 112 commits ahead. The active campaign edits remain uncommitted at this handoff point. Do not push or publish without approval. A separate `Saylacian-user-only` clone is divergent; do not use it.

**Completed this session:** aligned active Old Nubian mapping with the 29 entries in van Gerven Oei 2024 Table 1 (CC BY 4.0); removed the older DBMNT mapping source and retained warned v1 interchange imports; updated current user-facing copy to alpha-testing language; bounded/validated atomic local session restore; added a pinned Windows portable ZIP recipe and narrowed PyInstaller data collection; fixed packaging of the legacy Osmanya font path; added strict packaging regressions; added CI test and manual artifact-build jobs. Existing approved UI remains in place.

**Verification:** `pytest -q` → `194 passed, 2 skipped, 191 subtests`; Ruff lint/format, compilation, `pip check`, release-safety and whitespace checks passed. Kivy app self-test passed in a temp profile. Headless Edge website check passed eight API/conversion/clipboard-double/responsive checks. PyInstaller successfully generated and verified a 70 MB ZIP with 616 manifest files and no model weights; artifact runtime is explicitly unverified. Do not run the unsigned executable on the owner's host. `main.py --self-test` used a temporary APPDATA/LOCALAPPDATA/Kivy directory. No OS clipboard was touched.

**ACTIVE:** after committing the intended local code/doc changes, clone that commit to a unique temp directory; create a fresh venv; install `requirements-dev.txt`; rerun tests/self-test; download French and Somali packs under temporary LOCALAPPDATA; block network during inference. Rebuild the final ZIP from the clean committed tree and verify its manifest/hash.

**BLOCKED:** use a disposable Windows VM with clipboard sharing disabled to test Saylacian Text, image and Latin pastes in an external app; test keyboard/screen-reader behavior with Narrator/NVDA; obtain fluent Somali and Old Nubian specialist review. The Obsidian vault was not found in the top-level Documents/OneDrive directories checked; these repository progress/handoff files remain the active knowledge base.

**READY:** inspect CI YAML and local links, rerun checks after the clean clone, commit verified follow-up locally. No push, release, tag or Store submission.

## 2026-10-30 continuation — clean clone passed

The current code commit is `bab24a31b699c53601c6bfe780ede6bb7f43fbcb`; public GitHub remains unchanged. The commit was cloned locally into a clean source directory, installed into a fresh venv from `requirements-dev.txt`, and tested there. Results: 185 passed, 11 skipped, 191 subtests. Skips were model-dependent before pack installation. Ruff check/format, compileall, `pip check`, release-safety scan and clean Git status passed. The Kivy source-app self-test passed with a temporary profile.

The fresh clone downloaded the pinned French and Somali packs to a separate temporary data directory. Their SHA-256 asset checks and version receipts passed; both directions per pack returned output with socket connects blocked during inference. Sample Somali outputs demonstrate quality limits; fluency is not claimed. The initial portable candidate was superseded by these source/docs updates and must be rebuilt from the final commit.

**ACTIVE:** run final checks, build final portable ZIP from the committed tree, verify all payload hashes and version metadata, and record the artifact SHA-256. **BLOCKED:** clean-host binary launch (unsigned), real clipboard tests in a disposable VM, Narrator/NVDA observation, fluent Somali review and Old Nubian specialist review. **READY:** validate the manual CI artifact job, then stop at the explicit push gate. No push, tag or release.

## 2026-10-30 handoff — clean source and portable build

Latest code commit: `eebe9e9cb927d3e0cc834ee4ed689399798187bb`. Local `main` was 115 commits ahead of `origin/main`; public `main` was last read-only verified at `c4f2f87270c22a05e772816ce98e57a99b871b18`. No push, tag, release or setting change occurred. Preserve the existing unstaged `docs/TECHNICAL_AUDIT.md` edit; it was intentionally excluded from local commits.

Clean clone tests: 186 passed, 11 skipped, 191 subtests. The fresh clone installed `requirements-dev.txt`, launched the source Kivy app's `--self-test`, passed Ruff/format/compile/pip/release-safety gates, and had a clean git status. French and Somali packs were installed with SHA-256/version checks in isolated temporary storage and both directions per pack returned non-empty output with socket connections blocked during inference. Somali output examples still show semantic errors; no fluency claim is made.

Portable build recipe and pinned build lock are committed. `eebe9e9` produced a clean-tree candidate through an invocation from outside the source directory. It contained 607 manifest files; candidate size 68,453,261 bytes; SHA-256 `3cde0801f06fcca55846e65cb1bb71357d9032cc8dbd6086f6bb0d6ff0c30b01`; app version `0.1.0a1`; manifest `runtime_verified=false`, source tree clean. ZIP and manifest checks passed; no weights or Poppler files. Rebuild from the next documentation commit so the final manifest points to the final local source revision. Do not launch the unsigned EXE on the owner's Windows host.

A privacy-safe history scan covered 122 main commits and 732 unique text blobs for recognized credential strings and local Windows profile paths; no match. Website headless Edge checks passed eight API/conversion/clipboard-double/layout checks. Kivy source self-test passed. No external clipboard was accessed.

**ACTIVE:** finish the progress/handoff record, commit that docs-only update, rebuild and verify the portable ZIP from a clean clone of the latest commit, then run final source quality checks.

**BLOCKED:** unsigned package launch/installation on clean Windows requires an isolated host; actual Saylacian Text/image/Latin clipboard verification and Narrator/NVDA require a disposable VM and screen-reader; Somali translation needs a fluent-speaker review; Old Nubian table expansion needs specialist review. Native dependency/binary distribution terms remain separate from source licensing. Obsidian vault was not located in the top-level Documents/OneDrive folders checked; repo docs are the active handoff.

**READY:** after the clean artifact rebuild, confirm final workflow config and checksum. Stop before push, public release, Store submission or account-setting changes.
