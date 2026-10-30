# Script letter mapping guide

This page describes the mappings currently present in Saylacian's source tables. A listed pair means the app has a character-level conversion entry; it is not a claim that the scripts are historically equivalent or that the resulting spelling has been linguistically reviewed. Letters outside a table are preserved as typed and may be reported as unmapped. Unknown Borama and Kaddare private-use glyphs are also preserved and flagged throughout the Unicode private-use ranges.

## Osmanya

The app maps Somali Latin graphemes to assigned Unicode Osmanya characters. It has entries for `a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, q, r, s, t, u, w, x, y`, the digraphs `dh, kh, sh`, long-vowel tokens `aa, ee, ii, oo, uu`, and apostrophe. The matcher checks longer tokens first, so digraphs and long vowels are recognized before their first letters. Macron input `ā, ē, ī, ō, ū` is accepted as the equivalent long vowel and reads back with doubled Latin spelling. Somali spelling marks long vowels by doubling ([EUAA transliteration note](https://www.euaa.europa.eu/print/pdf/node/26484)); Unicode assigns distinct Osmanya `AA`, `EE` and `OO` letters, while `II` and `UU` share the `YA` and `WAW` characters ([Unicode 16, section 19.2](https://unicode.org/versions/Unicode16.0.0/core-spec/chapter-19/)).

There is no app mapping for `p`, `v` or `z`; these are not part of the Somali letter set represented by this table and remain Latin when present in borrowed or foreign words. This is a limitation of the app's Somali mapping, not a claim that Osmanya cannot represent every foreign sound. The table maps `w` and `uu` to the same Osmanya character, and `y` and `ii` to the same character. Reverse transliteration chooses `w` or `y` as the main reading and lists other possible readings in the app. For long text, the capped list prioritizes alternatives near the beginning before combined readings; the app warns when it omits other possibilities. The original spelling cannot always be recovered. Capitalization is not encoded.

The Unicode Standard describes Osmanya as having 22 consonants and 8 vowels, and specifies that long `uu` and `ii` use the same Waw and Ya letters as `w` and `y`. That is why the reverse readings are alternatives instead of a claim that the original spelling can be recovered. See [Unicode 16.0, chapter 19](https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-19/).

Saylacian also converts ASCII digits `0`–`9` to the Unicode Osmanya digits and back. These digits are distinct from the Latin digits and remain reversible; other numeral systems are preserved as typed. The code points are listed in the official [Unicode Osmanya chart](https://unicode.org/Public/18.0.0/charts/nameslist/10480/).

## Borama

The current table maps all 27 letter labels shown in the bundled Borama chart:

`a, e, i, ii, u, uu, oo, b, t, j, dh, g, h, kh, d, r, s, sh, c, f, q, k, l, m, n, w, y`

The chart has seven vowel labels and twenty consonant labels, including `q`. A previous record misread the chart's `LETTER Q` row as `o`; Saylacian now maps that chart glyph to `q`.

Saylacian also applies three source-cited aliases to existing glyphs: `aa` uses the `a` sign, `ee` uses the `e` sign, and `o` uses the `u` sign. Mauro Tosco's discussion of Lewis's Gadabuursi chart reports that vowel length is not distinguished for `/a/` and `/aa/` or `/e/` and `/ee/`, and that short `/o/` and `/u/` share a sign ([2015 proceedings, discussion of Table 16](https://www.maurotosco.net/ewExternalFiles/TOSCO_2015_Somali_Previous_Scripts.pdf)). These are aliases to the existing chart glyphs, not extra glyphs. When reading the glyph back, Saylacian uses the chart label as the main reading and shows the alias as an alternative; the original vowel distinction cannot be recovered. `x`, `p`, `v` and `z` remain unmapped and stay Latin. The app's glyphs use private-use code points: they need Saylacian's matching font/table, or use **Copy Latin** / **Copy image** when sharing outside the app. The [Writing Systems Technical Resources Borama page](https://writingsystems.info/scrlang/scripts/x-borama/) also describes the script inventory as twenty consonants and seven vowels. A chart label does not establish word-level spelling. Macron inputs `ā, ē, ī, ō, ū` are accepted as the corresponding doubled Somali long vowels and use existing Borama chart labels. `ā`/`ē` reuse the `a`/`e` signs, so length remains ambiguous; the other three use the chart labels `ii`, `oo` and `uu`. Somali long vowels are conventionally written doubled ([EUAA note](https://www.euaa.europa.eu/print/pdf/node/26484)); no new chart glyphs are assigned.

## Kaddare

The current chart-derived table contains:

`a, e, i, o, u, b, t, j, x, kh, d, r, s, sh, dh, c, g, f, q, k, l, m, n, w, h, y`

`p`, `v` and `z` have no entry in this table and remain Latin. The chart pairs uppercase forms with lowercase cursive forms; Saylacian emits distinct font slots for both. Single-letter entries and all-uppercase/all-lowercase multi-letter entries preserve case when read back. A single chart glyph has no separate titlecase form, so `Dh` reads back as `DH`; the app now warns when titlecase or irregular mixed case in a multi-letter entry cannot round-trip. Saylacian displays each lowercase form separately and does not reproduce connected cursive joining; the note appears only when lowercase forms are used. Existing Kaddare private-use slots remain readable as before. Ian James's chart notes that long vowels can be written by doubling the vowel or by adding a horizontal bar; he also notes that the forms were based on two poorly photographed examples and that actual usage is uncertain. Saylacian converts macron vowels to the doubled glyph form, so they read back as `aa`, `ee`, `ii`, `oo` or `uu` rather than preserving macron notation ([Kaddare alphabet notes](https://skyknowledge.com/kaddare.htm)). The chart notes that distinguish upper and lower forms are also described by [Omniglot's Kaddare reference](https://www.omniglot.com/writing/kaddare.htm); the lower forms are cursive according to [SIL Writing Systems Technical Resources](https://writingsystems.info/scrlang/scripts/x-kaddare/). These are Saylacian-assigned private-use code points, not portable Unicode letters, and require the matching font. Coverage remains limited to the 26 chart labels; broader spelling and word-level conventions have not been reviewed.

## Old Nubian

Old Nubian is different: Saylacian has a limited 29-entry character-to-scholarly-reading table, not a meaning translator. The letter reference also shows the published phonetic values. The source pairs are:

| Old Nubian/Coptic-derived character | App's Latin reading |
|---|---|
| `ⲁ` | `a` |
| `ⲃ` | `b` |
| `ⲅ` | `g` |
| `ⲇ` | `d` |
| `ⲉ` | `e` |
| `ⲍ` | `z` |
| `ⲏ` | `ē` |
| `ⲑ` | `th` |
| `ⲓ` | `i` |
| `ⲕ` | `k` |
| `ⲗ` | `l` |
| `ⲙ` | `m` |
| `ⲛ` | `n` |
| `ⲝ` | `x` |
| `ⲟ` | `o` |
| `ⲡ` | `p` |
| `ⲣ` | `r` |
| `ⲥ` | `s` |
| `ⲧ` | `t` |
| `ⲩ` | `u` |
| `ⲫ` | `ph` |
| `ⲭ` | `kh` |
| `ⲯ` | `ps` |
| `ⲱ` | `ō` |
| `ϣ` | `š` |
| `ⳝ` | `j` |
| `ⳟ` | `ŋ` |
| `ⳡ` | `ñ` |
| `ⳣ` | `w` |

This table and its phonetic-value column are adapted from van Gerven Oei's peer-reviewed 2024 [Old Nubian overview](https://doi.org/10.5070/G9.3919), Table 1, under CC BY 4.0; attribution is in [third-party notices](../THIRD_PARTY_NOTICES.md). Its digraphs `ⲉⲓ` and `ⲟⲩ` have several published phonetic values (`i`, `iː`, `j`; `u`, `uː`, `w`, `wu`), shown by Saylacian as alternatives to the direct character-by-character readings (`ei`, `ou`). Latin `ou` may be read back as `ⲟⲩ` or `ⳣ`; the app lists both. This is not meaning translation, complete manuscript reading or a modern Latin alphabet. Letters absent from this 29-entry table are preserved and flagged. Specialist review is still needed.

For the combining macron used as a supralinear stroke, Saylacian keeps the mark in its main reading. When it is attached to `l`, `n`, `r` or `j`, it offers an `i`-before-letter alternative; for example, `ⲧⲗ̄ⲗⲛ̄` is shown as `tl̄ln̄`, with `tillin` among the alternatives. When the mark is over a vowel immediately after one of those consonants, the app offers `i` before that consonant. The 2024 overview gives `ⲟⲕⲧⲁⲕⲛⲁ̄` as `/oktagina/`; Saylacian's character-based reading keeps its primary `k` value and offers `oktakinā`. It does not infer an `i` insertion for other local contexts. These are limited alternatives, not full word readings; editions differ, and a stroke can also mark a numeral. Saylacian warns about that ambiguity and does not convert numerals. Other combining marks, including a dot above, remain in the text with a warning rather than being guessed. Alternative lists are capped at 12. See the [Old Nubian overview](https://doi.org/10.5070/G9.3919), Smagina's [Old Nubian language book](https://books.punctumbooks.com/10.21983/P3.0179.1.00.pdf), §37, and Browne's [Old Nubian Grammar](https://search.worldcat.org/title/50410309), §1.2.3.

The 2024 peer-reviewed overview's phonetic table gives `ⲏ` possible values `[i, i:]` and `ⲩ` `[i, u]`. Saylacian keeps its existing main readings (`ē`, `u`) and includes `i`/`iː` and `i` as alternatives. These are reading possibilities, not one-to-one spelling rules. See the [Old Nubian scope and sources](OLD_NUBIAN_SCOPE.md).

## Sharing and limits

Osmanya uses Unicode, although recipient font coverage can vary. Current Borama and Kaddare chart glyphs are private-use code points, which have no universal meaning outside a compatible font and mapping; see [script interoperability](SOMALI_SCRIPT_INTEROPERABILITY.md) and [copy options](USER_GUIDE.md#copy-borama-and-kaddare). No table here performs meaning translation. Modern Nubian varieties are not implemented.

## Source tables in this project

- Osmanya: `saylacian/core/data/osmanya.json`.
- Borama and Kaddare: `saylacian/core/data/scripts/borama.json` and `kaddare.json`.
- Old Nubian: `OLD_NUBIAN_TO_LATIN` in `saylacian/core/transliteration.py`.

The script-table inventory documents current application behavior, not a community-approved standard. See [Old Nubian scope](OLD_NUBIAN_SCOPE.md) for specialist-review limits.
