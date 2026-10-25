# Saylacian

Saylacian is a free Python and Kivy app for language translation and Somali script conversion. Its primary translation route runs locally with downloadable language packs. Installed packs work without an account, request quota, subscription, or per-translation fee.

## Run on Windows

Install 64-bit Python 3.12, open this folder in PowerShell, then run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime-lock.txt
.\.venv\Scripts\python.exe main.py
```

PowerShell activation is not required. Flask is not required for the Kivy app. The app asks before downloading language packs; see [offline packs](docs/OFFLINE_PACKS.md) for sizes, storage and model details.

## What it supports

- English ↔ French offline translation after the French/English pack is installed.
- Experimental Somali translation using the Somali/English pack; fluent-speaker review is still needed.
- Experimental Somali Latin and Osmanya conversion.
- Partial Borama and Kaddare chart mappings. Their app glyphs use private-use code points, so other apps need Saylacian-compatible font support for editable script text.
- Limited Old Nubian character transliteration. It is not meaning translation or complete manuscript coverage. See [Old Nubian scope](docs/OLD_NUBIAN_SCOPE.md).

The app does not support modern Nubian varieties. See the [support matrix](docs/SUPPORT_MATRIX.md) for route-by-route limits and the [script letter guide](docs/SCRIPT_LETTER_GUIDE.md) for mapped and unmatched letters.

## Help and privacy

The [user guide](docs/USER_GUIDE.md) explains modes, scripts and clipboard choices. [Script interoperability](docs/SOMALI_SCRIPT_INTEROPERABILITY.md) explains what other apps can display. Translation defaults to installed local packs; optional online providers send text to the configured service and may have their own limits, privacy terms or costs.

## Licence

Saylacian-authored code the project licensor owns or may license is offered under [GNU AGPL-3.0-or-later](LICENSE). Fonts, chart-derived assets and models retain their own terms; see [third-party notices](THIRD_PARTY_NOTICES.md). Android and iOS builds are not verified.
