# Old Nubian mapping source ledger

## Active mapping source

Saylacian’s Old Nubian reader uses the 29 single-character readings in Table 1 of Vincent W. J. van Gerven Oei, “Old Nubian,” *UCLA Encyclopedia of Egyptology* 1(1), 2024. The article was published 2024-06-14, DOI [10.5070/G9.3919](https://doi.org/10.5070/G9.3919), and is licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The official article record identifies the license. See the full attribution and modification note in `docs/THIRD_PARTY_NOTICES.md`.

| Character | Code point | Table reading |
|---|---|---|
| ⲁ | U+2C81 | a |
| ⲃ | U+2C83 | b |
| ⲅ | U+2C85 | g |
| ⲇ | U+2C87 | d |
| ⲉ | U+2C89 | e |
| ⲍ | U+2C8D | z |
| ⲏ | U+2C8F | ē |
| ⲑ | U+2C91 | th |
| ⲓ | U+2C93 | i |
| ⲕ | U+2C95 | k |
| ⲗ | U+2C97 | l |
| ⲙ | U+2C99 | m |
| ⲛ | U+2C9B | n |
| ⲝ | U+2C9D | x |
| ⲟ | U+2C9F | o |
| ⲡ | U+2CA1 | p |
| ⲣ | U+2CA3 | r |
| ⲥ | U+2CA5 | s |
| ⲧ | U+2CA7 | t |
| ⲩ | U+2CA9 | u |
| ⲫ | U+2CAB | ph |
| ⲭ | U+2CAD | kh |
| ⲯ | U+2CAF | ps |
| ⲱ | U+2CB1 | ō |
| ϣ | U+03E3 | š |
| ⳝ | U+2CDD | j |
| ⳟ | U+2CDF | ŋ |
| ⳡ | U+2CE1 | ñ |
| ⳣ | U+2CE3 | w |

## Implementation boundaries

- This list follows the article’s transliteration column. The article also discusses phonetic values and two digraphs, ⲉⲓ and ⲟⲩ. Saylacian does not implement a digraph rule; characters are read independently.
- Unicode uppercase/lowercase pairs are handled mechanically for display. This is a software convention, not evidence about manuscript capitalization.
- Unlisted Coptic letters, combining marks and punctuation are preserved. Unlisted letters are reported; no reading or interpretation is inferred for marks or punctuation.
- Reverse conversion can split multi-character readings (th, ph, kh, ps) into alternative character sequences. These are possible parses, not verified manuscript spellings.
- The app has not received an independent Old Nubian specialist review. This is character transliteration only, not meaning translation, complete manuscript support, or modern Nubian support.

The earlier DBMNT-derived table was removed from the active code and documentation because its reuse terms were not established. DBMNT remains a bibliography reference only; no DBMNT mapping table or text is bundled.
