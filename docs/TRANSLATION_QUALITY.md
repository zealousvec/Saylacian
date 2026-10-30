# Somali translation quality

Somali translation is available in alpha testing, but it has not been reviewed by fluent Somali speakers. Check important translations before relying on them.

## Qor-trained candidate cross-check

A private English→Somali candidate trained on 3,470 synthetic pairs from verified Qor Somali text was tested through Saylacian's guarded route. The training text and weights stayed outside the repository. On the same deterministic 120-row sample from each benchmark, it improved over the installed standard route:

| Dataset | Route | BLEU | chrF++ | Guarded fallbacks | Mean warm time |
|---|---|---:|---:|---:|---:|
| HornMT v1.0.0 | Installed standard | 5.448 | 32.291 | 0 / 120 | not recorded in this run |
| HornMT v1.0.0 | Qor-trained candidate + standard fallback | 25.046 | 53.511 | 6 / 120 | not recorded in this run |
| FLORES-200 devtest | Installed standard | 5.353 | 29.882 | 0 / 120 | 521.1 ms |
| FLORES-200 devtest | Qor-trained candidate + standard fallback | 10.619 | 40.583 | 2 / 120 | 285.6 ms |

The existing optional WindyWord English→Somali pack was also run through the same FLORES sample and route checks. It scored 10.888 BLEU / 40.843 chrF++, with two guarded fallbacks and 291.1 ms mean warm time. On HornMT, its existing same-sample result is 24.893 / 53.980 with four fallbacks. The Qor candidate therefore trades a small HornMT BLEU increase for lower chrF++ and more fallbacks, and trails WindyWord on the FLORES screen. It is not a clear replacement for the already available optional pack.

These are screening samples, not proof of fluent Somali or meaning preservation. The base model's own training overlap with HornMT is not ruled out. Qor is CC BY-SA 4.0; the candidate's weight-distribution obligations have not been reviewed, so its weights remain private and are not included in the app or release. No production route changed. Evaluation used the pinned FLORES archive SHA-256 `b8b0b76783024b85797e5cc75064eb83fc5288b41e9654dabc7be6ae944011f6`, HornMT archive SHA-256 `3fc7c9fa3f82cdfabe4cefae16fca256c68b22a21014ec98fcd738c87a9a3f8c`, Qor training manifest SHA-256 `ebaf98120183a59c5c4add75e31e5e45eb9c573dea199419c9fe0f762b8425da`, and candidate model file SHA-256 `7b1b93734365d3877f76cf38005e180733d16810a6625c077151bb9333bc6670`. Only aggregate scores and hashes were recorded.

## What has been measured

Tests used deterministic samples from the English–Somali portion of [FLORES-200](https://github.com/facebookresearch/flores/tree/main/flores200). BLEU and chrF++ compare generated text with reference translations. They do not judge fluency, preserve every meaning, or replace human review.

| Direction and route | Sample result | What it shows |
|---|---|---|
| English → Somali, standard pack | BLEU 5.353; chrF++ 29.882 (120 pairs) | Baseline for this sample only. |
| English → Somali, optional model with fallback | BLEU 10.755; chrF++ 40.069 (same 120 pairs); fallback on 14 outputs | Higher reference similarity in this sample. The app replaced outputs containing an unreadable token. |
| English → Somali, optional model with incomplete-output check | BLEU 10.470; chrF++ 37.983 (a second 120-pair sample); fallback on 31 outputs | The check caught 11 outputs ending in an unprompted ellipsis. Scores fell after fallback, so the check prevents visibly unfinished text; it does not prove the replacement is more accurate. |
| Somali → English, standard pack | BLEU 9.728 → 10.598; chrF++ 32.954 → 33.460 (same 120 pairs) | A code fix stopped sending the model an unsupported Somali target tag. |

The optional AfriSLM model is slower and much larger than the standard pack. In one 240-pair sample it scored BLEU 11.866 / chrF++ 42.335 for English → Somali and 24.862 / 47.598 for Somali → English, with fallback enabled. This is not a full-dataset or human evaluation. Its model and training-data terms are listed separately in [third-party notices](../THIRD_PARTY_NOTICES.md).

## Limits

These scores come from small samples. The optional Somali model has not been checked for training/test overlap, and the standard model may share news or web sources with some evaluation material. Somali output can still be awkward, incomplete or wrong. None of these measurements establishes that a model is fluent or suitable for legal, medical, financial or other high-impact use.

An earlier TICO-19 source audit found mismatched English and Somali references, so its scores are not used here to compare models. No candidate trained during development replaced the installed packs. Model details, revisions and licences are in [`saylacian/core/data`](../saylacian/core/data/) and [third-party notices](../THIRD_PARTY_NOTICES.md).

### TICO-19 language-detection check

The pinned TICO-19 test TSV was also used to check language identification only. Each English and Somali column was classified independently; English–Somali sentence alignment is not needed for that check. The archive SHA-256 was `0e82fc7ceaa877606c8934f32ead185716c9d2c54b3818f2a7ae655f5e7a08d8`; all 2,100 rows were processed with the base `py3langid` detector (`0.4.0`), without the optional OpenLID pack. English was correctly detected in 2,040 rows and abstained on 60; Somali was correctly detected in 2,096 rows and abstained on 4. There were no wrong supported-language labels. The benchmark’s known shifted translations make it unsuitable for translation-quality scoring, but do not affect the language labels used in this detection-only check. Raw text and predictions were not retained. This is one medical-domain benchmark, not a general accuracy guarantee or approval for medical use.

## Decode-width comparison

A fresh evaluation used the installed standard Somali pack and the pinned FLORES-200 devtest archive (SHA-256 verified), with the same deterministic 120 sentence pairs per direction. No output used fallback. Beam widths 2, 4 and 6 were compared:

| Direction | Beam 2 BLEU / chrF++ | Beam 4 BLEU / chrF++ | Beam 6 BLEU / chrF++ | Mean time after first call, beam 2 → 4 → 6 |
|---|---:|---:|---:|---:|
| English → Somali | 5.010 / 29.472 | 5.353 / 29.882 | 5.096 / 29.930 | 334.7 → 409.4 → 480.6 ms |
| Somali → English | 8.938 / 32.574 | 10.598 / 33.460 | 10.306 / 33.300 | 231.6 → 240.6 → 290.9 ms |

Beam 4 scored higher on BLEU than both other settings in both directions. Beam 6 did not justify its extra latency: EN→SO BLEU fell from 5.353 to 5.096 and SO→EN from 10.598 to 10.306 versus beam 4. Beam 4 took about 22% longer than beam 2 for English→Somali and 4% longer for Somali→English on this host. Keep beam 4 on larger CPU profiles and beam 2 on devices with four or fewer logical processors. This is evidence for the trade-off on one host, not proof of quality or performance on every device; the small-core profile still needs physical-device measurement.

## Optional English-to-Somali repetition setting

The optional English-to-Somali pack (`WindyWord/translate-synthetic-en-so`, revision `11427877b7864afad1b5e93e10d1e89661d8b0c0`, CC BY 4.0) was evaluated through Saylacian's real guarded route. The pack was installed into an isolated temporary store, and the manager verified its pinned file hashes. The standard model remains the fallback for outputs flagged by the existing checks.

On the same deterministic 240-pair FLORES-200 devtest sample:

| Route | BLEU | chrF++ | Guarded fallbacks | Mean time after first call |
|---|---:|---:|---:|---:|
| Installed standard route | 4.803 | 29.690 | 0 | 397.6 ms |
| Optional pack, no-repeat size 3 | 10.434 | 39.224 | 55 / 240 | 259.1 ms |
| Optional pack, no-repeat size 2 | 11.011 | 40.511 | 26 / 240 | 217.6 ms |

No-repeat size 2 improved both automatic scores, reduced guarded fallbacks by 29, and was faster in this run. It is now used only by this optional model. The installed standard pack retains its size-3 repetition guard. Automatic scores do not establish fluency; the optional route still needs fluent-speaker review. Model terms and attribution remain in [third-party notices](../THIRD_PARTY_NOTICES.md).

### Additional decode settings on the same FLORES sample

The optional model was also tested with no-repeat size 1, and with beam widths 2 and 6 while holding its current no-repeat size 2. The selected size-2/beam-4 setting remains the best overall trade-off in this 240-pair sample:

| Optional model setting | BLEU | chrF++ | Guarded fallbacks | Mean time after first call |
|---|---:|---:|---:|---:|
| No-repeat 1, beam 4 | 7.753 | 37.429 | 45 / 240 | 323.8 ms |
| No-repeat 2, beam 2 | 10.912 | 40.384 | 28 / 240 | 179.3 ms |
| No-repeat 2, beam 4 | 11.011 | 40.511 | 26 / 240 | 217.6 ms |
| No-repeat 2, beam 6 | 10.909 | 40.554 | 26 / 240 | 224.0 ms |

Beam 2 was measured on a 16-logical-CPU host by changing the decoder beam only; it was not a physical low-core test and the host's thread count stayed at its high-core setting. The beam-6 trial changed only the candidate beam; its standard fallback kept beam 4. These variants do not justify changing current device profiles.

### Remaining guarded fallbacks

An aggregate-only audit of the pinned optional model on the 240-pair FLORES run classified its 26 size-2 fallbacks: 23 contained the model's unknown-token marker, 3 repeated a content word excessively, and none ended with an unprompted ellipsis. Saylacian keeps the existing standard-model fallback for all of these cases rather than removing unreadable text or relaxing the checks. Raw benchmark sentences and outputs were not saved.

### Cross-domain check: HornMT Somali-English news sample

The same decoder settings were checked on a disjoint source, HornMT v1.0.0. Its official archive hash was verified, and its release is CC BY 4.0 ([Zenodo record](https://zenodo.org/records/6369442)). The sample contains 120 deterministic rows; the standard route reproduces its recorded baseline.

| Route | BLEU | chrF++ | Guarded fallbacks | Mean time after first call |
|---|---:|---:|---:|---:|
| Installed standard route | 5.448 | 32.291 | 0 | 446.5 ms |
| Optional pack, no-repeat size 3 | 20.943 | 48.681 | 39 / 120 | 348.2 ms |
| Optional pack, no-repeat size 2 | 21.685 | 50.039 | 28 / 120 | 329.4 ms |

Size 2 also scored higher and reduced fallbacks on this news sample. Both corpora are limited automatic evaluations, and neither replaces fluent-speaker review.

### Optional model unknown-token replacement

The optional English-to-Somali candidate now enables CTranslate2 `replace_unknowns`, which uses attention alignment to replace unknown target tokens with source tokens. This setting applies only to that candidate; the installed standard route and its fallback behavior are unchanged. See the [CTranslate2 Translator API](https://opennmt.net/CTranslate2/python/ctranslate2.Translator.html) for the option definition.

The production Saylacian route was compared on the same deterministic 240-pair FLORES-200 devtest sample, with all existing output checks and standard-model fallback enabled:

| Optional route setting | BLEU | chrF++ | Guarded fallbacks | Mean time after first call |
|---|---:|---:|---:|---:|
| No-repeat size 2, unknown replacement off | 11.011 | 40.511 | 26 / 240 | 201.7 ms |
| No-repeat size 2, unknown replacement on | 11.228 | 41.181 | 6 / 240 | 178.7 ms |

This sample improved both automatic scores and reduced fallback count by 20. It does not establish that source-token substitutions are linguistically correct; names, borrowed words and alignment errors can still produce wrong output. The standard fallback and output guards remain enabled, and this result is not a fluency claim.

The same production-route comparison was repeated on a deterministic 120-pair sample from HornMT v1.0.0, an independent published Somali-English benchmark whose archive hash and CC BY 4.0 release are verified above:

| Optional route setting | BLEU | chrF++ | Guarded fallbacks |
|---|---:|---:|---:|
| No-repeat size 2, unknown replacement off | 21.685 | 50.039 | 28 / 120 |
| No-repeat size 2, unknown replacement on | 24.893 | 53.980 | 4 / 120 |

The direction is consistent across these two samples, but neither benchmark is specialist-reviewed, and possible overlap with the installed model's training data has not been ruled out. Keep Somali output marked for review.

## Optional detector threshold calibration

The optional OpenLID fallback currently uses a Somali-confidence threshold of 0.98. A fresh pass over the pinned Qor Af-Soomaali v0.4.0 release (3,629 verified CC BY-SA 4.0 rows; SHA-256 `f53ec99fbbd620ac65412d0c26c62a80faa534b9a939e95a0da6c53d5b38c60c`) selected 67 short Somali texts using the existing 12–19 character, three-word filter. At 0.98, the base detector labeled 37 Somali and the production detector with OpenLID labeled 40. At 0.95, 41 were labeled; at 0.90, 47. On 1,012 three-word prefixes per language from the hash-verified FLORES-200 archive (`b8b0b76783024b85797e5cc75064eb83fc5288b41e9654dabc7be6ae944011f6`), Somali detections rose from 845 at 0.98 to 857 at 0.95 and 868 at 0.90. English and French counts stayed at 262 and 412 respectively in those samples.

A separate SHA-256-ranked sample of 50 three-word prefixes from each of FLORES-200's 204 languages yielded 9,913 eligible probes. At 0.98, the detector labeled 43 Somali probes correctly and labeled one non-Somali probe Somali. At 0.95, those counts were 44 and one; at 0.70, 45 and three. These short samples do not establish general precision. An earlier 11,386-row MASSIVE screen found one false Somali label at 0.90 and none at 0.98. The fresh MASSIVE replication was stopped before completion because of CPU cost. Keep the production threshold at 0.98 until a complete, controlled evaluation supports a change.

Only aggregates were saved. Qor and FLORES text stayed outside the repository. This measures language identification, not translation quality or Somali fluency. Sources: [Qor Af-Soomaali](https://huggingface.co/datasets/unkadlabs/qor-af-soomaali) and [FLORES-200](https://github.com/facebookresearch/flores/tree/main/flores200), both CC BY-SA 4.0.

## Short mixed-language detection

The short-text confidence setting was compared at 0.70 and 0.75 using the pinned Qor and FLORES samples. For a separate stress check, each of 1,012 English FLORES rows was paired with one of the first 1,012 verified Qor Somali entries. Four synthetic three-word patterns were formed from their first words: English-English-Somali, Somali-English-English, English-Somali-Somali, and Somali-Somali-English. These are constructed probes, not natural conversations. At 0.70, single-language labels appeared on 981 of 4,048 probes; at 0.75, they appeared on 909. The lower threshold therefore adds 72 single-language guesses on this probe. A quick boundary-split guard screen caught at most 64 probes at confidence 0.50 and none at 0.90, with no false mixed warnings in 6,513 clean Qor/FLORES snippets; it was not added because it catches few mixtures and requires extra classifier calls. The 0.70 threshold remains selected for the measured short-fragment coverage increase, while short mixed text remains unreliable. The complete aggregate evaluation and construction method are recorded in `IMPLEMENTATION_PROGRESS.md`; all source text stayed outside Git.

The offline detector compares the first and last three-word chunks and checks a middle three-word chunk in text of at least nine words when the edges agree. The mixed-chunk confidence threshold is 0.50; whole-text and short-text thresholds remain unchanged. On 1,012 constructed English-prefix/Somali-prefix probes from aligned FLORES-200 rows, mixed warnings rose from 223 at the previous 0.70 threshold to 388. The current detector abstained on 737 probes, labeled 274 Somali and 1 English. Clean sentence, monolingual-edge and three-word-fragment outcomes remained unchanged; no mixed warnings appeared across 3,036 clean English, French and Somali FLORES sentences.

Three additional synthetic 1,012-row patterns placed a language switch in the middle of otherwise same-language text. The detector flagged 150 English–Somali–English probes, 322 Somali–English–Somali probes and 105 English–French–English probes. These are constructed diagnostics, not natural code-switch conversations or a reliable estimate of real-world recall. Many probes still abstain or receive one language, and no conclusion about broad code-switch accuracy follows.

## Decoder length-penalty screen

CTranslate2 exposes `length_penalty` for beam search ([version 4.8.3 API](https://opennmt.net/CTranslate2/python/ctranslate2.Translator.html)). A temporary sweep compared 0.8, 1.0 and 1.2 on the same deterministic 40-pair FLORES subset with the pinned optional English-to-Somali model, the normal output guards and the installed standard-model fallback. The candidate weights were hash-checked against the pinned model manifest. No output triggered fallback.

| Length penalty | BLEU | chrF++ | Mean time after first call |
|---:|---:|---:|---:|
| 0.8 | 12.525 | 42.313 | 224.5 ms |
| 1.0 (current) | 12.525 | 42.352 | 219.4 ms |
| 1.2 | 12.261 | 42.226 | 207.3 ms |

The differences are small on this screening sample. Length penalty 1.0 matched the best BLEU and slightly led chrF++; 1.2 was faster but scored lower on both measures. Keep the current default. This is not a full evaluation or human quality review.

### Compact AfriNano Somali model screen

On 2026-10-28, I screened QVAC's `TranslatePsy-AfriNano` Tiny English-to-African fp32 checkpoint against Saylacian's installed standard Somali route. The model is revision `7a793aac03e34b31f53388c22eda26ae108c58e5`; the inference source is pinned at `2a51da3e05653c412199b6365b2b1dcf7c05b71`. Both model artifacts were downloaded to a temporary directory and matched the Hugging Face LFS SHA-256 values: weights `73675170f9e529cde6262445fc2a8aa0e287da155a8f7856eab3f47bdc178db4`, vocabulary `f7e3068abd436998d3e6793dfa0ef55cd23ebb93d64324d9216e7f8e920d77b2`. They were not added to Saylacian or Git.

Using the same deterministic 120-pair FLORES-200 English-to-Somali sample, Saylacian's installed standard route scored 5.353 BLEU / 29.882 chrF++ with no fallback; the Tiny model through the publisher's pinned `qvac-nmt` PyTorch reader scored 9.899 / 36.555. Candidate model load took 290 ms, and mean warm translation time was 258 ms with two PyTorch threads. FLORES is not independent evidence for this model: its model card states that FLORES-200 devtest was used for the publisher's own test evaluation. This comparison also differs in decoder (the publisher's reader is greedy, beam 1), so it is a screening result rather than a like-for-like release benchmark.

On a deterministic 120-row HornMT v1.0.0 English-to-Somali sample, the same Tiny checkpoint scored 21.633 BLEU / 49.615 chrF++ at 282 ms mean warm time. On that same sample, Saylacian's currently selected optional WindyWord route was previously measured at 24.893 / 53.980 with four guarded fallbacks; the installed standard route scored 5.448 / 32.291. The compact candidate therefore did not beat the optional route on the independent cross-domain sample.

Do not add this checkpoint to the app or promote it as an improved default yet. The model card labels it `apache-2.0` but also says “for research and educational purposes”; that qualifier needs written interpretation before broader redistribution or use. It reports OPUS-100 and MADLAD-400 as training sources without publishing the exact Somali row-level provenance or derivative-weight terms. The Python reader requires PyTorch and does not consume the CTranslate2 format used by Saylacian. The publisher's CPU table reports 1,417 MB RAM for Tiny fp32; the local screening did not measure peak memory. Its smaller INTGEMM form needs the Bergamot runtime, which Saylacian does not currently use. These licensing and runtime costs outweigh the promising FLORES score until they are resolved. Sources: [AfriNano model card](https://huggingface.co/qvac/TranslatePsy-AfriNano), [pinned qvac-nmt source](https://github.com/tether-ai-research/qvac-translatepsy-euro-nano/tree/2a51da3e05653c412199b6365b2b1dcf7c05b71f).

### Candidate decoder controls on an independent sample

The optional WindyWord English-to-Somali route was screened on the same deterministic 120-row HornMT v1.0.0 sample used in the existing cross-domain comparison. Each setting ran through Saylacian's guarded route with the installed standard-model fallback. The base setting reproduces the earlier 24.893 BLEU / 53.980 chrF++ result and four guarded fallbacks.

| Candidate setting | BLEU | chrF++ | Guarded fallbacks | Mean time after first call |
|---|---:|---:|---:|---:|
| Repetition penalty 1.0; unknowns allowed (current) | 24.893 | 53.980 | 4 / 120 | 226.3 ms |
| Repetition penalty 1.05 | 24.953 | 54.016 | 3 / 120 | 221.5 ms |
| Repetition penalty 1.1 | 24.783 | 53.826 | 3 / 120 | 217.3 ms |
| Repetition penalty 1.0; disable unknown tokens | 24.698 | 53.659 | 4 / 120 | 224.3 ms |

The 1.05 penalty's small HornMT lead is not consistent across datasets: on the deterministic 240-row FLORES sample it scored 11.075 BLEU / 41.096 chrF++, below the current 1.0 setting's 11.228 / 41.181. The 1.05 and 1.1 penalties reduced HornMT fallbacks by one each, while unknown-token suppression did not; none of these small results held consistently across both datasets. Keep the current decode settings. These small automatic samples do not establish fluency or meaning preservation; no app defaults changed.

### AfriSLM-Q4 Somali route screen on HornMT

Saylacian already offers QVAC's optional AfriSLM-Q4 pack for English–Somali. I rechecked that exact pinned model (`qvac/TranslatePsy-AfriSLM-0.8B-Q4-GGUF`, revision `14d6fd1e24c9f94a5e40c2e91c066241aede0dce`; model SHA-256 `4af8ee1df3ec9008f763ebe95e6f21df3acd8d42c541feeb13314ca22e560afc`) on the same deterministic 40-row HornMT v1.0.0 sample used for the current optional WindyWord route. The model downloaded only to a temporary directory; the pinned hash matched. Its model card licenses the weights under Apache-2.0 and separately identifies CC BY-NC-4.0 terms for its synthetic training mix and NLLB teacher. Neither dataset was downloaded or included in Saylacian.

| English-to-Somali route | BLEU | chrF++ | Guarded fallbacks | Mean time after first call |
|---|---:|---:|---:|---:|
| Installed standard route | 5.256 | 31.875 | 0 | not timed here |
| Optional WindyWord route with standard fallback | 21.618 | 52.165 | 3 / 40 | 260.6 ms |
| AfriSLM-Q4 raw output | 29.622 | 57.633 | 1 guard rejection | 2,778 ms |
| AfriSLM-Q4 with the existing standard-route fallback | 28.855 | 56.389 | 1 / 40 | 2,778 ms |

The application prompt and the 2,048-token context were used with `llama-cpp-python` 0.3.36, one CPU thread, temperature 0 and a 256-token output cap. The Qwen chat template returned a leading `</think>` delimiter on all 40 rows; Saylacian's existing AfriSLM output cleanup removes it. One candidate output triggered the existing repeated-word guard. In an earlier interrupted run, the process working set was about 1.06 GiB while handling the model. The disjoint follow-up sample below also shows a metric lead, but the added latency and memory make the route unsuitable as a forced default for lower-resource devices. Keep it optional and get fluent-speaker review before making broader quality claims. HornMT overlap with model training cannot be fully ruled out.

Sources: [QVAC AfriSLM-Q4 model card](https://huggingface.co/qvac/TranslatePsy-AfriSLM-0.8B-Q4-GGUF), [publisher inference and license details](https://huggingface.co/qvac/TranslatePsy-AfriSLM-0.8B-Q4-GGUF#licensing-information), [HornMT v1.0.0](https://zenodo.org/records/6369442).

### Optional AfriSLM 2B comparison

Saylacian now offers the optional `qvac/TranslatePsy-AfriSLM-2B-Q4-GGUF` pack (1.56 GB). Its revision is pinned to `9bcceadebbcc5d36bba9f7f02141300a95ae8d04`; the weights' SHA-256 is `fc2a80532e58e0655efd9e68c5b7cb2c4373222e736bcc88de648502a4e30361`. The downloaded pack includes the publisher's checksum-pinned `ATTRIBUTIONS.md`. A matched evaluation used the same deterministic 120-row HornMT v1.0.0 sample per direction, Saylacian's guarded offline route, `llama-cpp-python` 0.3.36, one CPU thread and blocked network connections. Candidate fallbacks used the installed standard pack; only aggregate scores were saved.

| Route | English → Somali BLEU / chrF++ | Guarded fallbacks | Somali → English BLEU / chrF++ | Guarded fallbacks | Warm mean latency EN→SO / SO→EN |
|---|---:|---:|---:|---:|---:|
| AfriSLM 0.8B | 29.863 / 57.868 | 4 / 120 | 34.105 / 58.400 | 4 / 120 | 2,516.7 / 1,447.3 ms |
| AfriSLM 2B | 30.516 / 58.425 | 5 / 120 | 36.583 / 61.150 | 1 / 120 | 5,799.2 / 2,932.5 ms |

On this sample the 2B route scored higher in both directions, most noticeably Somali→English; it also ran roughly twice as slowly and used about 2.3 GB of working memory in the local Windows run. This does not establish general quality, fluency, or independence from model training data. The 2B pack remains optional. Saylacian selects it only when the device has more than four logical CPU cores and at least 4 GiB of available physical memory; otherwise it uses the smaller AfriSLM pack if installed, or the standard Somali pack. The resource check is a cautious local policy, not a physical low-end device benchmark. Model and training-data terms remain separate; see [third-party notices](../THIRD_PARTY_NOTICES.md). Fluent-speaker evaluation is still needed.

The initial route check used the actual downloaded 2B weights through Saylacian's new `en_so_afrislm_2b` pack path for one sentence in each direction, with network connections blocked. The route loaded the pinned 2B file and produced both outputs without triggering the fallback guard. This smoke check does not replace the benchmark or human review.

### Disjoint AfriSLM-Q4 HornMT holdout

On 2026-10-29, the same pinned AfriSLM-Q4 model was evaluated on deterministic HornMT sample ranks 41–120, disjoint from the 40-row screen above. The archive MD5 and model SHA-256 matched their pinned values. The route used Saylacian's `afrislm.translate` helper, the existing repeated-content-word guard, and the optional WindyWord route as fallback. Only aggregate metrics were saved; no sentence output was added to the repository.

| English-to-Somali route | BLEU | chrF++ | Guarded fallbacks | Mean time after first call |
|---|---:|---:|---:|---:|
| Optional WindyWord route | 26.623 | 54.970 | 0 | not timed in this run |
| AfriSLM-Q4 raw output | 32.041 | 59.910 | 3 guard rejections | 2,797.6 ms |
| AfriSLM-Q4 with WindyWord fallback | 30.999 | 59.148 | 3 / 80 | 2,797.6 ms |

This larger disjoint portion preserves the candidate's metric lead over WindyWord on the selected HornMT sample, but it is still only one deterministic sample from one corpus. Training overlap cannot be ruled out, and automatic metrics do not establish fluency or meaning preservation. The one-thread run reached roughly 1.1 GiB working set and about 2.8 seconds mean warm inference, so AfriSLM remains an optional, resource-heavy route; do not make it the default or force it onto low-memory devices. No app defaults changed. Fluent-speaker evaluation and a broader independent test set remain necessary.

### Direction-specific decoding for the standard Somali model

The standard English–Somali CTranslate2 pack was evaluated with no-repeat n-gram size 2 versus its existing size 3. Each setting used the same deterministic 120-row sample from HornMT v1.0.0 and FLORES-200 devtest, in both directions. Routes ran offline with one CPU thread and the existing beam size 4; no fallback occurred.

| Direction | No-repeat size | HornMT BLEU / chrF++ | FLORES BLEU / chrF++ | Mean warm ms: HornMT / FLORES |
|---|---:|---:|---:|---:|
| English → Somali | 2 | 5.368 / 32.133 | 5.218 / 29.758 | 599.4 / 499.6 |
| English → Somali | 3 (previous) | 5.448 / 32.291 | 5.353 / 29.882 | 614.9 / 502.0 |
| Somali → English | 2 | 12.249 / 37.902 | 10.681 / 33.481 | 341.0 / 292.8 |
| Somali → English | 3 (previous) | 11.822 / 37.277 | 10.598 / 33.460 | 343.9 / 300.7 |

Size 3 wins English → Somali on both samples; size 2 wins Somali → English on both. The English → Somali differences are small, so keep size 3 there. The Somali → English gain is stronger on HornMT and modest on FLORES; use size 2 in that direction. These are automatic scores on small samples, not fluent-speaker review, and model-training overlap is not ruled out.

### Beam-width retest after direction-specific decoding

After selecting no-repeat size 3 for English → Somali and 2 for Somali → English, beam 6 was compared with beam 4 on the same deterministic 120-row HornMT and FLORES samples. Both settings used the installed standard pack, one CPU thread, and the real offline app route; neither used fallbacks. Beam 4 below uses the current direction-specific settings.

| Direction and dataset | Beam 4 BLEU / chrF++ | Beam 6 BLEU / chrF++ | Beam 4 → 6 mean warm time |
|---|---:|---:|---:|
| English → Somali, HornMT | 5.448 / 32.291 | 5.742 / 32.146 | not measured for HornMT in this run |
| Somali → English, HornMT | 12.249 / 37.902 | 12.772 / 38.035 | not measured for HornMT in this run |
| English → Somali, FLORES | 5.353 / 29.882 | 5.096 / 29.930 | 352.9 → 438.9 ms |
| Somali → English, FLORES | 10.681 / 33.481 | 10.585 / 33.277 | 217.7 → 269.2 ms |

Beam 6 improved both HornMT BLEU scores and Somali → English chrF++, but its English → Somali chrF++ dipped slightly. On FLORES, beam 6 had lower BLEU in both directions, higher English → Somali chrF++ by only 0.048, and lower Somali → English chrF++; warm time was about 24% slower in both directions. The cross-corpus result does not support a general quality improvement, so the shipped beam width remains 4 on larger CPU profiles and 2 on devices with four or fewer logical processors. These automatic scores do not substitute for Somali-speaker review.
