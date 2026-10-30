# Saylacian user guide

## Contents

- [Choose a mode](#choose-a-mode)
- [Install an optional Somali model](#install-an-optional-somali-model)
- [Choose a language or script](#choose-a-language-or-script)
- [Letter mappings and unmatched letters](#letter-mappings-and-unmatched-letters)
- [Copy Borama and Kaddare](#copy-borama-and-kaddare)
- [What other apps can display](#what-other-apps-can-display)
- [Troubleshoot copied writing](#troubleshoot-copied-writing)
- [Feature limits](#feature-limits)

## Choose a mode

The button beside the Saylacian title switches between **Transliterate** and **Translate**. The button stays in the same place in both modes.

- **Transliterate** changes how text is written. It does not translate the meaning. Use it for Somali script conversion and the limited Old Nubian character-reading route.
- **Translate** changes meaning between supported languages. Translation packs must be installed for offline use. Somali routes are in alpha testing and need fluent-speaker review.

Changing mode does not change the positions of the language controls or text panels. Use the dropdowns to choose a route supported by the selected mode. The picker shows short names only; detailed coverage is in the [support matrix](SUPPORT_MATRIX.md).

Saylacian saves the latest input, output, mode and language pair in your per-user application data folder and restores them when you reopen the app. The saved session is local to your Windows account. To remove it, close Saylacian and delete `last-session-v1.json` from the Saylacian application-data folder.

## Install an optional Somali model

Open **Offline language packs** and download **Somali model (AfriSLM 0.8B)** to add the 641 MiB model. For Somali→English, the 2B pack is about 1.45 GiB and the 4B pack is about 2.86 GiB. The 4B model scored higher on one fresh automatic test sample but used about 5 GB of working memory on a 32 GB Windows computer and ran more slowly on CPU. These packs are separate from the standard Somali / English pack. Install the optional CPU runtime from the project folder with `python -m pip install -r requirements-afrislm.txt`, then restart Saylacian. The 0.8B pack remains the English→Somali choice. For Somali→English, Saylacian tries installed packs in order: 4B, 2B, then 0.8B; if a model cannot run, it falls back to the next installed model, then the standard Somali pack if available. Remove a pack from the same screen to reclaim storage.

On a 60-pair FLORES-200 devtest sample, 0.8B scored higher on English→Somali and 2B scored higher on Somali→English against both the 0.8B and standard routes. This small automatic comparison has not had fluent-speaker review and does not prove general quality. Somali routes remain in alpha testing. Model weights are declared Apache-2.0; the training dataset is CC-BY-NC-4.0 and is not included in the download. See [translation evidence and limitations](TRANSLATION_FEASIBILITY.md).

## Choose a language or script

Use the left dropdown for the source and the right dropdown for the target. `[x]` marks the current choice. Search accepts the displayed name, such as `Somali`, `Latin reading`, or `Borama alphabet chart`.

For Old Nubian, choose **Old Nubian** and **Latin reading**, then use **Read** to open the reading reference. This is limited character transliteration, not translation or a complete reading of every manuscript convention. Modern Nubian varieties are not implemented. See [Old Nubian reading scope](OLD_NUBIAN_READER_PLAN.md).

For Borama or Kaddare, choose a script route to convert the available chart-mapped letters. The mappings cover selected chart entries; spelling and word-level use have not been reviewed. Capitalization is lost. Letters without a chart mapping stay in Latin and are reported; the Borama chart has no `q` entry. The Kaddare chart shows two forms per label; conversion uses one glyph and cannot choose a word-level form. See [script interoperability](SOMALI_SCRIPT_INTEROPERABILITY.md).

For a side-by-side explanation of mapped and unmatched letters in Osmanya, Borama, Kaddare and Old Nubian, see [letter mappings and unmatched letters](SCRIPT_LETTER_GUIDE.md).

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

Translation and transliteration are different features. Somali routes are in alpha testing. Borama/Kaddare coverage follows selected chart entries. Old Nubian uses a limited, attributed character table; it is not meaning translation or complete manuscript coverage, and specialist review remains open. Modern Nubian varieties are unsupported. See the [support matrix](SUPPORT_MATRIX.md) and [project status](PROJECT_STATUS.md).

Offline translation accepts up to 4,000 characters. If a passage exceeds a model's token window, Saylacian splits it at whitespace and joins the translated segments; context can change at those joins. A single unbroken segment that exceeds the model window must be shortened manually.
