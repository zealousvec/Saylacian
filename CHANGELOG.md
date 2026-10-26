# Version history

This is a source snapshot, not a numbered app release. Changes stay under **Unreleased** until a version is tagged.

## Unreleased

### Translation

- Long offline passages can be translated in sentence-sized sections instead of failing at the model's input limit. Meaning can shift where one section ends and the next begins.
- An optional English-to-Somali model is available as a separate download. Saylacian checks its output and uses the standard Somali pack when a result appears incomplete or repetitive. Somali still needs fluent-speaker review; see the [quality notes](docs/TRANSLATION_QUALITY.md).
- The optional Somali detection pack can help identify Somali input. It does not improve translation quality.
- Raised the optional Somali detector's confidence threshold after a reproducible check found one false Somali prediction at 0.90. At 0.98, it identified 38 of 67 short Qor examples, compared with 33 from the original detector, with no Somali predictions in 11,386 sampled non-Somali MASSIVE texts. The threshold trades some Somali recall for fewer unsupported language selections; the sample does not establish general accuracy.
- When the optional Somali model falls back, the warning now names the checked issue, such as copied text, an unreadable token, excessive length or repeated output.
- The translation notes now include a FLORES-200 baseline. Earlier TICO-19 scores are marked unreliable after a source/reference audit found mismatched Somali rows in both dev and test samples.
- Fixed Somali-to-English input: the app no longer prepends an unknown Somali language tag to the many-to-English model. A 120-pair FLORES check improved BLEU from 9.728 to 10.598 and chrF++ from 32.954 to 33.460; see the [translation quality notes](docs/TRANSLATION_QUALITY.md) for the method and limitations.
- On a 120-pair FLORES sample, the optional English-to-Somali model with standard-pack fallback scored 10.755 BLEU / 40.069 chrF++, compared with 5.353 / 29.882 for the standard pack. It fell back on 14 unreadable outputs; the guard remains enabled. Somali still needs fluent-speaker review.
- The optional Somali model now falls back when it adds a trailing ellipsis to a complete source sentence. This caught 11 likely unfinished outputs in a second 120-pair sample; automatic scores dipped slightly after fallback, so this is an output-completeness safeguard rather than an accuracy claim.

### Script reading and writing

- Old Nubian Latin-to-script conversion keeps letters outside the table and warns when they are not mapped. Ambiguous Latin spellings can show more than one reading; long lists say when some alternatives are hidden.
- Old Nubian `ⳣ` now shows both table readings, `w` and `ou`. The combining macron used as a supralinear stroke now has an `i`-based alternative reading; other marks stay in the text and are not interpreted.
- Old Nubian `ⲧⲗ̄ⲗⲛ̄` now offers `tillin` as an alternative to the mark-preserving `tl̄ln̄`, following a published scholarly convention. The guide explains the limits and source.
- Osmanya reverse conversion shows alternatives for the shared `w`/`uu` and `y`/`ii` letters. The original spelling cannot always be recovered.
- Borama and Kaddare chart glyphs outside the known mapping are kept and flagged. Their private-use characters need Saylacian's matching font and mapping to display as editable text in another app.
- Repeated unmapped Borama or Kaddare letters and glyphs are listed once in the warning; the input text is preserved.

### Language packs and app checks

- The optional Somali model pack requires the standard Somali/English pack for fallback. Install the standard pack first and remove the optional pack before removing its fallback.
- Regression checks cover mapped and unmapped letters, ambiguous readings, long input and model fallback behavior.

No Android or iOS build has been verified. Somali translation has not had fluent-speaker review. Borama and Kaddare cover chart-listed characters only; Old Nubian transliteration covers selected table entries and needs specialist review.
