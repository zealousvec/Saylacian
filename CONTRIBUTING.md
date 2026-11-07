# Contributing

Saylacian is in alpha testing. Contributions can be proposed through GitHub issues or pull requests. Install the development dependencies from `requirements-dev.txt`, then run the same test command used in the README and CI:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Create a Python 3.12 virtual environment and install `requirements-dev.txt` before
running the checks below. See the [Windows setup](RUN.md) for the basic environment.

## Propose a change

Keep each pull request focused. Explain the user-visible problem, the change and
the checks you actually ran. Note skipped checks and known limitations. Use
synthetic examples or material you have permission to share; exclude personal
translation content, private research data and credentials.

Use concise, descriptive commit messages, for example:

```text
fix: correct Borama Q mapping
feat: show alternative Osmanya readings
docs: clarify supported scripts
chore: tidy repository documentation
```

Use a short-lived branch for the change. Do not rewrite published history or
bundle unrelated work. Maintainers merge after the required checks pass; an
alpha source change does not by itself approve binary or model distribution.

## Code style and checks

Use Ruff as the Python formatter and linter. Keep its 88-character line limit, one import per statement, and readable multiline control flow. Split a function only when the extracted helper has a clear responsibility; preserve public interfaces and output text during cleanup. Use named groups or `re.VERBOSE` for regular expressions that are hard to scan. Do not add comments that only repeat the code.

Before submitting Python changes, run:

```powershell
.\.venv\Scripts\python.exe -m ruff format --check main.py app saylacian tools tests
.\.venv\Scripts\python.exe -m ruff check main.py app saylacian tools tests
.\.venv\Scripts\python.exe -m compileall -q main.py app saylacian tools tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe tools/check_release_safety.py
```

For the optional website, use Prettier 3.6.2 on its JavaScript and CSS plus workflow YAML when Node/npm is available. The HTML template contains Jinja syntax that Prettier's HTML parser rejects; format it carefully by hand and preserve whitespace-sensitive template output. Do not reserialize chart mappings, linguistic evidence, or licensed source data as part of a code-formatting change. Parse JSON/YAML/XML and compare data values when modifying those files. Keep third-party licence text verbatim.

Use `python -m ruff format` on the Python files you changed when formatting is
needed. The normal test suite does not download translation packs; model-dependent
tests may be skipped when the corresponding packs are not installed.

Any Saylacian-authored code contribution intended for inclusion must be offered under GNU AGPL-3.0-or-later. Contributors must have the right to license their contribution under those terms. Before including copied, generated from, or adapted code, record its origin and licence and get any required permission. Do not assume the project licence covers third-party code or assets.

Keep Kivy startup independent of Flask. Add translation, script conversion and transliteration as separate features. Before claiming support, include an offline example, tests, source-backed orthography/mapping evidence and a clear description of coverage and review status. Do not add model weights, fonts or datasets without recording provenance, licence, version and hashes in `docs/THIRD_PARTY_NOTICES.md` and the relevant evidence file. Do not silently replace ambiguous input or invent Unicode/private-use characters.

Keep `app/original.kv` recoverable and make UI changes without requiring a core rollback. Update `docs/SUPPORT_MATRIX.md`, `docs/PROJECT_STATUS.md` and backup records when coverage or packaging changes. Never commit local environments, backups, secrets or unlicensed weights.
