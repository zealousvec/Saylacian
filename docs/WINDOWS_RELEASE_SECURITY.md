# Windows release security review

Checked 2026-10-23. No security settings were changed, no blocked executable was launched, and no files were uploaded to public scanning services.

## Finding: why Windows blocked the first candidate

Candidate checked: `<USER_PROFILE>\Downloads\Saylacian-release-candidate-20261023\dist\Saylacian\Saylacian.exe`.

- Its SHA-256 matches its manifest, but Authenticode status is **NotSigned**.
- The read-only registry value `HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy\VerifiedAndReputablePolicyState` is `1` (Smart App Control enforcement). Device Guard reports code-integrity and user-mode code-integrity enforcement as `2` (enforced).
- Code Integrity Operational events 3077 and 3033 at 2026-10-23 21:17 name this exact EXE and say it did not meet signing-level requirements. Event 3077 is Microsoft's enforced App Control block event. The recorded policy ID is `0283ac0f-fff1-49ae-ada1-8a933130cad6`.
- This supports the cause: the freshly built, unsigned executable was unknown to the enforced trust policy. **It is not a malware verdict.** The warning alone cannot establish maliciousness. `CiTool --list-policies` was denied access, so I could not distinguish the Smart App Control policy from any additional enforced policy by policy metadata. SAC was independently confirmed On by its read-only state value.

Microsoft explains that unknown unsigned code is blocked by Smart App Control and recommends signatures from a CA in Microsoft's Trusted Root Program: [Smart App Control overview](https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/overview), [signing for Smart App Control](https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/code-signing-for-smart-app-control). Event meanings: [App Control event IDs](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/operations/event-id-explanations).

## Package and dependency checks

- The first candidate's 654-file manifest was checked against disk: **654/654 matched**, including its EXE hash `0B9AD26C183780CD9A0ED0F750C1E8717627F40387391972261179A60CD92D2F`.
- That candidate included seven validly signed DLLs from a separate Poppler runtime. PyInstaller found them through the inherited `PATH`; Kivy's unused GStreamer provider pulled them into the build. This was packaging contamination, not evidence of malicious code. That candidate is preserved for audit and **must not be distributed**.
- `Saylacian.spec` now excludes Kivy's unused GStreamer audio/video provider. I preserved the prior spec before this change at `<USER_PROFILE>\Downloads\Saylacian-Safety-Backups\final-master-post-edit-20261023\Saylacian.spec.before-native-runtime-cleanup` (SHA-256 `FD6595A070A53EFD89BEB435BEF5FDD18045F5A09C08E2AC29A4931EA37C8823`). A second build used a process-only `PATH` with external runtime paths removed; the original PATH and security settings were not changed.
- Clean candidate: `<USER_PROFILE>\Downloads\Saylacian-clean-release-candidate-20261023\dist\Saylacian`. It has 602 files, 730,213,910 payload bytes, **zero Poppler-origin references**, no GStreamer player, and no unresolved non-Windows PE imports. Its 102 PE files all parsed successfully. Manifest and per-file checksums are adjacent to the candidate.
- Clean candidate's PE signature scan: 26 files have valid existing Authenticode signatures; **76 PE files are unsigned** (including `Saylacian.exe`, 8 DLLs and 67 `.pyd` native modules). There were no `HashMismatch` or `NotTrusted` signatures. Direct distribution therefore needs a properly trusted signing/package strategy for all code components, then real policy-permitted runtime validation.
- `pip check`: no broken requirements. Read-only OSV batch queries checked all 29 versions in `requirements-runtime-lock.txt` and seven build tools (PyInstaller, pyinstaller-hooks-contrib, pefile, setuptools, pip, altgraph and pywin32-ctypes); no matching advisories were returned on 2026-10-23. This covers known database matches for those PyPI versions only; it is not a full security audit of native libraries or model files.
- Static source scan of `main.py`, `app/`, and `saylacian/` found no `eval`, `exec`, `pickle`, `os.system`, or `subprocess` use. This is a narrow source scan, not a malware verdict. Defender was active and real-time protection was enabled. On 2026-10-23, `MpCmdRun.exe` custom scans of the clean onedir folder and the later MSIX each reported **no threats found**. This is time- and signature-dependent scan evidence, not a guarantee of safety.
- No signer identity or valid code-signing certificate was present in the personal certificate stores; `signtool.exe` was unavailable. No signing key was generated or installed.

## Safe distribution choices

### Recommended for this independent project: Microsoft Store MSIX

Prepare a separate MSIX wrapper and verify Kivy's desktop behavior, writes to the user-data directory, offline models, package size, clipboard, and update/uninstall behavior. Store submission re-signs MSIX after certification, so the project does not need to buy or manage its own public certificate. Microsoft's current onboarding offers free individual developer registration, appropriate for personal/hobby projects, with identity verification. This lets ordinary users install through Windows' normal trusted flow. It still requires account enrollment, package validation, Store certification and explicit approval before submission; none has been done. Sources: [Store signing FAQ](https://learn.microsoft.com/en-us/windows/apps/publish/faq/get-started-with-the-microsoft-store), [individual developer accounts](https://learn.microsoft.com/en-us/windows/apps/publish/faq/open-developer-account), [distribution path choices](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/choose-distribution-path).

### Direct download: public CA code signing

Use a CA-trusted signing identity and sign all relevant executable components (EXE, DLL/PYD, installers and uninstallers), with SHA-256 and RFC 3161 timestamping. Verify every signature and produce a new manifest after signing. Microsoft's guidance says to sign all app binaries. A valid signature addresses Smart App Control's trust gate, but does not guarantee immediate SmartScreen reputation; new direct-download apps can still receive a reputation warning. Sources: [Microsoft signing guidance](https://learn.microsoft.com/en-us/windows/security/book/application-security-application-and-driver-control), [SmartScreen reputation](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation), [timestamp guidance](https://learn.microsoft.com/en-us/windows/win32/seccrypto/time-stamping-authenticode-signatures).

### Azure Artifact Signing

Microsoft's managed signing service supports public-trust signing, but current eligibility restricts individual developers to the United States and Canada; organizations in the UK may qualify after organization identity verification. Saylacian is not a registered company and no signing account exists, so this is not currently an available route unless the publisher separately meets eligibility. [Current eligibility and quickstart](https://learn.microsoft.com/en-gb/azure/artifact-signing/quickstart).

Self-signed certificates, local trust-store edits, disabling SAC, registry changes, and “Run anyway” are not release solutions. No such action was taken.

## Store MSIX preparation — 2026-10-23

The existing clean onedir candidate was reused; it was not rebuilt. `tools/package_msix.py` verifies the input manifest and all 602 candidate file hashes, copies that candidate into a temporary package layout, overlays the current release notices, generates monochrome draft package logos, applies an MSIX full-trust desktop manifest, and calls Microsoft's signed Windows SDK `MakeAppx.exe`. It then unpacks the MSIX and verifies the complete file set and SHA-256 for every file. It never signs or installs the package.

- Unsigned MSIX: `<USER_PROFILE>\Downloads\Saylacian-unsigned-store-candidate-20261023-v3.msix` (see adjacent `.manifest.json` for exact inputs, notice hashes and result).
- It is 585,395,141 bytes; SHA-256 `bef1fa9e28a93b51b72ad333955c2ca85f8eeacf9b39a5abc7148f36933e2956`. Store's published MSIX size limit is 25 GB.
- Microsoft `MakeAppx.exe` 10.0.26100.9169 (Authenticode-valid Microsoft signature); its SHA-256 is in the adjacent package manifest. It was downloaded as a NuGet package to a temporary Downloads directory, not installed system-wide.
- `MakeAppx pack` and `MakeAppx unpack` both succeeded. All 620 unpacked payload files and hashes matched the package layout; its internal SHA256SUMS index separately verified 619 entries. Defender custom scans of the clean candidate folder and this final package both reported no threats (2026-10-23). Earlier unsigned drafts without the final notice/checksum overlay are superseded by `-v3.msix`.
- The manifest still uses `Saylacian.IdentityPending` and `CN=Saylacian-Publisher-PENDING`. It is not Store-submittable until Partner Center assigns the exact reserved name and publisher. The three monochrome `S` package logos are generated draft assets, not an approved Saylacian logo.
- Authenticode reports the `.msix` as **NotSigned**. This is intentional for the Store route: Microsoft's documentation says Store submissions do not need a CA signature and Microsoft signs MSIX after certification. This file cannot be installed as a trusted local build and must not be treated as one.
- The 76 unsigned native PE files remain inside the app payload. Package signing and individual PE Authenticode signing are distinct. Store certification and normal installation/runtime testing are still required; no claim is made that the unsigned candidate would pass Smart App Control if sideloaded.
- This host's enforced policy blocked the unsigned EXE. I did not install or launch the unsigned MSIX, and did not alter SAC or Defender. Therefore packaged UI, translation, font, clipboard, close/restart and first-run behavior remain **runtime-unverified**. Source offline tests and existing UI evidence do not substitute for this gate.
- Windows App Certification Kit (`appcert.exe`) is not installed or present in the extracted BuildTools package. MakeAppx's schema/pack/unpack checks are not a substitute for WACK or Store certification.
- Final source verification on 2026-10-23: `pytest -q` passed (61 tests, 66 subtests); `pip check` reported no broken requirements; both release scripts passed `py_compile`; `tools/prepare_models.py --verify-only` verified 743,874,994 bytes across all pinned model files and archives without network access.
- Offline benchmark output is generated in local app data and is not stored in source. English/French routes have local smoke coverage; Somali remains explicitly experimental and automatic scores do not replace fluent review. This is source/model evidence, not the unperformed MSIX runtime test.

### Store enrollment, cost and certification

Microsoft's current new Partner Center onboarding has no registration fee for either account type. An individual account is intended for hobby/personal projects not published in relation to a trade or profession; the new individual flow requires government ID and selfie verification. Company account is required for business/professional publication and requires business verification. No account was opened, no name reserved, and no submission made.

Store MSIX submissions are automatically signed by Microsoft after certification. Microsoft requires the exact account app identity in the manifest and recommends Windows App Certification Kit plus hardware testing. Store certification includes security, technical and content checks and can require correction/re-submission. Official requirements and links are collected in `STORE_SUBMISSION.md`.

## Remaining release gates

- Run the MSIX on an authorized Windows test environment after Microsoft signs it or after an approved trusted signature exists. Test startup, offline language routes, fonts, clipboard, persistence, shutdown and updates; capture real evidence. The present Windows host is not an acceptable place to launch the unsigned candidate.
- Complete Store account identity verification, reserve the app name, insert Partner Center identity, and run Windows App Certification Kit. Account creation, name reservation and submission need the user's approval; none has been done.
- Binary licence review remains open. The portable builder now includes the active CPython licence, all 13 SDL2 wheel licence texts, and the GLEW 2.3.1 upstream licence; it excludes cuDNN because the application selects CPU inference. Microsoft's [VC runtime redistribution terms](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170) require checking that the CPython redistribution conditions and end-user terms cover every copied runtime file. Intel's [deployment guidance](https://www.intel.com/content/www/us/en/docs/dpcpp-cpp-compiler/developer-guide-reference/2025-1/redistribute-libraries-when-deploying-apps.html) requires the applicable licence and redistributable list; neither is present for `libiomp5md.dll`. The Kivy GLEW wheel lacks binary provenance, and the exact Material Design Icons font source remains unpinned. These are binary-distribution gates, not source-repository blockers. Borama/Kaddare charts and derived font/data have CC BY-SA 4.0 attribution in `notices/HISTORICAL_SCRIPT_CHARTS.md`.
- Do not call either candidate a safe/release-ready binary until signed package validation and offline first-launch/use are tested on an authorized clean profile.
