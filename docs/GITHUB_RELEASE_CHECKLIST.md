# GitHub release candidate verification

> Historical prepublication checklist from 2026-10-30. The source-only alpha was later merged to `main` as `4533b55` through [PR #1](https://github.com/zealousvec/Saylacian/pull/1). Do not use the old push plan below. For current repository state, see [project status](PROJECT_STATUS.md).

**Checked:** 2026-10-30

**Repository:** [zealousvec/Saylacian](https://github.com/zealousvec/Saylacian)

**Scope:** local source update and Windows portable candidate. Nothing was pushed, tagged, or published.

## Checklist

| Criterion | Status | Evidence |
|---|---|---|
| Audit the local commit history and tracked files | **PASS** | Reviewed the 117 local commits present at the start of this verification, then checked the two focused packaging fixes separately. The history scan covered 1,035 unique reachable objects and 602 text blobs. No recognized credential strings, email addresses, or local Windows profile paths were found. No generated environments, build outputs, model packs, executables, DLLs, or tracked files over 5 MiB were found in the source tree. The pre-existing edit to `docs/TECHNICAL_AUDIT.md` remains uncommitted and excluded. |
| Confirm the project licence | **PASS** | `LICENSE` is byte-for-byte identical to the official GNU AGPLv3 text (SHA-256 `0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0`). AGPL-3.0-or-later applies only to code the project licensor owns or may license. |
| Review source assets and notices | **PASS** | Third-party notices distinguish fonts, chart-derived script data, test datasets, model packs, and dependencies. Pillow is identified as MIT-CMU with its codec notices. The package builder includes the active CPython licence and all 13 licence files exposed by the pinned SDL2 wheel. The upstream GLEW notice is preserved verbatim, including its trailing spaces; a whole-range `git diff --check` flags only those notice lines. The Windows bundle's unresolved native-code permissions are listed separately below. |
| Build and inspect the portable ZIP | **PASS** | Clean clone of `bea5ec1f393e7ff634db81b98ca6d048c5202247` produced a 69,945,461-byte ZIP. Its 629 manifest-listed files and checksum index verified; ZIP SHA-256: `43aaf3efbc54b29ee8c56b01c78eb3351d9bb5d5bbc0c7eb9c0adee846e557f7`. It contains one EXE, 4.59 MiB of py3langid language-detection data, no offline translation pack weights, no cuDNN DLL, and no Poppler files. Manifest: `runtime_verified: false`. |
| Run the packaged EXE on Windows | **EXTERNAL REVIEW REQUIRED** | No disposable Windows VM or Windows Sandbox is available. The candidate is unsigned and was not launched on the owner's Windows session. Startup, navigation, packaged conversion, offline inference, installation, and Smart App Control behavior remain unverified. No Windows security setting was changed. |
| Resolve binary dependency licensing | **EXTERNAL REVIEW REQUIRED** | The payload includes Microsoft VC runtime DLLs and Intel's `libiomp5md.dll` (SHA-256 `982233366b0afcda1e0f55a0b134097e35b779613f54ddb69e685e6cd06b755f`). Microsoft's [redistribution guidance](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170) limits distribution to licensed Visual Studio users and its terms. The package also carries CPython's Microsoft-code conditions; confirm that these cover every copied/renamed runtime file and the user's agreement path. Intel's [deployment guidance](https://www.intel.com/content/www/us/en/docs/dpcpp-cpp-compiler/developer-guide-reference/2025-1/redistribute-libraries-when-deploying-apps.html) requires checking the applicable licence and redistributable list; the candidate has no matching Intel EULA/list for its bundled DLL. The GLEW 2.3.1 notice is included, but the Kivy wheel does not provide binary build provenance. Exact Material Design Icons font provenance remains incomplete. Do not distribute the ZIP until those checks are resolved. |
| Run tests and source checks | **PASS** | Full dependency-rich checkout and a fresh local clone each passed **195 tests, 2 skipped, 191 subtests**. Ruff lint and format, compileall, `pip check`, and the release-safety scanner passed in both. |
| Verify real clipboard and accessibility behavior | **EXTERNAL REVIEW REQUIRED** | No disposable Windows VM is available for real external-app clipboard paste/import or Narrator/NVDA testing. Existing automated clipboard tests use safe doubles; the owner's clipboard and accessibility settings were not touched. |
| Review user-facing docs and CI | **PASS** | README, support matrix, source setup, portable setup notes, changelog, dependency notices, and GitHub Actions were checked against the current implementation. Somali and historical-script limits remain stated; the bundled detector model is distinguished from downloadable translation packs. The workflow's automatic CI checks source tests; the portable build is a manual workflow job. |
| Verify remote and GitHub Actions | **EXTERNAL REVIEW REQUIRED** | The public `main` still points to `c4f2f87270c22a05e772816ce98e57a99b871b18`; `codex/user-only-source` points to `50b741b12091de6feaad70a19b20bb7e5cd4201a`. Local `main` is 120 commits ahead of public `main`, including this release-candidate review commit. No CI run for these local commits exists until they are pushed. |

## Push and publication plan

After the owner approves the exact source snapshot, recheck `git status`, confirm public `main` still points to `c4f2f87270c22a05e772816ce98e57a99b871b18`, review the 120 local commits ahead of `main`, and push with a normal `git push origin main`. That command will send all 120 commits, not only the final review commit. Then inspect the new GitHub Actions run and fix any failure locally. Do not force-push.

Do not attach the portable ZIP or publish a Windows release until the external binary licence and isolated runtime checks pass. Do not create a tag or GitHub Release without separate approval. No Store account, package identity, signature, or submission is prepared.

Saylacian remains an alpha: Somali translation needs fluent-speaker review; Borama and Kaddare mappings are partial; Old Nubian reading is limited; modern Nubian varieties are unsupported. These are product limits, not release-check claims.
