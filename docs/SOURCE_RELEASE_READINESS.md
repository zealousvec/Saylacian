# Source release readiness audit

**Audit date:** 2026-10-24

**Scope:** source-only experimental GitHub alpha. Repository metadata was read and `origin` was configured; no GitHub security setting, source publication, or UI change occurred.

## Result

The candidate is prepared for final owner review. The owner approved GNU AGPL-3.0-or-later for Saylacian-authored code they own or have the right to license. Root `LICENSE` matches the complete official GNU text byte-for-byte (SHA-256 `0D96A4FF68AD6D4B6F1F30F713B18D5184912BA8DD389F86AA7710DB079ABCB0`). Project metadata and 62 first-party Python/Kivy/web/config source files identify AGPL-3.0-or-later. Third-party works remain separately licensed.

The authenticated profile `zealousvec` owns public [zealousvec/Saylacian](https://github.com/zealousvec/Saylacian); GitHub confirms default branch `main` and an empty repository. The local `origin` URL matches it. The actual GitHub description currently differs from the owner-approved wording and includes “non-profit”; correct this before the source push. Repository security settings and account email-privacy state are not exposed by the connected read-only tools.

The local folder is named `Saylacian`; source root commit `594b4807e32a3feb9da6a3c943845b423d8e9a29` and subsequent release-preparation commits are reachable from both local `main` and `codex/release-prep`. `origin` points to the empty public repo; no remote refs exist. The noreply author is configured locally. Account-level private-email privacy was not verifiable. No mouse or keyboard control was used.

## Staged-file audit

All 518 initial staged candidates were reviewed. Initial commit: 149 files. Largest file: 99,746 bytes. 373 original candidates remain unstaged but preserved. Exclusions include historical preview captures, generated test output, obsolete reports/inventories, unused UI experiment and preview utility, and a duplicate notice. No local data was deleted. The two real app screenshots and approved Kivy UI remain.

No staged file exceeds 1 MB. No installer, DLL, EXE, wheel, archive, or model weights are staged. There are 0 unstaged changes.

## Ownership and third-party licence audit

All 62 AGPL-marked source/config files were audited for external copyright/licence notices, source URLs, and copied/adapted-from markers. No externally attributed source implementation or known outside contributor was found. There is no Git history or contributor registry, so the repository cannot prove per-line provenance; no specific exception requiring separate permission was identified. The owner licence grant remains limited to original code they own or can license.

- Root AGPL applies only to code the project licensor owns or can license; no third-party rights are claimed.
- Borama/Kaddare charts, chart-derived JSON mappings, and PUA display fonts remain CC BY-SA 4.0 with attribution and modification notes. Creative Commons lists GPLv3 one-way compatibility for CC BY-SA 4.0 adaptations, but does not list AGPL. These files stay outside AGPL scope.
- Noto Coptic/Osmanya remain SIL OFL 1.1. KivyMD 1.2.0 transitively supplies MDI under its release metadata's OFL 1.1 declaration; exact collected font provenance is a binary-package check.
- TICO-19 fixture is under TICO's CC0 release statement; all 150 rows preserve source URL and source-material licence (88 CC BY-SA 3.0, 2 CC BY-SA 2.5, 44 CC BY 4.0, 16 public-domain-labelled rows).
- Model weights are not in Git; manifests retain upstream licenses. Offline English/French packs declare MIT and Somali packs Apache-2.0. An experimental synthetic model with CC BY training-data concerns is not bundled/enabled.
- Python dependencies are installed from pinned upstream packages, not vendored source. Their notices remain separate. Windows DLL/installer terms are a binary distribution check; no such binaries are in this source index.

## Clean-clone validation

A fresh checkout was materialized from the staged index and installed from `requirements-dev.txt`.

- Before model packs: **68 passed, 12 skipped**.
- Somali and French packs were fetched from pinned sources and verified through the app's SHA-256/size-checked installer. Store was outside the clone's Git tree.
- With network socket connections blocked, English “Good morning.” → Somali “Subaxda wanaagsan.”; Somali “Subax wanaagsan.” → English “Good morning.”; English “Hello, how are you?” → French “Bonjour, comment allez-vous ?”; French reverse returned “Hello, how are you?”. Kaddare `shadh!` round-tripped through PUA output and back.
- After pack installation: **71 passed, 9 skipped**. Compileall, selected Ruff, `pip check`, and release safety scan passed.
- Actual Kivy app entered its main loop and remained alive for 12 seconds. No mouse/keyboard interaction occurred.

Final source formatting preserved the Kivy interface. The current-worktree suite passes: **80 tests and 66 subtests**. Python files now open with module explanations; inline comments were removed while required SPDX and functional directives remain. Ruff formatting, import sorting, compilation, dependency checks and release safety scan pass. Somali quality and partial historical-script coverage remain experimental.

## Remaining blockers / approvals

1. Source scan found no specific ownership exception or copied third-party implementation. With no pre-existing Git history or contributor registry at audit time, per-line provenance cannot be proven; the owner licence grant remains limited to code they own or have the right to license.
2. Repository description does not match the approved wording and incorrectly labels the project “non-profit.” Update it in Settings → General.
3. Enable and verify private vulnerability reporting, Dependabot alerts/security updates, secret scanning, and push protection in Settings → Security → Advanced Security. The connected GitHub tools cannot change/read these settings.
4. Configure Watch → Custom → Security alerts and verify email notifications if desired.
5. The owner must separately approve initial publication. Exact operation: `git push -u origin main` (non-force, branch only; no tags). No source or release has been published.

### Separate binary/mobile work (not blockers for source alpha)

- Inspect the exact packaged KivyMD MDI font and all collected Windows DLL notices.
- Rebuild/test Windows installer; resolve code signing and Smart App Control reputation without weakening security.
- Build and test Android/iOS packages on real devices.
