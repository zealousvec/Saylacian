<div align="center">

# Saylacian

### Languages, scripts, and history — in one desktop app.

**A free, open-source, local-first translator and writing-system explorer.**

[![Windows](https://img.shields.io/badge/Windows-Alpha-0078D4?logo=windows11&logoColor=white)](https://github.com/zealousvec/Saylacian/releases/tag/v0.1.0a1)
[![Release](https://img.shields.io/github/v/release/zealousvec/Saylacian?include_prereleases&label=release)](https://github.com/zealousvec/Saylacian/releases)
[![CI](https://github.com/zealousvec/Saylacian/actions/workflows/ci.yml/badge.svg)](https://github.com/zealousvec/Saylacian/actions/workflows/ci.yml)
[![License: AGPL-3.0-or-later](https://img.shields.io/badge/license-AGPL--3.0--or--later-3DA639)](LICENSE)

**[Download for Windows](https://github.com/zealousvec/Saylacian/releases/download/v0.1.0a1/Saylacian-Windows-Portable.zip)** · **[Getting started](docs/GET_STARTED.md)** · **[User guide](docs/USER_GUIDE.md)** · **[Report an issue](https://github.com/zealousvec/Saylacian/issues)**

</div>

![Saylacian desktop application](assets/screenshots/saylacian-desktop.png)

> [!WARNING]
> **Experimental Windows alpha (v0.1.0a1).** The public ZIP is unsigned and has **not** been independently verified on a clean Windows PC. Third-party binary redistribution checks are also incomplete. Windows security may block the executable; **do not disable security protections to bypass a warning**. This is not a stable or approved installer. [Release verification status](docs/GITHUB_RELEASE_CHECKLIST.md).

## Get Saylacian

| I want to… | Start here |
|---|---|
| **Use the Windows app** | **[Download the Windows portable ZIP](https://github.com/zealousvec/Saylacian/releases/download/v0.1.0a1/Saylacian-Windows-Portable.zip)** (195 MB, experimental alpha) |
| **Understand the features** | [User guide](docs/USER_GUIDE.md) · [Supported languages and scripts](docs/SUPPORT_MATRIX.md) |
| **Run or change the source** | [Developer setup](RUN.md) · [Contributing](CONTRIBUTING.md) |
| **Check other devices** | [Platform support](docs/GET_STARTED.md#android-or-iphone) |

**Windows installation:** Download the **release asset**, extract the ZIP completely, locate `Saylacian.exe`, and keep the bundled application files together. **No Python, Git, or GitHub account is required.** If Windows blocks the app, do not override its protections. See [troubleshooting](docs/GET_STARTED.md#common-problems).

**Important:** GitHub's green **Code → Download ZIP** and the release's automatic **Source code (zip)** links contain the *source*, **not** the packaged Windows application.

## What can it do?

<table>
<tr><td width="33%" valign="top"><strong>🌍 Translate meaning</strong><br><br>English ↔ French, English ↔ Somali, and French ↔ Somali via English. Offline language packs are optional downloads. Somali quality is experimental and needs fluent-speaker review.</td><td width="33%" valign="top"><strong>✍️ Explore Somali scripts</strong><br><br>Convert between Somali Latin and Osmanya. Explore partial chart-based Borama and Kaddare mappings, with font and clipboard interoperability limitations.</td><td width="33%" valign="top"><strong>📜 Read historical writing</strong><br><br>Limited Old Nubian Coptic-script ↔ scholarly Latin character transliteration. This is a reading aid, not Old Nubian meaning translation.</td></tr>
</table>

> **Translation ≠ transliteration.** Translation changes meaning; transliteration changes how text is written. Saylacian distinguishes the two rather than claiming every script is a fully supported language.

### Feature status at a glance

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

## How it works

```text
Your text
   │
   ├── Transliterate ──> script mapping ──> converted writing
   │
   └── Translate ──────> installed language model ──> translated meaning
                              │
                       optional offline packs
```

- **Local-first:** standard installed translation packs run on your computer; no translation-by-translation cloud account is required.
- **Optional model downloads:** English/French pack ≈166 MiB; standard Somali/English pack ≈300 MiB. These are **separate** from the Windows app download.
- **Privacy:** local packs process text locally. Optional online providers have different privacy implications; see [online provider notes](docs/ONLINE_TRANSLATION.md).
- **Research-led limitations:** mappings and translation quality are documented rather than presented as universally validated.

## For developers

Saylacian is built primarily with **Python and Kivy**, with a separate optional **Flask** local website.

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

## Contribute

Found a translation issue, incorrect letter mapping, bug, or documentation gap? [Open an issue](https://github.com/zealousvec/Saylacian/issues). Code contributions are welcome via pull requests; please read [CONTRIBUTING.md](CONTRIBUTING.md) first. Avoid posting private translation text or credentials.

## Licence and acknowledgements

Saylacian-authored code is licensed under **[GNU AGPL-3.0-or-later](LICENSE)**. This is a copyleft open-source licence; it **does not prohibit all commercial use**. Bundled fonts, dependencies, and downloadable models may have **different licences**; consult [third-party notices](docs/THIRD_PARTY_NOTICES.md). Binary redistribution review is not complete.

---

<div align="center">

**Built to make language technology and historical writing systems more accessible.**

[Releases](https://github.com/zealousvec/Saylacian/releases) · [Documentation](docs/README.md) · [Issues](https://github.com/zealousvec/Saylacian/issues)

</div>
