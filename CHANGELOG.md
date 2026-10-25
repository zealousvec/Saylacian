# Version history

This source snapshot has no numbered application release, so unreleased work stays under **Unreleased** until a version is tagged.

## Unreleased

- Long offline passages now translate in sentence-sized sections when they exceed a model's input limit. Saylacian keeps the original spacing between sections and warns that context can change across them.
- Old Nubian Latin-to-script conversion now keeps unmapped letters visible, flags them, and retains alternate readings for the mapped parts of the text.
- Long ambiguous script readings now say when the app can show only some of the possible alternatives.
- Added an optional English-to-Somali model download. Saylacian checks its output and falls back to the standard Somali pack when a result looks incomplete or repetitive. The model is experimental and carries its own CC BY 4.0 terms.
- The pack screen now says the experimental Somali add-on needs the standard Somali / English pack for fallback.
- The pack manager enforces that dependency: install the standard pack first and remove the add-on before removing its fallback.
- Tightened the experimental Somali model's fallback for overlong and repeated-word output. On a 37-example TICO-19 sample, the guarded route scored higher than the standard pack, but took longer and still produced awkward Somali.
- Expanded the comparison to a reproducible 120-example TICO-19 sample. The optional route scored higher on this sample, took longer, and fell back on 47 inputs; Somali remains experimental and needs fluent-speaker review.
- Added an optional offline Somali detector. It helps identify some short Somali input; it does not improve translation quality.
- Reverse Osmanya conversion now shows alternate readings where `w`/`uu` or `y`/`ii` share a glyph.
- Unknown Borama and Kaddare private-use characters are now preserved and reported across all Unicode private-use ranges.
- Old Nubian reading now shows `ou` as an alternative for `ⳣ`, alongside the table's `w` reading.
- Added a guard that reduced repeated phrases in a Somali validation sample; see the [results and limits](docs/TRANSLATION_QUALITY.md).
- Added regression checks for Osmanya ambiguities and chart-based Borama, Kaddare, and Old Nubian table conversions.
