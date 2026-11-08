# Saylacian

A Python desktop app for offline translation and script conversion, with a focus
on Somali writing systems and a limited Old Nubian reading reference.

![Saylacian desktop app converting Somali Latin text to Osmanya](assets/screenshots/saylacian-desktop.png)

[![Python checks](https://github.com/zealousvec/Saylacian/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/zealousvec/Saylacian/actions/workflows/ci.yml) [![Python 3.12](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/downloads/) [![Code licence: AGPL-3.0-or-later](https://img.shields.io/badge/code-AGPL--3.0--or--later-blue)](LICENSE)

**Alpha software · version 0.1.0a1 · Windows source installation.**
No verified Windows binary release is available. Somali translation and
historical-script readings need linguistic review.

## Windows portable test download

You can build a portable Windows test copy on [GitHub Actions](https://github.com/zealousvec/Saylacian/actions/workflows/ci.yml). Select **Run workflow** on `main`; after the `windows-portable-zip` job succeeds, download the `Saylacian-Windows-portable-alpha-candidate` artifact from that run. Extract the artifact ZIP and then `Saylacian-Portable.zip`. Copy the **entire extracted application folder** to a 64-bit Windows PC and launch `Saylacian.exe` without installing Python or Git.

This is an **unsigned, unverified alpha test build**, not a permanent release or installer. Artifacts expire after 14 days and downloading may require signing into GitHub. Do not disable Windows security controls if the executable is blocked. Clean-PC validation and third-party binary redistribution checks remain outstanding.

**New here? Start with the [beginner installation guide](#install-and-run-on-windows--beginner-guide).**

## Features

- Translate locally after installing the relevant offline language packs.
- Convert supported scripts, with warnings and alternative readings where input
  is ambiguous.
- Browse the Old Nubian character reference and save paired reading records.
- Use the desktop app, shared Python core or optional local Flask website.

## Languages and scripts

| Meaning translation | Support |
|---|---|
| English ↔ French | Offline models |
| English ↔ Somali Latin | Offline models; alpha quality |
| French ↔ Somali Latin | Two-step route through English; errors can compound |

| Script conversion | Scope |
|---|---|
| Somali Latin ↔ Osmanya | Listed character mappings; reverse readings can be ambiguous |
| Somali Latin ↔ Borama / Kaddare | Partial historical-chart mappings; require bundled fonts and use private-use characters |
| Old Nubian Coptic script ↔ scholarly Latin | Limited 29-character table and alternative reverse parses; not meaning translation |

Modern Nubian varieties are not supported. See the [support matrix](docs/SUPPORT_MATRIX.md)
for route details and the [letter guide](docs/SCRIPT_LETTER_GUIDE.md) for mapping limits.

## Install and run on Windows — beginner guide

**You do not need to know how to code. Follow these steps in order.**
This guide is for a **64-bit Windows PC**. You will need internet for setup and
for downloading translation packs. There is no ready-to-install Saylacian
installer yet.

You do not need Git, VS Code, a paid account or a subscription.

### 1. Install Python 3.12

Python is the program that runs Saylacian.

1. Open the [official Python download page](https://www.python.org/downloads/).
2. Download **Python install manager**, open the downloaded file, and choose
   **Install**.
3. Open the Windows **Start** menu, type **PowerShell**, and open **Windows
   PowerShell**.
4. Copy this command, paste it into PowerShell, and press **Enter**:

   ```powershell
   pymanager install 3.12
   ```

5. Wait for it to finish. Then paste this command and press **Enter**:

   ```powershell
   py -3.12 --version
   ```

**You should see `Python 3.12...`.** The last number may vary. If you already
have Python 3.12 and this check works, you can skip installing it again.
If a command fails, use the troubleshooting table below before continuing.

These steps use Python's [official Windows install manager](https://docs.python.org/3/using/windows.html#python-install-manager).
Keep using `3.12` in the commands below, even if another Python version is also
installed.

### 2. Download Saylacian

1. [Download Saylacian as a ZIP](https://github.com/zealousvec/Saylacian/archive/refs/heads/main.zip).
   Alternatively, click the green **Code** button near the top of this
   repository, then **Download ZIP**.
2. Open your **Downloads** folder in File Explorer.
3. Right-click the downloaded ZIP, choose **Extract All...**, then **Extract**.
   **Do not run the app from inside the ZIP.**
4. Open the extracted folders until you can see **`main.py`** and
   **`requirements-runtime-lock.txt`** together. Windows may hide the
   `.py` and `.txt` endings, so they may appear as **main** and
   **requirements-runtime-lock**.

**Keep this folder.** You will use it whenever you open Saylacian.

### 3. Open PowerShell in the Saylacian folder

While viewing the folder containing `main.py`:

1. Click the **address bar at the top of File Explorer** — the bar showing the
   folder location, not the search box.
2. Type `powershell` and press **Enter**.
3. A PowerShell window opens. Paste this check and press **Enter**:

   ```powershell
   Test-Path .\main.py
   ```

**You should see `True`.** If you see `False`, go back to step 2 and open the
folder containing `main.py`, then open PowerShell there again.

### 4. Set up the app — first time only

Use the PowerShell window from step 3. **Run one command at a time. Wait for
each command to finish before running the next.** Copy only the command text;
do not type the word “powershell” or the box borders.

First, create the app's own Python folder:

```powershell
py -3.12 -m venv .venv
```

This may finish without printing anything. That is normal. When the
`PS ...>` prompt returns, run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime-lock.txt
```

This downloads the software Saylacian needs. Expect lots of text and allow
several minutes, depending on your connection. Wait until the `PS ...>`
prompt returns. **If it ends with an error, fix that before continuing.**

You do not need to activate anything or change PowerShell's execution policy.

### 5. Start Saylacian

In the same PowerShell window, run:

```powershell
.\.venv\Scripts\python.exe main.py
```

**The Saylacian app window should open.** Leave PowerShell open while using
the app; messages there are normal. Close the Saylacian window when finished.

### 6. Enable translation inside the app

Writing-system conversion and meaning translation are different features.
**Meaning translation needs a language pack downloaded separately.**

1. Open **Offline language packs** in the app. You can also press **Ctrl+P**.
2. Choose **Download** for **French / English** or **Somali / English**.
   Review the displayed size first: about **166 MiB** for French or
   **300 MiB** for Somali.
3. Wait for the pack to finish installing.
4. Return to the translator and choose **Translate meaning**. You can press
   **Ctrl+Shift+M** to switch modes.
5. Choose your source and target languages, then enter your text.

Once installed, the standard offline packs work without internet. Somali
translations are experimental: have a fluent speaker check important results.
You can leave the optional larger model packs for later.

### Opening Saylacian next time

**You do not need to download everything or repeat setup.**

1. Open the folder containing `main.py`.
2. Type `powershell` into File Explorer's address bar and press **Enter**.
3. Run this one command:

   ```powershell
   .\.venv\Scripts\python.exe main.py
   ```

### If something goes wrong

| What you see | What to do |
|---|---|
| `pymanager` is not recognised | Finish installing **Python install manager** from step 1, then close and reopen PowerShell. See [Python's Windows troubleshooting](https://docs.python.org/3/using/windows.html#troubleshooting) if it still fails. |
| `py` is not recognised, or Python 3.12 cannot be found | Complete step 1, close and reopen PowerShell, then check `py -3.12 --version` again. |
| `Test-Path .\main.py` prints `False` | You opened PowerShell in the wrong folder. Find the extracted folder with `main.py` and `requirements-runtime-lock.txt`, then repeat step 3. |
| `requirements-runtime-lock.txt` or `main.py` cannot be found | Extract the ZIP first, then open PowerShell in the folder containing both files. |
| `.venv\Scripts\python.exe` is not recognised or cannot be found | In the correct folder, run `py -3.12 -m venv .venv`, then run the dependency-install command from step 4. |
| `No module named kivy` or another missing-module error | Run the dependency-install command from step 4 and wait for it to finish successfully. |
| Installation reports `No matching distribution found` | Check that you are using **64-bit Python 3.12**. Copy the full error when asking for help; do not install random package versions to work around it. |
| A window flashes and disappears when you double-click `main.py` | Start it through PowerShell using step 5 so the error stays visible. |
| Translation says no local model is installed | Download the matching language pack inside the app using step 6. |
| A download fails | Check your internet connection and available disk space, then retry. Keep the full error text if it fails again. |

Still stuck? [Open a GitHub issue](https://github.com/zealousvec/Saylacian/issues)
and include **which step failed**, **the exact command**, and **the full error
message**. Leave out passwords, API keys and private translation text.
More setup details: [RUN.md](RUN.md).

<details>
<summary>Already use Git? Download with these commands instead of the ZIP</summary>

```powershell
git clone https://github.com/zealousvec/Saylacian.git
cd Saylacian
```

Then continue from **step 4** above. Git must already be installed.

</details>

### Optional: run the local website

The steps above open the **desktop app**. If you specifically want the separate
website, finish step 4, open PowerShell in the same folder, and run these
commands one at a time:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-website.txt
.\.venv\Scripts\python.exe run_website.py
```

Leave PowerShell open, open your browser, and visit
[http://127.0.0.1:5000](http://127.0.0.1:5000).
Press **Ctrl+C** in PowerShell to stop the website. The desktop app does not
need to be open. This starts a local website on your PC, not a public website.

## Offline translation

Open **Offline language packs** in the desktop app to install a pack. French ↔
English downloads about **166 MiB**; Somali ↔ English about **300 MiB**. Downloads
are opt-in, versioned and checked against pinned SHA-256 hashes. Installed packs
are stored in your application data folder and can be removed from the app.

After installation, the offline provider runs without an account or a network
connection. Optional larger AfriSLM packs require a separate runtime; see
[offline packs](docs/OFFLINE_PACKS.md) and [translation setup](docs/TRANSLATION_FEASIBILITY.md).
Online providers are optional and user-configured; review their
[privacy behavior](docs/ONLINE_TRANSLATION.md) before enabling one.

## Alpha limitations

Somali output can be incorrect. Script conversion does not establish accepted
word spelling, and the Old Nubian reference is not complete manuscript coverage
or specialist-validated interpretation. Check important results with a qualified
speaker or reader.

Android and iOS builds are unverified. Windows binary distribution remains
blocked by runtime and dependency-provenance checks. See the
[current project status](docs/PROJECT_STATUS.md) and [changelog](CHANGELOG.md).

## Documentation

- [User guide](docs/USER_GUIDE.md) — navigation, reading tools and clipboard behavior.
- [Documentation index](docs/README.md) — setup, architecture and source references.
- [Python and HTTP API](docs/API_REFERENCE.md) — use the shared core or local service.
- [Independent research runner](research/README.md) — bounded checks, checkpoints and evaluation.

## Contributing and licence

Bug reports, documentation fixes and source-backed linguistic review are welcome.
Read [Contributing](CONTRIBUTING.md), the [Code of Conduct](CODE_OF_CONDUCT.md)
and the [security policy](SECURITY.md) before submitting.

Saylacian-authored code is **AGPL-3.0-or-later**; see [LICENSE](LICENSE).
Third-party models, fonts and chart-derived assets retain their own terms.
The [third-party notices](docs/THIRD_PARTY_NOTICES.md) credit the upstream work,
including Kivy, translation-model projects, Noto fonts and historical-script sources.
Project attribution is recorded in [AUTHORS.md](AUTHORS.md).

