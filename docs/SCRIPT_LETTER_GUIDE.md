# Script letter mapping guide

This page describes the mappings currently present in Saylacian's source tables. A listed pair means the app has a character-level conversion entry; it is not a claim that the scripts are historically equivalent or that the resulting spelling has been linguistically reviewed. Letters outside a table are preserved as typed and may be reported as unmapped.

## Osmanya

The app maps Somali Latin graphemes to assigned Unicode Osmanya characters. It has entries for `a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, q, r, s, t, u, w, x, y`, the digraphs `dh, kh, sh`, long-vowel tokens `aa, ee, ii, oo, uu`, and apostrophe. The matcher checks longer tokens first, so digraphs and long vowels are recognized before their first letters.

There is no app mapping for `p`, `v` or `z`; these are not part of the Somali letter set represented by this table and remain Latin when present in borrowed or foreign words. This is a limitation of the app's Somali mapping, not a claim that Osmanya cannot represent every foreign sound. The table also maps `w` and `uu` to the same Osmanya character, and `y` and `ii` to the same character. Consequently reverse transliteration cannot always recover which Latin spelling was intended. Capitalization is not encoded.

## Borama

The current chart-derived table contains these graphemes:

`a, e, i, ii, u, uu, oo, b, t, j, dh, g, h, kh, d, r, s, sh, c, f, q, k, l, m, n, w, y`

The chart labels its U+E014 glyph as `LETTER Q`. Earlier Saylacian text used U+E014 for `o`, so that reading remains available for compatibility. New `q` output uses U+E01B; new `o` input stays Latin because the chart has no `o` glyph. The chart also has no `x` entry, so `x` stays Latin and is reported. `p`, `v` and `z` likewise have no mapping in this table. The app's glyphs use private-use code points: they need Saylacian's matching font/table, or use **Copy Latin** / **Copy image** when sharing outside the app. This is a partial chart transcription; do not infer a complete Borama alphabet or reviewed spelling from it.

A historical cross-check is available in Mauro Tosco's 2015 survey, which reproduces Lewis's 1958 Gadabuursi chart (pp. 142–143). Tosco notes that some signs are similar and that the chart's `d`/`q` distinction is difficult to resolve from the table alone. This supports treating chart labels as provisional mapping evidence, not as a fully attested orthography. The current source chart and this historical reproduction do not establish a safe Borama mapping for modern Somali `o` or `x`; Saylacian therefore preserves those inputs and reports them as unmapped. No new glyph mapping was inferred from this source.

## Kaddare

The current chart-derived table contains:

`a, e, i, o, u, b, t, j, x, kh, d, r, s, sh, dh, c, g, f, q, k, l, m, n, w, h, y`

`p`, `v` and `z` have no entry in this table and remain Latin. As with Borama, the chart glyphs use private-use code points and need Saylacian-compatible font support to display as editable writing in another app. Coverage is limited to these chart records; spelling and word-level conventions have not been reviewed.

## Old Nubian

Old Nubian is different: Saylacian has a limited 29-character reading table, not a complete A-to-Z alphabet conversion or meaning translator. Its entries follow Table 1 in van Gerven Oei (2024), licensed CC BY 4.0; attribution is in the [third-party notices](THIRD_PARTY_NOTICES.md).

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
| `ⳟ` | `ŋ` |
| `ⳡ` | `ñ` |
| `ⳣ` | `w` |
| `ⳝ` | `j` |

The 2024 table gives `kh` for `ⲭ`, `ŋ` for `ⳟ`, and `ñ` for `ⳡ`. It describes `ⲉⲓ` and `ⲟⲩ` as digraphs and gives multiple phonetic values for each. Saylacian warns when these sequences appear, but still transliterates each character separately and does not choose a pronunciation. It has no Old Nubian `v` entry; an unlisted character such as `ϥ` is preserved and flagged. This does not imply that all historical writing is represented by modern Latin letters. The multi-character readings `th`, `ph`, `kh`, and `ps` may be split at different letter boundaries when reversed; the app shows possible parses, not an authoritative spelling. See the [Old Nubian reading scope](OLD_NUBIAN_READER_PLAN.md).

## Sharing and limits

Osmanya uses Unicode, although recipient font coverage can vary. Current Borama and Kaddare chart glyphs are private-use code points, which have no universal meaning outside a compatible font and mapping; see [script interoperability](SOMALI_SCRIPT_INTEROPERABILITY.md) and [copy options](USER_GUIDE.md#copy-borama-and-kaddare). No table here performs meaning translation. Modern Nubian varieties are not implemented.

## Source tables in this project

- Osmanya: `saylacian/core/data/osmanya.json`.
- Borama and Kaddare: `saylacian/core/data/scripts/borama.json` and `kaddare.json`.
- Old Nubian: `OLD_NUBIAN_TO_LATIN` in `saylacian/core/transliteration.py`.

The script-table inventory documents current application behavior, not a community-approved standard. See [project status](PROJECT_STATUS.md) for review and rights limitations.
