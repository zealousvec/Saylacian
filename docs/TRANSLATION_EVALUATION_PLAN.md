# Translation evaluation plan

## Current baseline

English↔French is smoke-tested with installed offline packs. English↔Somali uses multilingual OPUS models and remains experimental; Somali↔French pivots through English and may compound errors. Model metadata and aggregate benchmark results live in `SOMALI_TRANSLATION_EVIDENCE.json`, `SOMALI_TRANSLATION_QUALITY.md`, `TRANSLATION_FEASIBILITY.md`, and the model manifests. Raw generated predictions stay in local app data and are not checked into source. These records are software/model smoke evidence, not fluent-speaker validation.

## Evaluation data

- Keep English→Somali, Somali→English, French→Somali and Somali→French as separate routes. Report pivoted directions separately from direct models.
- Use appropriately licensed, documented parallel data with stable version/hash and exact source revision. Do not add restricted or accepted-terms-only datasets to the repository.
- Reserve a held-out set that does not overlap training data where this can be checked. Record domain and limitations; avoid using one tiny health-domain sample as general Somali quality evidence.
- Maintain source, reference and model identifiers outside public logs containing private user text.

## Reviewer worksheet

For each pair, ask fluent reviewers to score adequacy and fluency separately, mark omitted or invented meaning, negation, names/numbers, tense/aspect, morphology, idioms, register and harmful ambiguity. Record disagreement and reviewer qualifications without collecting unnecessary personal data. Obtain owner approval before contacting or recruiting reviewers.

## Automated checks

Run fixed examples against pinned model/runtime revisions, with deterministic preprocessing and output normalization. Track chrF/BLEU only as secondary indicators, plus exact failure categories. Compare the same test set across direct, pivoted and candidate routes. Never treat automatic scores, synthetic candidates or guardrails as fluent validation.

## Acceptance before quality claims

Publish per-route sample size, domain, model/version, test revision and human-review status. Somali features remain labelled experimental until reviewers confirm the intended meaning across an appropriately broad set. Preserve all test input/output artifacts needed for reproducibility while redacting private user content.
