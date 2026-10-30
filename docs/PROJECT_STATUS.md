# Saylacian project status — 2026-10-30

Saylacian's initial alpha-testing source snapshot is public at [github.com/zealousvec/Saylacian](https://github.com/zealousvec/Saylacian). A read-only remote check on 2026-10-30 confirmed public `main` at `c4f2f87270c22a05e772816ce98e57a99b871b18`. The original source snapshot contained 149 files. No binary release or mobile release is published.

This page distinguishes public state from the current local cleanup. It must be updated again after a future approved push.

## Verified implementation status

- Current source version: `0.1.0a1` (alpha testing); version history is in `CHANGELOG.md`.
- The main application is Python with Kivy/KivyMD. The approved UI is preserved.
- Meaning translation has offline English↔French model routes. Somali↔English is in alpha testing; Somali↔French uses English as an intermediate step. Fluent-speaker evaluation has not established Somali quality.
- Somali Latin↔Osmanya conversion is implemented for the listed mapping, with spelling conventions and community review still open.
- Borama and Kaddare have partial chart-label conversions using private-use code points and separately licensed chart-derived assets. They are not standardized Unicode alphabets or validated word-level orthographies.
- Old Nubian Coptic-script→scholarly-Latin transliteration uses a limited 29-character table attributed under CC BY 4.0. Reverse conversion may split multi-character readings at ambiguous boundaries. It is not Old Nubian meaning translation or complete coverage.
- Modern Nubian varieties, including Nobiin, Kenzi/Mattokki, Dongolawi/Andaandi, Midob, Birgid, Dilling, Karko, Wali and Kadaru, have no implemented converter or translation route.
- The website source is a local Flask interface; it is not publicly deployed. The website UI does not expose the Old Nubian route.
- Android and iOS builds are not verified. No public Windows installer is available.
- AGPL-3.0-or-later applies only to Saylacian-authored code the licensor owns or may license. Third-party code and assets retain their separate terms.

## Follow-up after publication (local changes not yet published)

### Current release completion work (2026-10-30)

- The Old Nubian converter now uses the 29 single-character readings in van Gerven Oei (2024), Table 1, CC BY 4.0, with attribution recorded in `docs/THIRD_PARTY_NOTICES.md`. Unmapped Coptic letters remain unchanged and receive a warning. This replaces the prior 34-entry DBMNT-derived mapping; no DBMNT table content is bundled.
- User-facing app, website, README and support labels use alpha-testing language and state remaining language/script limits directly.
- Changes are local and unpushed. On 2026-10-30, the working branch was `main` at `527df1569da68a5dadb758eafd9f0693aff983db`, 112 commits ahead of public `main`; the working tree also contained the release-campaign edits listed by `git status`. No push was made.
- Built and verified a portable Windows ZIP candidate during development. It contained 616 manifest-listed payload files, a single app EXE, third-party notices and user/setup docs; no model weights or Poppler files. Later source edits make that draft checksum stale, so the candidate will be rebuilt from the final committed tree. Its manifest records `runtime_verified: false`; it is a build candidate, not a verified end-user release.
- The Kivy source-app self-test passed in an isolated temporary profile. The website headless Edge check passed its eight API, conversion, clipboard-double and responsive-layout checks. The package itself was not launched because it is unsigned; Windows Smart App Control and clean-machine behavior remain unverified.
- Full suite: **194 passed, 2 skipped, 191 subtests**. Ruff lint and formatting, compileall, `pip check`, release-safety scan, package-manifest hash verification and `git diff --check` passed. No external clipboard was accessed.

- Published `main` is now `ca0ef3e40215762f8e8cfb4da0c839680764d6c8`. The one-line normalization in `saylacian/core/model_packs.py` is included in that commit; download-security logic is unchanged.
- GitHub Actions run `40086510600` for that commit failed one test: `test_installed_pack_is_used_by_offline_route_and_removal_is_scoped`. Windows compared the resolved `runneradmin` path returned by the route with the same temporary directory written using its `RUNNER~1` alias.
- A local-only test adjustment compares the returned route to `folder.resolve()`, preserving the assertion that the route selects the exact expected directory. The earlier `test_download_verifies_hash_installs_version_and_reports_progress` remains unchanged. This follow-up has not been pushed.
- Five local educational/audit documents are prepared: `ARCHITECTURE_EXPLAINED.md`, `CODEBASE_WALKTHROUGH.md`, `TECHNICAL_AUDIT.md`, `FOUNDER_LEARNING_GUIDE.md`, and `DEVELOPMENT_ROADMAP.md`.
- After the local assertion adjustment, the affected two model-pack tests pass and the full local suite reports **80 tests and 66 subtests passed**. Compilation, workflow Ruff lint, formatting, dependency checks, release safety scan, whitespace, and changed-document link checks pass. No CI run has verified this follow-up yet.
- Public repository metadata still describes Saylacian as “non-profit,” while `AUTHORS.md` says it is not a registered nonprofit. A repository admin should correct that metadata separately.

## Release and verification history

Before publication, recorded clean-clone checks reported 68 passed/12 skipped before model packs and 71 passed/9 skipped after installing and verifying the packs. Those are prior recorded results, not a fresh clean-clone run for this cleanup.

In the current local checkout, the full test suite passed with **80 tests and 66 subtests**. Compilation, the workflow's Ruff correctness selection, Ruff formatting, the release safety scanner, and `git diff --check` passed. Local model weights were present, so installed-model tests ran; GitHub CI intentionally does not download those weights.

## Still open

1. Finish the clean-source setup and pack-install check; run Windows CI on the pending source changes after an approved push.
2. Verify screen-reader/keyboard accessibility and real clipboard formats in a disposable Windows VM; no such VM is available in this session.
3. Obtain fluent Somali review and specialist/community review for historical-script tables before making stronger quality claims.
4. Check native DLL distribution terms and validate the portable app on a clean Windows host; the current unsigned build is not ready for ordinary-user distribution.
5. Ask a repository administrator to correct the public project description and review account-level security settings.
6. Android/iOS builds and Store submission remain out of scope.
