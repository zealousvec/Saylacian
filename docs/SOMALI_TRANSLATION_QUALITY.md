# Somali translation quality work

## Current change

Saylacian's current English-to-Somali synthetic checkpoint can loop and produce far more text than the input warrants. `translation.py` now rejects only extreme length outliers: output longer than twice the source word count plus ten words. Saylacian then uses its installed multilingual OPUS route as a local rescue. Other candidate behavior and ordinary outputs remain unchanged.

The rule was evaluated on a deterministic, length-stratified 150-example sample from TICO-19's English/Somali **dev** split, separate from the 150-example test sample. On dev, BLEU changed from 6.138 to 7.299 and chrF++ from 27.577 to 28.509; only 5 of 150 examples used rescue. On the held-out test sample, BLEU changed from 6.245 to 7.057 and chrF++ from 28.608 to 28.996; 7 of 150 examples used rescue. The full test run still produced the same Somali-to-English scores (BLEU 6.300, chrF++ 24.680). Automatic metrics do not establish semantic correctness; fluent Somali review is still needed.

### Reproduction on 2026-10-24

The pre-guard 150-pair run used network connections blocked and an isolated result/checkpoint location. Dataset SHA-256: `be58b2d350badb7e03b73906471453311a8843534e4a2a572a772c60c394c7f7`. It scored EN→SO BLEU 7.057 / chrF++ 28.996 and SO→EN BLEU 6.300 / chrF++ 24.680. Its EN→SO route selected the synthetic candidate 143 times and used multilingual fallback 7 times, all for excessive output length. The stored outputs contained SentencePiece's default unknown-token marker U+2047 in 46/150 EN→SO rows (81 occurrences). The upstream documentation defines U+2047 as the default decoded surface for unknown tokens: [SentencePiece special symbols](https://google.github.io/sentencepiece/doc/special_symbols/).

The candidate route now detects U+2047 and falls back to the existing multilingual EN→SO model. A fresh Python 3.12 developer environment installed the pinned Somali pack, verified its hashes, and reran the same 150-pair benchmark with network access blocked during inference. Post-guard scores were EN→SO BLEU 5.287 / chrF++ 25.282 and SO→EN BLEU 6.300 / chrF++ 24.680. The candidate was selected 97 times; 47 unknown-token and 6 output-length fallbacks were used. No U+2047 marker remained in final EN→SO output. The aggregate automatic EN→SO scores decreased; this confirms a visible decode artifact was removed, not that translation meaning improved. Keep the feature, score change, and Somali quality status under review; no fluent-speaker assessment occurred. Numeric-token and possible-negation cues remain automatic review prompts only.

The temporary benchmark output and checkpoint are under `%TEMP%` and are not committed. The developer-only requirements now pin `sacrebleu==2.5.1`, which the benchmark imports; it is not a runtime dependency. Timing and memory figures from earlier runs are machine-specific.

The experiment rejected broad repeated-ngram blocking: it reduced some loops but caused errors such as replacing “cough” with unrelated words, and hurt chrF++ on dev. Only the length guard is enabled.

## Candidate model results

- **Maanka2 OPUS-MT fine-tune**, 60.6M parameters, locally converted to CTranslate2 int8: English-to-Somali BLEU 4.129, chrF++ 26.893 on same 150-example test sample. Worse than the guarded app route, so not selected. No-repeat trigram decode scored lower still (BLEU 3.754, chrF++ 26.240).
- **QVAC AfriSLM 0.8B Q4**: BLEU 7.474, chrF++ 29.847 EN-to-SO; BLEU 14.122, chrF++ 32.647 SO-to-EN. It scored higher automatically, but peaked near 1.09 GB resident memory on the benchmark PC. The model card declares Apache-2.0 weights while identifying CC-BY-NC training data; public redistribution rights need clarification. It is not bundled or enabled.

NLLB, MADLAD and M2M100 licensing/packaging evidence and the incomplete M2M100 runtime comparison are recorded in [SOMALI_MODEL_CANDIDATES.md](SOMALI_MODEL_CANDIDATES.md). No unmeasured candidate is described as better.

TICO-19 focuses on health/COVID-19 communication, and the current sample is only 150 pairs. Model training overlap is not fully established. Treat these scores as comparative signals, not general-purpose quality guarantees or human evaluation.

## Reproduce

```powershell
.\.venv\Scripts\python.exe tools\benchmark_somali_quality.py --system baseline --output PATH_TO_NEW_RESULT.json
.\.venv\Scripts\python.exe tools\evaluate_somali_repetition_fallback.py --parquet PATH_TO_TICO19_EN_SO_VALIDATION_PARQUET --limit 150
```

Raw per-example test predictions and benchmark metadata are in [`somali_translation_quality_results.json`](somali_translation_quality_results.json). Dev sample outputs and rule comparisons are in [`somali_repetition_guard_dev_results.json`](somali_repetition_guard_dev_results.json). The dev parquet was used from the `gmnlp/tico19` mirror, whose dataset card declares CC0; download it to a private benchmark directory, not the app pack.

## Candidate sources

- [Helsinki synthetic EN-SO model](https://huggingface.co/Helsinki-NLP/opus-mt-synthetic-en-so)
- [Maanka2 fine-tuned EN-SO model](https://huggingface.co/maanka2/opus-mt-en-so-finetuned)
- [QVAC AfriSLM model card](https://huggingface.co/qvac/TranslatePsy-AfriSLM-0.8B-Q4-GGUF)
- [TICO-19 benchmark and splits](https://tico-19.github.io/testset.html)
