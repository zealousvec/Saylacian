# Contributing

Saylacian is an experimental preservation project and has not been publicly released. When a public repository is approved, contributions can be proposed through its issue tracker or pull requests. Until then, use these local development checks:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
.\.venv\Scripts\python.exe tools\check_ui.py
```

For the full locked contributor environment and CI-equivalent checks, install `requirements-dev.txt`; see the root README.

Any Saylacian-authored code contribution intended for inclusion must be offered under GNU AGPL-3.0-or-later. Contributors must have the right to license their contribution under those terms. Before including copied, generated from, or adapted code, record its origin and licence and get any required permission. Do not assume the project licence covers third-party code or assets.

Keep Kivy startup independent of Flask. Add translation, script conversion and transliteration as separate features. Before claiming support, include an offline example, tests, source-backed orthography/mapping evidence and an explicit experimental/validated status. Do not add model weights, fonts or datasets without recording provenance, licence, version and hashes in `docs/THIRD_PARTY_NOTICES.md` and the relevant evidence file. Do not silently replace ambiguous input or invent Unicode/private-use characters.

Keep `app/original.kv` recoverable and make UI changes without requiring a core rollback. Update `docs/SUPPORT_MATRIX.md`, `docs/PROJECT_STATUS.md` and backup records when coverage or packaging changes. Never commit local environments, backups, secrets or unlicensed weights.
