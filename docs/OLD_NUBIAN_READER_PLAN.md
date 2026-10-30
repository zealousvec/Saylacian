# Old Nubian Reading Studio plan

## Goal

Help readers inspect original Old Nubian text alongside a documented scholarly transliteration. The first release must not claim meaning translation, complete manuscript coverage, OCR accuracy, or definitive reconstruction.

## Stages

1. **Source audit:** keep one source ledger entry per mapped character in `OLD_NUBIAN_SOURCE_LEDGER.md`; record citation, convention, code point, uncertainty and reviewer. Confirm source-text reuse rights before building fixtures.
2. **Conversion safety:** preserve unlisted characters, normalization, punctuation, line breaks and combining sequences. Keep reverse readings visibly plural where boundaries are ambiguous. Add source-linked tests without claiming linguistic correctness from tests alone.
3. **Reading view:** show original text and Latin reading together. Preserve line breaks and selection/copy. Align by grapheme or word only when a source supports the segmentation; otherwise align the whole passage or line.
4. **Search and save:** permit search in original Unicode and Latin reading; save the original text separately from transliteration and user notes. Export plain Unicode with route/convention metadata so an import can reconstruct the same record.
5. **Review gate:** require specialist review of conventions, fixtures and the user-facing description. Outreach requires owner approval. Mark each corpus item as attested source, editorial reconstruction, uncertain reading or user note.

## Acceptance checks

- Original characters remain unchanged through input, search, history and export.
- Each transliteration is linked to a named convention and a source-ledger entry.
- Reverse conversion shows alternatives or uncertainty; it does not silently choose a unique historical spelling.
- Mixed text, unknown Coptic characters, punctuation, combining marks, blank lines and long passages are preserved or explicitly rejected.
- No dictionary or meaning translation appears without licensed, provenance-linked content and evaluation.
- A reviewer records what was checked and what remains uncertain.

## Current state

The approved translator screen shows source text and its reading in paired input/output panels, preserving line breaks. The reader uses the 29 single-character entries in Table 1 of van Gerven Oei (2024), with Unicode uppercase/lowercase handling, and preserves unlisted characters, combining marks, punctuation and line breaks. The source table is CC BY 4.0 and its attribution is in `docs/THIRD_PARTY_NOTICES.md`. Saylacian reports unlisted Coptic letters and does not infer reading rules for combining marks. Reverse conversion shows alternative letter-boundary parses where available; it cannot establish manuscript spelling. The Reading Studio provides a searchable alphabet, code points, source details, copy actions and versioned JSON export/import with a checksum. This is a character-reading aid, not an aligned scholarly edition.

There is no searchable word lexicon, bundled manuscript corpus, OCR, meaning translation or specialist review. Word-level alignment and additional character readings remain backlog tasks until cited sources and a reviewer support them. Describe this as limited character transliteration. The 2017 Smagina/Alonso de la Fuente edition is CC BY-NC-SA 4.0; its text, transliteration and glossary are not copied into the repository. The earlier DBMNT-derived set has been replaced with a table from the 2024 CC BY 4.0 article; DBMNT's unresolved reuse terms therefore do not block the active letter table.
