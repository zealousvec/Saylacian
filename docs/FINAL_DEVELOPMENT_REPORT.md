# Saylacian final development report

**Date:** 2026-10-25
**Status:** COMPLETE WITH DOCUMENTED EXTERNAL BLOCKERS
**Release readiness:** READY FOR OWNER REVIEW — EXPERIMENTAL SOURCE ALPHA

## 1. Executive summary

Saylacian is an offline-first Python/Kivy application with English/French offline meaning translation when the relevant language packs are installed, experimental Somali translation, script conversion tools for Somali/Osmanya and partial chart-derived Borama/Kaddare, and a limited Old Nubian reading/transliteration studio. The app includes model-pack management, saved translation history, tagged Saylacian Text interchange, and distinct copy options. Somali fluency, modern Nubian support, historical-script completeness, and real external clipboard interoperability are not established.

## 2. Baseline and scope

The campaign began at local `main` commit `c80f4e1`, 56 commits ahead of public `origin/main` at `c4f2f87270c22a05e772816ce98e57a99b871b18`. The remote's latest Python Checks run, `40087020450`, completed successfully for that remote commit. The campaign reviewed the approved app and language routes, UI acceptance, clipboard claims, benchmark state, project documents and release safety. It fixed the visible Old Nubian toolbar spacing issue and reconciled a clipboard portability statement. No UI redesign or framework migration was undertaken.

## 3. Implemented improvements

- **Old Nubian toolbar:** widened the `Read` action from 48 dp to 72 dp and increased action spacing to 12 dp. Live Kivy acceptance checks at least 8 dp between action labels and confirms the visible Read Studio route. The captured studio screen was inspected after the fix.
- **Clipboard accuracy:** corrected the support matrix to distinguish implemented payload formats and guarded harnesses from actual clipboard delivery. The current HWND-owning Windows publisher has not been exercised against an external application.
- **Release workflow:** kept the app and test setup isolated for live acceptance; no host clipboard or physical input was used.

## 4. Important changed files

- `app/main.kv` — toolbar spacing and width for the Old Nubian Read action; added stable widget IDs for acceptance checks.
- `app/acceptance.py` — live layout assertions for action width and separation.
- `docs/SUPPORT_MATRIX.md` — accurate clipboard interoperability status.
- `docs/DEVELOPMENT_ROADMAP.md` — removed stale Ruff count and reconciled the remaining queues.
- `docs/IMPLEMENTATION_PROGRESS.md` — recorded this campaign and current blockers.
- `docs/SESSION_HANDOFF.md` — current session state and resumption context.
- `docs/FINAL_DEVELOPMENT_REPORT.md` — this final evidence summary.

## 5. Translation and detection evidence

Previously recorded full 150-pair Somali benchmark: EN→SO BLEU 5.287 and chrF++ 25.282; SO→EN BLEU 6.300 and chrF++ 24.680. The EN→SO figures were lower than the pre-guard baseline (BLEU 7.057, chrF++ 28.996); the unknown-token guard removes visible decode artifacts but is not evidence of improved semantic quality. Metrics are automatic overlap scores, not fluency judgments. The local checkout's `models/somali` folder has no model files, so this campaign did not claim a fresh reproduction. A fluent Somali reviewer and approved review sample remain necessary.

Previously recorded short-input detection work evaluated pinned Tatoeba, Qor and MASSIVE samples. Source locale labels and Somali-only recall-like signals are not independently adjudicated language-identification gold labels. The 0.75 short-input threshold is experimental; it is not a general accuracy claim. No new detection benchmark was run in this campaign.

## 6. Historical scripts and licensing

Osmanya, Borama and Kaddare are script-conversion routes, not meaning translation. Borama/Kaddare use partial chart-derived mappings and private-use glyphs, whose rendering depends on Saylacian fonts; raw PUA text is not universally interoperable Unicode. Tagged Saylacian Text preserves script identity for Saylacian import. Old Nubian support is limited table-based character reading/transliteration; it is not complete manuscript transcription or translation. Modern Nobiin, Kenzi/Mattokki, Dongolawi/Andaandi, Midob and other modern Nubian varieties remain unsupported. DBMNT-derived expansion is blocked pending written reuse terms and qualified specialist review. Keep all third-party assets under their respective notices and licences.

## 7. UI, accessibility, clipboard and Windows status

Isolated live Kivy self-test passed, including the Old Nubian Reading Studio and its revised toolbar geometry; the inspected capture showed distinct `Transliterate` and `Read` labels. The captured route does not establish compact-device pixel fidelity or screen-reader behavior. KivyMD 1.2.0 deprecation warnings remain; migration is deferred because no upgrade is needed for this fix and a framework move would be disruptive. Fake Win32 API regressions cover ownership and allocation cleanup. Actual system clipboard exchange remains unverified and intentionally was not attempted; use a disposable VM with host clipboard sharing disabled and a font-compatible external consumer. The unsigned Windows executable remains unsuitable for release and must not be used to weaken Smart App Control.

## 8. Security, privacy and data integrity

Existing protections include model-pack hash verification and path containment, safe saved-history recovery, and diagnostic logging that omits source directories and exception text. Clipboard test scripts are guarded and refuse unsafe host use. No credentials were printed, no user's clipboard was read or changed, and no personal diagnostics or history files were accessed. This campaign did not alter those protections.

## 9. Test results

Environment: project `.venv`, Windows, Python project test suite, Kivy live self-test with isolated temporary app/Kivy/evidence directories.

- `.\.venv\Scripts\python.exe -m pytest -q -rs` — **143 passed, 2 skipped, 197 subtests passed** in 12.57 s. Both skips are Windows symlink tests; the current process lacks the privilege required to create file/directory symlinks.
- `.\.venv\Scripts\ruff.exe check .` — passed.
- `.\.venv\Scripts\ruff.exe format --check .` — passed, 112 files already formatted.
- `.\.venv\Scripts\python.exe -m compileall -q main.py app saylacian tools tests` — passed.
- `.\.venv\Scripts\python.exe -m pip check` — no broken requirements.
- `git diff --check` and `git diff --cached --check` — passed; Git reports existing CRLF-to-LF normalization warnings for edited files.
- `.\.venv\Scripts\python.exe tools\check_release_safety.py` — passed; no recognized credential patterns found.
- PowerShell parser — both clipboard scripts parsed successfully.
- Isolated `main.py --self-test` — passed; test used a controlled clipboard fixture and blocked network access. It did not read or write the Windows clipboard.

## 10. Known failures, skips and blockers

The two skipped tests require Windows symlink privileges. Somali quality review and fresh benchmark reproduction require a local model pack and fluent reviewer. Old Nubian data expansion needs rights-holder terms and specialist review. Screen-reader verification requires a manual Narrator/NVDA run. Compact-layout screenshot validation needs a functioning isolated capture path; existing SDL captures at the compact viewport were invalid. Real clipboard interoperability needs a disposable isolated VM. Hosted integration tests need owner approval to push. Clean-host Windows packaging/signing requires an isolated test host and appropriate signing/distribution decisions. These blockers do not invalidate the local test suite or limited features stated above.

## 11. Git branch and unpublished commits

Branch: `main`. Before this campaign, HEAD was `c80f4e1` and 56 commits ahead of public `origin/main` at `c4f2f87270c22a05e772816ce98e57a99b871b18`. The verified implementation and campaign report are committed locally as `f7f27ed508343f2d3c9b0a21034810d56c52afc1`; final handoff synchronization follows in a separate local documentation commit. No force operation is authorized.

## 12. Owner edits and publication

The pre-existing edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` were treated as owner-owned and read-only; they were not modified, staged or included in this campaign. Nothing was pushed, released or published; public `main` remains at `c4f2f87270c22a05e772816ce98e57a99b871b18` as last verified.

## 13. Release readiness

**READY FOR OWNER REVIEW — EXPERIMENTAL SOURCE ALPHA.** The local checks and live app acceptance passed, but this is not a claim of linguistic completeness, verified external clipboard delivery, a signed Windows release, or complete accessibility/platform acceptance.

## 14. Remaining actions

**Owner/reviewer actions:** obtain DBMNT reuse terms and qualified Old Nubian review; arrange fluent Somali review; authorize any push needed for hosted workflows; provide an isolated Windows VM and appropriate clean-host/signing plan if pursuing binary distribution.

**Developer actions when evidence/resources exist:** rerun the pinned Somali benchmark with verified local model hashes; test clipboard delivery in the isolated VM; run Narrator/NVDA and valid compact viewport capture; then reassess the release checklist.

## 15. Final phase status

**COMPLETE WITH DOCUMENTED EXTERNAL BLOCKERS.** All currently feasible local gates and the targeted live Kivy acceptance passed. No safe, evidence-backed READY task remains in the current queue; remaining work depends on specialist input, rights, a clean VM, or owner approval. The code and backups were preserved, and this campaign did not push or release anything.
