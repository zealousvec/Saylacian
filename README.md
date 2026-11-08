# Saylacian

**Free, open-source translation and writing-system conversion.** Explore Somali scripts and a limited Old Nubian character reference.

![Saylacian desktop screenshot](assets/screenshots/saylacian-desktop.png)

**Alpha 0.1.0a1** · Windows desktop app · [Licence](LICENSE) · [Report a problem](https://github.com/zealousvec/Saylacian/issues)

## Download

**[Windows downloads — GitHub Releases](https://github.com/zealousvec/Saylacian/releases)**

**Windows alpha pre-release now available:** [Download Saylacian-Windows-Portable.zip](https://github.com/zealousvec/Saylacian/releases/download/v0.1.0a1/Saylacian-Windows-Portable.zip) (**195 MB**, as displayed by GitHub). Extract the entire ZIP and open `Saylacian.exe` inside the app folder. No Python, Git, or GitHub account required. **Unsigned and not yet clean-PC verified; redistribution review remains incomplete.** Do not disable Windows security if it blocks the EXE. **Source code (zip)** on the release page is *not* the app.

For developers and testers only: [temporary Windows build artifacts](docs/GET_STARTED.md#windows-computer--portable-test-build) may require GitHub sign-in.

## Users vs developers

**Just want to use Saylacian?** Download the **experimental Windows portable ZIP** from [Releases](https://github.com/zealousvec/Saylacian/releases/tag/v0.1.0a1), extract it, find `Saylacian.exe` inside the app folder, and double-click it. No Python, Git, VS Code, or GitHub account required. This is an **unverified pre-release**, not an approved stable installer.

**Want to edit the code or contribute?** Follow [RUN.md](RUN.md) for Python 3.12, a virtual environment, dependencies, tests, and development commands. The green **Code → Download ZIP** button downloads **source code, not the Windows application**.

**Windows test candidate:** The uploaded GitHub Release ZIP is **195 MB**. A separate locally cleaned archive was approximately **68.3 MB**; these are **different archives**, and the contents of the 195 MB upload have **not been independently inspected**. The published archive has not been clean-PC tested or cleared for public binary redistribution.

## Start here

| What you have | What to do |
|---|---|
| **Windows computer** | [Download the experimental Windows alpha ZIP](https://github.com/zealousvec/Saylacian/releases/tag/v0.1.0a1), extract it and run `Saylacian.exe` (unsigned; unverified) |
| **Windows computer, build unavailable or blocked** | [Install from source](docs/GET_STARTED.md#windows-computer--source-installation) — requires Python 3.12 |
| **Android or iPhone** | [Read the phone status](docs/GET_STARTED.md#android-or-iphone) — **no mobile app or public mobile website yet** |
| **Developer / contributor** | [Development instructions](RUN.md) and [contribution guide](CONTRIBUTING.md) |

**Important:** The portable download is an **unsigned test candidate**, not a verified public installer. A successful GitHub build does not guarantee it will work on every PC. Do not disable Windows security to run it. [Release blockers](docs/GITHUB_RELEASE_CHECKLIST.md).

## What can it do?

- **Translate meaning:** English ↔ French, English ↔ Somali (experimental), and French ↔ Somali through English. Download the appropriate offline language pack inside the app first.
- **Change writing system:** Somali Latin ↔ Osmanya; partial Borama and Kaddare chart mappings.
- **Explore Old Nubian characters:** limited Coptic-script ↔ scholarly Latin transliteration, **not** meaning translation.

**Translation and transliteration are different:** translation changes meaning; transliteration changes how words are written. Somali translations need review by a fluent speaker. Borama/Kaddare mappings are partial; Old Nubian coverage is limited. Modern Nubian varieties are not supported.

[Full language and platform support](docs/SUPPORT_MATRIX.md) · [How to use the app](docs/USER_GUIDE.md)

## First use

1. Open Saylacian on a supported Windows PC.
2. Select **Transliterate** for script conversion, or **Translate** for meaning translation.
3. For offline meaning translation, open **Offline language packs** (Ctrl+P) and download a pack. English/French is about **166 MiB**; Somali/English about **300 MiB**.
4. Choose source and target, enter text, and review the output. Packs work offline after installation.

[Step-by-step setup and troubleshooting](docs/GET_STARTED.md)

## Guides

- [Get started — Windows, phones, downloads, troubleshooting](docs/GET_STARTED.md)
- [User guide — features and copying text](docs/USER_GUIDE.md)
- [Documentation index — technical and research topics](docs/README.md)
- [Project status](docs/PROJECT_STATUS.md) · [Changelog](CHANGELOG.md)

## Privacy, licence and contributing

The standard installed translation packs run locally without sending each translation to an online provider. Optional online providers have different privacy implications: [read before enabling](docs/ONLINE_TRANSLATION.md). Offline packs require a one-time download.

Saylacian-authored code is licensed under [AGPL-3.0-or-later](LICENSE). Third-party models, fonts and other assets retain their own licences: [notices](docs/THIRD_PARTY_NOTICES.md). Contributions and bug reports are welcome: [CONTRIBUTING.md](CONTRIBUTING.md).
