# Somali translation quality work

## Current change

Saylacian's current English-to-Somali synthetic checkpoint can loop and produce far more text than the input warrants. `translation.py` now rejects only extreme length outliers: output longer than twice the source word count plus ten words. Saylacian then uses its installed multilingual OPUS route as a local rescue. Other candidate behavior and ordinary outputs remain unchanged.

The rule was evaluated on a deterministic, length-stratified 150-example sample from TICO-19's English/Somali **dev** split, separate from the 150-example test sample. On dev, BLEU changed from 6.138 to 7.299 and chrF++ from 27.577 to 28.509; only 5 of 150 examples used rescue. On the held-out test sample, BLEU changed from 6.245 to 7.057 and chrF++ from 28.608 to 28.996; 7 of 150 examples used rescue. The full test run still produced the same Somali-to-English scores (BLEU 6.300, chrF++ 24.680). Automatic metrics do not establish semantic correctness; fluent Somali review is still needed.

The experiment rejected broad repeated-ngram blocking: it reduced some loops but caused errors such as replacing “cough” with unrelated words, and hurt chrF++ on dev. Only the length guard is enabled.

## Candidate model results

- **Maanka2 OPUS-MT fine-tune**, 60.6M parameters, locally converted to CTranslate2 int8: English-to-Somali BLEU 4.129, chrF++ 26.893 on same 150-example test sample. Worse than the guarded app route, so not selected. No-repeat trigram decode scored lower still (BLEU 3.754, chrF++ 26.240).
- **QVAC AfriSLM 0.8B Q4**: BLEU 7.474, chrF++ 29.847 EN-to-SO; BLEU 14.122, chrF++ 32.647 SO-to-EN. It scored higher automatically, but peaked near 1.09 GB resident memory on the benchmark PC. The model card declares Apache-2.0 weights while identifying CC-BY-NC training data; public redistribution rights need clarification. It is not bundled or enabled.

NLLB, MADLAD and M2M100 licensing/packaging evidence and the incomplete M2M100 runtime comparison are recorded in [SOMALI_MODEL_CANDIDATES.md](SOMALI_MODEL_CANDIDATES.md). No unmeasured candidate is described as better.

TICO-19 focuses on health/COVID-19 communication, and the current sample is only 150 pairs. Model training overlap is not fully established. Treat these scores as comparative signals, not general-purpose quality guarantees or human evaluation.

## Reproduce

```powershell
.\.venv\Scripts\python.exe tools\benchmark_somali_quality.py --system baseline
.\.venv\Scripts\python.exe tools\evaluate_somali_repetition_fallback.py --parquet PATH_TO_TICO19_EN_SO_VALIDATION_PARQUET --limit 150
```

Raw per-example test predictions and benchmark metadata are in [`somali_translation_quality_results.json`](somali_translation_quality_results.json). Dev sample outputs and rule comparisons are in [`somali_repetition_guard_dev_results.json`](somali_repetition_guard_dev_results.json). The dev parquet was used from the `gmnlp/tico19` mirror, whose dataset card declares CC0; download it to a private benchmark directory, not the app pack.

## Candidate sources

- [Helsinki synthetic EN-SO model](https://huggingface.co/Helsinki-NLP/opus-mt-synthetic-en-so)
- [Maanka2 fine-tuned EN-SO model](https://huggingface.co/maanka2/opus-mt-en-so-finetuned)
- [QVAC AfriSLM model card](https://huggingface.co/qvac/TranslatePsy-AfriSLM-0.8B-Q4-GGUF)
- [TICO-19 benchmark and splits](https://tico-19.github.io/testset.html)
