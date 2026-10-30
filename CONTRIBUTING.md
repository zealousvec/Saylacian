# Contributing

Saylacian is in alpha testing. Contributions can be proposed through GitHub issues or pull requests. Install the development dependencies from `requirements-dev.txt`, then run the same test command used in the README and CI:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

For the full locked contributor environment and CI-equivalent checks, install `requirements-dev.txt`; see the root README.

Any Saylacian-authored code contribution intended for inclusion must be offered under GNU AGPL-3.0-or-later. Contributors must have the right to license their contribution under those terms. Before including copied, generated from, or adapted code, record its origin and licence and get any required permission. Do not assume the project licence covers third-party code or assets.

Keep Kivy startup independent of Flask. Add translation, script conversion and transliteration as separate features. Before claiming support, include an offline example, tests, source-backed orthography/mapping evidence and a clear description of coverage and review status. Do not add model weights, fonts or datasets without recording provenance, licence, version and hashes in `docs/THIRD_PARTY_NOTICES.md` and the relevant evidence file. Do not silently replace ambiguous input or invent Unicode/private-use characters.

Keep `app/original.kv` recoverable and make UI changes without requiring a core rollback. Update `docs/SUPPORT_MATRIX.md`, `docs/PROJECT_STATUS.md` and backup records when coverage or packaging changes. Never commit local environments, backups, secrets or unlicensed weights.
