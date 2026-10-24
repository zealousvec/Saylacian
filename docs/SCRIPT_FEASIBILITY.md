# Script feasibility and implementation

This document distinguishes language, script, transliteration, translation, encoding and rendering. None of the script converters translates meaning.

## Working conversions

### Somali Latin ↔ Osmanya

Somali is the language; Latin and Osmanya are writing systems. Saylacian maps Somali Latin digraphs and letters to Unicode Osmanya U+10480–U+1049D and back. Unicode documents 22 consonants and eight vowels, but `w`/`uu` and `y`/`ii` share letters. Reverse conversion therefore warns about lost vowel/semivowel distinction. Capitalization is not encoded. Punctuation and whitespace pass through. This remains **experimental** because the community has not reviewed the whole table. The bundled Noto Sans Osmanya font is OFL 1.1; Unicode characters are portable, although recipient font support varies.

Source: [Unicode Core Specification, Osmanya](https://unicode.org/versions/Unicode17.0.0/core-spec/chapter-19/).

### Old Nubian Coptic script → scholarly Latin; reverse is experimental

Old Nubian is a historical language, not a name for modern Nubian varieties. This route transliterates the encoded Coptic/Greek-derived Old Nubian letters; it does not translate Old Nubian. The table is grounded in the published comparative transliteration table linked below. It covers its explicitly listed ordinary letters and Old Nubian additions `ⳟ`, `ⳡ`, `ⳣ`, and `ⳝ`; the corresponding outputs follow that table (`ng`, `ny`, `w`, `j`). The table notes that some letters have other conventions under ALA-LC. Unlisted Coptic letters are preserved and warned about, not guessed. Reverse parsing is longest-match and experimental because Latin digraphs may also occur across letter boundaries and romanization conventions differ.

Noto Sans Coptic is bundled under SIL OFL 1.1. Its cmap was checked for all characters used by the converter, including U+2CDF, U+2CE1, U+2CE3, U+2CDD and Greek/Coptic letters. Copy/paste emits standard Unicode, but this is a script transliteration and glyph appearance depends on fonts and platform shaping.

Sources: [Old Nubian/Coptic transliteration table](https://dbmnt.uw.edu.pl/static/pdf/transliteration_tables.pdf), [Noto Coptic source and license](https://github.com/notofonts/coptic), [Noto Coptic glyph sample](https://notofonts.github.io/coptic/).

## Research targets; not enabled as converters

### Borama / Gadabuursi

The app includes a partial converter and font derived from Jugydmort's CC BY-SA 4.0 chart. Borama is a historical Somali script, not a separate language, and has no assigned Unicode block. The chart supports only chart-label-level correspondences; word orthography remains unreviewed. App output uses private-use code points and renders in Saylacian's bundled font. Pasting Saylacian-generated glyphs back into the app detects the private-use mapping, loads its font and converts back to Somali Latin. Other applications may show empty boxes unless they have the same font; unrelated private-use encodings cannot be recognized from clipboard text alone because the clipboard omits font metadata. The separately licensed 1961 report is not copied or derived here.

Sources: [Tosco, 2015](https://www.maurotosco.net/ewExternalFiles/TOSCO_2015_Somali_Previous_Scripts.pdf), [Unicode African scripts update](https://www.unicode.org/L2/L2023/23203-update-african-scripts.pdf), [CC BY-SA Borama chart](https://commons.wikimedia.org/wiki/File:Borama_Alphabet_Chart.jpg), [1961 report and licence record](https://arcadia.sba.uniroma3.it/handle/2307/2620?mode=full).

### Kaddare

The app includes a partial converter and font derived from Jugydmort's CC BY-SA 4.0 chart. The chart lists two glyph forms per label but does not establish which form to use in words. Kaddare is a Somali script, not a separate language. Output uses nonstandard private-use code points; paste-back inside Saylacian auto-selects the bundled font and reverses the chart-label mapping. Paste from unrelated private-use fonts cannot be interpreted because clipboard text carries no font metadata. Independent transcription checks and fluent review remain needed.

Sources: [Tosco, 2015](https://www.maurotosco.net/ewExternalFiles/TOSCO_2015_Somali_Previous_Scripts.pdf), [1961 report](https://arcadia.sba.uniroma3.it/handle/2307/2620?mode=full), [CC BY-SA Kaddare chart](https://commons.wikimedia.org/wiki/File:Kaddare_Alphabet_Chart.jpg), [Ian James's research notes](https://skyknowledge.com/kaddare.htm).

### Modern Nubian varieties

The selector's `Nobiin`, `Kenzi / Mattokki`, `Dongolawi / Andaandi`, `Midob`, `Birgid`, `Dilling`, `Karko`, `Wali`, and `Kadaru` entries are distinct research targets, not one generic Nubian language or script. Modern Nobiin uses documented Latin orthographies (including agii); other Nubian communities may use Latin, Arabic, or Coptic-derived writing with variety-specific conventions. A Coptic font or Old Nubian scholarly table does not establish those modern orthographies. These entries remain unavailable until a specific language, writing convention, and licensed/reviewed mapping or translation model are identified.

Sources: [Nobiin orthography study](https://www.lddjournal.org/article/1214/galley/2458/download/), [Starostin, “Restoring Nile-Nubian”](https://escholarship.org/content/qt6663f1nt/qt6663f1nt.pdf?t=qozj86) (classification includes Kenuzi–Dongolawi, Nobiin, Hill Nubian varieties, Birgid and Midob), [Glottolog Kenuzi-Dongola split record](https://glottolog.org/resource/languoid/id/kenu1236), [WALS Andaandi/Dongolese](https://wals.info/languoid/lect/wals_code_nbd), [Coptic script usages](https://scriptsource.org/cms/scripts/page.php?item_id=script_detail&key=Copt&sort_writing_system_entries_gen=wrSys_displayCode).

## Rendering test result

`NotoSansCoptic-Regular.ttf` coverage is asserted in `tests/test_script_info.py`. A live Kivy route test uses the font in the input field, checks script detection and the local conversion result; generated historical screenshots and probe captures are retained locally but omitted from the source release. This verifies current-font rendering, not every manuscript's palaeographic form.
