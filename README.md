# Saylacian

Saylacian is a Python and Kivy app for translating text and converting it between Somali and selected writing systems. It runs on Windows and can translate offline after you install the language packs you need.

## Get started on Windows

Install 64-bit Python 3.12, open this folder in PowerShell, then run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime-lock.txt
.\.venv\Scripts\python.exe main.py
```

You do not need to activate the virtual environment. The app asks before downloading language packs. See [Offline language packs](docs/OFFLINE_PACKS.md) for download sizes and storage details.

## What you can do

- Translate between English and French offline after installing the French/English pack.
- Translate English and Somali with the Somali/English pack. Somali results are experimental and need review by fluent speakers.
- Try an optional English-to-Somali model pack. Saylacian checks its output and uses the standard Somali pack when the result appears incomplete or repetitive. This add-on is experimental, takes more time, and has separate CC BY 4.0 terms.
- Identify English, French or Somali in longer Latin text. Short text may need a manual language choice.
- Convert Somali Latin text to and from Osmanya.
- Convert some Somali letters to Borama or Kaddare using chart-based mappings. These mappings are incomplete; editable script text needs a compatible Saylacian font.
- Read selected Old Nubian letters using a published character table. This is transliteration, not translation, and does not cover every manuscript convention.

Modern Nubian varieties are not supported. See the [support matrix](docs/SUPPORT_MATRIX.md) for available routes and their limits, and the [script letter guide](docs/SCRIPT_LETTER_GUIDE.md) for mapped and unmatched letters.

## Help and version history

The [user guide](docs/USER_GUIDE.md) explains language selection and copy options. [Sharing Borama and Kaddare](docs/SOMALI_SCRIPT_INTEROPERABILITY.md) explains why copied script may look different in other apps. Translation uses installed local packs by default. Optional online services send text to the selected provider; check that provider's privacy terms and any limits or costs.

The [version history](CHANGELOG.md) describes changes and what they mean for app users. This repository is an experimental alpha; no numbered release has been published.

## Licence

Original Saylacian code is offered under [GNU AGPL-3.0-or-later](LICENSE). Fonts, chart images and model packs have separate licences; see [third-party notices](THIRD_PARTY_NOTICES.md). Windows is the only platform checked so far; Android and iOS builds have not been tested.
