# Saylacian project status — 2026-10-24

Saylacian's initial experimental-alpha source snapshot is public at [github.com/zealousvec/Saylacian](https://github.com/zealousvec/Saylacian). The published `main` commit at the start of this cleanup is `0f771f157da32d614690f927901896dd1e1b1c22` (`Clarify Saylacian's licensing and release status`). The initial source snapshot contains 149 files. No binary release or mobile release is available.

This page distinguishes public state from the current local cleanup. It must be updated again after a future approved push.

## Verified implementation status

- The main application is Python with Kivy/KivyMD. The approved UI is preserved.
- Meaning translation has offline English↔French model routes. Somali↔English is experimental; Somali↔French uses an experimental English pivot. Fluent-speaker evaluation has not established Somali quality.
- Somali Latin↔Osmanya conversion is implemented and experimental because mapping ambiguities and community review remain.
- Borama and Kaddare have partial chart-label conversions using private-use code points and separately licensed chart-derived assets. They are not standardized Unicode alphabets or validated word-level orthographies.
- Old Nubian Coptic-script→scholarly-Latin transliteration has a limited character table. Reverse conversion is experimental and can be ambiguous. It is not Old Nubian meaning translation or complete coverage.
- Modern Nubian varieties, including Nobiin, Kenzi/Mattokki, Dongolawi/Andaandi, Midob, Birgid, Dilling, Karko, Wali and Kadaru, have no implemented converter or translation route.
- The website source is a local Flask interface; it is not publicly deployed. The website UI does not expose the Old Nubian route.
- Android and iOS builds are not verified. No public Windows installer is available.
- AGPL-3.0-or-later applies only to Saylacian-authored code the licensor owns or may license. Third-party code and assets retain their separate terms.

## Current local cleanup (not yet published)

- Local branch: `codex/release-prep`, based on the published `main` snapshot.
- One focused code fix in `saylacian/core/model_packs.py` normalizes a verified installed pack root with `Path.resolve()`. This addresses a Windows path-alias mismatch in the existing pack-install regression test. It does not alter network hosts, file size checks, SHA-256 verification, staging, extraction, or installation behavior.
- Five local educational/audit documents are prepared: `ARCHITECTURE_EXPLAINED.md`, `CODEBASE_WALKTHROUGH.md`, `TECHNICAL_AUDIT.md`, `FOUNDER_LEARNING_GUIDE.md`, and `DEVELOPMENT_ROADMAP.md`.
- The local model-pack regression test passes. The full local suite passes with installed local model files. GitHub Actions on the published commit previously failed that Windows path assertion; this local fix has not yet been pushed, so no CI run has verified it remotely.
- Public repository metadata still describes Saylacian as “non-profit,” while `AUTHORS.md` says it is not a registered nonprofit. A repository admin should correct that metadata separately.

## Release and verification history

Before publication, recorded clean-clone checks reported 68 passed/12 skipped before model packs and 71 passed/9 skipped after installing and verifying the packs. Those are prior recorded results, not a fresh clean-clone run for this cleanup.

In the current local checkout, the full test suite passed with **80 tests and 66 subtests**. Compilation, the workflow's Ruff correctness selection, Ruff formatting, the release safety scanner, and `git diff --check` passed. Local model weights were present, so installed-model tests ran; GitHub CI intentionally does not download those weights.

## Still open

1. Review and approve the local path normalization fix and documentation changes.
2. After approval, push the focused commit and verify its Windows GitHub Actions run.
3. Align all published user-facing Nubian descriptions as part of that push.
4. Ask a repository admin to correct the public project description.
5. Obtain fluent Somali review and specialist/community review for historical script tables before making stronger support claims.
6. Continue separate Windows binary licensing/signing and Android/iOS device-build work before claiming those release targets.
