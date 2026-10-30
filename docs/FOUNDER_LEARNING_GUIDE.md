# Founder’s learning guide to Saylacian

This handbook teaches the implementation as it exists. It does not assign code authorship beyond what is recorded in [AUTHORS.md](../AUTHORS.md), and it does not claim translation quality that has not been independently reviewed.

## A simple starting picture

Saylacian is a Python program with a graphical front end and a set of language-processing functions. The screen collects text and a requested operation. The core either changes the writing system (transliteration) or asks a translation model to express meaning in another language. Optional model packs supply large files the source repository does not contain.

```text
Interface (Kivy)  →  Core decision  →  Mapping table or translation model
       ↑                                      │
       └──────── result + warnings ───────────┘
```

The program can return a string without that string being correct. Automated tests check that code follows expected paths; people who know the language must assess language quality.

## 30-minute guided tour

### Minutes 0–5: identify the project pieces

Open `README.md`, `main.py`, `app/main.kv`, and `saylacian/core/`. The README describes the alpha; Python files implement behavior; KV describes widgets; core modules do not draw the UI.

### Minutes 5–10: launch the app

In a Windows checkout with Python 3.12:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime-lock.txt
.\.venv\Scripts\python.exe main.py
```

No PowerShell script activation is needed. If no language pack is installed, script conversion may still work while meaning translation reports the required pack. Start with an Osmanya conversion, which does not need a translation model.

### Minutes 10–15: follow one button

Find Convert in `app/main.kv`; find the method it calls in `main.py`. Read `SaylacianApp.convert()` and note that the selected mode separates meaning translation from transliteration. Do not assume every item visible in a selector has an implemented route; capability checks are authoritative.

### Minutes 15–20: trace a conversion

Try Somali Latin `dhagax!` to Osmanya. The code searches for matching Latin sequences in the mapping table, emits Unicode Osmanya and leaves punctuation intact. This is script conversion, not an English definition. Try converting back and observe warnings about distinctions that cannot be recovered.

### Minutes 20–25: inspect translation plumbing

Read `translate_meaning()` in `saylacian/core/translation.py`. It validates the pair, chooses provider behavior, locates a model, tokenizes, runs inference, and decodes. Follow `load_model()` to see CTranslate2 and SentencePiece. Somali results carry a notice that they are in alpha testing and need fluent-speaker review.

### Minutes 25–30: run tests

With development dependencies installed:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests may skip model inference if the relevant local weights are absent. A passing test means the assertion passed; it does not mean Somali speakers approved the output.

## 1. What Saylacian currently does

It is a Windows-focused Python/Kivy app for language translation and writing-system conversion. English↔French has offline model routes. Somali meaning translation is available for alpha testing, and Somali↔French uses English as an intermediate language. Osmanya conversion is implemented from a mapping table. Borama/Kaddare are partial chart-label mappings using private-use code points. Old Nubian has a limited, cited Coptic-to-Latin character table; reverse readings may be ambiguous. Modern Nubian varieties are unavailable.

Translation changes language/meaning; transliteration changes writing system. A font displays code points as glyphs; it does not translate, define, or infer the intended private-use alphabet.

## 2. Why Python and Kivy

The implementation uses Python for application logic and language libraries, Kivy for cross-platform UI/event handling, and KivyMD for Material-style widgets. A visible advantage is one Python core shared by the desktop UI and Flask interface. Limitations include packaging complexity, native dependency management, and the need for separate builds and device tests on mobile. “Cross-platform toolkit” describes potential portability, not tested support on every operating system.

The repository does not document a full historical decision record for choosing these tools; treat this as the practical fit visible in the code, not a claimed original motivation.

## 3. How the app starts and responds

`main.py` initializes configuration/imports and runs `SaylacianApp`. `build()` creates services and loads `app/main.kv`. The Kivy event loop waits for input. UI callbacks update properties, which Kivy reflects in widgets. Translation can take time, so the app uses worker threads and posts completed output to the Kivy UI thread. Kivy UI elements should not be mutated from an arbitrary background thread.

## 4. How offline models work

The repository contains small JSON manifests, not model weights. Users download packs explicitly. `ModelPackManager` retrieves pinned files, checks expected size and SHA-256, stages/extracts them, installs a version, and records which version is active. At translation time, the app loads tokenizers and model runtime in local memory. Offline model execution needs no online provider request once files are installed, but model download itself needs connectivity.

“Offline” does not mean cost-free hardware or tiny storage: the device must store weights and spend CPU/RAM to run them. No artificial per-request service quota applies to local inference.

## 5. Translation routes and evidence

French↔English uses local direction-specific models. Somali↔English uses a multilingual OPUS-MT-derived model. An optional synthetic candidate may exist in a local development setup but is not part of the current downloadable Somali pack. Somali↔French chains two models through English. Each stage can change meaning, and errors can compound.

The model may produce plausible output even when wrong. Tokenization turns text into the model’s learned pieces; inference predicts output pieces; SentencePiece turns those back into text. A model trained on a data distribution may not handle names, dialects, idioms, or specialized language well. Review [SOMALI_TRANSLATION_EVIDENCE.json](SOMALI_TRANSLATION_EVIDENCE.json) and [SOMALI_TRANSLATION_QUALITY.md](SOMALI_TRANSLATION_QUALITY.md) for what was measured and what remains uncertain.

## 6. Historical scripts and sharing

Osmanya uses Unicode characters with assigned script code points. Some reading distinctions are not reversible from the chosen mapping. Borama and Kaddare use chart-derived mappings represented in the private-use area. A code point in that area has no universal assigned glyph; the Saylacian font only helps applications that have the matching font. Saylacian Text v1 is a portable tagged envelope for exchanging/importing the source script through Saylacian. An image preserves appearance but is not editable text.

Old Nubian is historical. The app’s Coptic table transliterates listed characters; it does not translate Old Nubian meaning and does not cover all manuscripts or competing scholarly conventions. Modern Nobiin and other Nubian varieties need their own language and orthography evidence.

## 7. Website versus desktop

`saylacian/website/app.py` creates a local Flask app. It calls shared core functions via HTTP form/JSON routes; it is not the Kivy desktop interface and is not publicly hosted. The optional `cloud/oci` service is a separate self-hosted API with a token, TLS proxy, input limits and bounded concurrency. Self-hosting transfers translation text to the operator’s server; users should know where their text goes.

## 8. Tests, CI, and licences

Unit tests check mappings, unsupported routes, limits, pack checksums, website responses and clipboard output. Model tests are conditional on local model files. CI compiles code, performs a narrow Ruff correctness scan, scans for accidental credentials, and runs tests without downloading weights. None of those checks is a human language review.

AGPL-3.0-or-later applies to Saylacian code the licensor has a right to license. Fonts, chart-derived assets, models, data and dependencies keep separate licences; check `docs/THIRD_PARTY_NOTICES.md` and the source asset-specific notices before redistribution.

## Glossary

| Term | Plain meaning |
|---|---|
| API | A defined way for one program to request work from another. |
| Capability | A source/target operation the code explicitly supports. |
| Checksum / SHA-256 | A digest used to detect file changes; not a quality or safety certificate. |
| CI | Automated checks run on a hosted build system when code changes. |
| Inference | Running a trained model to generate a result. |
| Manifest | A structured list of pack files, versions, sizes, hashes and licensing metadata. |
| Model pack | Downloadable files needed to run one or more language directions locally. |
| Private-use code point | Unicode space reserved for private agreement; meaning is not universal. |
| Tokenization | Dividing text into model-specific pieces. |
| Transliteration | Changing the script used to write text, usually preserving its reading. |
| Translation | Expressing meaning from one language in another language. |
| UI thread | The event-loop thread that owns Kivy widgets. |

## Practical exercises

1. **UI label:** change one explanatory label in `app/main.kv`, launch the app, then revert the edit. Learn KV property syntax.
2. **Known mapping:** find a specific Osmanya pair in `osmanya.json`, write a focused assertion, run the related test. Learn fixture/assertion basics.
3. **Unsupported route:** inspect `capabilities.py` and the error path for an unsupported meaning pair. Add or update a test for a clear error, not a fake route.
4. **Pack integrity:** read the model pack test that modifies a downloaded file. Observe that a checksum mismatch prevents installation.
5. **Warning behavior:** trace Somali translation warnings from `Conversion` through `show_translation()`. Ensure a UI change does not hide them.

## Deeper learning plan

1. **Python foundation:** functions, classes, imports, exceptions, paths, JSON and virtual environments. Practice on a tiny standalone script.
2. **UI flow:** Kivy properties, KV bindings, callbacks, screen manager and event loop. Trace one button end-to-end.
3. **Testing:** unittest/pytest assertions, mocks for network isolation, temporary directories and skip conditions. Add tests before behavioral changes.
4. **Text processing:** Unicode code points, normalization, graphemes, fonts, PUA and reversibility. Inspect actual code points, not only the rendered glyph.
5. **NMT basics:** models, tokenizers, training data, inference, evaluation metrics, and human review. Separate code correctness from translation quality.
6. **Release engineering:** dependency locks, source vs binary assets, model manifests, hashes, CI, licensing and release checklists.
7. **Community research:** document orthography variants, consent, review process, language ownership and data provenance before adding content.

## How to explain the project accurately

Say: “Saylacian is a Windows Python/Kivy app in alpha testing, with offline English–French translation, Somali translation that needs fluent-speaker review, and several script conversion features. Offline model files are downloaded separately and verified by hash. Borama/Kaddare cover selected chart entries with private-use glyphs; Old Nubian has a limited scholarly transliteration route. Software tests do not establish translation quality.”

Avoid saying that Somali translation is accurate, all Nubian varieties work, private-use glyphs are standard Unicode, or local inference has unlimited service capacity. Those statements are not supported by current evidence.
