# Verified app release sprint — 2026-11-07

## Published scope

- Osmanya → Somali Latin now returns bounded alternative character readings for ambiguous w/uu and y/ii glyphs, while retaining the primary output and preserving unknown text. These are possible readings, not automatic spelling corrections.
- The website exposes the existing limited Old Nubian Coptic/scholarly Latin routes. JSON responses include alternatives; JavaScript and form-rendered results show up to three readings. Client rendering uses textContent, and template output remains escaped.
- Old Nubian sequences ⲉⲓ and ⲟⲩ produce source-attributed ambiguity warnings in both directions, including uppercase input. Per-letter transliteration stays unchanged; no pronunciation is selected.
- Regression coverage checks ambiguity, bounded output, preservation, API responses, form rendering and route availability.

## Borama mapping correction

The bundled source chart visibly labels the disputed entry LETTER Q. The converter now maps q to U+E01B, keeps unlisted o/x as flagged Latin, and retains legacy U+E014 decoding as o with a compatibility warning. The updated font maps both private-use positions to the same chart glyph. Borama and Kaddare records include source artifact hashes; existing source attribution and CC BY-SA terms remain. The source chart was visually inspected during this sprint. This fixes chart transcription, not word-level orthography.

## Verification

The release was prepared in a separate checkout based on current origin/main, not by staging the owner's dirty research workspace. Local checks use the already installed development interpreter.

- Full pytest suite before the final bounded-output regression: 190 passed, 11 skipped, 193 subtests passed.
- Final test counts and GitHub CI status are recorded in the PR and local sprint completion report.
- Repository-wide Ruff lint and formatting passed before the final regression; both are rerun before commit.
- Credential scan, Python compilation and whitespace checks run before publication.

No datasets, weights or credentials are included. No translation model was trained, integrated or promoted. These are converter/UI improvements; no new translation accuracy claim is made. Linguistic review remains open. Local model-dependent skips do not verify packaged EXE behavior, actual browser interaction, or every installed model route.

## Research fix preserved locally

The private working tree's M2M100 held-out evaluator incorrectly reversed English/Somali rows when language metadata was absent. The fix assumes canonical English→Somali only when both tags are absent, correctly reverses the requested direction, and rejects partial/mismatched tags. Its focused suite passes 18 tests. It is not part of this app PR because the evaluator and its dependencies are an unfinished unpublished research tree. Prior incorrect full-evaluation scores must not be used as release evidence. No expensive benchmark was rerun during this sprint.

## Remaining work

Independently evaluate transliteration spellings and translation meaning; validate actual installed app model routes; finish and review the research tree separately; test packaged Windows binaries and real browser/accessibility behavior. See the existing support matrix for script limits. This PR does not establish Google Translate parity or 90% accuracy.
