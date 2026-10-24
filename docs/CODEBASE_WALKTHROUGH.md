# Saylacian codebase walkthrough

This guide starts at the files a new developer will encounter and follows a request through the program. Paths below are relative to the repository root.

## Project map

| Path | Responsibility |
|---|---|
| `main.py` | Desktop Kivy/KivyMD app, screens, user actions, thread-to-UI handoff, pack controls, history, and clipboard menu. |
| `app/main.kv` | Approved Kivy layout and widget bindings. Keep layout and event logic conceptually separate. |
| `app/original.kv`, `app/original_compat.py` | Preserved prototype and compatibility loader; not the main app entry point. |
| `saylacian/core/translation.py` | Meaning-translation validation, provider selection, model lookup, tokenization and inference. |
| `saylacian/core/model_packs.py` | Manifest parsing, secure relative paths, downloads, verification, version install, progress, and deletion. |
| `saylacian/core/transliteration.py` | Osmanya, chart-based Borama/Kaddare, Old Nubian transliteration and script detection. |
| `saylacian/core/capabilities.py` | Registry of currently implemented routes and unavailable research targets. |
| `saylacian/core/interchange.py`, `windows_clipboard.py` | Saylacian Text v1 and Windows clipboard formats. |
| `saylacian/core/history.py`, `diagnostics.py` | Local saved conversions and bounded local diagnostic logging. |
| `saylacian/website/` | Separate local Flask web interface using the shared core. |
| `cloud/oci/` | Optional token-authenticated self-hosted translation API and deployment files. |
| `models/*.json` | Pack manifests. Actual model weights are not part of the source release. |
| `assets/`, `notices/` | Fonts, historical charts, screenshots and third-party license/attribution records. |
| `tests/` | Unit, integration and locally available model smoke tests. |
| `.github/workflows/ci.yml` | Windows Python 3.12 checks in GitHub Actions. |
| `requirements-*.txt`, `pyproject.toml`, `Saylacian.spec` | Dependencies, tool configuration and PyInstaller build recipe. |
| `README.md`, `RUN.md`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE` | User setup, contribution/security policy, and project license. |

## Read the app in this order

1. **Start at the entry point.** [main.py](../main.py#L887) runs `SaylacianApp`. Module setup above it configures Kivy and imports app services.
2. **Find the app class.** [SaylacianApp](../main.py#L122) owns UI-level state such as chosen source/target, mode, status, workers, and model pack manager.
3. **Read `build()`.** [build](../main.py#L139) constructs dependencies and loads the Kivy interface. Kivy reads [app/main.kv](../app/main.kv).
4. **Follow an action binding.** In the KV file, inspect the button's `on_release` or property binding. It calls an app method such as `convert`, `swap`, `open_packs`, or `open_copy_menu`.
5. **Follow conversion.** [convert](../main.py#L449) handles conversion mode, supported script cases, and meaning-translation dispatch. [begin_translation](../main.py#L591) submits slower inference to a worker; [show_translation](../main.py#L625) returns the result to the UI thread.
6. **Follow offline inference.** [translate_meaning](../saylacian/core/translation.py#L139) selects route/provider, finds a model, loads it with SentencePiece/CTranslate2, and returns text plus warnings.
7. **Follow a download.** [start_pack_download](../main.py#L266) invokes [ModelPackManager.install](../saylacian/core/model_packs.py#L248); progress callbacks update the screen.

## Example: user asks to translate English into French

Input: `Hello, how are you?`, source `English`, target `French`, mode `Meaning`.

```text
KV Convert button
  → SaylacianApp.convert(text)
  → begin_translation(text)
  → background worker calls translate_meaning(...)
  → capability check + provider selection
  → model_directory("English", "French")
  → SentencePiece encodes pieces; CTranslate2 runs inference
  → SentencePiece decodes result
  → UI thread calls show_translation(result)
```

With no pack installed, offline mode reports that the pack is missing. It does not silently fetch model files. Install the English/French pack in the app first.

## Example: Latin Somali into Osmanya

Input `dhagax!`, source Somali Latin, target Osmanya, mode Transliteration. The core chooses the longest matching Latin sequences, looks them up in the Osmanya table, and copies punctuation through. This changes script, not meaning. Reverse conversion can be ambiguous because some Latin distinctions share an Osmanya character. The actual table is [osmanya.json](../saylacian/core/data/osmanya.json); conversion logic is in [transliteration.py](../saylacian/core/transliteration.py#L200).

## Example: Borama/Kaddare sharing

Chart-label conversion maps a partial set of Somali graphemes to private-use code points. On Windows, copy actions can publish Latin, image, Saylacian Text v1, RTF and CF_HTML representations. Plain PUA text in an arbitrary app is not self-describing; compatible font and matching mapping are needed. Importing the Saylacian envelope restores the tagged text/script round trip. Review [interchange.py](../saylacian/core/interchange.py#L64) and [clipboard menu](../main.py#L765).

## Example: Somali to French

The route is Somali→English followed by English→French. Each stage can make an error; the core attaches a warning. A successful HTTP response or nonempty string only proves the code returned output. It is not proof the Somali is correct. Evaluation data and limits are catalogued in [Somali translation evidence](SOMALI_TRANSLATION_EVIDENCE.json) and the [technical audit](TECHNICAL_AUDIT.md).

## Where the website differs

The desktop app is Kivy and imports `saylacian.core` directly. The optional website starts at [run_website.py](../run_website.py) and registers routes in [website/app.py](../saylacian/website/app.py#L12). Both call shared converters, but the website has browser form validation, HTTP status codes and HTML security headers. It is currently a local development site, not a configured public service.

## Run locally on Windows

From the repository root, use Python 3.12. PowerShell activation is unnecessary:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime-lock.txt
.\.venv\Scripts\python.exe main.py
```

For development, install `requirements-dev.txt` and run `python -m pytest -q`. The test suite does not fetch model weights. Follow [RUN.md](../RUN.md) to prepare/download local model files or use the app’s pack manager.

## Safe first changes

1. **Change a label:** edit a text string in `app/main.kv`, launch, and inspect the layout. This exercises only UI resources.
2. **Add a mapping test:** add a test case in the focused `tests/test_transliteration.py` for a documented mapping. Run that test by name. Do not invent a linguistic mapping to make a test pass.
3. **Improve an error message:** make a small, tested change at the validation boundary in `translation.py` or the UI error handler. Keep unsupported pairs unsupported.
4. **Improve docs:** update the relevant capability table and README together when implementation status changes.

For every change, inspect `git diff`, run the narrow test, then the CI commands in the workflow. Never commit downloaded weights, `.env`, tokens, local diagnostics, or build folders.
