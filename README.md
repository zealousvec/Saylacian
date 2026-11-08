# Saylacian

**Free, open-source translation and writing-system conversion.** Explore Somali scripts and a limited Old Nubian character reference.

![Saylacian desktop screenshot](assets/screenshots/saylacian-desktop.png)

**Alpha 0.1.0a1** · Windows desktop app · [Licence](LICENSE) · [Report a problem](https://github.com/zealousvec/Saylacian/issues)

## Start here

| What you have | What to do |
|---|---|
| **Windows computer** | [Try the Windows portable test build](docs/GET_STARTED.md#windows-computer--portable-test-build) — no Python needed on the receiving PC |
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
