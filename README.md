<div align="center">

# Saylacian

### Making translation and lesser-supported writing systems easier to explore.

**A free, open-source project I've been developing to bring translation and different writing systems together, with a focus on Somali scripts and historical languages.**

[![Windows](https://img.shields.io/badge/Windows-Alpha-0078D4?logo=windows11&logoColor=white)](https://github.com/zealousvec/Saylacian/releases/tag/v0.1.0a1)
[![Release](https://img.shields.io/github/v/release/zealousvec/Saylacian?include_prereleases&label=release)](https://github.com/zealousvec/Saylacian/releases)
[![CI](https://github.com/zealousvec/Saylacian/actions/workflows/ci.yml/badge.svg)](https://github.com/zealousvec/Saylacian/actions/workflows/ci.yml)
[![License: AGPL-3.0-or-later](https://img.shields.io/badge/license-AGPL--3.0--or--later-3DA639)](LICENSE)

**[Download for Windows](https://github.com/zealousvec/Saylacian/releases/download/v0.1.0a1/Saylacian-Windows-Portable.zip)** · **[Getting started](docs/GET_STARTED.md)** · **[User guide](docs/USER_GUIDE.md)** · **[Report an issue](https://github.com/zealousvec/Saylacian/issues)**

</div>

![Saylacian desktop application](assets/screenshots/saylacian-desktop.png)

> [!WARNING]
> **Experimental Windows alpha (v0.1.0a1).** The public ZIP is unsigned and has **not** been independently verified on a clean Windows PC. Third-party binary redistribution checks are also incomplete. Windows security may block the executable; **do not disable security protections to bypass a warning**. This is not a stable or approved installer. [Release verification status](docs/GITHUB_RELEASE_CHECKLIST.md).

## Download and setup

| I want to… | Start here |
|---|---|
| **Use the Windows app** | **[Download the Windows portable ZIP](https://github.com/zealousvec/Saylacian/releases/download/v0.1.0a1/Saylacian-Windows-Portable.zip)** (195 MB, experimental alpha) |
| **Understand the features** | [User guide](docs/USER_GUIDE.md) · [Supported languages and scripts](docs/SUPPORT_MATRIX.md) |
| **Run or change the source** | [Developer setup](RUN.md) · [Contributing](CONTRIBUTING.md) |
| **Check other devices** | [Platform support](docs/GET_STARTED.md#android-or-iphone) |

**Windows installation:** Download the **release asset**, extract the ZIP completely, locate `Saylacian.exe`, and keep the bundled application files together. **No Python, Git, or GitHub account is required.** If Windows blocks the app, do not override its protections. See [troubleshooting](docs/GET_STARTED.md#common-problems).

**Important:** GitHub's green **Code → Download ZIP** and the release's automatic **Source code (zip)** links contain the *source*, **not** the packaged Windows application.

## What I've built so far

<table>
<tr><td width="33%" valign="top"><strong>🌍 Translate meaning</strong><br><br>English and French translation, alongside experimental Somali translation. I've kept the language models as optional offline downloads, although Somali output still needs proper review by fluent speakers.</td><td width="33%" valign="top"><strong>✍️ Explore Somali scripts</strong><br><br>Convert between Somali Latin and Osmanya. I've also been working on Borama and Kaddare, although their mappings are still partial and some text needs the project's fonts to display properly.</td><td width="33%" valign="top"><strong>📜 Read historical writing</strong><br><br>I've added a limited Old Nubian character-reading feature using scholarly Latin transliteration. It doesn't translate Old Nubian meaning or cover every historical convention.</td></tr>
</table>

> **A quick distinction:** translation changes what something means, whereas transliteration changes the writing system used to represent it. They're separate features in Saylacian, and I don't want to claim a language is fully supported when it isn't.

### What's working, and what's still experimental

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

- **Offline where possible:** once you've downloaded a supported language pack, translations can run on your computer without sending every request to a cloud service.
- **Optional model downloads:** English/French pack ≈166 MiB; standard Somali/English pack ≈300 MiB. These are **separate** from the Windows app download.
- **Privacy:** local packs process text locally. Optional online providers have different privacy implications; see [online provider notes](docs/ONLINE_TRANSLATION.md).
- **Still a work in progress:** I'm documenting the limits of the models and script mappings as I test them. I'd rather make those clear than overstate what the app can do.

## Running it from source

I've built the desktop app mainly with **Python and Kivy**. There's also a separate **Flask** version for running a local website, but it isn't publicly hosted.

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

If you've noticed a mistake in a translation, a script mapping that doesn't look right, or something that simply doesn't work, feel free to [open an issue](https://github.com/zealousvec/Saylacian/issues). I'd especially appreciate feedback from people familiar with the languages and writing systems involved. Contributions are welcome too; please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request. Don't include private text or credentials in reports.

## Licence and acknowledgements

Saylacian-authored code is licensed under **[GNU AGPL-3.0-or-later](LICENSE)**. This is a copyleft open-source licence; it **does not prohibit all commercial use**. Bundled fonts, dependencies, and downloadable models may have **different licences**; consult [third-party notices](docs/THIRD_PARTY_NOTICES.md). Binary redistribution review is not complete.

---

<div align="center">

**My aim is to keep improving Saylacian and make these languages and writing systems easier for people to use and learn about.**

[Releases](https://github.com/zealousvec/Saylacian/releases) · [Documentation](docs/README.md) · [Issues](https://github.com/zealousvec/Saylacian/issues)

</div>
