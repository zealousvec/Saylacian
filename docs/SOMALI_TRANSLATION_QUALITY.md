# Somali translation quality work

## Current change

Saylacian's current English-to-Somali synthetic checkpoint can loop and produce far more text than the input warrants. `translation.py` now rejects only extreme length outliers: output longer than twice the source word count plus ten words. Saylacian then uses its installed multilingual OPUS route as a local rescue. Other candidate behavior and ordinary outputs remain unchanged.

The rule was evaluated on a deterministic, length-stratified 150-example sample from TICO-19's English/Somali **dev** split, separate from the 150-example test sample. On dev, BLEU changed from 6.138 to 7.299 and chrF++ from 27.577 to 28.509; only 5 of 150 examples used rescue. On the held-out test sample, BLEU changed from 6.245 to 7.057 and chrF++ from 28.608 to 28.996; 7 of 150 examples used rescue. The full test run still produced the same Somali-to-English scores (BLEU 6.300, chrF++ 24.680). Automatic metrics do not establish semantic correctness; fluent Somali review is still needed.

### Reproduction on 2026-10-24

The pre-guard 150-pair run used network connections blocked and an isolated result/checkpoint location. Dataset SHA-256: `be58b2d350badb7e03b73906471453311a8843534e4a2a572a772c60c394c7f7`. It scored EN→SO BLEU 7.057 / chrF++ 28.996 and SO→EN BLEU 6.300 / chrF++ 24.680. Its EN→SO route selected the synthetic candidate 143 times and used multilingual fallback 7 times, all for excessive output length. The stored outputs contained SentencePiece's default unknown-token marker U+2047 in 46/150 EN→SO rows (81 occurrences). The upstream documentation defines U+2047 as the default decoded surface for unknown tokens: [SentencePiece special symbols](https://google.github.io/sentencepiece/doc/special_symbols/).

The candidate route now detects U+2047 and falls back to the existing multilingual EN→SO model. A fresh Python 3.12 developer environment installed the pinned Somali pack, verified its hashes, and reran the same 150-pair benchmark with network access blocked during inference. Post-guard scores were EN→SO BLEU 5.287 / chrF++ 25.282 and SO→EN BLEU 6.300 / chrF++ 24.680. The candidate was selected 97 times; 47 unknown-token and 6 output-length fallbacks were used. No U+2047 marker remained in final EN→SO output. The aggregate automatic EN→SO scores decreased; this confirms a visible decode artifact was removed, not that translation meaning improved. Keep the feature, score change, and Somali quality status under review; no fluent-speaker assessment occurred. Numeric-token and possible-negation cues remain automatic review prompts only.

The temporary benchmark output and checkpoint are under `%TEMP%` and are not committed. The developer-only requirements now pin `sacrebleu==2.5.1`, which the benchmark imports; it is not a runtime dependency. Timing and memory figures from earlier runs are machine-specific.

### Reproduction on 2026-10-25

Reinstalled the pinned Somali pack with `tools/verify_pack_integration.py --pack somali` into a new temporary store. The installer verified all 10 manifest assets and passed English→Somali and Somali→English offline smoke translations. Installed pack version: `1-bfd6cf52bd69`; runtime versions: CTranslate2 4.8.3, SentencePiece 0.2.2, SacreBLEU 2.5.1. The 150-pair test fixture SHA-256 remained `be58b2d350badb7e03b73906471453311a8843534e4a2a572a772c60c394c7f7`.

This run also used the already-present, ignored local Helsinki synthetic EN→SO candidate, independently checked against the tracked manifest: revision `49384e6b2c3ddd374f2cccc8efecb678724b739d`, CC-BY-4.0, `model.bin` SHA-256 `62aacb4ec5812ce20a1eb2563fe763d16d20858e2490d6d8bdd0a3a1f4f72c22`. It was not added to Git or the downloaded pack. The official pack's English→Somali and Somali→English models are Apache-2.0 declarations at revisions `89fdef87793d0b4a3860bd4d7c5e4cf77e7575b9` and `fb574c2082b1a49f89e55064aca6c1fba1125474`, respectively.

With network connections blocked during inference, the run reproduced the previous post-guard scores exactly: EN→SO BLEU 5.287 / chrF++ 25.282; SO→EN BLEU 6.300 / chrF++ 24.680. The synthetic candidate was accepted for 97/150 English inputs; 53 fell back (47 unreadable-token, 6 output-length, 0 repeat/copy). No U+2047 marker remained in final EN→SO output. This remains below the pre-guard EN→SO BLEU 7.057 / chrF++ 28.996 and is not evidence of semantic improvement.

This Windows run took 134.91 seconds, with 548,204,544 bytes peak process working set. Warm per-sample latency medians were 254.9 ms EN→SO and 207.3 ms SO→EN; p95 values were 1,356.1 ms and 530.9 ms. Heuristic review cues flagged 41 EN→SO / 40 SO→EN numeric mismatches and 23 possible negation mismatches in each direction. These are automatic review cues, not confirmed errors; no fluent reviewer rated the samples.

The run exposed stale route-audit string matching that had reported zero fallbacks. `tools/benchmark_somali_quality.py` now counts the current warning phrases, distinguishes candidate selections from fallbacks, and has a regression test for each reason. The complete result JSON, checkpoints, downloaded pack and raw examples remain in temporary storage only; none were committed.

The experiment rejected broad repeated-ngram blocking: it reduced some loops but caused errors such as replacing “cough” with unrelated words, and hurt chrF++ on dev. Only the length guard is enabled.

## Candidate model results

- **Maanka2 OPUS-MT fine-tune**, 60.6M parameters, locally converted to CTranslate2 int8: English-to-Somali BLEU 4.129, chrF++ 26.893 on same 150-example test sample. Worse than the guarded app route, so not selected. No-repeat trigram decode scored lower still (BLEU 3.754, chrF++ 26.240).
- **QVAC AfriSLM 0.8B Q4**: BLEU 7.474, chrF++ 29.847 EN-to-SO; BLEU 14.122, chrF++ 32.647 SO-to-EN. It scored higher automatically, but peaked near 1.09 GB resident memory on the benchmark PC. The model card declares Apache-2.0 weights while identifying CC-BY-NC training data; public redistribution rights need clarification. It is not bundled or enabled.

NLLB, MADLAD and M2M100 licensing/packaging evidence and the incomplete M2M100 runtime comparison are recorded in [SOMALI_MODEL_CANDIDATES.md](SOMALI_MODEL_CANDIDATES.md). No unmeasured candidate is described as better.

TICO-19 focuses on health/COVID-19 communication, and the current sample is only 150 pairs. Model training overlap is not fully established. Treat these scores as comparative signals, not general-purpose quality guarantees or human evaluation.

## Reproduce

```powershell
.\.venv\Scripts\python.exe tools\benchmark_somali_quality.py --system baseline
.\.venv\Scripts\python.exe tools\benchmark_somali_en_candidate.py --model-dir PATH_TO_MODEL --results PATH_TO_BASELINE_RESULT.json
.\.venv\Scripts\python.exe tools\evaluate_somali_repetition_fallback.py --parquet PATH_TO_TICO19_EN_SO_VALIDATION_PARQUET --limit 150
```

Benchmark tools default to unique result files under `%LOCALAPPDATA%\Saylacian\benchmark`, outside the source repository. You may pass `--output` or `--results` to choose another path, but repository paths are rejected. Checkpoints also stay under local application data. The current source snapshot retains aggregate metrics and limitations; generated reports stay outside the checkout. Historical Git commits have not been rewritten. The dev parquet was used from the `gmnlp/tico19` mirror, whose dataset card declares CC0; download it to a private benchmark directory, not the app pack.

## Candidate sources

- [Helsinki synthetic EN-SO model](https://huggingface.co/Helsinki-NLP/opus-mt-synthetic-en-so)
- [Maanka2 fine-tuned EN-SO model](https://huggingface.co/maanka2/opus-mt-en-so-finetuned)
- [QVAC AfriSLM model card](https://huggingface.co/qvac/TranslatePsy-AfriSLM-0.8B-Q4-GGUF)
- [TICO-19 benchmark and splits](https://tico-19.github.io/testset.html)

## Independent isolated re-run on 2026-10-25

Reinstalled the Somali pack into a new temporary store: version `1-bfd6cf52bd69`, 314,460,806 verified bytes, all 10 pinned assets valid, and both offline smoke directions passed. The 150-pair fixture SHA-256 remained `be58b2d350badb7e03b73906471453311a8843534e4a2a572a772c60c394c7f7`. The local Helsinki candidate `model.bin` matched pinned SHA-256 `62aacb4ec5812ce20a1eb2563fe763d16d20858e2490d6d8bdd0a3a1f4f72c22`. Inference ran with `socket.socket.connect` blocked; the complete result and checkpoint stayed in isolated temporary storage outside the repository.

Scores reproduced EN→SO BLEU/chrF++ `5.287/25.282` and SO→EN `6.300/24.680`. Route accounting: 97 synthetic selections and 53 fallbacks (47 unreadable-marker, six output-length, zero repeat/copy); no U+2047 in final EN→SO. Runtime was 115.26 seconds and peak working set 548,388,864 bytes. The outputs are not human-rated and do not establish Somali translation quality.

### Reproduction after translation-model cache bound — 2026-10-25

After capping the in-process LRU model cache at three, installed the pinned Somali pack into a fresh isolated store (version `1-bfd6cf52bd69`; 10/10 assets, 314,460,806 bytes) and passed both offline smoke directions. The local Helsinki candidate hash matched the manifest. Re-ran the exact 150-pair TICO-19 fixture with network blocked and results/checkpoint in temp. Scores remained exactly EN→SO BLEU/chrF++ 5.287/25.282 and SO→EN 6.300/24.680; 97 candidate selections, 53 fallbacks (47 unreadable marker, six output length), no U+2047. Runtime 108.06 seconds; peak working set 547,704,832 bytes. This confirms the cache change did not alter outputs on this fixture. It is not human Somali quality evidence.

The old four-entry cache left 422 MiB working set after sequentially loading all four static routes; the three-entry cache settled at 318 MiB and cache clear returned to 34 MiB. A two-entry setting was tested and rejected: it caused route reload churn, 178.67-second benchmark time and 583,114,752-byte peak. Three is the measured balance for the current three-engine Somali route; mobile and low-memory-device behavior remain untested.
