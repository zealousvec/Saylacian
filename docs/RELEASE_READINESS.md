# Windows release status

Saylacian is in alpha testing for Windows. The source app and offline routes have been checked in a fresh clone. A repeatable PyInstaller build and unsigned MSIX packaging path are included, but this repository does not yet contain a Store-ready submission.

## Checks completed

- Created a new clone of the public user-only source branch and installed its pinned Python 3.12 dependencies.
- Installed the French and Somali packs into a disposable test data folder. The app verified pack hashes, loaded the packs, and exercised the documented translation, transliteration, mode-switching, layout, pack-management and restart-state paths.
- Repeated the app smoke checks with a test network guard after the packs were installed. The offline routes still worked.
- Built the Windows onedir app with PyInstaller and launched it as a hidden smoke check. The payload contains app code, fonts, notices and runtimes; it excludes translation model weights.
- Created and unpacked a local MSIX with the Windows SDK MakeAppx tool. Its manifest, package identity, required files and included assets were checked.
- Audited `requirements-runtime-lock.txt` and `packaging/windows/requirements-build-lock.txt` with pip-audit; no known advisories were reported for these lock files on 28 October 2026.

These checks were run on one Windows 11 machine. They do not replace the Windows App Certification Kit, a clean VM install, screen-reader review or a Store certification result.

GitHub reported one moderate Dependabot alert on the default branch during the source update. The unauthenticated alerts endpoint did not reveal the affected package, so the lockfile audit does not resolve that alert. Review it under the repository's Security → Dependabot alerts before release.

## Build the app and local MSIX

Use 64-bit Python 3.12. Install the normal runtime dependencies and pinned packaging tools, then run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime-lock.txt
.\.venv\Scripts\python.exe -m pip install -r packaging/windows/requirements-build-lock.txt
pwsh -NoProfile -File packaging/windows/build.ps1 -SkipPackage
```

To create a local MSIX, install the Windows SDK and pass MakeAppx plus the exact identity and publisher values from Partner Center. A test identity can verify packaging mechanics but cannot be submitted as Saylacian's identity. The generated MSIX is unsigned and cannot be installed as a normal Store customer build. Do not create or trust a local signing certificate to work around this.

The current package script creates temporary monochrome “S” logo files because this source snapshot has no dedicated Store icon set. Replace those with owner-approved Store artwork before preparing the real submission.

MakeAppx produces an `.msix`, not Microsoft's recommended `.msixupload` Partner Center submission file. Store submission also needs the registered app identity, listing materials, a supported upload package, and the Windows App Certification Kit report. Microsoft signs MSIX packages distributed through the Store after certification. See Microsoft's [MSIX certification process](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/app-certification-process) and [MakeAppx documentation](https://learn.microsoft.com/en-us/windows/msix/package/create-app-package-with-makeappx-tool).

## Still required for a Windows release

- Run the Windows App Certification Kit on a clean Windows environment and resolve its findings.
- Install, launch, update and uninstall through the packaged route on a disposable VM. No clean VM is available in the current environment.
- Test keyboard navigation and focus visibility with Narrator or NVDA. This requires an actual screen-reader session.
- Test real Saylacian Text, RTF, HTML, image and Latin clipboard delivery in external apps inside a disposable VM. The current acceptance harness has not been run against an isolated Windows clipboard.
- Measure startup, translation and memory on a low-end physical Windows device. A constrained run on a development PC is not equivalent.
- Replace the local test package identity with Partner Center's exact registered identity and prepare Store listing assets, screenshots and certification notes.
- Build the Store upload package in the supported `.msixupload` format and confirm it in Partner Center. Do not submit until the owner approves publication.

## Feature limits

Somali translation still needs fluent-speaker review. Borama and Kaddare use partial chart-derived mappings. Old Nubian transliteration is limited to a documented character table and needs specialist review. Modern Nubian varieties are unsupported. Android and iOS remain out of scope for this Windows completion plan. See the [support matrix](SUPPORT_MATRIX.md).
