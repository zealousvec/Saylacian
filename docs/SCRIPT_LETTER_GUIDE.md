# Script letter mapping guide

This page describes the mappings currently present in Saylacian's source tables. A listed pair means the app has a character-level conversion entry; it is not a claim that the scripts are historically equivalent or that the resulting spelling has been linguistically reviewed. Letters outside a table are preserved as typed and may be reported as unmapped.

## Osmanya

The app maps Somali Latin graphemes to assigned Unicode Osmanya characters. It has entries for `a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, q, r, s, t, u, w, x, y`, the digraphs `dh, kh, sh`, long-vowel tokens `aa, ee, ii, oo, uu`, and apostrophe. The matcher checks longer tokens first, so digraphs and long vowels are recognized before their first letters.

There is no app mapping for `p`, `v` or `z`; these are not part of the Somali letter set represented by this table and remain Latin when present in borrowed or foreign words. This is a limitation of the app's Somali mapping, not a claim that Osmanya cannot represent every foreign sound. The table also maps `w` and `uu` to the same Osmanya character, and `y` and `ii` to the same character. Consequently reverse transliteration cannot always recover which Latin spelling was intended. Capitalization is not encoded.

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

So there is no single `v` reading in this current table; that does not mean a modern Latin alphabet maps directly to Old Nubian. For example, `c` is not a standalone table entry, while `ch` is the reading assigned to `ⲭ`. `dj`, `ky`, `ng`, `ny`, `sh`, `th`, `ch`, `ph`, `ps`, `ti` and `ou` can be ambiguous as Latin sequences; reverse conversion can show alternatives or preserve the sequence rather than prove one original spelling. Characters absent from the table are kept, not guessed. Source reuse permission and specialist review remain unresolved; see the [Old Nubian scope](OLD_NUBIAN_SCOPE.md).

## Sharing and limits

Osmanya uses Unicode, although recipient font coverage can vary. Current Borama and Kaddare chart glyphs are private-use code points, which have no universal meaning outside a compatible font and mapping; see [script interoperability](SOMALI_SCRIPT_INTEROPERABILITY.md) and [copy options](USER_GUIDE.md#copy-borama-and-kaddare). No table here performs meaning translation. Modern Nubian varieties are not implemented.

## Source tables in this project

- Osmanya: `saylacian/core/data/osmanya.json`.
- Borama and Kaddare: `saylacian/core/data/scripts/borama.json` and `kaddare.json`.
- Old Nubian: `OLD_NUBIAN_TO_LATIN` in `saylacian/core/transliteration.py`.

The script-table inventory documents current application behavior, not a community-approved standard. See [Old Nubian scope](OLD_NUBIAN_SCOPE.md) for its review and rights limitations.
