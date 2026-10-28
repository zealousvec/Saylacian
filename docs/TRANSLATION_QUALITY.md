# Somali translation quality

Somali translation is available in alpha testing, but it has not been reviewed by fluent Somali speakers. Check important translations before relying on them.

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
