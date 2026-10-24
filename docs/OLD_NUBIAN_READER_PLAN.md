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

The approved translator screen already shows source text and its reading in paired input/output panels, preserving line breaks. The limited 34-entry table now applies Unicode uppercase/lowercase pairs mechanically and preserves unsupported letters, combining marks, punctuation and line breaks. It reports unverified letters, warns when Coptic combining marks may not render beside Latin, and makes reverse alternatives visible. This is a reading aid for character-level transliteration, not an aligned scholarly edition.

There is no searchable lexicon, manuscript corpus, source-linked passage set, OCR, meaning translation or specialist review. Word-level alignment and additional character readings remain backlog tasks until cited sources and a reviewer support them. The current UI and README must continue to describe this as limited transliteration.
