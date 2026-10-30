# Contributing

Saylacian is in alpha testing. Contributions can be proposed through GitHub issues or pull requests. Install the development dependencies from `requirements-dev.txt`, then run the same test command used in the README and CI:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

For the full locked contributor environment and CI-equivalent checks, install `requirements-dev.txt`; see the root README.

## Code style and checks

Use Ruff as the Python formatter and linter. Keep its 88-character line limit, one import per statement, and readable multiline control flow. Split a function only when the extracted helper has a clear responsibility; preserve public interfaces and output text during cleanup. Use named groups or `re.VERBOSE` for regular expressions that are hard to scan. Do not add comments that only repeat the code.

Before submitting Python changes, run:

```powershell
.\.venv\Scripts\python.exe -m ruff format .
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m compileall -q main.py app saylacian tools tests
.\.venv\Scripts\python.exe -m pytest -q
```

For the optional website, use Prettier 3.6.2 on its JavaScript and CSS plus workflow YAML when Node/npm is available. The HTML template contains Jinja syntax that Prettier's HTML parser rejects; format it carefully by hand and preserve whitespace-sensitive template output. Do not reserialize chart mappings, linguistic evidence, or licensed source data as part of a code-formatting change. Parse JSON/YAML/XML and compare data values when modifying those files. Keep third-party licence text verbatim.

Any Saylacian-authored code contribution intended for inclusion must be offered under GNU AGPL-3.0-or-later. Contributors must have the right to license their contribution under those terms. Before including copied, generated from, or adapted code, record its origin and licence and get any required permission. Do not assume the project licence covers third-party code or assets.

Keep Kivy startup independent of Flask. Add translation, script conversion and transliteration as separate features. Before claiming support, include an offline example, tests, source-backed orthography/mapping evidence and a clear description of coverage and review status. Do not add model weights, fonts or datasets without recording provenance, licence, version and hashes in `docs/THIRD_PARTY_NOTICES.md` and the relevant evidence file. Do not silently replace ambiguous input or invent Unicode/private-use characters.

Keep `app/original.kv` recoverable and make UI changes without requiring a core rollback. Update `docs/SUPPORT_MATRIX.md`, `docs/PROJECT_STATUS.md` and backup records when coverage or packaging changes. Never commit local environments, backups, secrets or unlicensed weights.
