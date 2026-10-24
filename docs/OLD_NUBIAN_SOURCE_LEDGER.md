# Old Nubian mapping source ledger

## Scope and source

The current route is a limited Coptic/Greek-derived character transliteration table, not meaning translation, complete language coverage, manuscript interpretation, or a validated reader. The implementation lives in `saylacian/core/transliteration.py` as `OLD_NUBIAN_TO_LATIN`.

Primary mapping reference: Database of Medieval Nubian Texts, [transliteration tables](https://dbmnt.uw.edu.pl/static/pdf/transliteration_tables.pdf), page 1. The table gives a comparative `Greek, Coptic, Old Nubian` column. Its footnotes state that the romanization generally follows ALA-LC, with `ϣ` represented as `sh`, `ϫ` as `dj`, `ⳟ` as `ng`, `ⳡ` as `ny`, and `ⳝ` as `j`; it describes `ⳣ` as `w, ou`. The app's `ky` for `ϭ` follows this table, not the Sahidic Coptic value. The PDF's reuse licence was not confirmed; Saylacian cites the reference but does not bundle its text or manuscript records.

Unicode NamesList evidence: [Coptic block names list, Unicode 18.0](https://www.unicode.org/Public/18.0.0/charts/nameslist/2c80/). The names list identifies the Old Nubian additions at U+2CDD, U+2CDF, U+2CE1 and U+2CE3. Standard character names establish code-point identity, not the correct language-specific reading.

Every implemented entry below is source-linked but **not independently reviewed**. The reviewer field is intentionally explicit. The table is generated from the checked-in code mapping, so changes to that mapping must update this ledger and its tests together.

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
- Only the 34 lowercase entries listed above are mapped. Unlisted alphabetic characters, including Old Nubian capital letters, are preserved with a warning. Old Nubian punctuation and combining marks currently pass through unchanged, without transliteration rules; tests cover the encoded punctuation/marks. Numerals, spacing, case policy and editorial conventions still need scholarly review.
- Unicode includes additional Coptic/Old Nubian characters and punctuation. Presence in Unicode does not itself license a transliteration rule; audit them against scholarly references before mapping.
- Do not add word definitions, translation claims, manuscript excerpts, or canonical orthographic rules based on this table alone.

## Verification required before expanding the table

1. Check each row against a legally accessible scholarly edition and record its exact page/table.
2. Determine reuse terms before copying any example or dataset.
3. Add a test for each accepted mapping and Unicode normalization edge case.
4. Record an independent reviewer and convention name before presenting a disputed value as settled.
