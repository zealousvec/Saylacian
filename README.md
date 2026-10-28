# Saylacian

Saylacian is a Python and Kivy desktop app for translating text and converting it between Somali and selected writing systems. It runs on Windows. Translation can run locally after you install the language packs you need.

![Saylacian desktop interface](assets/screenshots/saylacian-desktop.png)

## Run on Windows

Install 64-bit Python 3.12, open the project folder in PowerShell, and run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime-lock.txt
.\.venv\Scripts\python.exe main.py
```

The app asks before downloading a pack. See [Offline packs](docs/OFFLINE_PACKS.md) for sizes, storage and model details.

## What it supports

- English ↔ French translation offline.
- English ↔ Somali translation with local packs. Somali output has not had fluent-speaker review, so check important translations.
- Optional local Somali translation models. They need extra downloads and may take longer to run; details and evaluation limits are in [Translation quality](docs/TRANSLATION_QUALITY.md).
- English, French and Somali language detection for longer Latin text. Short or mixed text may need a manual choice.
- Somali Latin ↔ Osmanya conversion.
- Partial, chart-based Somali Latin ↔ Borama and Kaddare conversion. These tables cover selected letters, not complete spelling rules. Borama and Kaddare text uses private-use characters and needs Saylacian's matching font to display as editable script.
- Limited Old Nubian character transliteration. This is not translation or complete manuscript reading. Modern Nubian varieties are not supported.

## Help and project details

- [User guide](docs/USER_GUIDE.md): choose routes and copy Borama or Kaddare text.
- [Supported routes](docs/SUPPORT_MATRIX.md): what works and where coverage stops.
- [Script letter guide](docs/SCRIPT_LETTER_GUIDE.md): mapped letters and ambiguities.
- [Sharing Borama and Kaddare](docs/SOMALI_SCRIPT_INTEROPERABILITY.md): what each copy option preserves.
- [Optional online translation](docs/ONLINE_TRANSLATION.md): provider setup and privacy.
- [Version history](CHANGELOG.md): changes in the current source snapshot.
- [Third-party notices](THIRD_PARTY_NOTICES.md): separate licences for fonts, models and other assets.

Saylacian is in alpha testing. The Windows app and offline routes passed a clean-clone check, but this source checkout is not a Microsoft Store release. Somali and historical-script features retain the limits above. Android and iOS builds have not been tested. See [Windows build status](docs/RELEASE_READINESS.md).

## Licence

Original Saylacian code is licensed under [GNU AGPL-3.0-or-later](LICENSE). Third-party fonts, charts and model packs retain their own licences, listed in [third-party notices](THIRD_PARTY_NOTICES.md).
