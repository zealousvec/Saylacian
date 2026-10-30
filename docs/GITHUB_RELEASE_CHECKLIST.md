# GitHub source alpha status

**Checked:** 2026-10-30
**Repository:** [zealousvec/Saylacian](https://github.com/zealousvec/Saylacian)
**Scope:** public source repository only. No release, tag, installer or mobile package is published.

## Published and verified

- The initial alpha-testing source snapshot was published on `main`; its reviewed snapshot contained 149 files.
- The repository contains the approved GNU AGPLv3-or-later licence for Saylacian-authored code the owner can license. Third-party works retain separate notices and licences.
- Somali translation remains in alpha testing. Borama and Kaddare cover selected chart entries. Old Nubian has a limited, attributed 29-character table. Modern Nubian varieties are not implemented.
- A read-only remote check on 2026-10-30 confirmed public `main` at `c4f2f87270c22a05e772816ce98e57a99b871b18`. The local `main` was 112 commits ahead at `527df1569da68a5dadb758eafd9f0693aff983db`, with release-campaign edits still uncommitted. Nothing was pushed.
- A Windows portable ZIP candidate was built and its archive/manifest hashes verified. The manifest records `runtime_verified: false`; the candidate was not launched under Smart App Control or validated on a clean Windows host. Its current checksum and detailed evidence are in `docs/PROJECT_STATUS.md`.
- Local code commit `eebe9e9cb927d3e0cc834ee4ed689399798187bb` includes the portable-builder import fix. A fresh clone and virtual environment passed 186 tests with 11 model-dependent skips; Kivy self-test passed. French and Somali pinned packs were downloaded to a temporary store and both directions per pack produced output with network connections blocked during inference. This does not replace a clean-host binary test.

## Owner-controlled settings not verified here

- GitHub repository description and topics.
- Private vulnerability reporting, Dependabot, secret scanning, push protection, and maintainer notification settings.

These account settings are not changed or claimed enabled by this code audit. Verify them in GitHub settings if needed.

## Separate future release work

- Windows installer and native DLL licence audit, signing, Smart App Control reputation, and clean-device install tests.
- Android/iOS builds and real-device tests.
- A GitHub Release or tag requires separate owner approval.
