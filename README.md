# Saylacian

Saylacian is a free Python/Kivy language and script-preservation app for Windows. The current source version is **0.1.0a1 (alpha testing)**. Translation runs on-device after the relevant pack is installed; local use has no account, quota, subscription, or per-translation charge. Changes are listed in the [changelog](CHANGELOG.md).

![Saylacian desktop interface](assets/screenshots/saylacian-desktop.png)

## What works

| Feature | Status |
|---|---|
| English ↔ French meaning translation | Offline model route; smoke-tested |
| English ↔ Somali Latin | Local models; optional AfriSLM 0.8B is used for English→Somali, and 4B → 2B → 0.8B for Somali→English; fluent review is still needed |
| Somali ↔ French | Two-step route through English; errors can compound |
| Somali Latin ↔ Osmanya | Listed script mappings; this changes writing, not meaning |
| Borama/Kaddare | Selected chart-based mappings; glyphs use private-use code points, not standardized Unicode letters |
| Old Nubian | Limited 29-character Coptic-script to scholarly Latin table; reverse conversion may have ambiguous letter boundaries. It does not translate Old Nubian meaning or cover all conventions. |
| Modern Nubian varieties | Unsupported; each variety and orthography needs separate research and review. |

Somali meaning translation has not had fluent-speaker review. Borama and Kaddare cover selected entries from historical charts and do not establish accepted spelling or general orthography. Old Nubian reading uses an attributed 29-character table; it is not complete manuscript transcription or specialist-reviewed. Modern Nubian varieties are not implemented. See the [user guide](docs/USER_GUIDE.md) for navigation and clipboard behavior, the [documentation index](docs/README.md), and the [script letter guide](docs/SCRIPT_LETTER_GUIDE.md) for mappings and unmatched letters. The [support matrix](docs/SUPPORT_MATRIX.md), [script feasibility](docs/SCRIPT_FEASIBILITY.md), [quality evidence](docs/SOMALI_TRANSLATION_QUALITY.md), and [project status](docs/PROJECT_STATUS.md) give full scope.

Optional AfriSLM packs are available in Offline language packs: **0.8B** for English→Somali (**641 MiB**) and **2B** (**1.45 GiB**) or **4B** (**2.86 GiB**) for Somali→English. They need the separately installed `llama-cpp-python` runtime; the app tries the 4B model first for Somali→English, then falls back to smaller installed models. The 4B model used about 5 GB of working memory in one test. Model weights are declared Apache-2.0; training datasets are not downloaded. Somali output is in alpha testing and needs fluent review. See the [translation guide](docs/TRANSLATION_FEASIBILITY.md) for setup and benchmark limits.

## Install and run on Windows

Use Python 3.12. From a clean checkout in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime-lock.txt
.\.venv\Scripts\python.exe main.py
```

No PowerShell activation or execution-policy change is required. Flask belongs to the optional website and is not needed for the Kivy app.

The app restores your latest input, output, mode and language pair on the next launch. The saved session stays in your per-user application data folder.

To run the separate legacy website, install `requirements-website.txt` and use `python run_website.py`.

## Download offline packs

Open **Offline language packs** in the app and choose Download for the required pair. Review the displayed download size first. Downloads are opt-in, pinned to upstream revisions, checked against SHA-256, versioned, and stored in the user's application data directory. Packs can be removed to reclaim space. After installation, choose the offline provider and translation works without internet; local translations have no artificial daily limit.

Current download sizes:

- Somali / English: about 300 MiB.
- French / English: about 166 MiB.

An offline pack contains two directional models. The Somali pack uses the smaller multilingual models; optional AfriSLM packs are installed separately. Model licence and runtime metadata are recorded in the manifests and installed pack record. Full setup and troubleshooting: [RUN.md](RUN.md) and [offline packs](docs/OFFLINE_PACKS.md).

For Old Nubian, select the script and Latin reading, then choose **Read** to open the Reading Studio. It provides a searchable 29-character reference from an attributed 2024 table, a line-preserving reading panel, copy actions, and a versioned JSON record that can be exported and imported from the clipboard. It does not translate meaning or interpret manuscripts; the table has not had independent specialist review, and reverse letter boundaries can be ambiguous. See the [reader scope and sources](docs/OLD_NUBIAN_READER_PLAN.md).

![Offline language pack screen](assets/screenshots/offline-language-packs.png)

## Development

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q main.py app saylacian tools tests
.\.venv\Scripts\ruff.exe check --select E9,F63,F7,F82 main.py app saylacian tools tests
.\.venv\Scripts\python.exe tools\check_release_safety.py
```

The test suite and CI do not download model weights. To reproduce a full local model install, run `tools/prepare_models.py` as documented in [RUN.md](RUN.md); this downloads large model files. Do not commit models or credentials.

See [CONTRIBUTING.md](CONTRIBUTING.md) for code and linguistic review expectations. Historical models, datasets, and scripts require source, version, licence, and checksum evidence before inclusion.

The [API reference](docs/API_REFERENCE.md) documents the Python core and optional self-hosted HTTP endpoints. No public Saylacian translation API is hosted.

## Privacy, platform, and release

Offline translation stays on-device. Optional online providers are user-configured enhancements and are not required for local translation. Review [online provider behavior](docs/ONLINE_TRANSLATION.md) before enabling one. Android and iOS builds are not verified; see [mobile runtime status](docs/MOBILE_RUNTIME_STATUS.md).

Saylacian's source is on the public [GitHub repository](https://github.com/zealousvec/Saylacian); the app is in alpha testing. Saylacian-authored code that the project licensor owns is licensed under GNU AGPL version 3 or (at your option) any later version (SPDX: `AGPL-3.0-or-later`). The complete official text is in [LICENSE](LICENSE). This grant does not cover third-party code or independently licensed fonts, chart-derived data, datasets, or model weights; their terms and notices remain separate in [third-party notices](docs/THIRD_PARTY_NOTICES.md). Public Windows installers and verified mobile releases are not available.
