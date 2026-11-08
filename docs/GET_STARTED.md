# Get started with Saylacian

**Choose your device:** [Windows computer](#windows-computer--portable-test-build) · [Android or iPhone](#android-or-iphone) · [Source installation](#windows-computer--source-installation)

Saylacian is **alpha software**. It is free and open source, but a verified public installer and mobile app are not yet available.

**Ordinary Windows users:** Check [GitHub Releases](https://github.com/zealousvec/Saylacian/releases). When an approved Windows portable ZIP appears there, download it under **Assets**, extract the whole ZIP, and open `Saylacian/Saylacian.exe`. No GitHub account, Python, Git, or VS Code is required. **No approved download has been published yet.**

**Developers:** Go to [RUN.md](../RUN.md) for Python setup and source-code instructions. **Code → Download ZIP is source code, not the app.**

**Size:** The current locally supplied Windows candidate is approximately **68.3 MB (65.1 MiB)** compressed, containing 600 ZIP entries. Extracted size and model-pack downloads are additional. The candidate is not approved for public distribution.

## Windows computer — portable test build

**Best for testing on another Windows computer.** You do not need Python, Git or VS Code on that computer.

1. On GitHub, open [Saylacian's Windows build workflow](https://github.com/zealousvec/Saylacian/actions/workflows/ci.yml).
2. Select **Run workflow** on branch `main` (you may need repository permissions to start a new run). Alternatively, open a recent successful manually triggered run.
3. Wait for **windows-portable-zip** to finish with a green check.
4. Open the run's **Artifacts** section. Download **Saylacian-Windows-portable-alpha-candidate** (GitHub sign-in may be needed).
5. Extract the downloaded ZIP. Inside it, extract **Saylacian-Portable.zip** too.
6. Open the extracted application folder and double-click **Saylacian.exe**. **Keep all the files in that folder together.**
7. Try script conversion. To translate meaning offline, open **Offline language packs** (Ctrl+P) and download the desired pack.

**If you don't see Artifacts:** the job may still be running, may have failed, or the artifact may have expired. The workflow retains artifacts for **14 days**. A GitHub source-code ZIP from the green **Code** button is **not** the Windows application.

**Safety and release status:** This build is unsigned and has not been validated on a clean Windows PC. Windows may block it. Do not disable Smart App Control, SmartScreen or other security features to bypass a block. The project's binary redistribution/licensing review is also incomplete. This is a development test candidate, **not an approved public release**.

## Android or iPhone

**There is no Android APK, iPhone app or public mobile website available yet.** The downloadable Windows EXE cannot run on Android or iOS. The optional Flask website is only a *local* website running on a computer; it is not a public site you can open from your phone.

You can read the [project](../README.md), [language support](SUPPORT_MATRIX.md) and [guides](README.md) from your phone. Do **not** download a third-party “Saylacian APK” claiming to be an official build.

## Windows computer — source installation

Use this only if the portable candidate is unavailable or you want to run the Python source. Requires **64-bit Windows** and **Python 3.12**.

1. Install Python 3.12 from the [official Python website](https://www.python.org/downloads/). Confirm `py -3.12 --version` works in PowerShell.
2. [Download the source ZIP](https://github.com/zealousvec/Saylacian/archive/refs/heads/main.zip) and **Extract All**.
3. Open the folder containing `main.py`. Click File Explorer's address bar, type `powershell`, and press Enter.
4. Run these commands **one at a time**:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime-lock.txt
.\.venv\Scripts\python.exe main.py
```

To reopen the app later, use only the final command from the same folder. You do not need to activate the environment or change PowerShell execution policy. For more technical setup and developer options, see [RUN.md](../RUN.md).

## Translate or convert writing

- **Transliterate:** converts supported characters between writing systems. This does **not** translate meaning.
- **Translate:** translates meaning between supported languages. Offline models are optional downloads: English/French about **166 MiB**, Somali/English about **300 MiB**.
- To download a pack, open **Offline language packs** or press **Ctrl+P**. Once installed, standard packs work offline. Somali results are experimental and should be reviewed.

[Full user guide](USER_GUIDE.md) · [Support and limitations](SUPPORT_MATRIX.md)

## Common problems

| Problem | What to do |
|---|---|
| I downloaded GitHub's **Code → Download ZIP**, but there's no EXE | That is source code. Follow the **portable test build** steps above instead. |
| I see a ZIP inside a ZIP | Extract **both** ZIPs; then keep the application folder intact. |
| Windows blocks the EXE | Do not disable security protections. Use the source-install route or wait for a signed, verified release. |
| The app says no translation model is installed | Open **Offline language packs** and install the correct pack. |
| I have only a phone | There is no official phone app or publicly hosted Saylacian website yet. |
| `py -3.12` is not recognised | Install Python 3.12 and reopen PowerShell; check `py -3.12 --version`. |
| `No module named kivy` | From the source folder, rerun the dependency-install command above using the virtual-environment Python. |

Still stuck? [Open an issue](https://github.com/zealousvec/Saylacian/issues) with the device, the step that failed and the exact error. **Do not post passwords, API keys or private translation text.**
