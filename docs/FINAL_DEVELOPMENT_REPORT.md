# Saylacian final development report

**Date:** 2026-10-25
**Status:** PARTIALLY COMPLETE — DEVELOPMENT CONTINUES
**Release readiness:** NOT READY — experimental source acceptance passed, but required validation and release gates remain open.

## 1. Executive summary

Saylacian is an offline-first Python/Kivy application with English/French offline meaning translation when the relevant language packs are installed, experimental Somali translation, script conversion tools for Somali/Osmanya and partial chart-derived Borama/Kaddare, and a limited Old Nubian reading/transliteration studio. The app includes model-pack management, saved translation history, tagged Saylacian Text interchange, and distinct copy options. Somali fluency, modern Nubian support, historical-script completeness, and real external clipboard interoperability are not established.

## 2. Baseline and scope

The earlier UI/acceptance campaign began at local `main` commit `c80f4e1`, 56 commits ahead of public `origin/main` at `c4f2f87270c22a05e772816ce98e57a99b871b18`. This recovery began at local commit `80c868fc30521a2603bf20a255631ff0c09d14fb`, 61 commits ahead of that public commit. The remote's latest Python Checks run, `40087020450`, completed successfully for the remote commit. The recovery added fresh Somali benchmark reproduction and a development-dependency advisory fix. No UI redesign or framework migration was undertaken.

## 3. Implemented improvements

- **Old Nubian toolbar:** widened the `Read` action from 48 dp to 72 dp and increased action spacing to 12 dp. Live Kivy acceptance checks at least 8 dp between action labels and confirms the visible Read Studio route. The captured studio screen was inspected after the fix.
- **Clipboard accuracy:** corrected the support matrix to distinguish implemented payload formats and guarded harnesses from actual clipboard delivery. The current HWND-owning Windows publisher has not been exercised against an external application.
- **Release workflow:** kept the app and test setup isolated for live acceptance; no host clipboard or physical input was used.
- **Model-pack path safety:** reject Windows backslashes and drive paths in manifest destinations before creating or downloading into a destination; regression proves traversal is rejected before network access.
- **Model-pack integrity recovery:** recheck installed model hashes before routes load them, cache verified hashes by file metadata, and identify changed files in the Packs screen with a confirmed removal path.

## 4. Important changed files

- `app/main.kv` — toolbar spacing and width for the Old Nubian Read action; added stable widget IDs for acceptance checks.
- `app/acceptance.py` — live layout assertions for action width and separation; model-path, clipboard and publisher fixtures now patch the running app module during acceptance.
- `docs/SUPPORT_MATRIX.md` — accurate clipboard interoperability status.
- `docs/DEVELOPMENT_ROADMAP.md` — removed stale Ruff count and reconciled the remaining queues.
- `docs/IMPLEMENTATION_PROGRESS.md` — recorded this campaign and current blockers.
- `docs/SESSION_HANDOFF.md` — current session state and resumption context.
- `docs/FINAL_DEVELOPMENT_REPORT.md` — this final evidence summary.
- `tools/benchmark_somali_quality.py` and `tests/test_somali_benchmark_output.py` — current fallback-warning accounting and regression coverage.
- `requirements-dev.txt` — pytest 9.1.1 replaces the advisory-affected 8.4.2 pin.
- `saylacian/core/model_packs.py` and `tests/test_model_packs.py` — reject Windows-specific asset path escapes before download.
- `main.py` and `app/acceptance.py` — show changed-pack recovery and verify keyboard/button removal flows without deleting a real pack.

## 5. Translation and detection evidence

Fresh 2026-10-25 reproduction on the pinned 150-pair TICO-19 test fixture (SHA-256 `be58b2d350badb7e03b73906471453311a8843534e4a2a572a772c60c394c7f7`) matched the recorded post-guard scores: EN→SO BLEU 5.287 / chrF++ 25.282; SO→EN BLEU 6.300 / chrF++ 24.680. The verified Somali pack version was `1-bfdcf52bd69` (10/10 assets). Runtime versions: CTranslate2 4.8.3, SentencePiece 0.2.2 and SacreBLEU 2.5.1. The route also used the already-present ignored synthetic candidate, independently checked against the tracked manifest (Helsinki revision `49384e6b2c3ddd374f2cccc8efecb678724b739d`, `model.bin` SHA-256 `62aacb4ec5812ce20a1eb2563fe763d16d20858e2490d6d8bdd0a3a1f4f72c22`); no weights or raw predictions were added to Git. The synthetic candidate was selected for 97/150 items; 53 fell back (47 unknown-token, six output-length, zero repeat/copy), with no U+2047 in final EN→SO output. This remains below pre-guard EN→SO BLEU 7.057 / chrF++ 28.996 and does not prove semantic improvement. Machine-specific runtime was 134.91 s, peak working set 548,204,544 bytes; EN→SO median/p95 254.9/1,356.1 ms, SO→EN 207.3/530.9 ms. Heuristic review cues are documented in `docs/SOMALI_TRANSLATION_QUALITY.md`; they are not confirmed errors. All scores are automatic and fluent Somali review remains BLOCKED.

Previously recorded short-input detection work evaluated pinned Tatoeba, Qor and MASSIVE samples. Source locale labels and Somali-only recall-like signals are not independently adjudicated language-identification gold labels. The 0.75 short-input threshold is experimental; it is not a general accuracy claim. No new detection benchmark was run in this campaign.

## 6. Historical scripts and licensing

Osmanya, Borama and Kaddare are script-conversion routes, not meaning translation. Borama/Kaddare use partial chart-derived mappings and private-use glyphs, whose rendering depends on Saylacian fonts; raw PUA text is not universally interoperable Unicode. Tagged Saylacian Text preserves script identity for Saylacian import. Old Nubian support is limited table-based character reading/transliteration; it is not complete manuscript transcription or translation. Modern Nobiin, Kenzi/Mattokki, Dongolawi/Andaandi, Midob and other modern Nubian varieties remain unsupported. DBMNT-derived expansion is blocked pending written reuse terms and qualified specialist review. Keep all third-party assets under their respective notices and licences.

## 7. UI, accessibility, clipboard and Windows status

Isolated live Kivy self-test passed, including the Old Nubian Reading Studio and its revised toolbar geometry; the inspected capture showed distinct `Transliterate` and `Read` labels. The captured route does not establish compact-device pixel fidelity or screen-reader behavior. KivyMD 1.2.0 deprecation warnings remain; migration is deferred because no upgrade is needed for this fix and a framework move would be disruptive. Fake Win32 API regressions cover ownership and allocation cleanup. Actual system clipboard exchange remains unverified and intentionally was not attempted; use a disposable VM with host clipboard sharing disabled and a font-compatible external consumer. The unsigned Windows executable remains unsuitable for release and must not be used to weaken Smart App Control.

## 8. Security, privacy and data integrity

Existing protections include model-pack hash verification and path containment, safe saved-history recovery, and diagnostic logging that omits source directories and exception text. Clipboard test scripts are guarded and refuse unsafe host use. No credentials were printed, no user's clipboard was read or changed, and no personal diagnostics or history files were accessed. This campaign did not alter those protections.

## 9. Test results

Environment: project `.venv`, Windows, Python project test suite, Kivy live self-test with isolated temporary app/Kivy/evidence directories.

- `.\.venv\Scripts\python.exe -m pytest -q -rs` — **144 passed, 2 skipped, 197 subtests passed** in 11.26 s. Both skips are Windows symlink tests; the current process lacks the privilege required to create file/directory symlinks.
- `.\.venv\Scripts\ruff.exe check .` — passed.
- `.\.venv\Scripts\ruff.exe format --check .` — passed, 113 files already formatted.
- `.\.venv\Scripts\python.exe -m compileall -q main.py app saylacian tools tests` — passed.
- `.\.venv\Scripts\python.exe -m pip check` — no broken requirements.
- `git diff --check` and `git diff --cached --check` — passed; Git reports existing CRLF-to-LF normalization warnings for edited files.
- `.\.venv\Scripts\python.exe tools\check_release_safety.py` — passed; no recognized credential patterns found.
- PowerShell parser — both clipboard scripts parsed successfully.
- `pytest -q tests/test_somali_benchmark_output.py` — 3 passed, including current fallback-warning audit coverage.
- `pytest -q tests/test_model_packs.py` — 11 passed, 2 Windows symlink-permission skips, 8 subtests; coverage includes Windows path traversal rejection and same-size post-install corruption detection/recovery after a prior hash-cache hit.
- Latest full suite after the integrity recovery change: **146 passed, 2 skipped, 200 subtests passed**. The two skips are existing Windows symlink-privilege skips.
- Live Kivy `main.py --self-test` passed from isolated app/Kivy/pack/evidence directories after installing the pinned French pack; both offline French directions passed with network blocked. Pack corruption UI checks passed; no physical input or real clipboard was used.
- Somali benchmark — 150 pairs reproduced in 134.91 s using the verified temporary pack; socket connections were denied during inference; raw result/checkpoint remained in temp.
- `pip-audit` — audited every `requirements*.txt` file. Initial run identified pytest 8.4.2 (PYSEC-2026-1845); updated the development pin to 9.1.1. Re-scan found no known vulnerabilities in the pinned requirements.
- Fresh temporary Python 3.12 Windows environment installed `requirements-dev.txt`; `pip check` passed and pytest 9.1.1 passed the full suite: 144 passed, 2 Windows symlink-permission skips, 197 subtests.
- Clean clone of local commit `2dc7378` — `tools/verify_pack_integration.py --pack french` downloaded the pinned French pack into an isolated temporary store, verified both assets, installed its receipt, and passed offline English→French and French→English inference. Then `main.py --self-test` passed from the clone with output `Bonjour, comment allez-vous ?`; inference and Kivy acceptance ran with network access blocked, five screenshots were produced in isolated temporary evidence, and the clone's tracked working tree remained clean.
- The live acceptance harness patches model-path, clipboard and publisher fixtures on the running app module (`__main__` for script launch). This makes detector and clipboard assertions independent of a machine's local Somali pack and avoids host clipboard access. The meaning-translation acceptance still correctly requires its verified French pack.

## 10. Known failures, skips and blockers

The two skipped tests require Windows symlink privileges. Somali linguistic quality still requires fluent reviewer input; model outputs and heuristic cues are not human quality judgments. Old Nubian data expansion needs rights-holder terms and specialist review. Screen-reader verification requires a manual Narrator/NVDA run. Compact-layout screenshot validation needs a functioning isolated capture path; existing SDL captures at the compact viewport were invalid. Real clipboard interoperability needs a disposable isolated VM. Hosted integration tests need owner approval to push. Clean-host Windows packaging/signing requires an isolated test host and appropriate signing/distribution decisions. These blockers do not invalidate the local test suite or limited features stated above.

## 11. Git branch and unpublished commits

Branch: `main`, recovery commit `72a3e5ee8554401fd36d9901722bd64bcf1ed66b` contains the benchmark, route-audit, development dependency and campaign report files. Follow-up commit `6f294db2bf8be75bfba88334325635784fd9631a` contains only Windows pack-path validation and its regression test. Integrity recovery commit `b4904be9643dee1f8dfb2a5e484b4e731a8f06d6` contains only `saylacian/core/model_packs.py`, `tests/test_model_packs.py`, `main.py` and `app/acceptance.py`. Public `origin/main` remains at the last verified `c4f2f87270c22a05e772816ce98e57a99b871b18`. All commits are local and unpublished. No force operation is authorized.

## 12. Owner edits and publication

The pre-existing edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` were treated as owner-owned and read-only; they were not modified, staged or included in this campaign. Nothing was pushed, released or published; public `main` remains at `c4f2f87270c22a05e772816ce98e57a99b871b18` as last verified.

## 13. Release readiness

**NOT READY.** Local source checks pass, but external clipboard delivery, accessibility, specialist linguistic validation, and clean-host Windows signing/package validation are still outstanding.

## 14. Remaining actions

**Owner/reviewer actions:** obtain DBMNT reuse terms and qualified Old Nubian review; arrange fluent Somali review; authorize any push needed for hosted workflows; provide an isolated Windows VM and appropriate clean-host/signing plan if pursuing binary distribution.

**Completed developer actions:** fresh Somali benchmark reproduction with verified pack, network-blocked inference and temp-only outputs; corrected and regression-tested stale route-audit accounting; fixed the vulnerable development pytest pin and audited all requirement files; closed a Windows-specific pack destination traversal gap; detect same-size post-install model corruption and give users a confirmed recovery path. Changes are committed locally at `72a3e5ee8554401fd36d9901722bd64bcf1ed66b`, `6f294db2bf8be75bfba88334325635784fd9631a`, and `b4904be9643dee1f8dfb2a5e484b4e731a8f06d6`. No other safe, evidence-backed task is currently READY; reassess if required people, permissions, or isolated environments become available.

## 15. Final phase status

**PARTIALLY COMPLETE — NOT FINISHED.** The toolbar fix, clean-clone pack workflow, Somali benchmark reproduction and route-audit correction, dependency advisory remediation, Windows-specific pack-path containment, and post-install integrity recovery are verified. This does not complete the project or release readiness: linguistic review, historical-data rights, accessibility observation, real clipboard validation, and clean-host/signing checks remain open. The previous report's “complete” label was premature. Nothing was pushed; no files were released.
