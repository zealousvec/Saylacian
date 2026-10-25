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

## English-to-Somali candidate check

I also compared the current pack with Helsinki-NLP's `opus-mt-synthetic-en-so` checkpoint, pinned to `e69e7d6b2e6180242c2600d02fe93f77832a5ecd`. I converted its safetensors weights to CTranslate2 int8 locally and used the same three-token repetition guard for both systems.

| Sample | Current pack BLEU / chrF++ | Candidate BLEU / chrF++ | Mean time: current / candidate |
|---|---:|---:|---:|
| TICO-19 validation, 120 pairs | 3.820 / 23.437 | 6.626 / 28.622 | 259 / 127 ms |
| FLORES-200 devtest, 60 pairs | 3.114 / 28.639 | 10.801 / 41.056 | 180 / 86 ms |

The candidate scored higher in both samples and had fewer repeated outputs. This is promising evidence, not a release decision: the samples are small, automatic metrics can reward the wrong wording, the model has not had fluent-speaker review, and I have not audited training/test overlap. The candidate is listed as CC BY 4.0 and derives from GPT-4o-generated Europarl translations in the [upstream model card](https://huggingface.co/Helsinki-NLP/opus-mt-synthetic-en-so). Its licence and attribution must stay separate from Saylacian's code licence.

## Optional CTranslate2 pack

Saylacian now offers `WindyWord/translate-synthetic-en-so` as a separate, optional download, pinned to revision `11427877b7864afad1b5e93e10d1e89661d8b0c0`. Its card provides a CPU INT8 CTranslate2 variant and CC BY 4.0 license, plus a bundled attribution notice. It derives from the Helsinki synthetic model above. The pack is about 62 MiB and is not bundled in the source repository. The standard Somali/English pack remains the fallback. The experimental model card publishes no quality score.

I installed the pinned pack through Saylacian's checksum-verifying installer and ran it through the app's English-to-Somali routing path. Smoke examples included “I need help finding the hospital.” → “Waxaan u baahanahay caawimaad si aan u helo isbitaalka.” and “Where is the nearest bus station?” → “Halkee buu ku yaal saldhigga baska ee ugu dhow?” The output guard rejected a repeated “Good morning” result and used the standard model instead. These few sentences only verify installation and routing; they are not a quality benchmark or evidence of fluent translation. The model still needs a scored held-out evaluation and fluent-speaker review.

Other model candidates remain experimental until their outputs, dataset overlap, licence terms and runtime costs have been checked against the shipped pack.
