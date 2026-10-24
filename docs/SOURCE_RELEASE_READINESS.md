# Source release readiness audit

**Audit date:** 2026-10-24

**Scope:** source-only experimental GitHub alpha. Local checkout/index and authenticated-profile read only; no repository, account setting, publication, or UI changes.

## Result

The candidate is prepared for final owner review. The owner approved GNU AGPL-3.0-or-later for Saylacian-authored code they own or have the right to license. Root `LICENSE` matches the complete official GNU text byte-for-byte (SHA-256 `0D96A4FF68AD6D4B6F1F30F713B18D5184912BA8DD389F86AA7710DB079ABCB0`). Project metadata and 62 first-party Python/Kivy/web/config source files identify AGPL-3.0-or-later. Third-party works remain separately licensed.

The authenticated GitHub profile has display name `zealous` and login `zealousvec`; the owner selected `zealous` for public attribution. The connector does not expose the account's privacy toggle or generated noreply address, and GitHub CLI is not installed. No email was configured. No accessible `zealousvec/Saylacian` repository was found; GitHub 404 cannot establish name availability because private or inaccessible repositories can return the same response.

The local folder is named `Saylacian`; branch is `codex/release-prep`. A local initial commit and `main` branch are prepared. No remote is configured. No mouse or keyboard control was used. The authenticated account is `zealousvec`; its visible repository list contains no `Saylacian` repository. Repository creation and security settings are unavailable through the connected GitHub tools, and GitHub CLI is absent. The owner-provided noreply identity is set locally; account-level private-email settings could not be verified.

## Staged-file audit

All 518 initial staged candidates were reviewed. Final index: 149 files, 1,298,779 bytes, largest file 99,746 bytes. 373 original candidates remain unstaged but preserved. Exclusions include historical preview captures, generated test output, obsolete reports/inventories, unused UI experiment and preview utility, and a duplicate notice. No local data was deleted. The two real app screenshots and approved Kivy UI remain.

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

1. Source scan found no specific ownership exception or copied third-party implementation. With no Git history or contributor registry, per-line provenance cannot be proven; the owner licence grant remains limited to code they own or have the right to license.
2. The owner-authorized public repository still needs creation. The authenticated account is verified and no `Saylacian` repository appears in its visible repository list. The installed GitHub connector has no create-repository operation and GitHub CLI is absent.
3. Local branch `codex/release-prep` contains the initial commit; local `main` points to the same commit. The confirmed noreply identity is configured per-repository. GitHub profile privacy settings are not exposed to current tools.
4. Private vulnerability reporting, Dependabot, secret scanning/push protection and notification settings remain unverified/unconfigured because the repository is not created and the connector exposes no repository-settings operations.
5. The owner must separately approve the initial public push. No remote, push, release or publication exists.

### Separate binary/mobile work (not blockers for source alpha)

- Inspect the exact packaged KivyMD MDI font and all collected Windows DLL notices.
- Rebuild/test Windows installer; resolve code signing and Smart App Control reputation without weakening security.
- Build and test Android/iOS packages on real devices.
