# Offline semantic translation

## Implemented experimental subset

English ↔ French runs locally through CTranslate2 and SentencePiece with archived Argos model packages. The runtime performs no model download and calls no external translation service. Two directions were tested on four sentence examples while Python socket connections were disabled. Aggregate timing is retained here; raw outputs are kept in local app data, not the repository. These are small smoke examples, not a broad quality benchmark or expert review.

The UI uses a background worker with a short typing debounce and rejects stale results. Models are cached rather than reloaded per keystroke. Inputs above 4,000 characters are rejected. Longer model inputs are segmented at whitespace into bounded batches with a warning that context can change at joins; a single unbroken segment over the model limit is rejected rather than silently truncated. A packaged build includes only the model and tokenizer needed by this path, not the unused Stanza resources in the original model archives.

Model source commit, hashes and archive sizes are in `models/manifest.json`. The official current Argos and DigitalOcean endpoints returned HTTP 403 during this session; the archived GitHub repository supplied the 1.0 packages. The use of older weights is intentional and remains a quality/maintenance limitation.

Argos collaborator licence clarification explicitly covers model binaries under MIT/CC0:
https://github.com/argosopentech/argos-translate/issues/533

The exact archived repository contains an MIT licence, copied to `notices/Models-MIT.txt`:
https://raw.githubusercontent.com/uav4geo/LibreTranslate-Models/3d5ca0a2c3c302287339b2944329f767ac1673f4/LICENSE

## Somali ↔ English — experimental offline support

Both directions now run locally through pinned CTranslate2 conversions of Helsinki-NLP's multilingual OPUS-MT models. The English-to-multilingual model needs the OPUS source-side `>>som<<` language marker; the shared core adds it and the source end token. Reversing this marker placement produced unusable output during integration and is not the runtime path. Exact commits and SHA-256 digests are recorded in `SOMALI_TRANSLATION_EVIDENCE.json`; raw smoke outputs are excluded from source.

The converted model cards declare Apache-2.0 and attribute the work to Helsinki-NLP OPUS-MT and CTranslate2. Somali support is experimental: these are multilingual checkpoints with materially weaker evidence than the English/French smoke-tested pair. A few offline examples pass, but no broad benchmark or fluent community review has been done. The app warns that Somali output needs fluent human review.

Somali ↔ French is now offered as an explicitly experimental two-step route through English using the existing local pairs. No direct Somali/French model is bundled. A Somali greeting returns French `Comment allez-vous ?`; the reverse returns Somali `Halo, sidee baad u leedahay?`, which is known to need fluent correction. Both routes carry warnings that model errors may compound. This is functional offline coverage, not release-quality accuracy. FLORES-200 could provide a larger independent evaluation, but its official Hugging Face dataset requires acceptance of access terms and imposes controls on redistribution; it was not downloaded or bundled. A properly licensed, accessible, non-contaminated Somali↔French reference test remains needed.

The QVAC TranslatePsy-AfriSLM 0.8B Q4 GGUF candidate has been evaluated locally on the same 150-pair TICO-19 test sample. It reached EN→SO BLEU 7.474 / chrF++ 29.847 and SO→EN BLEU 14.122 / chrF++ 32.647, above the current CTranslate2 app route's 5.287 / 25.282 and 6.300 / 24.680 on that sample. These are automatic, domain-limited scores, not a human quality judgement. The model is not wired into the app: its GGUF runtime and roughly 672 MB weights need a separate optional-pack path, and the model card's Apache-2.0 weights are distinct from its CC-BY-NC-4.0 synthetic training dataset. Keep redistribution and runtime/device requirements under review; see `SOMALI_TRANSLATION_QUALITY.md` for benchmark provenance and limits.

- https://huggingface.co/gaudi/opus-mt-en-mul-ctranslate2
- https://huggingface.co/gaudi/opus-mt-mul-en-ctranslate2
- https://huggingface.co/Helsinki-NLP/opus-mt-en-mul
- https://huggingface.co/Helsinki-NLP/opus-mt-mul-en
- https://opennmt.net/CTranslate2/guides/opus_mt.html
- https://huggingface.co/qvac/TranslatePsy-AfriSLM-0.8B-Q4-GGUF
- https://huggingface.co/datasets/facebook/flores (evaluation data is access-gated; CC BY-SA 4.0)
- https://github.com/facebookresearch/flores

## Functionality-first benchmark (2026-10-23)

`tools/benchmark_translation.py` ran 10 sentences on each of the six bundled routes (60 outputs total), with `socket.socket.connect` patched to raise throughout. Raw results default to a unique file in local app data, outside source control. On the development Windows host, mean CPU times were 50–62 ms for direct English/French, 110–136 ms for direct Somali/English, and 92–112 ms for the two-leg pivot. Peak process working set was 679,718,912 bytes across the full warmed run; the complete `models/` folder was 681,479,977 bytes. These are one-machine measurements, not promised minimums.

After integrating the synthetic EN→SO candidate, the same 60-case offline benchmark was rerun. The current output file is authoritative: peak process working set was 761,131,008 bytes; English→Somali averaged 1,165.5 ms (candidate inference plus fallback where needed); French→Somali averaged 1,153.9 ms; other routes remained about 68–120 ms. Candidate outputs were accepted for six of the ten original EN→SO prompts, with four falling back. These are CPU measurements on this machine, not release minimums. The candidate increases runtime/model footprint and stays experimental.

The 10-sentence Somali set makes the current quality limitation concrete. The English→Somali model generated `Thank you.` → `Mahad nabiyow.`; the Somali→English model generated `Mahadsanid.` → `The Magi.` and `Fadlan i caawi.` → `Food and drink.` A known set of leading decorative artifacts (`○`, `▪`, `❏`, `▸`, `←`) is removed with a warning; semantic errors are not post-edited or hidden. Somali stays explicitly experimental pending fluent review.

### Synthetic English→Somali candidate — integrated with conservative fallback

Helsinki-NLP publishes `opus-mt-synthetic-en-so`, a 156 MB English/Somali Marian checkpoint under CC BY 4.0. Its model card reports FLORES+ ChrF 45.10 and COMET 78.15 for the paper's English↔Somali experiments; these are model-card results, not Saylacian measurements. I evaluated the same 10 English prompts against the installed multilingual model using the cached upstream revision `49384e6b2c3ddd374f2cccc8efecb678724b739d`, converted to CTranslate2 int8. On that local sample it improved `Thank you.` (`Waad ku mahadsan tahay.` vs `Mahad nabiyow.`), `Good morning.` (`Subax wanaagsan.` vs `Subaxda wanaagsan.`), and several ordinary clauses. It also produced obvious repetition for `How are you?`, `Please help me.`, and other items.

The candidate now handles English→Somali when its output is not identical to the English input and does not repeat a normalized full sentence or show a duplicated initial token. For those detectable pathologies the existing multilingual model is used instead, with an explicit warning. This is a narrow guard, not a Somali quality judge: fluent review is still necessary, and subtler semantic errors pass through. The candidate remains one-way and experimental. Its model-card license and attribution are included in `notices/OPUS-MT-Synthetic-Somali.txt`; the converted file hashes and source revision are in `models/manifest.json`.

- https://huggingface.co/Helsinki-NLP/opus-mt-synthetic-en-so (CC BY 4.0 model card, data description, and reported scores)
- https://arxiv.org/abs/2505.14423 (paper: synthetic data generation for low-resource MT)

- https://huggingface.co/Helsinki-NLP/opus-mt-synthetic-en-so (model card, file list, CC BY 4.0)
- https://arxiv.org/abs/2505.14423 (paper: synthetic data generation for low-resource MT)

## Offline language identification — cautious subset

The app and local website now use pinned `py3langid==0.4.0` to identify English, French or Somali Latin from longer Latin text. The model is bundled with the package, uses no network, and reports confidence. It abstains below 70%, on inputs shorter than 20 characters or three words, and when a confidently identified language is outside the current translation subset. Pure Osmanya is checked separately as a script; script recognition is not meaning translation. Short phrases can be ambiguous and users can choose a source language manually.

Project checks include three supported-language examples, a short-text abstention, unsupported Spanish, an uncertain English/Somali sentence and a live Kivy Somali-to-English auto-detection run. This is smoke evidence, not a general accuracy claim or independent benchmark. Exact outputs and confidence values are in `LANGUAGE_DETECTION_EVIDENCE.json`.

The detector selection comes from its pinned local model, not an online API. The PyPI release describes its 139-language model, probability-normalized confidence and abstention support, and declares BSD-3-Clause; the bundled notice is `notices/py3langid-BSD-3-Clause.txt`.

- https://pypi.org/project/py3langid/0.4.0/
- https://github.com/adbar/py3langid
- https://aclanthology.org/P12-3005/
