# GitHub source alpha checklist

Scope: source-only experimental alpha. One local initial commit has been prepared; no remote, public repository, push, tag, release, deployment, or account-setting change exists.

## Completed locally

- [x] Audited all 518 initial staged candidates. Historical/generated captures, obsolete reports, unused UI experiment, duplicate notice and other clutter were unstaged without deleting local data. Approved Kivy interface and two clean screenshots remain. Final index: 149 files / 1,298,779 bytes.
- [x] README labels Somali translation and partial Borama/Kaddare conversion experimental; setup and contribution guidance retained.
- [x] Root `LICENSE` is byte-identical to official GNU AGPLv3 text. Owner approved AGPL-3.0-or-later only for Saylacian-authored code they own or can license. Project source/config files carry SPDX identifiers; independently licensed assets and data remain separately noticed.
- [x] Audited all 62 AGPL-marked code/config files for copyright/licence headers, source URLs, and copied/adapted-from markers. No third-party implementation or known outside contributor was found. Git history is empty, so the scan cannot prove per-line provenance; no specific exception requiring separate permission was identified. AGPL remains limited to original code the owner has rights to license.
- [x] Reviewed chart/font/model/dataset/dependency notices and recorded file-level scope in `docs/LICENSING.md` and `docs/THIRD_PARTY_NOTICES.md`.
- [x] Clean Windows clone installed dependencies, fetched/checksummed Somali and French packs, tested offline translations and a Kaddare round-trip, and launched the Kivy event loop. Full local suite and static checks are documented in `docs/SOURCE_RELEASE_READINESS.md`.
- [x] Secret/path scan found no recognized credentials or local profile paths; staged Markdown local links resolve. No installer/DLL/EXE/model weights are staged.
- [x] The local checkout folder is named `Saylacian`. Authenticated GitHub profile selection: public attribution `zealous`; login `zealousvec`. No accessible `zealousvec/Saylacian` repository was found, but the 404 cannot prove name availability (private/inaccessible repositories may also return 404).

## Remaining before publication

- [ ] Create the already-authorized public `zealousvec/Saylacian` repository. The authenticated account and currently visible repositories were checked; no repository with this name is present. The available GitHub connector has no create-repository or repository-security-settings operation, and GitHub CLI is absent, so creation cannot be completed from this session.
- [ ] Repository-local author identity is `zealous` with the owner-provided GitHub noreply address. Commit `594b4807e32a3feb9da6a3c943845b423d8e9a29` contains 149 files on `codex/release-prep`; local `main` points at this commit. GitHub account email-privacy settings are not exposed to the connected tools, so they remain unverified.
- [ ] After repository creation and initial push approval, enable and verify Private vulnerability reporting, Dependabot alerts/updates, secret scanning/push protection where available, and maintainer security notifications. The connector has no repository security-settings operation; none of these are claimed enabled.
- [ ] Owner must separately approve the initial public push. No source or release has been published.

## Separate binary/mobile checks (not source-alpha blockers)

- [ ] Inspect exact packaged KivyMD MDI font and native Windows DLLs; include required notices.
- [ ] Rebuild/test Windows installer and address signing/Smart App Control reputation without weakening security settings.
- [ ] Build and test Android/iOS packages on real devices.

## Optional after source alpha

- Fluent-speaker Somali review, expanded translation evaluation, and broader historical-script validation.
- Mobile runtime and device performance work.
