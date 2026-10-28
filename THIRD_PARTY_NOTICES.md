# Third-party notices

## Old Nubian alphabet table

The 29 Old Nubian character-to-Latin readings and phonetic values in Saylacian are adapted from Vincent W. J. van Gerven Oei, [“Old Nubian,” *UCLA Encyclopedia of Egyptology* (2024)](https://escholarship.org/uc/item/03x6d68h), Table 1, DOI [10.5070/G9.3919](https://doi.org/10.5070/G9.3919). The peer-reviewed article explicitly licenses this material under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Saylacian formats the table for lookup and transliteration and preserves the source's distinction between Latin transliteration and phonetic values. No article prose, manuscript passages or word lexicon is included. The 29-entry table is not independently reviewed by an Old Nubian specialist. This replaces the previous DBMNT-derived table; future DBMNT reuse still requires permission.

The root [LICENSE](LICENSE) applies only to Saylacian-authored code that the project licensor owns or has the right to license. It does not relicense third-party material.

## Fonts and charts

- Noto Sans Osmanya and Noto Sans Coptic are by The Noto Project Authors and licensed under SIL Open Font License 1.1. The complete licence texts and copyright notices are in `assets/OFL-Osmanya.txt` and `assets/OFL-Coptic.txt`.
- Borama and Kaddare chart images are by Jugydmort, under CC BY-SA 4.0. The chart-derived mapping data and display fonts are adaptations under the same licence. Attribution, original source links, hashes and modification notes are in [`notices/HISTORICAL_SCRIPT_CHARTS.md`](notices/HISTORICAL_SCRIPT_CHARTS.md).
- KivyMD supplies its Material Design Icons font as a dependency; the applicable SIL OFL 1.1 text is retained in `notices/SIL-OFL-1.1-Material-Design-Icons.txt`.

## Translation models

Model weights are downloaded by user choice and are not included here. The app's model manifests record upstream projects, revisions, checksums and licences. The current French/English model is MIT-licensed; the downloadable Somali/English model is Apache-2.0. The optional Somali language detector uses an ONNX model whose upstream card lists MIT, trained on `hac541309/open-lid-dataset`, whose dataset card lists GPL-3.0. The model is fetched from its upstream Hugging Face revision only after the user selects its pack. See [`notices/OPENLID_LANGUAGE_DETECTION.md`](notices/OPENLID_LANGUAGE_DETECTION.md) and [offline packs](docs/OFFLINE_PACKS.md). Included licence notices are in `notices/`.

The optional English-to-Somali model, `WindyWord/translate-synthetic-en-so`, is pinned to revision `11427877b7864afad1b5e93e10d1e89661d8b0c0` and released under CC BY 4.0. Its weights derive from Helsinki-NLP's `opus-mt-synthetic-en-so`; the upstream card says its training translations were synthetically generated from English Europarl using GPT-4o. The downloaded pack includes the model's full `LICENSE` and `NOTICE.md` files. Sources: [model card](https://huggingface.co/WindyWord/translate-synthetic-en-so), [upstream model card](https://huggingface.co/Helsinki-NLP/opus-mt-synthetic-en-so), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The model card publishes no quality score; its output still needs fluent-speaker review. It does not replace the Somali-to-English model or establish human-level translation quality.

The optional AfriSLM model, `qvac/TranslatePsy-AfriSLM-0.8B-Q4-GGUF`, is pinned to revision `14d6fd1e24c9f94a5e40c2e91c066241aede0dce`, with a SHA-256-pinned Q4_K_M file listed as Apache-2.0. Its model card separately identifies the synthetic training mix and NLLB-200 teacher model as CC BY-NC-4.0. The model card recommends human evaluation and notes that dialect coverage and quality vary. Keep the model, its training-data terms and the `llama-cpp-python` runtime's MIT licence distinct from Saylacian's code licence. Sources: [quantized model card](https://huggingface.co/qvac/TranslatePsy-AfriSLM-0.8B-Q4-GGUF), [base model card and licence details](https://huggingface.co/qvac/TranslatePsy-AfriSLM-0.8B), [llama-cpp-python](https://github.com/abetlen/llama-cpp-python).

Python dependencies are installed from their respective package publishers and are not vendored in this source snapshot. Their own licence terms apply.

The optional detector's pinned runtime uses ONNX Runtime (MIT) and Hugging Face Tokenizers (Apache-2.0). The optional AfriSLM route uses `llama-cpp-python` (MIT). Runtime package notices remain with their respective distributions.
