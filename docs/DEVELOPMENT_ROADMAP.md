# Saylacian development roadmap

This roadmap is ordered by correctness and evidence dependencies. Complexity describes relative engineering/research effort, not promised dates. Keep the approved interface and the Python/Kivy stack.

## Immediate correctness and release clarity

| Priority | Work | Complexity | Depends on / acceptance evidence |
|---|---|---:|---|
| P0 | Keep README, support matrix, website copy and capabilities aligned on Nubian: Old Nubian transliteration exists; modern Nubian varieties do not. | Small | Source review on 2026-10-24 found the user-facing claims aligned; repeat when route behavior changes. |
| P0 | Windows model-pack path normalization and strict test correction. | Small | Completed on public `main` at `c4f2f87270c22a05e772816ce98e57a99b871b18`; Windows CI run `40087020450` passed. |
| P0 | Correct public GitHub About description that says “non-profit” while project records say it is not a registered nonprofit. | Small | Repository admin action; no source code change. |
| P1 | Continue narrow cleanup of the 30 remaining repository-wide Ruff findings. | Small–medium | Five findings were removed in local clipboard/pack changes; changed modules pass targeted checks. Do not mass-fix or mix with behavior changes. |
| P1 | Add a manual integration workflow for manifest-pinned packs and real offline model smoke checks. | Medium | Implemented locally in `.github/workflows/offline-pack-integration.yml`; tested against French and Somali packs in an isolated temp store. Host run is pending owner-approved push; no weights are uploaded and routine CI remains unchanged. |

## Translation evaluation and Somali improvement

| Work | Complexity | Dependencies / completion evidence |
|---|---:|---|
| Establish a small, consented reference set by direction and domain with fluent Somali reviewers. | Large research | Provenance, consent, dialect/orthography labels, secure data handling, reviewer agreement. |
| Track model versions, source revisions, tokenizer/runtime, decoding settings, and exact evaluation command. | Medium | Reproducible manifests and benchmark reports. |
| Report automatic metrics as diagnostics, not a substitute for humans; include adequacy, omission, hallucination and terminology review. | Medium | Translation-quality methodology reviewed by language specialists. |
| Analyze known weak cases; compare openly licensed models on the same split. | Large | Candidate licences compatible with intended distribution, sufficient Somali evidence, reproducible tests. |
| Evaluate English↔Somali separately from Somali↔French pivot. | Medium | Direction-specific scores and error review; retain explicit pivot warning. |
| Improve language detection with short-text abstention and labeled test data. | Medium | Representative examples and false-positive/false-negative report. |

The first short-text pass is implemented locally: texts under 20 characters need at least 12 characters, three words, and 0.85 model confidence; longer texts retain the existing 20-character/0.70 gate. On 40 hand-authored prompts (10 each for English, French, Somali and unsupported languages), the new behavior accepted 17 versus 5 under the previous gate: 13 supported-language labels and 4 explicit unsupported-language results, with no false supported labels in this small sample. This is model-specific engineering evidence, not a representative accuracy estimate or Somali linguistic review. Keep thresholds conservative until a larger, provenance-labeled test set is reviewed.

**Acceptance rule:** a software test passing or a model returning text never upgrades a route’s linguistic status on its own. Publish evaluation method, sample limits, model identity, reviewer role, and known failure classes.

## Historical Somali scripts

| Work | Complexity | Dependencies / completion evidence |
|---|---:|---|
| Independently verify every Osmanya mapping and document reverse ambiguities. | Medium | Unicode references plus community/linguist review; property tests for round trips where mapping is reversible. |
| Double-transcribe Borama/Kaddare source charts and record disagreements. | Medium–large | Attribution and CC BY-SA compliance; reviewed table and provenance per entry. |
| Define word-level orthography only with credible language-community evidence. | Large research | Multiple examples and expert/community review; charts alone are insufficient. |
| Improve copy/paste interoperability while labeling PUA data honestly. | Medium | Windows/external-app tests; Saylacian Text v1 round trip; recipient-font caveats retained. |
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
- **Medium:** assess long-input and low-memory handling across model types; document limits and provide actionable errors.
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
