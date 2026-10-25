# Somali translation quality checks

Somali translation is experimental. These reproducible checks compare shipped routes; they do not establish fluent or general-purpose translation quality.

## TICO-19 alignment warning

Earlier scores below used TICO-19 dev and test TSV files. A later source/reference audit found clear mismatches in both files, so those scores must not be used to rank models. For example, test row `Wikipedia_handpicked_1:1172` pairs “About 364,000 people have recovered” with a Somali sentence about case-fatality rates; that Somali sentence translates the next English row, `:1173`. Test row `:1521` pairs “Certainly, this is not a good sign of European solidarity” with a Somali sentence about Russia sending medical staff to Italy, which translates row `:1522`. In the dev sample, row `wiki_5:2800` also pairs an English sentence about more than 8,000 infections with a Somali sentence about a new coronavirus variant being identified in 2012.

The TICO measurements below are retained only as a record of earlier runs. The audit found incorrect source/reference pairs, so BLEU and chrF scores cannot support quality claims or model rankings. Repetition and timing counts describe those runs but say nothing about whether the translation preserves meaning. Correcting the affected pairs requires a verified alignment or independent Somali review; I have not guessed replacement references.

## Historical TICO-19 repetition-control run (invalid for quality comparison)

I compared the model's usual beam decoding with CTranslate2's three-token no-repeat option on 120 examples from the English–Somali TICO-19 validation split. Examples were selected by SHA-256 rank of their IDs using the seed `saylacian-v1`. The evaluation used CTranslate2 4.8.3 and SacreBLEU 2.5.1, with effective-order BLEU and chrF++ (`word_order=2`).

| Route and decoding | BLEU | chrF++ | Outputs with a repeated word trigram | Mean time per sentence |
|---|---:|---:|---:|---:|
| English → Somali, default | 3.755 | 23.222 | 7 of 120 | 284.5 ms |
| English → Somali, no repeated three-token sequence | 3.820 | 23.437 | 3 of 120 | 298.2 ms |
| Somali → English, default | 6.775 | 23.339 | 14 of 120 | 156.5 ms |
| Somali → English, no repeated three-token sequence | 6.907 | 23.575 | 1 of 120 | 187.8 ms |

Because the audited split contains misaligned references, the scores cannot support a quality claim or model ranking. The measured repeat counts can still describe how often the guard's narrow target appeared in these outputs; they do not assess meaning or fluency. The run recorded roughly 14 ms additional time per English-to-Somali sentence and 31 ms per Somali-to-English sentence in that CPU run, but those timings depend on the sampled inputs. The guard applies to model tokens, not Somali grammar, and can suppress valid repetition. The benchmark split is [available as CC0](https://huggingface.co/datasets/gmnlp/tico19).

## Historical English-to-Somali candidate check (invalid for quality comparison)

I also compared the current pack with Helsinki-NLP's `opus-mt-synthetic-en-so` checkpoint, pinned to `e69e7d6b2e6180242c2600d02fe93f77832a5ecd`. I converted its safetensors weights to CTranslate2 int8 locally and used the same three-token repetition guard for both systems.

| Sample | Current pack BLEU / chrF++ | Candidate BLEU / chrF++ | Mean time: current / candidate |
|---|---:|---:|---:|
| TICO-19 validation, 120 pairs | 3.820 / 23.437 | 6.626 / 28.622 | 259 / 127 ms |
| FLORES-200 devtest, 60 pairs | 3.114 / 28.639 | 10.801 / 41.056 | 180 / 86 ms |

These automatic-score comparisons are invalid for ranking models because the audited TICO references are misaligned; the FLORES sample in this table is also too small to establish quality. The candidate has not had fluent-speaker review, and training/test overlap has not been audited. The candidate is listed as CC BY 4.0 and derives from GPT-4o-generated Europarl translations in the [upstream model card](https://huggingface.co/Helsinki-NLP/opus-mt-synthetic-en-so). Its licence and attribution must stay separate from Saylacian's code licence.

## Optional CTranslate2 pack

Saylacian now offers `WindyWord/translate-synthetic-en-so` as a separate, optional download, pinned to revision `11427877b7864afad1b5e93e10d1e89661d8b0c0`. Its card provides a CPU INT8 CTranslate2 variant and CC BY 4.0 license, plus a bundled attribution notice. It derives from the Helsinki synthetic model above. The pack is about 62 MiB and is not bundled in the source repository. The standard Somali/English pack remains the fallback. The experimental model card publishes no quality score.

I installed the pinned pack through Saylacian's checksum-verifying installer and ran it through the app's English-to-Somali routing path. Smoke examples included “I need help finding the hospital.” → “Waxaan u baahanahay caawimaad si aan u helo isbitaalka.” and “Where is the nearest bus station?” → “Halkee buu ku yaal saldhigga baska ee ugu dhow?” The output guard rejected a repeated “Good morning” result and used the standard model instead. These few sentences verify installation and routing only; they are not a quality benchmark or evidence of fluent translation.

I first evaluated all 37 rows marked `public` in the TICO-19 English–Somali **dev** file, pinned to [dataset revision `55d70dc0b1d1d0b2151c5e22815d823fedac3f2f`](https://huggingface.co/datasets/gmnlp/tico19/tree/55d70dc0b1d1d0b2151c5e22815d823fedac3f2f/dev). I then expanded the check to a deterministic 120-row sample drawn from all 971 rows in that file. Rows were ranked by SHA-256 of `saylacian-windy-pack-v1` plus each row ID, then the first 120 were selected. The dataset card marks the translations CC0. Both comparisons use the app's single-sentence route, CTranslate2 4.8.3, and SacreBLEU 2.5.1 with effective-order BLEU and chrF++ (`word_order=2`).

| Sample and route | BLEU | chrF++ | Mean time per sentence | Candidate fallbacks |
|---|---:|---:|---:|---:|
| 37 public rows, standard pack | 2.197 | 27.427 | 207 ms | — |
| 37 public rows, experimental model with guard | 4.332 | 35.376 | 770 ms | 15 of 37 |
| 120-row sample, standard pack | 2.142 | 22.005 | 632 ms | — |
| 120-row sample, experimental model with guard | 4.894 | 25.961 | 834 ms | 47 of 120 |

These comparisons cannot establish that either route is more accurate because the source/reference alignment is unreliable. The timing varied between runs and should not be read as a stable device-performance estimate. Some wording remains awkward, repeated ideas can pass the guard, and fluent-speaker review is still needed.

The output guard rejects copied text, output that is unusually long for its input, repeated content words, duplicate sentences, repeated opening fragments, and unreadable SentencePiece markers. Fallback warnings identify which check was triggered. These checks do not recognize every paraphrased repetition, and some outputs remain awkward. The TICO score tables above are retained as historical run records only; misaligned references make them unsuitable for judging the guard or comparing routes.

## Fine-tuned model screened, not selected

I also screened [`maanka2/opus-mt-en-so-finetuned`](https://huggingface.co/maanka2/opus-mt-en-so-finetuned), pinned to revision `af92fdea79083bbb6c9d753bd56b117bedff4c11`. Its model card declares Apache-2.0 and names `maanka2/english-somali-parallel-corpus` as training data. I could not inspect that dataset's public metadata or terms, so I have not independently verified its training-data rights.

On the same 37 TICO-19 rows, earlier runs recorded the scores and fallback counts below. Because the references are not reliably aligned, those values cannot establish that one checkpoint is better or worse. The candidate's training-data terms also remain unchecked, so it is not wired into the app or download list.

Other model candidates remain experimental until their outputs, dataset overlap, licence terms and runtime costs have been checked against the shipped pack.

## Candidate for another comparison

The [`Rogendo/mt-so-en-helpline-v1` model card](https://huggingface.co/Rogendo/mt-so-en-helpline-v1/tree/7b4608d45a4192976fd2de1fc3c7b502dfcd6ebe) reports BLEU 7.45 and chrF 33.07 on TICO-19 test. It says the model was fine-tuned on TICO-19 dev and declares Apache-2.0. These are publisher-reported results, not Saylacian measurements. The checkpoint is about 243 MB before conversion, and it is English-to-Somali only. Because it is based on [Helsinki-NLP's synthetic English-to-Somali model](https://huggingface.co/Helsinki-NLP/opus-mt-synthetic-en-so), its licence relationship needs review before redistribution. The current host received HTTP 401 when requesting the public model files, so the checkpoint could not be independently tested or converted to Saylacian's CTranslate2 pack format. Revisit it when the weights are accessible and the licence chain is clear.

## Held-out test-split check

To check whether the dev-split result carried over, I evaluated a deterministic sample of 120 rows from the English–Somali TICO-19 **test** split at the same dataset revision. The TSV has 2,100 rows and SHA-256 `f42bf20622626e7b510bb8244dc503310df08f8b093260c2f231626410860e57`. Rows were ranked by SHA-256 of `saylacian-tico19-test-v1:` followed by each row ID. Scores use the same SacreBLEU settings as the earlier comparison.

| Route | BLEU | chrF++ | Mean time per sentence | Fallbacks |
|---|---:|---:|---:|---:|
| Standard Somali pack | 2.496 | 21.632 | 611 ms | — |
| Optional model with Saylacian's output guard | 4.369 | 24.765 | 646 ms | 58 of 120 |
| Optional model, guard bypassed for measurement only | 6.298 | 28.728 | 321 ms | Not applicable |

The table records earlier measurements only. Because source/reference alignment is unreliable, the score difference cannot support a quality conclusion. An output screen found repeated-content indicators in 12 of 120 raw candidate outputs; this is a mechanical warning count, not a judgment of Somali quality. The guard remains in place pending fluent-speaker review.

This is one small medical-domain sample, not a general translation score. It does not assess fluency, meaning preservation or medical safety, and the candidate model's training/test overlap has not been independently audited. Somali remains experimental and needs fluent-speaker review.

## FLORES-200 baseline

I also checked the standard Somali pack on the FLORES-200 English–Somali `devtest` set, which has 1,012 aligned sentence pairs. The archived Meta FLORES-200 release labels this dataset CC BY-SA 4.0; it is used here only for evaluation and is not included in this repository. The downloaded archive SHA-256 was `b8b0b76783024b85797e5cc75064eb83fc5288b41e9654dabc7be6ae944011f6`.

The sample contains 120 pairs, ranked by SHA-256 of `saylacian-flores-devtest-v1:` followed by each English sentence. I ran each input through Saylacian's actual offline English-to-Somali route using CTranslate2 4.8.3 and SentencePiece 0.2.2. Scores use SacreBLEU 2.5.1 with effective-order BLEU and chrF++ (`word_order=2`).

| Route | BLEU | chrF++ | Mean time per sentence |
|---|---:|---:|---:|
| Standard Somali pack | 5.353 | 29.882 | 662 ms |

These scores are only a small automatic-metric baseline. They do not show that the Somali is natural or accurate. For example, “Each temple had an open temple courtyard and then an inner sanctuary that only the priests could enter” produced “Wixii macbud walba waxay lahaayeen meelaha macbudka furan, markaasaa meesha quduuska ah oo gudaha ah oo wadaaddadu keliya ayaa galay.” The output retains some of the source meaning but reads awkwardly. Fluent-speaker review is still needed.

## Somali-to-English input-tag correction

An audit found that the app added the `>>som<<` output-language tag to both Somali model directions. The Somali-to-English pack is pinned to [`gaudi/opus-mt-mul-en-ctranslate2`](https://huggingface.co/gaudi/opus-mt-mul-en-ctranslate2/tree/fb574c2082b1a49f89e55064aca6c1fba1125474), whose source is multilingual and target is English; the tokenizer maps `>>som<<` to its unknown token. The upstream [Helsinki-NLP model card](https://huggingface.co/Helsinki-NLP/opus-mt-mul-en) confirms the multiple-source-to-English direction. Saylacian now adds the Somali target tag only for English-to-Somali and sends Somali-to-English input without that tag.

I compared the two inputs on the same deterministic 120-pair FLORES-200 `devtest` sample above, using CTranslate2 4.8.3, beam size 4, and the existing three-token repetition guard. Removing the unknown prefix changed BLEU from 9.728 to 10.598 and chrF++ from 32.954 to 33.460; measured batch time changed from 145.1 to 129.3 ms per sentence. These are sample-specific automatic metrics, not a claim of fluent English. A regression test checks that only English-to-Somali receives `>>som<<`.

## Optional English-to-Somali model on FLORES-200

I compared the standard pack with the optional synthetic model using the app's normal English-to-Somali route, including its output checks and standard-model fallback. Both runs used the same deterministic 120-pair sample described above. The optional pack is not part of the base installation; users must choose to download it.

| Route | BLEU | chrF++ | Fallbacks |
|---|---:|---:|---:|
| Standard pack | 5.353 | 29.882 | — |
| Optional model, raw output (diagnostic only) | 10.907 | 40.987 | Not applied |
| Optional model with standard fallback | 10.755 | 40.069 | 14 of 120 |

These automatic scores favor the optional route on this sample, but they do not establish that the Somali is fluent or meaning-preserving. The guard rejected 14 candidate outputs containing the unreadable SentencePiece marker `⁇`; the raw route left this marker inside words such as `New ⁇ ealand's`. Fallback avoids returning that marker, even though those replacement translations scored slightly lower automatically. The optional route's example for “Each temple had an open temple courtyard and then an inner sanctuary that only the priests could enter” was “Mid kasta oo macbud ah wuxuu lahaa barxad furan oo macbad ah ka dibna waxaa jiray hoy gudaha ah oo kaliya wadaadadu ay gali karaan.” It appears more complete than the standard route's output for that sentence, but it still needs fluent-speaker review. Training/test overlap has not been audited.

## Somali-to-English repetition setting check

After removing the unknown language tag, I compared CTranslate2 no-repeat sizes on two independently ranked 120-pair samples from the same FLORES-200 `devtest` archive. Both used beam size 4 and the current Somali-to-English model input. “Repeated trigrams” counts repeated word-level three-word sequences in the English output; CTranslate2 applies its restriction to model tokens, so the counts are not expected to be zero in every run.

| Sample | No-repeat size | BLEU | chrF++ | Outputs with a repeated word trigram |
|---|---:|---:|---:|---:|
| `saylacian-flores-devtest-v1` | 0 | 11.098 | 33.702 | 11 of 120 |
| `saylacian-flores-devtest-v1` | 2 | 10.681 | 33.481 | 0 of 120 |
| `saylacian-flores-devtest-v1` | 3 (current) | 10.598 | 33.460 | 1 of 120 |
| `saylacian-flores-devtest-v1` | 4 | 11.059 | 33.731 | 10 of 120 |
| `saylacian-flores-devtest-v2` | 2 | 10.831 | 31.985 | 0 of 120 |
| `saylacian-flores-devtest-v2` | 3 (current) | 10.956 | 31.765 | 1 of 120 |

There is no clear winner: size 2 has slightly higher chrF++ on both samples and no repeated trigrams, but it changes decoding more aggressively and BLEU results are mixed. Size 4 allows many more repeated phrases. Size 3 had one repeated trigram in each sample and the higher BLEU on the second sample. I kept the current setting; a change needs broader output review, not just another metric comparison.
