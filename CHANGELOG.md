# Version history

This source snapshot has no numbered application release, so unreleased work stays under **Unreleased** until a version is tagged.

## Unreleased

- Added an optional offline Somali detector. It helps identify some short Somali input; it does not improve translation quality.
- Reverse Osmanya conversion now shows alternate readings where `w`/`uu` or `y`/`ii` share a glyph.
- Old Nubian reading now shows `ou` as an alternative for `ⳣ`, alongside the table's `w` reading.
- Added a guard that reduced repeated phrases in a Somali validation sample; see the [results and limits](docs/TRANSLATION_QUALITY.md).
- Added regression checks for Osmanya ambiguities and chart-based Borama, Kaddare, and Old Nubian table conversions.
