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

I then evaluated the app's single-sentence route on the public-labeled rows in the TICO-19 English–Somali **dev** file, pinned to [dataset revision `55d70dc0b1d1d0b2151c5e22815d823fedac3f2f`](https://huggingface.co/datasets/gmnlp/tico19/tree/55d70dc0b1d1d0b2151c5e22815d823fedac3f2f/dev). Only 37 rows in that file carry the `public` label. I selected all 37 by sorting on SHA-256 of `saylacian-windy-pack-v1` plus each row ID. Scores use SacreBLEU 2.5.1 with effective-order BLEU and chrF++ (`word_order=2`).

| Route | BLEU | chrF++ | Mean time per sentence | Candidate fallbacks |
|---|---:|---:|---:|---:|
| Standard Somali/English pack | 2.197 | 27.427 | 207 ms | — |
| Experimental model, output guard on | 4.332 | 35.376 | 770 ms | 15 of 37 |

The guard rejects copied text, output that is unusually long for its input, and content words of four or more characters repeated three or more times. It improved both scores in this small sample, at a substantial latency cost. It does not recognize every paraphrased repetition: for example, the remaining result for “do your relatives have the same symptoms” repeats a phrase about relatives. Other outputs are also awkward. These automatic scores do not establish useful or fluent Somali; a larger held-out evaluation and fluent-speaker review are still needed. TICO-19 is medical-domain data, so this result must not be generalized to other topics.

## Fine-tuned model screened, not selected

I also screened [`maanka2/opus-mt-en-so-finetuned`](https://huggingface.co/maanka2/opus-mt-en-so-finetuned), pinned to revision `af92fdea79083bbb6c9d753bd56b117bedff4c11`. Its model card declares Apache-2.0 and names `maanka2/english-somali-parallel-corpus` as training data. I could not inspect that dataset's public metadata or terms, so I have not independently verified its training-data rights.

On the same 37 TICO-19 rows, the Transformers checkpoint scored BLEU 5.898 / chrF++ 36.656 at 537 ms per sentence. After conversion to CTranslate2 INT8 and running through Saylacian's actual route, it scored 3.673 / 30.691, fell back on 26 of 37 inputs and averaged 1,013 ms. The selected optional CTranslate2 pack scored 4.332 / 35.376 with 15 fallbacks at 770 ms on that sample. Because the converted candidate performed worse in the app runtime and its training data terms remain unchecked, it is not wired into the app or download list. These results are still small-sample automatic metrics, not fluent-speaker review.

Other model candidates remain experimental until their outputs, dataset overlap, licence terms and runtime costs have been checked against the shipped pack.
