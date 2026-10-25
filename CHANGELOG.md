# Version history

This is an experimental-alpha source snapshot, not a numbered app release. Changes stay under **Unreleased** until a version is tagged.

## Unreleased

### Translation

- Long offline passages can be translated in sentence-sized sections instead of failing at the model's input limit. Meaning can shift where one section ends and the next begins.
- An optional English-to-Somali model is available as a separate download. Saylacian checks its output and uses the standard Somali pack when a result appears incomplete or repetitive. On the 120-example TICO-19 sample, the optional route scored higher than the standard pack, but it was slower and fell back on 47 inputs. Somali still needs fluent-speaker review; the [quality notes](docs/TRANSLATION_QUALITY.md) explain the test and its limits.
- The optional Somali detection pack can help identify Somali input. It does not improve translation quality.

### Script reading and writing

- Old Nubian Latin-to-script conversion keeps letters outside the table and warns when they are not mapped. Ambiguous Latin spellings can show more than one reading; long lists say when some alternatives are hidden.
- Old Nubian `ⳣ` now shows both table readings, `w` and `ou`. Combining marks remain in the text, with a warning that Saylacian does not interpret their reading or placement.
- Osmanya reverse conversion shows alternatives for the shared `w`/`uu` and `y`/`ii` letters. The original spelling cannot always be recovered.
- Borama and Kaddare chart glyphs outside the known mapping are kept and flagged. Their private-use characters need Saylacian's matching font and mapping to display as editable text in another app.

### Language packs and app checks

- The optional Somali model pack requires the standard Somali/English pack for fallback. Install the standard pack first and remove the optional pack before removing its fallback.
- Regression checks cover mapped and unmapped letters, ambiguous readings, long input and model fallback behavior.

No Android or iOS build has been verified. Somali translation and the partial historical-script mappings remain experimental.
