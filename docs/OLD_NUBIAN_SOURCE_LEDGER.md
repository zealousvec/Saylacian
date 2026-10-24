# Old Nubian mapping source ledger

## Scope and source

The current route is a limited Coptic/Greek-derived character transliteration table, not meaning translation, complete language coverage, manuscript interpretation, or a validated reader. The implementation lives in `saylacian/core/transliteration.py` as `OLD_NUBIAN_TO_LATIN`.

Primary mapping reference: Database of Medieval Nubian Texts, [transliteration tables](https://dbmnt.uw.edu.pl/static/pdf/transliteration_tables.pdf), page 1. The table gives a comparative `Greek, Coptic, Old Nubian` column. Its footnotes state that the romanization generally follows ALA-LC, with `ϣ` represented as `sh`, `ϫ` as `dj`, `ⳟ` as `ng`, `ⳡ` as `ny`, and `ⳝ` as `j`; it describes `ⳣ` as `w, ou`. The app's `ky` for `ϭ` follows this table, not the Sahidic Coptic value. The PDF's reuse licence was not confirmed; Saylacian cites the reference but does not bundle its text or manuscript records.

## Rights review (2026-10-24)

The official [DBMNT General Guidelines](https://dbmnt.uw.edu.pl/guidelines/general/) say the transliteration tables can be downloaded and identify the database copyright as © 2011–2026 Grzegorz Ochała. The page contains no licence or reuse grant. Download availability is not redistribution permission. The 34 source-linked readings already implemented in Saylacian therefore remain a rights question; do not extend or redistribute additional table-derived data until terms are clarified. The PDF itself is not bundled.

Unicode NamesList evidence: [Coptic block names list, Unicode 18.0](https://www.unicode.org/Public/18.0.0/charts/nameslist/2c80/). The names list identifies the Old Nubian additions at U+2CDD, U+2CDF, U+2CE1 and U+2CE3. Standard character names establish code-point identity, not the correct language-specific reading.

Every lowercase entry below is source-linked but **not independently reviewed**. The implementation derives uppercase entries mechanically from Unicode's paired uppercase characters and uppercases the corresponding Latin reading; this is a software case-preservation convention, not a claim about capitalization in Old Nubian manuscripts. The bundled Coptic font is checked against every generated converter glyph. The reviewer field is intentionally explicit. Changes to the lowercase mapping must update this ledger and its tests together.

| Character | Code point | Unicode name | Current Latin reading | Evidence/convention | Confidence | Reviewer |
|---|---|---|---|---|---|---|
| ⲁ | U+2C81 | COPTIC SMALL LETTER ALFA | a | DBMNT p. 1 | source-linked | none |
| ⲃ | U+2C83 | COPTIC SMALL LETTER VIDA | b | DBMNT p. 1 | source-linked | none |
| ⲅ | U+2C85 | COPTIC SMALL LETTER GAMMA | g | DBMNT p. 1 | source-linked | none |
| ⲇ | U+2C87 | COPTIC SMALL LETTER DALDA | d | DBMNT p. 1 | source-linked | none |
| ⲉ | U+2C89 | COPTIC SMALL LETTER EIE | e | DBMNT p. 1 | source-linked | none |
| ⲍ | U+2C8D | COPTIC SMALL LETTER ZATA | z | DBMNT p. 1 | source-linked | none |
| ⲏ | U+2C8F | COPTIC SMALL LETTER HATE | ē | DBMNT p. 1 | source-linked | none |
| ⲑ | U+2C91 | COPTIC SMALL LETTER THETHE | th | DBMNT p. 1 | source-linked | none |
| ⲓ | U+2C93 | COPTIC SMALL LETTER IAUDA | i | DBMNT p. 1 | source-linked | none |
| ⲕ | U+2C95 | COPTIC SMALL LETTER KAPA | k | DBMNT p. 1 | source-linked | none |
| ⲗ | U+2C97 | COPTIC SMALL LETTER LAULA | l | DBMNT p. 1 | source-linked | none |
| ⲙ | U+2C99 | COPTIC SMALL LETTER MI | m | DBMNT p. 1 | source-linked | none |
| ⲛ | U+2C9B | COPTIC SMALL LETTER NI | n | DBMNT p. 1 | source-linked | none |
| ⲝ | U+2C9D | COPTIC SMALL LETTER KSI | x | DBMNT p. 1 | source-linked | none |
| ⲟ | U+2C9F | COPTIC SMALL LETTER O | o | DBMNT p. 1 | source-linked | none |
| ⲡ | U+2CA1 | COPTIC SMALL LETTER PI | p | DBMNT p. 1 | source-linked | none |
| ⲣ | U+2CA3 | COPTIC SMALL LETTER RO | r | DBMNT p. 1 | source-linked | none |
| ⲥ | U+2CA5 | COPTIC SMALL LETTER SIMA | s | DBMNT p. 1 | source-linked | none |
| ⲧ | U+2CA7 | COPTIC SMALL LETTER TAU | t | DBMNT p. 1 | source-linked | none |
| ⲩ | U+2CA9 | COPTIC SMALL LETTER UA | u | DBMNT p. 1 | source-linked | none |
| ⲫ | U+2CAB | COPTIC SMALL LETTER FI | ph | DBMNT p. 1 | source-linked | none |
| ⲭ | U+2CAD | COPTIC SMALL LETTER KHI | ch | DBMNT p. 1 | source-linked | none |
| ⲯ | U+2CAF | COPTIC SMALL LETTER PSI | ps | DBMNT p. 1 | source-linked | none |
| ⲱ | U+2CB1 | COPTIC SMALL LETTER OOU | ō | DBMNT p. 1 | source-linked | none |
| ϣ | U+03E3 | COPTIC SMALL LETTER SHEI | sh | DBMNT p. 1; footnote convention | source-linked | none |
| ϥ | U+03E5 | COPTIC SMALL LETTER FEI | f | DBMNT p. 1 | source-linked | none |
| ϩ | U+03E9 | COPTIC SMALL LETTER HORI | h | DBMNT p. 1 | source-linked | none |
| ϫ | U+03EB | COPTIC SMALL LETTER GANGIA | dj | DBMNT p. 1; footnote convention | source-linked | none |
| ϭ | U+03ED | COPTIC SMALL LETTER SHIMA | ky | DBMNT p. 1 | source-linked | none |
| ϯ | U+03EF | COPTIC SMALL LETTER DEI | ti | DBMNT p. 1 | source-linked | none |
| ⳝ | U+2CDD | COPTIC SMALL LETTER OLD NUBIAN SHIMA | j | DBMNT p. 1; footnote convention | source-linked | none |
| ⳟ | U+2CDF | COPTIC SMALL LETTER OLD NUBIAN NGI | ng | DBMNT p. 1; footnote convention | source-linked | none |
| ⳡ | U+2CE1 | COPTIC SMALL LETTER OLD NUBIAN NYI | ny | DBMNT p. 1; footnote convention | source-linked | none |
| ⳣ | U+2CE3 | COPTIC SMALL LETTER OLD NUBIAN WAU | w | DBMNT p. 1; `ou` alternative is handled only in reverse parser | source-linked | none |

## Known gaps and uncertainty

- The route has no source-linked manuscript fixture set and no independent Old Nubian specialist review.
- Reverse transliteration is ambiguous. The code reports candidate strings, but the candidate generator is experimental and does not reconstruct a manuscript spelling.
- The 34 lowercase entries listed above are the only linguistic readings implemented. Their Unicode uppercase partners are accepted using Python Unicode case pairs and an uppercase Latin rendering; this adds no new source reading. Unlisted alphabetic characters are preserved with a warning. Coptic combining marks and punctuation pass through unchanged and now produce a notice that Saylacian applies no reading or interpretation rule to them. The live Latin output may not visibly render combining Coptic marks; the original input retains them. Numerals, manuscript capitalization, spacing and editorial conventions still need scholarly review.
- Unicode NamesList identifies uppercase/lowercase pairs for the Old Nubian additions: U+2CDC/U+2CDD (shima), U+2CDE/U+2CDF (ngi), U+2CE0/U+2CE1 (nyi), and U+2CE2/U+2CE3 (wau). Saylacian preserves case mechanically across these pairs but does not infer manuscript capitalization. Unicode also lists Coptic combining marks and Old Nubian punctuation; their code-point names establish identity, not reading or interpretation.
- The Reading Studio identifies preserved combining marks by Unicode name and one-based code-point position and uses the bundled Noto Sans Coptic font in its Latin-reading field. This is font/display behavior plus Unicode identification, not a claim about Old Nubian mark values or how they should be read. Unicode NamesList describes U+2CEF COPTIC COMBINING NI ABOVE as extending above the following character, usually a space; it does not establish an Old Nubian reading rule. Though the font has glyphs for U+2CEF–U+2CF1 and Kivy draws them, their attachment/positioning in Latin context is not validated; retain the textual code-point note. The display change is covered by tests and live Kivy acceptance.
- Unicode includes additional Coptic/Old Nubian characters and punctuation. Presence in Unicode does not itself license a transliteration rule; audit them against scholarly references before mapping.
- Do not add word definitions, translation claims, manuscript excerpts, or canonical orthographic rules based on this table alone.

## Verification required before expanding the table

1. Check each row against a legally accessible scholarly edition and record its exact page/table.
2. Determine reuse terms before copying any example or dataset.
3. Add a test for each accepted mapping and Unicode normalization edge case.
4. Record an independent reviewer and convention name before presenting a disputed value as settled.
