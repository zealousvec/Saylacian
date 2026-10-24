# Script engineering evidence

## Osmanya — experimental conversion

The mapping is an inspectable JSON resource at `saylacian/core/data/osmanya.json`. Unicode 16.0 chapter 19.2.1 documents Osmanya and its vowel/semivowel ambiguities. The Unicode chart establishes the assigned letter positions, but is not by itself a validated transliteration dictionary.

Sources:
- https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-19/
- https://www.unicode.org/charts/nameslist/c_10480.html

The corrective engine removes the previous invented p/v/z mappings: U+1049E and U+1049F are unassigned, and U+104A0 is the digit zero. Unmapped input is retained with a warning. Longest matches handle multigraphs; NFC normalization precedes conversion. Capitalization is lost, and reverse w/uu and y/ii are ambiguous. This is script conversion of Somali text, not English/Somali meaning translation. Word-level community validation is still needed.

Noto Sans Osmanya was recovered from the original font asset. Its embedded metadata identifies the Noto Project Authors (2022), version 2.001, and SIL OFL 1.1. Every U+10480–1049D letter has a cmap entry. Actual Osmanya glyph rendering was inspected in the Windows Kivy UI, not only through escaped console output. Licence text: `assets/OFL-Osmanya.txt`.

## Borama and Kaddare — unavailable

The Unicode-hosted 2023 African Scripts update describes preliminary encoding work and contact with Somali language institutions. A check of Unicode's current 2026 UTC document register (last updated 2026-09-29) found no entries under Borama, Kaddare or Gadabuursi. This is evidence about the Unicode pipeline, not proof that no community or legacy encoding exists. No code points or private-use mappings have been invented.

New archival lead: the 1961 Somali Language Committee report contains a Kaddare alphabet chart and describes 41 letters, left-to-right direction and four cursive/printing forms. The archive record says the item is under a Creative Commons licence, but the exact licence and reuse conditions still need confirmation. A chart in a historical committee report is not by itself a verified modern transliteration convention. Next research step: transcribe each chart against the report's example text, identify glyph/font rights, then ask a fluent Somali/Kaddare reviewer before implementing/exporting characters.

The Gadabuursi/Borama script has historical academic documentation by I.M. Lewis (1958), and a later scholarly note describes orthographic ambiguities (including merged vowel distinctions and visually similar signs). That evidence can seed a careful mapping study but does not establish a current standard or interoperable encoding. Complete inventories, orthographic rules, licensed glyph sources and an explicit rendering/export convention remain unresolved.

- https://www.unicode.org/L2/L2023/23203-update-african-scripts.pdf
- https://unicode.org/L2/L-curdoc.htm (UTC document register for 2026; checked 2026-10-23)
- https://arcadia.sba.uniroma3.it/handle/2307/2620?mode=full (Somali Language Committee, 1961 report; Kaddare chart)
- https://www.cambridge.org/core/journals/bulletin-of-the-school-of-oriental-and-african-studies/article/gadabuursi-somali-script/CB18BB69C8FEDB4CB60966709EB93643 (I.M. Lewis, 1958)
- https://www.maurotosco.net/ewExternalFiles/TOSCO_2015_Somali_Previous_Scripts.pdf

## Nubian — distinct language/orthography decisions remain

Nobiin, Kenzi/Mattokki, Dongolawi/Andaandi, Midob, Birgid, and the listed Hill Nubian varieties are distinct research targets. Old Nubian is a historical written language and cannot stand in for all modern varieties. No generic Nubian conversion table has been implemented.

Unicode includes Old Nubian characters within Coptic. That is encoding evidence, not a universal modern Nubian orthography or a meaning dictionary:

- https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-7/
- https://unicode.org/charts/PDF/U2C80.pdf

The picker exposes these targets with unavailable status. Expert/community review and exact transliteration conventions are required before their conversions can be advertised.
