# Script engineering evidence

## Osmanya — experimental conversion

The mapping is an inspectable JSON resource at `saylacian/core/data/osmanya.json`. Unicode 16.0 chapter 19.2.1 documents Osmanya and its vowel/semivowel ambiguities. The Unicode chart establishes the assigned letter positions, but is not by itself a validated transliteration dictionary.

Sources:
- https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-19/
- https://www.unicode.org/charts/nameslist/c_10480.html

The corrective engine removes the previous invented p/v/z mappings: U+1049E and U+1049F are unassigned, and U+104A0 is the digit zero. Unmapped input is retained with a warning. Longest matches handle multigraphs; NFC normalization precedes conversion. Capitalization is lost, and reverse w/uu and y/ii are ambiguous. This is script conversion of Somali text, not English/Somali meaning translation. Word-level community validation is still needed.

Noto Sans Osmanya was recovered from the original font asset. Its embedded metadata identifies the Noto Project Authors (2022), version 2.001, and SIL OFL 1.1. Every U+10480–1049D letter has a cmap entry. Actual Osmanya glyph rendering was inspected in the Windows Kivy UI, not only through escaped console output. Licence text: `assets/OFL-Osmanya.txt`.

## Borama and Kaddare — partial app mappings, no standard encoding

The project includes partial chart-label mappings adapted from Jugydmort's CC BY-SA 4.0 alphabet charts. They are not general spelling systems and do not establish accepted word orthography. Saylacian stores their glyphs in project-specific private-use code points and provides tagged text, image and Latin copy options on Windows. Plain, untagged private-use text cannot identify its script or font.

Unicode's 2023 African-scripts update says no Borama or Kaddare Unicode proposal had been submitted at that time and describes preliminary research with Somali institutions. The 2026 UTC register, last updated 2026-10-23, has no Borama or Kaddare entry. This documents the public Unicode pipeline checked on that date; it does not prove that no community, legacy font or private encoding exists. No standard Unicode block is assigned to either script in the sources checked.

The 1961 Somali Language Committee report is a research lead for Kaddare, not an adopted orthographic standard. Its archive metadata and reuse terms require separate verification before report material is copied or adapted. Lewis (1958) and Tosco (2015) provide historical context for Borama and other Somali scripts; they do not validate Saylacian's word-level mappings. Community review, independent chart transcription and broader orthographic evidence remain open.

- https://www.unicode.org/L2/L2023/23203-update-african-scripts.pdf
- https://unicode.org/L2/L-curdoc.htm (UTC register last updated 2026-10-23; searched for Borama and Kaddare)
- https://arcadia.sba.uniroma3.it/handle/2307/2620?mode=full (Somali Language Committee, 1961 report; Kaddare chart)
- https://www.cambridge.org/core/journals/bulletin-of-the-school-of-oriental-and-african-studies/article/gadabuursi-somali-script/CB18BB69C8FEDB4CB60966709EB93643 (I.M. Lewis, 1958)
- https://www.maurotosco.net/ewExternalFiles/TOSCO_2015_Somali_Previous_Scripts.pdf

## Nubian — distinct language/orthography decisions remain

Nobiin, Kenzi/Mattokki, Dongolawi/Andaandi, Midob, Birgid, and the listed Hill Nubian varieties are distinct research targets. Old Nubian is a historical written language and cannot stand in for all modern varieties. No generic Nubian conversion table has been implemented.

Unicode includes Old Nubian characters within Coptic. That is encoding evidence, not a universal modern Nubian orthography or a meaning dictionary:

- https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-7/
- https://unicode.org/charts/PDF/U2C80.pdf

The picker exposes these targets with unavailable status. Expert/community review and exact transliteration conventions are required before their conversions can be advertised.
