# Version history

This repository has no numbered app release yet. Changes are listed under **Unreleased** until a version is tagged.

## Unreleased

### Translation

- Offline English ↔ French multi-line input now runs in batches of up to 16 lines. Line breaks, blank lines and surrounding spaces are kept. Each line is translated on its own, so context between lines can be lost.
- Longer offline passages can be split at sentence or paragraph boundaries when they exceed a model's input limit. Meaning can shift at those boundaries.
- Somali translation now offers an optional English-to-Somali model with checks for visibly incomplete or unreadable output and fallback to the standard pack. Somali still needs fluent-speaker review; automatic scores do not establish fluency or accuracy. See [translation quality](docs/TRANSLATION_QUALITY.md).
- Somali-to-English no longer sends an unsupported language tag to the model. A small FLORES-200 sample improved, but it does not replace human review.
- Somali detection was adjusted to reduce false Somali selections in the tested sample. The higher threshold also misses more Somali text; it is not a general accuracy guarantee.

### Writing systems and navigation

- Switching between **Translate** and **Transliterate** keeps a valid language choice for each mode. Longer status messages can scroll without moving the text panels.
- Osmanya reverse reading now shows alternatives where one letter can represent either a short or long vowel spelling.
- Borama and Kaddare tables include source-cited chart labels and shared-vowel aliases. Coverage is still partial; unmapped letters are kept and reported.
- Old Nubian reading shows documented alternatives for selected letters and digraphs. It remains a limited character table and needs specialist review.
- Borama and Kaddare copy options explain which forms preserve the writing. Editable text uses private-use characters, so display outside Saylacian needs compatible mapping and fonts.

Saylacian is in alpha testing. Somali translation and historical-script features retain the limits above. Modern Nubian varieties are not supported. Android and iOS builds have not been tested. See the [support matrix](docs/SUPPORT_MATRIX.md) for current coverage.
