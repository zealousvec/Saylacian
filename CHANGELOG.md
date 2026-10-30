# Version history

This repository has no numbered app release yet. Changes are listed under **Unreleased** until a version is tagged.

## Unreleased

- Borama conversion now accepts Somali macron vowels using existing chart labels.
- Osmanya conversion now accepts Somali macron vowels and writes the equivalent long-vowel letters.
- Clarified that Saylacian does not join Kaddare cursive forms; the note appears only when lowercase forms are used.

### Windows packaging

- Added a pinned PyInstaller build script and payload checks for the Windows app. The checks reject known model-weight files and catch local user paths in packaged text files.
- Added a local MSIX packaging path and archive validation. The package is unsigned and uses the supplied identity; it is a build artifact, not a Store-ready upload or installable release.
- Repeated clean-clone pack installation and offline app checks. Store certification, clean-VM testing, screen-reader testing and real external clipboard testing remain outstanding.

### Translation

- Short language detection now considers text from eight characters when it contains at least three words, with a 0.70 confidence threshold. Fixed samples recovered more short English, French and Somali detections. The lower threshold also produced three extra English labels on the Qor Somali sample and more single-language guesses on constructed three-word mixed snippets, so mixed input may be mislabeled.
- Offline English ↔ French multi-line input now runs in batches of up to 16 lines. Line breaks, blank lines and surrounding spaces are kept. Each line is translated on its own, so context between lines can be lost.
- Longer offline passages can be split at sentence or paragraph boundaries when they exceed a model's input limit. Meaning can shift at those boundaries.
- Somali translation now offers an optional English-to-Somali model with checks for visibly incomplete or unreadable output and fallback to the standard pack. Somali still needs fluent-speaker review; automatic scores do not establish fluency or accuracy. See [translation quality](docs/TRANSLATION_QUALITY.md).
- The optional AfriSLM route now rejects an unclosed internal-thinking marker instead of displaying it as translated text; the existing fallback selects another installed Somali model.
- Somali-to-English no longer sends an unsupported language tag to the model. A small FLORES-200 sample improved, but it does not replace human review.
- Somali detection was adjusted to reduce false Somali selections in the tested sample. The higher threshold also misses more Somali text; it is not a general accuracy guarantee.

### Writing systems and navigation

- Kaddare transliteration now uses the chart's separate uppercase and lowercase cursive forms and reads their case back. Lowercase glyphs are not joined contextually. Older Saylacian Kaddare private-use text remains readable; Borama and Kaddare are still chart-limited, and their private-use characters still need a compatible font.
- Kaddare warns when titlecase or irregular mixed-case input inside a multi-letter chart entry cannot be preserved by its single upper/lower chart forms.
- Kaddare transliteration now converts macron vowels to the doubled-letter form described in the chart notes; reverse reading returns doubled Latin vowels.
- Osmanya transliteration now converts Unicode digits `0`–`9` to the matching Osmanya digits and back. Other numeral systems stay unchanged.
- Switching between **Translate** and **Transliterate** keeps a valid language choice for each mode. Longer status messages can scroll without moving the text panels.
- Osmanya reverse reading now shows alternatives where one letter can represent either a short or long vowel spelling.
- Long Osmanya readings prioritize local alternatives from the start of the text before combined readings when the displayed list is capped.
- Borama and Kaddare tables include source-cited chart labels and shared-vowel aliases. Coverage is still partial; unmapped letters are kept and reported.
- Old Nubian reading shows documented alternatives for selected letters and digraphs. It remains a limited character table and needs specialist review.
- Old Nubian's supralinear-stroke alternatives now place `i` before the preceding `l`, `n`, `r` or `j` when the stroke is over a following vowel, following the cited published example. Other contexts are preserved without an inferred insertion.
- Added an optional 1.56 GB AfriSLM 2B Somali / English pack. It is selected only when CPU and available-memory checks pass; otherwise Saylacian falls back to a smaller installed model or the standard pack. A matched HornMT sample scored higher than 0.8B in both directions but ran more slowly; the measured trade-off and limits are documented.
- Borama and Kaddare copy options explain which forms preserve the writing. Editable text uses private-use characters, so display outside Saylacian needs compatible mapping and fonts.

Saylacian is in alpha testing. Somali translation and historical-script features retain the limits above. Modern Nubian varieties are not supported. Android and iOS builds have not been tested. See the [support matrix](docs/SUPPORT_MATRIX.md) for current coverage.
