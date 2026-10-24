# Saylacian architecture, explained

This is an implementation guide to the checked-out source, not a claim of release readiness. Saylacian is a Python desktop application for Somali script conversion and experimental language translation. Its primary interface is Kivy/KivyMD; the translation and script functions are Python modules shared with a small Flask website and an optional self-hosted API.

## The shape of the application

```text
User
  │ types, selects a route, chooses Convert
  ▼
main.py + app/main.kv                 Kivy user interface
  ├── transliteration.py              writing-system conversion
  ├── translation.py                 meaning translation and route selection
  │     ├── model_packs.py            download, verify, install, remove
  │     └── CTranslate2 + SentencePiece
  ├── interchange.py / windows_clipboard.py
  └── history.py / diagnostics.py

Separate entry points:
  run_website.py → saylacian/website/app.py → same core functions
  cloud/oci/service.py → same translation function, over authenticated HTTPS
```

The desktop interface imports the core directly; it does not call the Flask website. This keeps one implementation of conversion and translation logic while allowing different interfaces. See [main.py](../main.py#L122), [translation.py](../saylacian/core/translation.py#L139), [transliteration.py](../saylacian/core/transliteration.py#L200), and [website/app.py](../saylacian/website/app.py#L12).

## What “translation” and “conversion” mean here

Meaning translation tries to express a sentence in another language. Transliteration changes how text is written while aiming to preserve its reading. For example, the Somali Latin word `dhagax` can be written in Osmanya glyphs by mapping letters; this does not translate the word into English. The app has separate paths and capability declarations for these jobs.

The current meaning-translation routes are English↔French, English↔Somali, and Somali↔French through English. Somali routes are explicitly experimental and need fluent-speaker evaluation. Script conversion includes Somali Latin↔Osmanya, partial chart-derived Somali Latin↔Borama/Kaddare, and an Old Nubian Coptic-to-scholarly-Latin table plus experimental reverse conversion. Modern Nubian languages are not implemented. See [capabilities.py](../saylacian/core/capabilities.py#L1) and [support matrix](SUPPORT_MATRIX.md).

## Launching the desktop app

1. `main.py` sets Kivy/runtime configuration and imports the application modules.
2. `SaylacianApp.build()` creates app services, loads the KV layout, and selects the initial screen.
3. Kivy evaluates [app/main.kv](../app/main.kv), which describes widgets and binds their events to Python methods.
4. The window event loop waits for typing and button actions. `on_input_text()` handles input changes; `convert()` selects script conversion or delegates meaning translation.
5. Meaning translation is submitted to a worker executor in `begin_translation()`. Its completion is posted back to Kivy’s UI thread so widgets are changed safely.
6. `show_translation()` presents the result and warnings. Copy, saved history, pack management, and screen navigation are separate app methods.

Key entry points: [main.py:139](../main.py#L139) (`build`), [main.py:449](../main.py#L449) (`convert`), [main.py:591](../main.py#L591) (`begin_translation`), [main.py:625](../main.py#L625) (`show_translation`), [main.py:887](../main.py#L887) (script entry point).

Kivy is a cross-platform Python toolkit with its own drawing and event-loop model; KivyMD supplies Material-style widgets. This code already has a Windows desktop interface. A framework being cross-platform does not prove that a given app will build or behave correctly on Android or iOS: those platforms need packaging, native runtime, permission, font, and device testing.

## What happens to a translation request

`translate_meaning(text, source, target)` first validates that the capability table permits the pair and enforces a 4,000-character limit. It resolves the selected provider. In offline mode it locates model files, loads a tokenizer and CTranslate2 CPU engine, turns text into model tokens, runs inference, and converts generated tokens back to text. Offline mode does not silently download a model. Missing packs produce an actionable error.

English↔French uses separate direction-specific Argos-derived CTranslate2 model directories. English↔Somali uses an OPUS-MT multilingual model with the Somali target marker; both directions are experimental. Somali↔French is two translations with English in the middle, so errors can accumulate. An optional synthetic English→Somali model may be used when present in the local model roots; it is not in the current downloadable pack and is guarded against obvious repeated or identity output. These guards cannot judge whether a translation is correct.

The translation result is represented as `Conversion`, which can carry text and warnings. The UI surfaces warnings so model output is not presented as independently verified language. Model and runtime facts are recorded in [translation.py](../saylacian/core/translation.py#L67), [model manifests](../models/manifest.json), [Somali manifest](../models/somali-manifest.json), and [third-party notices](THIRD_PARTY_NOTICES.md).

### Neural translation words in plain English

- **Model:** learned numeric parameters that map an input sequence to a likely output sequence.
- **Tokenization:** splitting text into model-specific units. SentencePiece can use subword pieces, so a token is not always a whole word.
- **Inference:** running a trained model to produce output. It is not training and does not inherently improve from user input.
- **CTranslate2:** runtime that executes converted translation models. The project configures CPU inference and compact integer computation.
- **Hugging Face:** a model hosting and version-control service used by manifest-pinned downloads. A model page or host does not guarantee linguistic quality or license compatibility; the project records revision, checksum, and license metadata.

## Offline packs

`ModelPackManager` reads pack specifications containing upstream revision, file names, sizes, hashes, and licence metadata. A pack download is explicit. Each file is downloaded into staging, checked for expected byte size and SHA-256, extracted where needed, and installed into a versioned directory. A pointer selects the active version. Cancellation and progress callbacks are supported. Users can list and remove installed packs. The platform-specific data root is selected by `default_store_root()`; `SAYLACIAN_MODEL_PACKS_DIR` can override it.

`active_model_roots()` gives the translation engine installed pack directories; the source checkout’s ignored `models/` directory is also a development fallback. The `models` directory in this working copy contains local weights, but weights are excluded from the Git source release. Never copy local model binaries into a commit without an explicit licensing and release review.

Main references: [model_packs.py](../saylacian/core/model_packs.py#L24), [ModelPackManager](../saylacian/core/model_packs.py#L168), [install](../saylacian/core/model_packs.py#L248), [download](../saylacian/core/model_packs.py#L414), [remove](../saylacian/core/model_packs.py#L500), and the [UI pack actions](../main.py#L203).

## Script routes, fonts, and interchange

Osmanya uses Unicode code points. A mapping table converts Somali Latin sequences to Osmanya and back, preserving punctuation. The reverse cannot recover distinctions where spellings share a glyph; conversion warns about this.

Borama and Kaddare mappings are partial transcriptions from cited charts. They use private-use Unicode code points, which have no universal assigned meaning. Saylacian’s chart fonts render the app’s own mapping, but another private-use font may assign the same code points differently. The separate Saylacian Text v1 clipboard format carries a script label and original text for round-trip import. Image and rich clipboard formats help sharing, but editable PUA text requires compatible font/mapping support. See [interchange.py](../saylacian/core/interchange.py#L31) and [Windows clipboard support](../saylacian/core/windows_clipboard.py#L18).

The Old Nubian route is historical language/script transliteration. It maps a documented set of Coptic/Greek-derived characters to scholarly Latin; reverse conversion is ambiguous and experimental. Detecting Coptic letters does not identify the language. Modern Nobiin, Kenzi/Mattokki, Dongolawi/Andaandi, Midob, Birgid, Dilling, Karko, Wali, and Kadaru are distinct research targets with no implemented conversion or translation route.

## Website and optional API

The Flask website is a separate, small interface that calls the same core functions. `run_website.py` launches it locally; it is not a public hosted service. Browser requests are sent on conversion and tests cover its routes and headers.

`cloud/oci/service.py` is an optional self-hosted translation API, not a vendor-free unlimited service. Compose requires a bearer token, Caddy terminates HTTPS, requests are size-limited, and active work is bounded. Hardware and network still impose capacity limits. A public application must not bundle one shared server token.

## Testing and licensing boundaries

The test suite checks code behavior such as mappings, route selection, checksum verification, error cases, clipboard representations, website responses, and installed-model smoke examples where local weights exist. CI intentionally does not download weights; model smoke tests skip when weights are absent. Tests do not establish Somali translation quality, community acceptance of orthography, or full Windows/mobile release reliability.

The root AGPL-3.0-or-later grant applies only to original Saylacian code the licensor owns or can license. Fonts, chart-derived mappings, datasets, model weights, and dependencies retain separate terms. The repository’s [third-party notice inventory](THIRD_PARTY_NOTICES.md) is the place to begin license review; check exact artifacts before distributing a binary.

## Limitations to remember

- Translation quality, especially Somali, has not been validated by fluent-speaker evaluation.
- Historical-script mappings are partial and orthography is not established by a chart.
- Local model weights require substantial download and storage; inference speed depends on device hardware.
- Windows source app is the main supported platform. Android and iOS are not built/device-tested.
- The local website is not a production public service.
