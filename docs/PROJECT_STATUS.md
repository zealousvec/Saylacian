# Saylacian project status — 2026-10-31

The source-only alpha is public at [github.com/zealousvec/Saylacian](https://github.com/zealousvec/Saylacian). GitHub `main` points to `4533b55` (`Update V1!`), merged through [pull request #1](https://github.com/zealousvec/Saylacian/pull/1) on 2026-10-30. No binary release or mobile build is published. The application is version `0.1.0a1` and remains in alpha testing.

The main Python workflow for this commit completed successfully: [run 41129890132](https://github.com/zealousvec/Saylacian/actions/runs/41129890132). Its Windows tests passed; its portable ZIP job was skipped. The offline-pack integration workflow [run 41129888732](https://github.com/zealousvec/Saylacian/actions/runs/41129888732) reports failure but has zero jobs and no failed check-run, so GitHub provides no step or log identifying a code failure. That manually dispatched workflow failure remains unexplained.

The current implementation and language limitations are summarized below. The dated release-preparation notes later in this file are historical records, not current instructions.

## Final local release-candidate verification — historical record (2026-10-30)

- At the time of this prepublication review, public `main` remained at `c4f2f87270c22a05e772816ce98e57a99b871b18`. The source alpha was subsequently merged in PR #1.
- A clean clone of local commit `bea5ec1f393e7ff634db81b98ca6d048c5202247` built the latest portable candidate. It has 629 manifest-listed files plus the checksum index, one EXE, and a 69,945,461-byte ZIP with SHA-256 `43aaf3efbc54b29ee8c56b01c78eb3351d9bb5d5bbc0c7eb9c0adee846e557f7`. No translation pack weights, cuDNN DLL or Poppler files are included. The 4.59 MiB py3langid language-detection model is included. The manifest records `runtime_verified: false`.
- The dependency-rich checkout and a fresh clone each passed 195 tests, 2 skips and 191 subtests. Ruff, compilation, dependency consistency and release-safety checks passed. French and Somali pack download/hash/inference checks were previously run in isolated temporary storage with network denied during inference; they do not verify the packaged EXE.
- No disposable Windows VM was available for that review. Packaged EXE launch, true external clipboard delivery and screen-reader behavior were not verified. Binary licensing still needs confirmation for Microsoft VC runtime files, Intel `libiomp5md.dll`, GLEW wheel provenance and the Material Design Icons binary. These remain relevant to binary distribution; no binary is published. See the [historical release checklist](GITHUB_RELEASE_CHECKLIST.md).
- The pre-existing unstaged edit to `docs/TECHNICAL_AUDIT.md` remains outside the candidate commits and is preserved.

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

## Historical development record (2026-10-30)

### Current release completion work (2026-10-30)

- The Old Nubian converter now uses the 29 single-character readings in van Gerven Oei (2024), Table 1, CC BY 4.0, with attribution recorded in `docs/THIRD_PARTY_NOTICES.md`. Unmapped Coptic letters remain unchanged and receive a warning. This replaces the prior 34-entry DBMNT-derived mapping; no DBMNT table content is bundled.
- User-facing app, website, README and support labels use alpha-testing language and state remaining language/script limits directly.
- Changes are local and unpushed. On 2026-10-30, the working branch was `main` at `527df1569da68a5dadb758eafd9f0693aff983db`, 112 commits ahead of public `main`; the working tree also contained the release-campaign edits listed by `git status`. No push was made.
- Local commits `bab24a31b699c53601c6bfe780ede6bb7f43fbcb`, `11c4a9eba28739fb701fd5b1e870625b63472bbf`, and `eebe9e9cb927d3e0cc834ee4ed689399798187bb` prepare the alpha source, record clean-clone verification and make the portable builder independent of the caller's working directory. The local branch is 115 commits ahead of public `main`; no push was made. A pre-existing edit to `docs/TECHNICAL_AUDIT.md` remains unstaged and preserved.
- The superseded portable candidate from commit `5a749ad169f78cd5f4693f80c183fd431990d95c` contained no offline translation pack weights and no Poppler files. It did include py3langid's 4.59 MiB language-detection model; earlier notes saying “no model weights” omitted that classifier. Its runtime was not verified.
- The Kivy source-app self-test passed in an isolated temporary profile. The website headless Edge check passed its eight API, conversion, clipboard-double and responsive-layout checks. The package itself was not launched because it is unsigned; Windows Smart App Control and clean-machine behavior remain unverified.
- Full suite in the dependency-rich checkout: **195 passed, 2 skipped, 191 subtests**. Ruff lint and formatting, compileall, `pip check`, release-safety scan, package-manifest hash verification and `git diff --check` passed. No external clipboard was accessed.
- Fresh local clone `eebe9e9` installed from `requirements-dev.txt` passed **186 tests, 11 skips, 191 subtests**. The skips are model-dependent tests before packs were installed. Kivy self-test passed. Pinned French and Somali packs were downloaded to isolated temporary storage; SHA-256/version receipts passed and both directions per pack returned output with socket connections blocked during inference. Somali sample output remains imperfect and is not human-validated.

- A prior publication recorded `main` at `ca0ef3e40215762f8e8cfb4da0c839680764d6c8`. Later publication superseded it; current `main` is identified at the top of this page.
- GitHub Actions run `40086510600` for that commit failed one test: `test_installed_pack_is_used_by_offline_route_and_removal_is_scoped`. Windows compared the resolved `runneradmin` path returned by the route with the same temporary directory written using its `RUNNER~1` alias.
- A local-only test adjustment compares the returned route to `folder.resolve()`, preserving the assertion that the route selects the exact expected directory. The earlier `test_download_verifies_hash_installs_version_and_reports_progress` remains unchanged. This follow-up has not been pushed.
- Five local educational/audit documents are prepared: `ARCHITECTURE_EXPLAINED.md`, `CODEBASE_WALKTHROUGH.md`, `TECHNICAL_AUDIT.md`, `FOUNDER_LEARNING_GUIDE.md`, and `DEVELOPMENT_ROADMAP.md`.
- After the local assertion adjustment, the affected two model-pack tests pass and the full local suite reports **80 tests and 66 subtests passed**. Compilation, workflow Ruff lint, formatting, dependency checks, release safety scan, whitespace, and changed-document link checks pass. No CI run has verified this follow-up yet.
- Public repository metadata still describes Saylacian as “non-profit,” while `AUTHORS.md` says it is not a registered nonprofit. A repository admin should correct that metadata separately.

## Release and verification history

Before publication, recorded clean-clone checks reported 68 passed/12 skipped before model packs and 71 passed/9 skipped after installing and verifying the packs. Those are prior recorded results, not a fresh clean-clone run for this cleanup.

In the current local checkout, the full test suite passed with **80 tests and 66 subtests**. Compilation, the workflow's Ruff correctness selection, Ruff formatting, the release safety scanner, and `git diff --check` passed. Local model weights were present, so installed-model tests ran; GitHub CI intentionally does not download those weights.

## Still open

1. Build the final portable ZIP from the final committed tree and verify manifest/checksum; inspect the workflow artifact job.
2. Run Windows CI on the pending source changes after an approved push.
3. Verify screen-reader/keyboard accessibility and real clipboard formats in a disposable Windows VM; no such VM is available in this session.
4. Obtain fluent Somali review and specialist/community review for historical-script tables before making stronger quality claims.
5. Check native DLL distribution terms and validate the portable app on a clean Windows host; the current unsigned build is not ready for ordinary-user distribution.
6. Ask a repository administrator to correct the public project description and review account-level security settings.
7. Android/iOS builds and Store submission remain out of scope.
