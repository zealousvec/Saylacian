# Third-party notices

The root [LICENSE](LICENSE) applies only to Saylacian-authored code that the project licensor owns or has the right to license. It does not relicense third-party material.

## Fonts and charts

- Noto Sans Osmanya and Noto Sans Coptic are by The Noto Project Authors and licensed under SIL Open Font License 1.1. The complete licence texts and copyright notices are in `assets/OFL-Osmanya.txt` and `assets/OFL-Coptic.txt`.
- Borama and Kaddare chart images are by Jugydmort, under CC BY-SA 4.0. The chart-derived mapping data and display fonts are adaptations under the same licence. Attribution, original source links, hashes and modification notes are in [`notices/HISTORICAL_SCRIPT_CHARTS.md`](notices/HISTORICAL_SCRIPT_CHARTS.md).
- KivyMD supplies its Material Design Icons font as a dependency; the applicable SIL OFL 1.1 text is retained in `notices/SIL-OFL-1.1-Material-Design-Icons.txt`.

## Translation models

Model weights are downloaded by user choice and are not included here. The app's model manifests record upstream projects, revisions, checksums and licences. The current French/English model is MIT-licensed; the downloadable Somali/English model is Apache-2.0. The optional Somali language detector uses an ONNX model whose upstream card lists MIT, trained on `hac541309/open-lid-dataset`, whose dataset card lists GPL-3.0. The model is fetched from its upstream Hugging Face revision only after the user selects its pack. See [`notices/OPENLID_LANGUAGE_DETECTION.md`](notices/OPENLID_LANGUAGE_DETECTION.md) and [offline packs](docs/OFFLINE_PACKS.md). Included licence notices are in `notices/`.

The optional “Somali translation (experimental)” pack is a separate English-to-Somali model, `WindyWord/translate-synthetic-en-so`, pinned to revision `11427877b7864afad1b5e93e10d1e89661d8b0c0` and released under CC BY 4.0. Its weights derive from Helsinki-NLP's `opus-mt-synthetic-en-so`; the upstream card says its training translations were synthetically generated from English Europarl using GPT-4o. The downloaded pack includes the model's full `LICENSE` and `NOTICE.md` files. Sources: [model card](https://huggingface.co/WindyWord/translate-synthetic-en-so), [upstream model card](https://huggingface.co/Helsinki-NLP/opus-mt-synthetic-en-so), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The model card publishes no quality score; its output still needs fluent-speaker review. It does not replace the Somali-to-English model or establish human-level translation quality.

## Old Nubian data

The limited 34-entry Old Nubian reading table is based on the DBMNT transliteration table. Its public guidelines permit downloading but do not state a reuse licence or grant. Permission for redistribution of these table-derived readings remains unresolved. This app's Old Nubian feature is limited and should not be treated as a licensed scholarly corpus; see [Old Nubian scope](docs/OLD_NUBIAN_SCOPE.md).

Python dependencies are installed from their respective package publishers and are not vendored in this source snapshot. Their own licence terms apply.

The optional detector's pinned runtime uses ONNX Runtime (MIT) and Hugging Face Tokenizers (Apache-2.0); package notices remain with their respective distributions.
