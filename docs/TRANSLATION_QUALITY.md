# Somali translation quality checks

Somali translation is experimental. This page records one reproducible check of the current offline model; it does not establish fluent or general-purpose translation quality.

## Repetition-control check

I compared the model's usual beam decoding with CTranslate2's three-token no-repeat option on 120 examples from the English–Somali TICO-19 validation split. Examples were selected by SHA-256 rank of their IDs using the seed `saylacian-v1`. The evaluation used CTranslate2 4.8.3 and SacreBLEU 2.5.1, with effective-order BLEU and chrF++ (`word_order=2`).

| Route and decoding | BLEU | chrF++ | Outputs with a repeated word trigram | Mean time per sentence |
|---|---:|---:|---:|---:|
| English → Somali, default | 3.755 | 23.222 | 7 of 120 | 284.5 ms |
| English → Somali, no repeated three-token sequence | 3.820 | 23.437 | 3 of 120 | 298.2 ms |
| Somali → English, default | 6.775 | 23.339 | 14 of 120 | 156.5 ms |
| Somali → English, no repeated three-token sequence | 6.907 | 23.575 | 1 of 120 | 187.8 ms |

The small score increases and fewer repeated phrases support using the guard in both Somali routes. It adds about 14 ms per English-to-Somali sentence and 31 ms per Somali-to-English sentence in this CPU run. The guard applies to model tokens, not Somali grammar, and can suppress valid repetition. These scores are sample-specific and are not a measure of human-rated accuracy. TICO-19 is a medical-information dataset; Saylacian still needs fluent-speaker review and evaluation on broader material. The benchmark split is [available as CC0](https://huggingface.co/datasets/gmnlp/tico19).

Other model candidates remain experimental until their outputs, dataset overlap, licence terms and runtime costs have been checked against the shipped pack.
