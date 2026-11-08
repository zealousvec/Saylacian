# Getting started with Saylacian

Saylacian is an experimental Windows alpha. There is no stable installer or mobile app yet.

## Windows — download and run

You **do not** need Python, Git, VS Code, a terminal or a GitHub account.

1. Open **[Saylacian v0.1.0a1 on GitHub Releases](https://github.com/zealousvec/Saylacian/releases/tag/v0.1.0a1)**.
2. Find **Assets** near the bottom of the release and click to expand it if it is collapsed.
3. Click **`Saylacian-Portable-Fixed-20261108-115138.zip`** under Assets. **Do not click** `Source code (zip)`, `Source code (tar.gz)` or the repository's green **Code → Download ZIP** button. Those are source archives, not the Windows application.
4. Open your **Downloads** folder. Right-click the downloaded ZIP → **Extract All** → **Extract**.
5. Open the newly extracted folder. Find the folder named **Saylacian**; inside it, locate **Saylacian.exe** alongside the **_internal** folder.
6. Double-click **Saylacian.exe** to open the app. **Do not move the EXE out of its folder**, because it needs the bundled files. Do not launch it from within the ZIP.
7. To translate meaning offline, open **Offline language packs** (or press **Ctrl+P**) and download the pack you need. Script conversion can be tried without downloading translation models.

**Important:** The Windows alpha is unsigned. The portable build has been reported working on a second Windows PC, but wider compatibility testing and third-party binary redistribution review are still outstanding. If Windows blocks the executable, **do not disable SmartScreen, Smart App Control or other security protections**. Report the problem in [GitHub Issues](https://github.com/zealousvec/Saylacian/issues).

### Which ZIP is the correct one?

| Where you downloaded it | What it contains | What to do |
|---|---|---|
| **Releases → Assets → Windows portable ZIP** | Packaged Windows app | **Use this one** |
| **Releases → Source code (zip)** | Python source | Not the Windows download |
| **Code → Download ZIP** | Python source | Not the Windows download |
| **Actions → Artifacts** | Developer build artifact, sometimes a ZIP inside another ZIP | Only for build testing |

**If there is no `Saylacian.exe` after extracting the Release asset**, report the exact asset name in an [issue](https://github.com/zealousvec/Saylacian/issues). The release attachment may be incorrect; don't try random files or download unofficial builds.

## Developers — run from source or build an EXE

For source setup, follow [RUN.md](../RUN.md). The application is built with Python 3.12 and Kivy. To build the portable Windows ZIP from a checked-out repository on Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build-lock.txt
.\.venv\Scripts\python.exe tools/build_windows_portable.py
```

If the build succeeds, the outputs are `dist/portable/Saylacian/Saylacian.exe` and `dist/Saylacian-Portable.zip`. The build checks package contents, but does not establish clean-PC compatibility or redistribution approval. See the [release checklist](PUBLISH_WINDOWS_RELEASE.md).

## Android or iPhone

**There is no Android APK, iPhone app or public mobile website available yet.** The downloadable Windows EXE cannot run on Android or iOS. The optional Flask website is only a *local* website running on a computer; it is not a public site you can open from your phone.

You can read the [project](../README.md), [language support](SUPPORT_MATRIX.md) and [guides](README.md) from your phone. Do **not** download a third-party “Saylacian APK” claiming to be an official build.

## Translate or convert writing

- **Transliterate:** converts supported characters between writing systems. This does **not** translate meaning.
- **Translate:** translates meaning between supported languages. Offline models are optional downloads: English/French about **166 MiB**, Somali/English about **300 MiB**.
- To download a pack, open **Offline language packs** or press **Ctrl+P**. Once installed, standard packs work offline. Somali results are experimental and should be reviewed.

[Full user guide](USER_GUIDE.md) · [Support and limitations](SUPPORT_MATRIX.md)

## Common problems

| Problem | What to do |
|---|---|
| I downloaded GitHub's **Code → Download ZIP**, but there's no EXE | That is source code. Download the **Windows portable ZIP under Assets on the v0.1.0a1 release page** instead. |
| I see a ZIP inside a ZIP | If using a CI artifact, extract both ZIPs. For the public Release asset, extract the ZIP fully and keep the application folder intact. |
| Windows blocks the EXE | Do not disable security protections. Use the source-install route or wait for a signed, verified release. |
| The app says no translation model is installed | Open **Offline language packs** and install the correct pack. |
| I have only a phone | There is no official phone app or publicly hosted Saylacian website yet. |
| `py -3.12` is not recognised | Install Python 3.12 and reopen PowerShell; check `py -3.12 --version`. |
| `No module named kivy` | From the source folder, rerun the dependency-install command above using the virtual-environment Python. |

Still stuck? [Open an issue](https://github.com/zealousvec/Saylacian/issues) with the device, the step that failed and the exact error. **Do not post passwords, API keys or private translation text.**
