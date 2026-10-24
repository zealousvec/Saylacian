# GitHub source alpha checklist

Scope: source-only experimental alpha. The verified public repository exists and `origin` is configured. No source push, tag, release, deployment, or account-setting change has occurred.

## Completed locally

- [x] Audited all 518 initial staged candidates. Historical/generated captures, obsolete reports, unused UI experiment, duplicate notice and other clutter were unstaged without deleting local data. Approved Kivy interface and two clean screenshots remain. Final index: 149 files / 1,298,779 bytes.
- [x] README labels Somali translation and partial Borama/Kaddare conversion experimental; setup and contribution guidance retained.
- [x] Root `LICENSE` is byte-identical to official GNU AGPLv3 text. Owner approved AGPL-3.0-or-later only for Saylacian-authored code they own or can license. Project source/config files carry SPDX identifiers; independently licensed assets and data remain separately noticed.
- [x] Audited all 62 AGPL-marked code/config files for copyright/licence headers, source URLs, and copied/adapted-from markers. No third-party implementation or known outside contributor was found. Git history is empty, so the scan cannot prove per-line provenance; no specific exception requiring separate permission was identified. AGPL remains limited to original code the owner has rights to license.
- [x] Reviewed chart/font/model/dataset/dependency notices and recorded file-level scope in `docs/LICENSING.md` and `docs/THIRD_PARTY_NOTICES.md`.
- [x] Clean Windows clone installed dependencies, fetched/checksummed Somali and French packs, tested offline translations and a Kaddare round-trip, and launched the Kivy event loop. Full local suite and static checks are documented in `docs/SOURCE_RELEASE_READINESS.md`.
- [x] Secret/path scan found no recognized credentials or local profile paths; staged Markdown local links resolve. No installer/DLL/EXE/model weights are staged.
- [x] Authenticated owner `zealousvec` verified. Public repo [zealousvec/Saylacian](https://github.com/zealousvec/Saylacian) is public, has default branch `main`, and is empty (size 0, no remote refs). Local `origin` matches the expected HTTPS URL. The current GitHub description differs from the approved copy and mentions “non-profit”; correct it before publication.

## Remaining before publication

- [ ] In Settings → General → Description, set `Open-source, offline-first translation and language-preservation software.` and save. The current text is different and calls the project “non-profit,” which conflicts with the project credits.
- [ ] In Settings → Security → Advanced Security, enable Private vulnerability reporting, Dependabot alerts, Dependabot security updates, Secret scanning, and Push protection wherever GitHub offers the toggle. Verify each control after enabling; current connector only reads public repository data, so none are claimed enabled.
- [ ] Watch → Custom → Security alerts (or All activity), then check GitHub Settings → Notifications → Watching and enable email delivery if desired. Verify the repository notification subscription.
- [ ] Local commit `594b4807e32a3feb9da6a3c943845b423d8e9a29` contains the 149-file source tree; docs follow-up `0744ccf2f0d7f80aa83f31eff31028c472c0dd50` is at local `main` and `codex/release-prep`. Local `origin` points to the empty public repo.
- [ ] Owner must separately approve the initial public push. Proposed command: `git push -u origin main`. It publishes only local `main` history (the two commits above), no tags, and does not force-push. No source or release has been published.

See [GitHub security settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-security-and-analysis-settings-for-your-repository) and [private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository) for the controls above.

## Separate binary/mobile checks (not source-alpha blockers)

- [ ] Inspect exact packaged KivyMD MDI font and native Windows DLLs; include required notices.
- [ ] Rebuild/test Windows installer and address signing/Smart App Control reputation without weakening security settings.
- [ ] Build and test Android/iOS packages on real devices.

## Optional after source alpha

- Fluent-speaker Somali review, expanded translation evaluation, and broader historical-script validation.
- Mobile runtime and device performance work.
