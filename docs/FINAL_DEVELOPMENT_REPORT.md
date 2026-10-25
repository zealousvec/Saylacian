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
- `tools/check_ui.py`, `tools/in_memory_clipboard.py` and `tests/test_in_memory_clipboard.py` — use and verify an in-memory clipboard for automated UI round-trips.

## 5. Translation and detection evidence

Fresh 2026-10-25 reproduction on the pinned 150-pair TICO-19 test fixture (SHA-256 `be58b2d350badb7e03b73906471453311a8843534e4a2a572a772c60c394c7f7`) matched the recorded post-guard scores: EN→SO BLEU 5.287 / chrF++ 25.282; SO→EN BLEU 6.300 / chrF++ 24.680. The verified Somali pack version was `1-bfd6cf52bd69` (10/10 assets). Runtime versions: CTranslate2 4.8.3, SentencePiece 0.2.2 and SacreBLEU 2.5.1. The route also used the already-present ignored synthetic candidate, independently checked against the tracked manifest (Helsinki revision `49384e6b2c3ddd374f2cccc8efecb678724b739d`, `model.bin` SHA-256 `62aacb4ec5812ce20a1eb2563fe763d16d20858e2490d6d8bdd0a3a1f4f72c22`); no weights or raw predictions were added to Git. The synthetic candidate was selected for 97/150 items; 53 fell back (47 unknown-token, six output-length, zero repeat/copy), with no U+2047 in final EN→SO output. This remains below pre-guard EN→SO BLEU 7.057 / chrF++ 28.996 and does not prove semantic improvement. Machine-specific runtime was 134.91 s, peak working set 548,204,544 bytes; EN→SO median/p95 254.9/1,356.1 ms, SO→EN 207.3/530.9 ms. Heuristic review cues are documented in `docs/SOMALI_TRANSLATION_QUALITY.md`; they are not confirmed errors. All scores are automatic and fluent Somali review remains BLOCKED.

Previously recorded short-input detection work evaluated pinned Tatoeba, Qor and MASSIVE samples. Source locale labels and Somali-only recall-like signals are not independently adjudicated language-identification gold labels. The 0.75 short-input threshold is experimental; it is not a general accuracy claim. No new detection benchmark was run in this campaign.

## 6. Historical scripts and licensing

Osmanya, Borama and Kaddare are script-conversion routes, not meaning translation. Borama/Kaddare use partial chart-derived mappings and private-use glyphs, whose rendering depends on Saylacian fonts; raw PUA text is not universally interoperable Unicode. Tagged Saylacian Text preserves script identity for Saylacian import. Old Nubian support is limited table-based character reading/transliteration; it is not complete manuscript transcription or translation. Modern Nobiin, Kenzi/Mattokki, Dongolawi/Andaandi, Midob and other modern Nubian varieties remain unsupported. DBMNT-derived expansion is blocked pending written reuse terms and qualified specialist review. Keep all third-party assets under their respective notices and licences.

## 7. UI, accessibility, clipboard and Windows status

Isolated live Kivy self-test passed, including the Old Nubian Reading Studio and its revised toolbar geometry; the inspected capture showed distinct `Transliterate` and `Read` labels. The captured route does not establish compact-device pixel fidelity or screen-reader behavior. KivyMD 1.2.0 deprecation warnings remain; migration is deferred because no upgrade is needed for this fix and a framework move would be disruptive. Fake Win32 API regressions cover ownership and allocation cleanup. Actual system clipboard exchange remains unverified and intentionally was not attempted; use a disposable VM with host clipboard sharing disabled and a font-compatible external consumer. The unsigned Windows executable remains unsuitable for release and must not be used to weaken Smart App Control.

## 8. Security, privacy and data integrity

Existing protections include model-pack hash verification and path containment, safe saved-history recovery, and diagnostic logging that omits source directories and exception text. `tools/check_ui.py` now substitutes an in-memory clipboard and publisher. Its 2026-10-23 recorded run called the native Windows publisher without evidence that prior clipboard contents were preserved; that run is not accepted as a safe clipboard or external-app test. No clipboard was read or changed during this campaign. No credentials were printed, and no personal diagnostics or history files were accessed.

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
- After making the legacy UI clipboard round-trip safe: **149 passed, 2 skipped, 200 subtests passed**. Both skips remain Windows symlink-permission limits; the 3 new focused clipboard helper tests pass.
- Latest full suite after the integrity recovery change: **146 passed, 2 skipped, 200 subtests passed**. The two skips are existing Windows symlink-privilege skips.
- Live Kivy `main.py --self-test` passed from isolated app/Kivy/pack/evidence directories after installing the pinned French pack; both offline French directions passed with network blocked. Pack corruption UI checks passed; no physical input or real clipboard was used.
- Somali benchmark — 150 pairs reproduced in 134.91 s using the verified temporary pack; socket connections were denied during inference; raw result/checkpoint remained in temp.
- `pip-audit` — audited every `requirements*.txt` file. Initial run identified pytest 8.4.2 (PYSEC-2026-1845); updated the development pin to 9.1.1. Re-scan found no known vulnerabilities in the pinned requirements.
- Fresh temporary Python 3.12 Windows environment installed `requirements-dev.txt`; `pip check` passed and pytest 9.1.1 passed the full suite: 144 passed, 2 Windows symlink-permission skips, 197 subtests.
- Clean clone of local commit `2dc7378` — `tools/verify_pack_integration.py --pack french` downloaded the pinned French pack into an isolated temporary store, verified both assets, installed its receipt, and passed offline English→French and French→English inference. Then `main.py --self-test` passed from the clone with output `Bonjour, comment allez-vous ?`; inference and Kivy acceptance ran with network access blocked, five screenshots were produced in isolated temporary evidence, and the clone's tracked working tree remained clean.
- The live acceptance harness patches model-path, clipboard and publisher fixtures on the running app module (`__main__` for script launch). This makes detector and clipboard assertions independent of a machine's local Somali pack and avoids host clipboard access. The meaning-translation acceptance still correctly requires its verified French pack.

## 10. Known failures, skips and blockers

The two skipped tests require Windows symlink privileges. Somali linguistic quality still requires fluent reviewer input; model outputs and heuristic cues are not human quality judgments. Old Nubian data expansion needs rights-holder terms and specialist review. Screen-reader verification requires a manual Narrator/NVDA run. Desktop compact-layout capture is now valid through Kivy FBO export: six viewports, including 320×500 dp, were captured and reviewed; physical-device layout remains unverified. Real clipboard interoperability needs a disposable isolated VM. Hosted integration tests need owner approval to push. Clean-host Windows packaging/signing requires an isolated test host and appropriate signing/distribution decisions. The pinned MIT M2M100 candidate also remains unevaluated beyond 25/150 development examples because this host's CPU throughput was too slow; complete the full dev evaluation on faster suitable hardware before considering it. These blockers do not invalidate the local test suite or limited features stated above.

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

**PARTIALLY COMPLETE — NOT FINISHED.** The toolbar fix, clean-clone pack workflow, Somali benchmark reproduction and route-audit correction, dependency advisory remediation, Windows-specific pack-path containment, post-install integrity recovery, compact portrait layout and bounded online response parsing are verified. This does not complete the project or release readiness: linguistic review, historical-data rights, accessibility observation, real clipboard validation, and clean-host/signing checks remain open. The previous report's “complete” label was premature. Nothing was pushed; no files were released.

## 16. Required isolated benchmark re-run — 2026-10-25

A new temporary app-data and pack-store root was used to install Somali pack `1-bfd6cf52bd69`. `tools/verify_pack_integration.py --pack somali` verified all 10 pinned assets (314,460,806 bytes) and both offline smoke directions. The 150-pair TICO-19 fixture retained SHA-256 `be58b2d350badb7e03b73906471453311a8843534e4a2a572a772c60c394c7f7`. The local Helsinki synthetic candidate matched pinned `model.bin` SHA-256 `62aacb4ec5812ce20a1eb2563fe763d16d20858e2490d6d8bdd0a3a1f4f72c22`. During the full benchmark, `socket.socket.connect` was blocked; results and checkpoint remained in isolated temporary storage outside Git.

Results reproduced EN→SO BLEU/chrF++ `5.287/25.282` and SO→EN `6.300/24.680`. Route audit: 97 candidate selections; 53 fallbacks (47 unreadable-token, 6 output-length, 0 repeat/copy); no U+2047 in final EN→SO. Runtime was 115.26 seconds and peak working set 548,388,864 bytes. These automatic scores establish reproducibility, not translation quality. Earlier campaign notes had a mistyped Somali pack version; the verified version is `1-bfd6cf52bd69`.

## 17. Clipboard test safety correction — 2026-10-25

Code review found the legacy `tools/check_ui.py` round-trip invoked the actual Windows publisher and system paste API. Its historical output does not establish that clipboard contents present before the test were preserved. The harness now replaces the app's clipboard object and Windows publisher with `InMemoryClipboard` before creating the Kivy app; the test checks the CF_UNICODETEXT payload and round-trips text locally. Three focused tests verify in-memory text, format capture and missing Unicode text handling. The full suite passes 149 tests, 2 Windows symlink-permission skips and 200 subtests; Ruff, format, compileall, `pip check`, release-safety and diff checks pass. The full live UI script was not rerun, and actual Windows/external-app acceptance remains BLOCKED until the documented disposable VM is available.

## 2026-10-25 — Safe isolated Kivy acceptance restored

Updated `tools/check_ui.py` to match current language-picker/status wording and the separately listed Borama chart reference. The harness now defaults all screenshots, failure traces and JSON results to a fresh temporary evidence directory (overridable with `SAYLACIAN_UI_EVIDENCE_DIR`) instead of overwriting tracked or ignored `docs/` artifacts. Clipboard actions remain replaced by an in-memory clipboard and stub publisher.

Ran the actual Kivy acceptance script with isolated APPDATA, LOCALAPPDATA, Kivy home, pack store and evidence output, with network connections blocked. All 19 checks passed, including the in-memory clipboard round trip, offline Somali routes, installed-pack screen, stale-worker handling, and layout geometry at 320x640, 390x780, 780x390, 768x1024 and 1366x768. Evidence is at `%TEMP%\Saylacian-safe-ui-a2d90f6ce6bd4b159781638269540aab\evidence`. The 320x640 PNG was visually inspected at 400x800 RGBA and is legible, with all primary controls and status visible. This clears the compact-capture-path blocker for this viewport; broad platform visual regression, screen-reader announcements and real system clipboard remain unverified.

Full verification after the harness fix: `149 passed, 2 skipped, 200 subtests passed`; Ruff check and format, compileall, `pip check` pass. The two skipped tests require Windows symlink privilege. Owner edits in `docs/PROJECT_STATUS.md` and `docs/TECHNICAL_AUDIT.md` remain untouched. No host clipboard access, push or publication.

ACTIVE: commit this focused harness correction and then reassess the next independently verifiable READY work. BLOCKED: fluent Somali review; Old Nubian rights/specialist review; Narrator/NVDA; external clipboard test in disposable VM; hosted CI workflow approval; clean-host Windows signing/packaging; full M2M100 development evaluation on suitable faster hardware. READY: none established beyond this verification/commit step; do not invent tasks.

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

## 18. Continuing audit — compact layout and online response safety (2026-10-25)

The 320×500 dp compact portrait layout keeps source/target controls in one row and input/output panels stacked. Live Kivy acceptance checks both text fields remain at least 56 dp high; the rendered screenshot was visually reviewed. Desktop FBO evidence is now valid through six viewports; physical-device behavior remains unverified.

Optional online translation clients now bound JSON response reads to 1 MiB + 1 byte and reject non-object JSON roots as provider-specific recoverable errors. No online request or credential was used. Regression tests cover Cloudflare and self-hosted paths.

Local commits: `05d5608753c08980502f16fa352e76b5d074af8b` (compact portrait usability), `5d8ee03b227cd7fb5a1913e1b36625c83db8f082` (56 dp live viewport assertion), `240a5361b419dc3887fef84596c3f60917d84e69` (handoff record), `0cd520638aad45b97081d06ad0ea7b22b33c6c9a` (progress checkpoint), and `93aa1484ed63f21b8074e598973555a0a63a8876` (online response bounds). Latest full suite: 155 passed, 2 skipped, 208 subtests; Ruff, format, compileall, `pip check`, release-safety and diff checks passed. Everything remains local/unpublished. Goal remains ACTIVE — NOT FINISHED; external blockers and exact resolution actions remain in the progress board.
