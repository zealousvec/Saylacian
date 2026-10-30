# Saylacian user guide

## Contents

- [Choose a mode](#choose-a-mode)
- [Choose a language or script](#choose-a-language-or-script)
- [Letter mappings and unmatched letters](#letter-mappings-and-unmatched-letters)
- [Copy Borama and Kaddare](#copy-borama-and-kaddare)
- [What other apps can display](#what-other-apps-can-display)
- [Troubleshoot copied writing](#troubleshoot-copied-writing)
- [Feature limits](#feature-limits)

## Choose a mode

The button beside the Saylacian title switches between **Transliterate** and **Translate**. The button stays in the same place in both modes.

- **Transliterate** changes how text is written. It does not translate the meaning. Use it for Somali script conversion and the limited Old Nubian character-reading route.
- **Translate** changes meaning between supported languages. Translation packs must be installed for offline use. Somali output has not had fluent-speaker review; check important translations before relying on them.

Long offline text is split at sentence or paragraph boundaries when needed. Context between the resulting sections may change. A single sentence beyond the model's input limit still needs to be shortened or split.

Changing mode does not change the positions of the language controls or text panels. Use the dropdowns to choose a route supported by the selected mode. The picker shows short names only; detailed coverage is in the [support matrix](SUPPORT_MATRIX.md).

## Choose a language or script

Use the left dropdown for the source and the right dropdown for the target. `[x]` marks the current choice. Search accepts the displayed name, such as `Somali`, `Latin reading`, or `Borama alphabet chart`.

For Old Nubian, choose **Old Nubian** and **Latin reading**, then use **Read** to open the reading reference. Where the cited table lists another Latin reading for a character, it appears below the main reading. For long ambiguous text, Saylacian may show only some alternatives and will say when the list is incomplete. In Latin-to-script conversion, letters absent from the table stay Latin and are flagged. This is limited character transliteration, not translation or a complete reading of every manuscript convention. Modern Nubian varieties are not implemented. See [Old Nubian scope](OLD_NUBIAN_SCOPE.md).

For Borama or Kaddare, choose a script route to convert chart-mapped letters. The mappings do not validate spelling or word-level use. Kaddare preserves case with separate uppercase and lowercase cursive font slots; Borama's current mapping does not preserve capitalization. Letters without a chart mapping stay in Latin and are reported. See [script interoperability](SOMALI_SCRIPT_INTEROPERABILITY.md).

For a side-by-side explanation of mapped and unmatched letters in Osmanya, Borama, Kaddare and Old Nubian, see [letter mappings and unmatched letters](SCRIPT_LETTER_GUIDE.md).

When reading Osmanya back into Latin, the shared glyphs produce a main reading plus alternatives: `𐒓` can be `w` or `uu`, and `𐒕` can be `y` or `ii`.

The guide identifies table entries and ambiguities, including why a Latin `v` remains unchanged in these current Somali mappings. It does not claim missing Latin letters are missing from a historical script.


## Copy Borama and Kaddare

When the active route uses Borama or Kaddare, the copy menu offers three choices:

| Choice | What goes to the clipboard | Best use |
|---|---|---|
| **Copy text** | A versioned **Saylacian Text v1** package. On Windows, the clipboard also carries RTF and HTML rich-text forms. | Paste into Saylacian to restore the exact script and letters. A compatible font is needed for editable glyphs in other rich-text apps. |
| **Copy image** | A PNG and Windows bitmap image, with a Latin-reading text alternative. | Share a visual copy when the recipient does not have a font. The image is not editable script text. |
| **Copy Latin** | Ordinary Somali Latin text. | Paste into general text boxes and apps. It is broadly readable, but it does not preserve the original script glyphs. |

The Saylacian Text package is ASCII text beginning with `SAYLACIAN-TEXT/1`. It records the script name, the original chart characters, a Latin reading, the mapping identifier, and a SHA-256 integrity value. Saylacian checks those fields when the package is pasted back. The format is a Saylacian interchange format; it is not a Unicode standard for Borama or Kaddare.

On Windows, rich-text-capable apps may choose the RTF or HTML clipboard form. Those forms identify the Saylacian chart font but do not embed that font. The glyphs may therefore look blank or different if the font is missing or the app ignores the format. Plain-text-only apps may display the ASCII package instead of script glyphs. External-app acceptance has not yet been verified on a disposable Windows VM, so do not assume every app selects the same format.

On other platforms, **Copy text** places the tagged package on the text clipboard; **Copy image** is currently Windows-only. **Copy Latin** remains the portable text option.

The mapping uses private-use Unicode code points. Those code points do not have a universal Borama/Kaddare meaning: another app needs the matching mapping and font to render editable glyphs. An untagged private-use string is not guessed as Borama or Kaddare. More detail and verification status: [script interoperability](SOMALI_SCRIPT_INTEROPERABILITY.md).

## What other apps can display

- **Somali Latin:** ordinary Unicode text; widely supported.
- **Osmanya:** assigned Unicode characters; visible glyphs still depend on the other app's font.
- **Borama and Kaddare:** this project's current mappings use private-use code points, so editable display requires compatible Saylacian chart-font support.
- **Copy image:** carries appearance, not editable letters.

## Troubleshoot copied writing

1. To preserve script through a Saylacian round trip, choose **Copy text** and paste the package into Saylacian.
2. To show the writing to someone without the font, choose **Copy image** on Windows.
3. To paste text into any ordinary text field, choose **Copy Latin**.
4. If another app displays empty boxes, it lacks a compatible chart font or did not accept the rich-text format. The app may not support Saylacian Text packages.

The Saylacian Text package preserves the glyph sequence and script label; it does not validate Borama/Kaddare spelling or provide a universally interoperable character encoding.

## Feature limits

Translation and transliteration are different features. Somali output has not had fluent-speaker review. Borama/Kaddare cover selected chart entries, and Old Nubian reading covers selected character-table entries; neither validates complete words or every historical convention. Modern Nubian varieties are unsupported. See the [support matrix](SUPPORT_MATRIX.md).
