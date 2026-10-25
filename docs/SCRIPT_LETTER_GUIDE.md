# Script letter mapping guide

This page describes the mappings currently present in Saylacian's source tables. A listed pair means the app has a character-level conversion entry; it is not a claim that the scripts are historically equivalent or that the resulting spelling has been linguistically reviewed. Letters outside a table are preserved as typed and may be reported as unmapped. Unknown Borama and Kaddare private-use glyphs are also preserved and flagged throughout the Unicode private-use ranges.

## Osmanya

The app maps Somali Latin graphemes to assigned Unicode Osmanya characters. It has entries for `a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, q, r, s, t, u, w, x, y`, the digraphs `dh, kh, sh`, long-vowel tokens `aa, ee, ii, oo, uu`, and apostrophe. The matcher checks longer tokens first, so digraphs and long vowels are recognized before their first letters.

There is no app mapping for `p`, `v` or `z`; these are not part of the Somali letter set represented by this table and remain Latin when present in borrowed or foreign words. This is a limitation of the app's Somali mapping, not a claim that Osmanya cannot represent every foreign sound. The table maps `w` and `uu` to the same Osmanya character, and `y` and `ii` to the same character. Reverse transliteration chooses `w` or `y` as the main reading and now lists other possible readings in the app. The original spelling cannot always be recovered. Capitalization is not encoded.

The Unicode Standard describes Osmanya as having 22 consonants and 8 vowels, and specifies that long `uu` and `ii` use the same Waw and Ya letters as `w` and `y`. That is why the reverse readings are alternatives instead of a claim that the original spelling can be recovered. See [Unicode 16.0, chapter 19](https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-19/).

## Borama

The current chart-derived table contains these graphemes:

`a, e, i, ii, u, uu, oo, b, t, j, dh, g, h, kh, d, r, s, sh, c, f, o, k, l, m, n, w, y`

The chart explicitly lists `q` as unsupported. The current records also have no `x` entry. `p`, `v` and `z` likewise have no mapping in this table. Any of these characters stay Latin in converted output. The app's glyphs use private-use code points: they need Saylacian's matching font/table, or use **Copy Latin** / **Copy image** when sharing outside the app. This is a partial chart transcription; do not infer a complete Borama alphabet or reviewed spelling from it.

## Kaddare

The current chart-derived table contains:

`a, e, i, o, u, b, t, j, x, kh, d, r, s, sh, dh, c, g, f, q, k, l, m, n, w, h, y`

`p`, `v` and `z` have no entry in this table and remain Latin. As with Borama, the chart glyphs use private-use code points and need Saylacian-compatible font support to display as editable writing in another app. Coverage is limited to these chart records; spelling and word-level conventions have not been reviewed.

## Old Nubian

Old Nubian is different: Saylacian has a 34-entry character-to-scholarly-reading table, not a complete A-to-Z alphabet conversion or meaning translator. The current source pairs are:

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
| `ⲭ` | `ch` |
| `ⲯ` | `ps` |
| `ⲱ` | `ō` |
| `ϣ` | `sh` |
| `ϥ` | `f` |
| `ϩ` | `h` |
| `ϫ` | `dj` |
| `ϭ` | `ky` |
| `ϯ` | `ti` |
| `ⳟ` | `ng` |
| `ⳡ` | `ny` |
| `ⳣ` | `w` |
| `ⳝ` | `j` |

The DBMNT table gives `ⳣ` two Latin readings, `w` and `ou`; Saylacian shows `w` as the main reading and `ou` as an alternative. This does not mean a modern Latin alphabet maps directly to Old Nubian. For example, `c` is not a standalone table entry, while `ch` is the reading assigned to `ⲭ`. Latin-to-script sequences can still be ambiguous where multiple table entries line up; alternatives do not establish the original spelling. Latin letters absent from the table, such as `v`, are kept as Latin and flagged; they are not guessed. Source reuse permission and specialist review remain unresolved; see the [Old Nubian scope](OLD_NUBIAN_SCOPE.md).

For the combining macron used as a supralinear stroke, Saylacian keeps the mark in its main reading and also offers an `i`-based alternative. For example, `ⲧⲗ̄ⲗⲛ̄` is shown as `tl̄ln̄`, with `tillin` among the alternatives. This reflects one published scholarly convention; editions differ in how they represent and interpret the stroke, so the alternative is not a universal reading. Other combining marks, including a dot above, remain in the text with a warning rather than being guessed. Alternative lists are capped at 12. See [The Old Nubian Language, “Script: Reconstruction of the Phonological System”](https://books.punctumbooks.com/10.21983/P3.0180.1.00.pdf) and the [DBMNT transliteration table](https://dbmnt.uw.edu.pl/static/pdf/transliteration_tables.pdf).

## Sharing and limits

Osmanya uses Unicode, although recipient font coverage can vary. Current Borama and Kaddare chart glyphs are private-use code points, which have no universal meaning outside a compatible font and mapping; see [script interoperability](SOMALI_SCRIPT_INTEROPERABILITY.md) and [copy options](USER_GUIDE.md#copy-borama-and-kaddare). No table here performs meaning translation. Modern Nubian varieties are not implemented.

## Source tables in this project

- Osmanya: `saylacian/core/data/osmanya.json`.
- Borama and Kaddare: `saylacian/core/data/scripts/borama.json` and `kaddare.json`.
- Old Nubian: `OLD_NUBIAN_TO_LATIN` in `saylacian/core/transliteration.py`.

The script-table inventory documents current application behavior, not a community-approved standard. See [Old Nubian scope](OLD_NUBIAN_SCOPE.md) for its review and rights limitations.
