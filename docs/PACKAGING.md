# Platform build evidence

For current language and platform capability status, see [`SUPPORT_MATRIX.md`](SUPPORT_MATRIX.md). For Windows signing and application-control evidence, see [`WINDOWS_RELEASE_SECURITY.md`](WINDOWS_RELEASE_SECURITY.md). The build details below are historical evidence, not a claim that a binary is releasable.

## Current source acceptance

As of 2026-10-25, the local Windows Python source app passes 149 tests, 2 symlink-permission skips, and 200 subtests. The isolated live Kivy acceptance passed 19 checks with networking blocked and runtime data redirected to a temporary directory. FBO captures at 320x640, 390x780, 780x390, 768x1024 and 1366x768 were visually reviewed; the landscape case is intact. Clipboard tests use an in-memory adapter; real Windows/external-app delivery is unverified. The unsigned packaged app remains runtime-unverified under the host's enforced application-control policy. Do not bypass Windows security controls or distribute the candidate.

## Windows

A PyInstaller 6.22.3 directory build completed with KivyMD resources, Noto fonts, mapping JSON, and local English/French models/tokenizers. `Saylacian.spec` is the reproducible recipe:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm Saylacian.spec
```

The previous output is preserved at `_cleanup_review/generated-files/dist/corrective-20261023/Saylacian/Saylacian.exe`. The whole output directory is needed; the EXE alone is not a standalone release. The console setting is currently enabled to diagnose launch failures. This is an unsigned local development build.

The first windowed smoke check timed out without evidence. A subsequent diagnostic console build was rejected by Windows with: “An Application Control policy has blocked this file.” No security policy was changed or bypassed. Packaged startup, packaged inference and clean-machine/offline acceptance are therefore **not verified**, despite a successful build. Source `--self-test` passed with Python socket connections blocked. A package must pass the same checks on an authorized Windows test machine before release.

`--self-test` writes evidence to the folder selected by `SAYLACIAN_EVIDENCE`; it does not use OS mouse/keyboard automation.

## Android

No APK was built or tested. Kivy documents Buildozer/python-for-android, with Linux/macOS or WSL for Windows:
https://kivy.org/doc/stable/guide/packaging-android.html

`wsl.exe` exists on the host, but the available-distribution query returned no distribution names. No WSL/SDK/NDK installation or system setting was changed. CTranslate2 also requires an Android-compatible native build/recipe; its Windows wheel cannot be copied into an APK. A mapping-only build route and a tested native semantic runtime must be distinguished. Do not advertise English/French meaning translation on Android until actually built and tested.

## iOS

No build was attempted. Kivy's documented route requires macOS, Xcode, kivy-ios and device/simulator testing; signing/distribution constraints remain:
https://kivy.org/doc/stable/guide/packaging-ios.html

No free public App Store release is promised and no signing/purchase action has been taken.

Final historical build used a fresh `--distpath dist/corrective-20261023` after an overwrite failed on generated cache files. Its output was moved, intact, to `_cleanup_review/generated-files/dist/corrective-20261023`. Revision B external KV resource was subsequently copied into that directory and its SHA-256 verified. Binary and layout fingerprints are in `windows-build-result.json`. The blocked runtime gate still applies; no package success is inferred from source tests.

## Offline language-detection rebuild — 2026-10-23

After adding bundled offline language identification, PyInstaller completed successfully with `Saylacian.spec` using isolated paths:

- Output: `build/`
- Build work files: `<PROJECT_ROOT>`
- EXE SHA-256: `A449B80100C70DB642814A9606F368CBAB44F51A73AE7B8B5DA8D2A41CC44982`
- Complete onedir payload: 672,772,874 bytes. It includes `py3langid/data/model.npz.xz`, Somali model/tokenizer files, Noto Osmanya and project notices.

The build completed; the new binary was **not launched**. Windows Application Control blocked the prior unsigned build and remains a known host gate. No security settings were changed or bypassed. This artifact is a development build, not a runtime-verified release. The full output directory, rather than only the EXE, is required.

## Current all-pairs rebuild — 2026-10-23

Rebuilt the current source after adding the Somali↔French local pivot, using an isolated temporary output path to preserve the project's older build:

- Output directory: `dist/`
- Build work files: `%TEMP%/`
- Complete onedir payload: 672,773,295 bytes across 639 files.
- `Saylacian.exe`: 11,627,781 bytes; SHA-256 `CF313D0BA9DD6BE79A135D0D414AC255EE9DE7F4C63F0A8144D3C5DD8FB43FF7`.
- PyInstaller archive inspection confirmed `saylacian.core.translation`, `saylacian.core.transliteration` and `py3langid.langid` are bundled.
- SHA-256 matches passed for all four meaning-model weights, the Osmanya font, sampled notices and language-ID model data.

This proves build/resource inclusion, not runtime behavior. The package was not launched: the host previously blocked its unsigned executable under Application Control. No bypass or security-setting change was attempted. Use the source launcher in `RUN.md` for the verified UI and meaning-pair checks.

## Clean Windows security candidate — 2026-10-23

The prior onedir build was inspected after Windows blocked it. The Code Integrity log recorded an enforced block, the executable was unsigned, and PyInstaller had included seven unrelated DLLs from Codex's Poppler runtime via inherited `PATH`. That candidate remains preserved for audit and is not distributable.

`Saylacian.spec` now excludes unused Kivy GStreamer audio/video support. A second build used a child-process-only PATH with Codex runtime paths removed:

- Candidate: `dist/`
- 602 files, 730,213,910 bytes; full manifest at `<PROJECT_ROOT>`; per-file `SHA256SUMS.txt` is inside the directory.
- EXE SHA-256: `07F0BEC5DC29BB4C8D3FCB793C1B1191A8803EA475696F5755A70EC604272ED2`.
- PE import scan: 102 native PE files parsed, no non-system unresolved imports, no GStreamer player, no Poppler DLLs or Codex runtime references.
- The candidate is still unsigned (76 of 102 PE files lack Authenticode signatures), and it was not run. Source tests do not establish packaged runtime. See `WINDOWS_RELEASE_SECURITY.md` for block evidence, dependency checks and signing options.

## Clipboard and synthetic-model rebuild — 2026-10-23

Rebuilt after adding the Saylacian Text clipboard representations and the guarded synthetic English→Somali candidate. Output is isolated from prior package artifacts:

- Directory: `dist\Saylacian-share-release-20261023` (preserved in the project; `dist/` is ignored by Git)
- 653 files; total payload 736,313,937 bytes.
- `Saylacian.exe`: 11,709,849 bytes; SHA-256 `6B5B2E2DA1025563B4F30DC032004BCA0B3ADC9A101213BDB337170643678343`.
- Candidate weight: 61,622,739 bytes; SHA-256 `62AACB4EC5812CE20A1EB2563FE763D16D20858E2490D6D8BDD0A3A1F4F72C22`, matching the source model manifest.
- Required chart fonts, external KV layout, candidate model/tokenizers, and model attribution notice exist in the output. Recursive archive inspection confirmed `saylacian.core.interchange`, `saylacian.core.clipboard_repr`, `saylacian.core.windows_clipboard`, and `saylacian.core.translation` are bundled.
- Build completed and source tests passed (60 tests plus 66 subtests). The unsigned package was not run; host Application Control blocked an earlier development executable. Runtime acceptance remains gated by an authorized Windows policy path.

## Final-master rebuild — 2026-10-23

Rebuilt the current source, including privacy-safe startup diagnostics and the script-reference picker fix, into a separate Downloads folder:

- Candidate: `dist/`
- Build: PyInstaller 6.22.3, `Saylacian.spec`; 654 files, 736,562,181 bytes before checksum list.
- EXE SHA-256: `0B9AD26C183780CD9A0ED0F750C1E8717627F40387391972261179A60CD92D2F`.
- Full per-file manifest: `<PROJECT_ROOT>`; `SHA256SUMS.txt` is beside the executable.
- PyInstaller archive inspection found `saylacian.core.diagnostics`, `saylacian.core.interchange` and `saylacian.core.translation`. External Kivy KV, Borama chart font, synthetic Somali model and notices were present.
- Build and inclusion are verified. Executable was not launched: an earlier unsigned build hit Windows Application Control. No bypass was attempted; packaged runtime needs an authorized tester/environment.

## Windows Store MSIX preparation — 2026-10-23

`tools/package_msix.py` consumes the already-built clean candidate; it does not invoke PyInstaller. It validates every source-manifest checksum, overlays current `notices/`, creates draft monochrome package logos, writes a full-trust desktop Appx manifest, calls Microsoft MakeAppx, unpacks the result, and compares every payload file byte-for-byte. It does not sign, install, or launch the package.

- Package: `<PROJECT_ROOT>`.
- Adjacent integrity/build manifest: `.msix.manifest.json`; package SHA-256 and Microsoft MakeAppx hash/version are recorded there.
- Package is 585,395,141 bytes (below Microsoft's 25 GB Store MSIX limit), SHA-256 `bef1fa9e28a93b51b72ad333955c2ca85f8eeacf9b39a5abc7148f36933e2956`. Its internal SHA256SUMS lists and verifies all 619 other payload files; MakeAppx unpack verification matched all 620 files. Defender reported no threats; `Get-AuthenticodeSignature` reports `NotSigned` by design for a Store submission draft.
- `IdentityPending` and `Publisher-PENDING` must be replaced by exact values from Partner Center. No account or app name has been reserved.
- Runtime, offline UI use, fonts, clipboard and installation remain unverified because this unsigned build is not installable under the active Windows policy. Source-app tests are not package-runtime evidence.
- Microsoft's current onboarding has no registration fee; individual onboarding requires government ID and selfie verification. Store certification and publisher approval are still required. See `STORE_SUBMISSION.md`.

## Portable alpha candidate — 2026-10-30

Built from a clean clone of commit `bea5ec1f393e7ff634db81b98ca6d048c5202247` with the pinned portable-build recipe. The ZIP is 69,945,461 bytes (SHA-256 `43aaf3efbc54b29ee8c56b01c78eb3351d9bb5d5bbc0c7eb9c0adee846e557f7`). Its manifest covers 629 payload files; the ZIP also contains the checksum index. Manifest hashes, archive entries and the sidecar all verified. It contains one EXE, no offline translation packs, no cuDNN DLL and no Poppler files. It does include py3langid's 4.59 MiB language-detection model, CPython licence and all 13 SDL2 wheel licence texts. The builder excludes cuDNN because the app uses CTranslate2 on CPU.

The manifest deliberately records `runtime_verified: false`. No isolated Windows VM was available, so the EXE was not launched and clipboard/screen-reader checks were not performed. Microsoft VC runtime distribution terms, Intel OpenMP redistribution terms, GLEW wheel provenance and exact Material Design Icons font provenance remain binary-release gates. The candidate is local and unpublished; do not distribute it until these checks pass.
