# Saylacian development roadmap

This roadmap is ordered by correctness and evidence dependencies. Complexity describes relative engineering/research effort, not promised dates. Keep the approved interface and the Python/Kivy stack.

## Immediate correctness and release clarity

| Priority | Work | Complexity | Depends on / acceptance evidence |
|---|---|---:|---|
| P0 | Keep README, support matrix, website copy and capabilities aligned on Nubian: Old Nubian transliteration exists; modern Nubian varieties do not. | Small | Source review on 2026-10-24 found the user-facing claims aligned; repeat when route behavior changes. |
| P0 | Windows model-pack path normalization and strict test correction. | Small | Completed on public `main` at `c4f2f87270c22a05e772816ce98e57a99b871b18`; Windows CI run `40087020450` passed. |
| P0 | Correct public GitHub About description that says “non-profit” while project records say it is not a registered nonprofit. | Small | Repository admin action; no source code change. |
| P1 | Broad Ruff cleanup of remaining repository findings. | Small–medium | Current `ruff check .` is clean across the checkout; no outstanding Ruff findings remain at this checkpoint. |
| P1 | Add a manual integration workflow for manifest-pinned packs and real offline model smoke checks. | Medium | Implemented locally in `.github/workflows/offline-pack-integration.yml`; tested against French and Somali packs in an isolated temp store. Host run is pending owner-approved push; no weights are uploaded and routine CI remains unchanged. |

## Translation evaluation and Somali improvement

| Work | Complexity | Dependencies / completion evidence |
|---|---:|---|
| Establish a small, consented reference set by direction and domain with fluent Somali reviewers. | Large research | Provenance, consent, dialect/orthography labels, secure data handling, reviewer agreement. |
| Track model versions, source revisions, tokenizer/runtime, decoding settings, and exact evaluation command. | Medium | Reproducible manifests and benchmark reports. |
| Report automatic metrics as diagnostics, not a substitute for humans; include adequacy, omission, hallucination and terminology review. | Medium | Translation-quality methodology reviewed by language specialists. |
| Analyze known weak cases; compare openly licensed models on the same split. | Large | Candidate licences compatible with intended distribution, sufficient Somali evidence, reproducible tests. |
| Evaluate English↔Somali separately from Somali↔French pivot. | Medium | Direction-specific scores and error review; retain explicit pivot warning. |
| Improve language detection with short-text abstention and labeled test data. | Medium | Natural short examples with independently verified labels, clear reuse terms, and confusion/abstention report. Tatoeba row labels need validation; long-paragraph corpora cannot prove phrase-level behavior. |

Initial short-text policy accepted inputs under 20 characters only with at least 12 characters, three words and 0.85 confidence. A 40-prompt hand-authored probe showed 17 expected accepted/unsupported outcomes versus 5 under the prior gate; this was only a smoke sample.

A reproducible evaluator pins 15 Tatoeba per-language archives by SHA-256 and stores only aggregate results. It filters stripped 12–19 code-point, three-word rows; 403,820 eligible items remain across English, French, Somali and 12 unsupported languages. At 0.80 it returned 562 supported-language source-label matches (456 development, 106 deterministic holdout), with six source-label disagreements in development and none in holdout. At 0.85 it returned 432 matches (346/86) and four development disagreements (none in holdout). Spot checks found Tatoeba language tags that conflict with sentence text, so these are label matches/disagreements, not accuracy or false-positive measurements. The split is exploratory and not preregistered; the 43 Somali examples do not validate Somali language quality. The 0.80 threshold remains unchanged pending stronger evidence at this historical checkpoint; the Qor/MASSIVE comparison below later lowered the current cutoff to 0.75. WiLI-2018 has no native short rows within the 12–19-character gate; see its [Zenodo record](https://zenodo.org/records/841984). Tatoeba labels conflict with some texts. A stronger candidate is Mozilla’s [Common Voice Text Language Identification dataset](https://mozilladatacollective.com/datasets/cmj8ddapc02c8mb07l6wyr882), listed as CC0-1.0 and intended for text LID, with official test split; its description says it contains 19 million sentences. The current archive is 950.41 MB and Common Voice data is distributed exclusively through Mozilla Data Collective; no authorized archive/API credentials are available in this session. Its locale label remains source metadata, not expert adjudication of each phrase. The local aggregate-only evaluator is `tools/evaluate_common_voice_lid.py`; after obtaining the official archive through MDC, run `python tools/evaluate_common_voice_lid.py --data <path-to-mcv_text_lid.tsv>`. The script hashes the archive, evaluates only the test split, caps a stable sample at 500 rows per language, and never prints sentence text. Do not mirror or commit the dataset. A second candidate is SomaliWeb v1’s 200-row LID test set (40 rows each for English, Somali, Arabic, French and Swahili), manually annotated by one Somali speaker. The paper says it spans clean/short/noisy/code-switched text, but its benchmark script loads `../language-id-practice/data/multilingual_samples.csv`; that CSV is not in the corpus repository. Its own licence and actual short-row distribution need verification before use; do not truncate long text. See the [paper](https://arxiv.org/abs/2605.18232) and [benchmark source](https://github.com/khaledyusuf44/somali-corpus). No actual Common Voice score exists yet. Lingua 2.2.0 was not added solely for detection: the official [PyPI Windows CPython 3.12 wheel listing](https://pypi.org/project/lingua-language-detector/2.2.0/#files) is about 170 MB.

The initial five-language probe used Tatoeba `_CC0` English/French/German/Spanish exports and Somali standard data under CC BY 2.0 France. The expanded run uses CC0 English/French and standard CC BY 2.0 France exports for the other languages. Tatoeba's official [downloads page](https://tatoeba.org/en/downloads) states the corpus terms and identifies a CC0 subset; see also its [attribution FAQ](https://en.wiki.tatoeba.org/articles/show/faq). No sentence text is included in Saylacian. English/French use CC0 exports; the remaining exports use CC BY 2.0 France, recorded per language by the evaluator. The script classifies each row once, sweeps 0.80–0.90 and reports aggregates only. No corpus sentence text is bundled. None of this changes Somali translation-quality status or replaces fluent-speaker review.

### Somali short-input detector sample

Evaluated the public [Qor Af-Soomaali corpus](https://huggingface.co/datasets/unkadlabs/qor-af-soomaali) at immutable revision `5234876e5019cc4b1c79096c9f046fe2f8113b1e`. The sentence export uses CC BY-SA 4.0, and each row is marked verified; the source notes that longer passages were sometimes reviewed at passage level. The evaluator checks SHA-256 `f53ec99fbbd620ac65412d0c26c62a80faa534b9a939e95a0da6c53d5b38c60c`, evaluates the native short-input gate and reports aggregate counts only. Of 3,629 rows, 67 native rows meet Saylacian’s 12–19-code-point / three-word gate. At the earlier 0.80 threshold, 30/67 were detected as Somali and 37/67 abstained. At 0.70, 37/67 were detected as Somali, 29/67 abstained and one was classified as another language. These are Somali-only recall-like detection shares—not precision, overall accuracy, or translation quality. This earlier Qor-only checkpoint did not establish the precision tradeoff; the current 0.75 evaluation is recorded below.

The Qor export is not bundled. `tools/evaluate_qor_somali_lid.py` accepts the pinned `data/sentences.jsonl` file. SomaliWeb v1’s paper describes a 200-row LID test, but its benchmark script references a CSV in a sibling project; the cited repository and raw CSV path currently return 404. Its reuse terms and native short-row eligibility remain unresolved.

### MASSIVE 1.1 short-input locale check and current threshold

The official [AmazonScience/MASSIVE dataset card](https://huggingface.co/datasets/AmazonScience/massive) reports CC BY 4.0; the 1.1 archive and included SLURP notice were checked directly. The archive is pinned in `tools/evaluate_massive_lid.py` by SHA-256 and is never bundled. Across 154,648 test rows, 12,729 satisfy the app's 12–19-code-point/three-word gate. The evaluator picks up to 500 deterministic rows per locale; this sample contained 11,386 phrases across 52 locales. At 0.75 confidence, 142/451 English/French samples matched their source locale; zero of 10,935 other-locale samples reached an app-supported label. At 0.80, 116/451 matched. At 0.70, two unsupported-locale rows reached a supported label. The raw official archive has no per-row language-identification judgements, so these are locale-agreement counts, not adjudicated accuracy. MASSIVE has no Somali data.

At 0.75, the pinned Qor set detected 33/67 verified Somali short rows, abstaining on 34 with no other-language prediction. At 0.80, it detected 30 and abstained on 37; at 0.70 it detected 37 but produced one other-language prediction. The live short-input confidence cutoff is now 0.75, with a tested 0.75/0.749 boundary. This raises observed capture in both corpora without a wrong supported route in these samples. The evidence is not independently reviewed for every label, does not include Somali negatives, and does not establish broad language-detection accuracy or translation quality. Keep the accuracy task BLOCKED until consented, per-row short-text adjudication across Somali, English/French and unsupported languages is available. The resolution action is to obtain appropriate reviewer approval and clear data-use terms; Common Voice and CommonLID are only additional locale-labelled sources, not a substitute for that review.

**Acceptance rule:** a software test passing or a model returning text never upgrades a route’s linguistic status on its own. Publish evaluation method, sample limits, model identity, reviewer role, and known failure classes.

## Historical Somali scripts

| Work | Complexity | Dependencies / completion evidence |
|---|---:|---|
| Independently verify every Osmanya mapping and document reverse ambiguities. | Medium | Unicode references plus community/linguist review; property tests for round trips where mapping is reversible. |
| Double-transcribe Borama/Kaddare source charts and record disagreements. | Medium–large | Attribution and CC BY-SA compliance; reviewed table and provenance per entry. |
| Define word-level orthography only with credible language-community evidence. | Large research | Multiple examples and expert/community review; charts alone are insufficient. |
| Improve copy/paste interoperability while labeling PUA data honestly. | Medium | Saylacian Text v1 round trip and payload construction are tested. The Windows publisher now uses the native Kivy window handle; real Windows/external-app tests remain required in a disposable VM, with recipient-font caveats retained. |
| Test rendering and conversion separately across fonts/platforms. | Medium | Glyph coverage and screenshot fixtures do not substitute for script correctness. |

## Nubian language/script research

| Work | Complexity | Dependencies / acceptance evidence |
|---|---:|---|
| Keep Old Nubian separate from modern Nubian varieties in selector, docs and research. | Small | Consistent route names and user-facing scope. |
| Review Old Nubian table and reverse alternatives with a specialist; clarify manuscript and romanization conventions. | Large research | Cited source version, independent transcription, documented ambiguous cases. |
| Select one modern variety (for example Nobiin or Dongolawi) before implementation. | Large research | Community/linguist partners, chosen dialect and orthography, licensed texts. |
| Build a transliterator only after collecting an authoritative grapheme/orthography specification. | Large | Tests backed by source material and reviewer sign-off. |
| Consider meaning translation only if a lawful, representative parallel corpus/model exists. | Very large research | Data rights, evaluation set, fluent reviewers, model/runtime licensing and practical resource plan. |

Do not create a generic “Nubian” converter from the presence of a Coptic font or an Old Nubian chart.

## Routing, user experience, and accessibility

- **Quick win, small:** clarify per-route status and warnings using existing UI structures; retain the approved design.
- **Medium:** test keyboard navigation, focus order, screen-reader labels, contrast, scaling, and small-window behavior. Kivy tests do not guarantee accessibility.
- **Medium:** ensure missing-pack flows explain estimated download/storage and an offline error has a clear recovery action.
- **Medium:** manage model memory and input limits across offline routes. Inputs above 400 tokenizer tokens fail with a split-passage instruction; `load_model` now retains at most three engines to balance memory and route reuse; successful offline-pack removal and installation clear cached engines, while failed operations preserve them. On this Windows host, loading all four static model routes left 422 MiB resident with the old four-entry cache and 318 MiB with the three-entry cap; clearing the cache returned to 34 MiB. Results are host-specific and do not establish Android or low-RAM-device behavior.
- **Large:** any new source-target route must be capability-gated, tested offline/online as applicable, and paired with quality evidence.

## Packaging and platforms

1. **Windows source setup, small:** maintain locked, reproducible instructions; validate clean environments and Kivy startup.
2. **Windows binary, medium–large:** build from a clean clone; audit every bundled DLL/font/license; test on clean Windows hosts; investigate signing/Smart App Control distribution without weakening user security.
3. **Android, large:** select and validate Python/native runtime, model compatibility and storage/download UX, then build and test on physical devices. Kivy cross-platform support is not proof this app works there.
4. **iOS, very large:** establish Apple toolchain/signing, compatible inference runtime and device tests. No verified iOS release exists.
5. **Store releases, large:** privacy disclosures, permissions, accessibility, crash/error handling, asset licences and model download policies need per-platform review.

## Website and community

- Keep the Flask site local until it has production hosting, TLS, authentication/abuse controls where needed, privacy policy, monitoring and load tests.
- Never embed a shared server token in public clients. Self-hosted capacity must be described as finite.
- Make contribution tasks evidence-oriented: code changes require tests; language changes require provenance and reviewer notes.
- Invite reviewers with clear consent and attribution terms; avoid publishing sensitive user text or unlicensed corpora.
- Keep issues/bug reports free of credentials, private translation content and personal diagnostic logs.

## Quick wins versus research problems

**Quick wins:** correct stale Nubian copy, fix repository description, land/retest the local path fix after review, improve small error messages, add tests for deterministic code behavior, and make current warnings consistent.

**Research problems:** Somali translation quality, accepted Borama/Kaddare spelling, Old Nubian convention choices, modern Nubian orthographies and translation corpora, human evaluation design, and validated mobile inference. These require external language evidence and/or representative data, not merely more Python code.


**Current queue (2026-10-25, rechecked after local commit `8b748ab1fca48408355759545079f3c7b5a50c6e`):** ACTIVE: no implementation item remains after the verified benchmark-output safeguards, UI wording cleanup, and live UI acceptance; keep the goal unfinished and select the next independent evidence-backed task when resources arrive. BLOCKED: independent LID accuracy needs reviewer-adjudicated short text with reuse terms; Somali quality needs consented fluent review; Old Nubian expansion needs written DBMNT rights and specialist review; screen-reader behavior needs manual Narrator/NVDA observation; real clipboard delivery needs a disposable VM; hosted workflow requires push approval; Windows binary release needs code-signing/package trust and authorized clean-host runtime testing. FBO-based isolated Kivy captures at all six acceptance viewports are valid and visually reviewed; physical-device and broader platform review remain unverified. READY: none identified after current code and roadmap review. See `docs/IMPLEMENTATION_PROGRESS.md` for exact unblock actions; do not add speculative tasks.

## Current queue — 2026-10-30

**ACTIVE:** prepare the final portable ZIP from the committed `0.1.0a1` source and inspect the manifest and GitHub Actions artifact workflow. Source commit `bab24a31b699c53601c6bfe780ede6bb7f43fbcb` was tested in a fresh local clone and fresh venv: 185 passed, 11 skipped, 191 subtests; Kivy self-test passed. French and Somali packs downloaded and passed offline smoke inference in both directions with network blocked during inference.

**BLOCKED:** clean-host EXE launch and install require an isolated Windows host; real clipboard interchange and Narrator/NVDA require a disposable VM and screen-reader review; stronger Somali claims require a fluent reviewer; Old Nubian expansion requires specialist review and evidence. Do not bypass Windows security or use the owner's clipboard.

**READY:** rebuild the final ZIP from the final local commit, check payload licensing and hashes, run local source checks, and prepare the exact future CI run command. Windows CI, public upload and GitHub release wait for push approval. No Store or mobile work in this source-release pass.
