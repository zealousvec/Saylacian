<div align="center">

# Saylacian

### An open-source translator and writing-system conversion project.

Saylacian is a free, open-source desktop application focused on language translation and the conversion of Somali writing systems, alongside a limited reference for historical Old Nubian characters.

[![Windows](https://img.shields.io/badge/Windows-Alpha-0078D4?logo=windows11&logoColor=white)](https://github.com/zealousvec/Saylacian/releases/tag/v0.1.0a1)
[![Release](https://img.shields.io/github/v/release/zealousvec/Saylacian?include_prereleases&label=release)](https://github.com/zealousvec/Saylacian/releases)
[![CI](https://github.com/zealousvec/Saylacian/actions/workflows/ci.yml/badge.svg)](https://github.com/zealousvec/Saylacian/actions/workflows/ci.yml)
[![License: AGPL-3.0-or-later](https://img.shields.io/badge/license-AGPL--3.0--or--later-3DA639)](LICENSE)

**[Download for Windows](https://github.com/zealousvec/Saylacian/releases/tag/v0.1.0a1)** · **[Getting started](docs/GET_STARTED.md)** · **[User guide](docs/USER_GUIDE.md)** · **[Report an issue](https://github.com/zealousvec/Saylacian/issues)**

</div>

![Saylacian desktop application](assets/screenshots/saylacian-desktop.png)

> [!WARNING]
> **Experimental Windows alpha (v0.1.0a1).** The public ZIP is unsigned and has **not** been independently verified on a clean Windows PC. Third-party binary redistribution checks are also incomplete. Windows security may block the executable; **do not disable security protections to bypass a warning**. This is not a stable or approved installer. [Release verification status](docs/GITHUB_RELEASE_CHECKLIST.md).

## Download for Windows

**Windows 10/11 (64-bit) · Experimental alpha**

1. Open the **[latest Windows release](https://github.com/zealousvec/Saylacian/releases/tag/v0.1.0a1)**.
2. Scroll to **Assets** and expand it if necessary.
3. Download the **Saylacian portable ZIP** listed under Assets. **Do not select** `Source code (zip)` or GitHub's green **Code → Download ZIP**; those contain source files, not the Windows app.
4. In **Downloads**, right-click the ZIP and select **Extract All**, then **Extract**. Do not run the application from inside the ZIP.
5. Open the extracted **Saylacian** folder and double-click **Saylacian.exe**. Keep the `_internal` folder and the other files beside it.
6. For offline language translation, open **Offline language packs** in the app (or press **Ctrl+P**) and install the language pack you want.

**No Python, Git, terminal or GitHub account is required.** This is a portable application, not a Windows installer. The ZIP does not include the optional translation models.

**If Windows blocks the EXE, do not turn off Windows security protections to run it.** This build is unsigned and remains experimental. See the [step-by-step Windows guide and troubleshooting](docs/GET_STARTED.md).

## Features

Saylacian currently includes three areas of functionality:

- **Language translation:** offline English–French translation and experimental Somali translation. Language models are downloaded separately.
- **Somali script conversion:** Latin–Osmanya conversion, with partial Borama and Kaddare chart mappings. Some output requires the bundled fonts or specific clipboard formats.
- **Old Nubian reference:** limited transliteration between Coptic-script characters and scholarly Latin readings. This does not translate Old Nubian text.

Translation and transliteration are separate operations. The former changes the meaning expressed in a language; the latter represents writing in a different script. Support varies by language and writing system.

### Current support

| Capability | Status |
|---|---|
| English ↔ French offline translation | Implemented; smoke-tested |
| English ↔ Somali offline translation | Experimental; quality review needed |
| Somali Latin ↔ Osmanya | Implemented character mappings; linguistic review open |
| Somali Latin ↔ Borama / Kaddare | Partial chart mappings; special fonts / clipboard formats |
| Old Nubian character transliteration | Limited historical reading reference |
| Android / iOS | Not released |
| Public web app | Not deployed |

See the [complete support matrix](docs/SUPPORT_MATRIX.md) for exact routes, limitations, and evidence.

## Offline translation and privacy

Installed language packs allow supported translations to run locally without sending the text to an external translation service. The English–French pack is approximately 166 MiB, while the standard Somali–English pack is approximately 300 MiB. Both are separate downloads from the Windows application.

Optional online translation providers may transmit text to third-party services. Their behaviour and privacy considerations are described in the [online translation documentation](docs/ONLINE_TRANSLATION.md).

The application remains under development. Somali translation quality, historical-script coverage and some clipboard operations require further review and testing.

## Running it from source

The desktop application uses **Python and Kivy**. An optional **Flask** implementation is available for local use; no public website is currently deployed.

```powershell
# Windows + Python 3.12, from the repository root
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime-lock.txt
.\.venv\Scripts\python.exe main.py
```

For development dependencies, tests, architecture, and packaging, see [RUN.md](RUN.md), [codebase walkthrough](docs/CODEBASE_WALKTHROUGH.md), and [contribution guidelines](CONTRIBUTING.md).

## Documentation

| Guide | Contents |
|---|---|
| [Getting started](docs/GET_STARTED.md) | Download, install, troubleshoot |
| [User guide](docs/USER_GUIDE.md) | Translation, scripts, copy formats |
| [Support matrix](docs/SUPPORT_MATRIX.md) | Verified, experimental, and unsupported features |
| [Project status](docs/PROJECT_STATUS.md) | Current work and known limitations |
| [Research and technical docs](docs/README.md) | Architecture, linguistic evidence, model evaluation |
| [Release verification](docs/GITHUB_RELEASE_CHECKLIST.md) | Binary licensing, clean-PC testing, remaining checks |
| [Changelog](CHANGELOG.md) | Development history |

## Contributing

Bug reports, corrections to script mappings and feedback on translation quality are welcome through [GitHub Issues](https://github.com/zealousvec/Saylacian/issues). Contributions from speakers and researchers familiar with the supported languages are particularly valuable. Before submitting code, please review [CONTRIBUTING.md](CONTRIBUTING.md). Do not include private text or credentials in issue reports.

## Licence and acknowledgements

Saylacian-authored code is licensed under **[GNU AGPL-3.0-or-later](LICENSE)**. This is a copyleft open-source licence; it **does not prohibit all commercial use**. Bundled fonts, dependencies, and downloadable models may have **different licences**; consult [third-party notices](docs/THIRD_PARTY_NOTICES.md). Binary redistribution review is not complete.

---

<div align="center">

**An ongoing project to improve access to language tools and lesser-supported writing systems.**

[Releases](https://github.com/zealousvec/Saylacian/releases) · [Documentation](docs/README.md) · [Issues](https://github.com/zealousvec/Saylacian/issues)

</div>
