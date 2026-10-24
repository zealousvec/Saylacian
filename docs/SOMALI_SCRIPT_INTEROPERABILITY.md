# Somali script interoperability

This note separates text encoding from how a font displays it. A successful conversion test proves that the code emits its expected characters; it does not prove that every recipient app has a font or accepts every clipboard format.

## Current behavior

| Script/route | Stored output | Portability | Current limitation |
|---|---|---|---|
| Somali Latin | Standard Latin Unicode | Broad text support | Somali spelling and translation quality still need fluent review |
| Osmanya | Assigned Unicode characters U+10480–U+1049D | Text is standard Unicode; glyph display depends on the recipient font | Mapping is experimental; capitalization and some Somali vowel/semivowel distinctions are lost |
| Borama | Saylacian chart mapping in private-use code points | Requires matching mapping/font for editable glyphs | No standard Unicode assignment in sources checked; word spelling unreviewed |
| Kaddare | Saylacian chart mapping in private-use code points | Requires matching mapping/font for editable glyphs | No standard Unicode assignment in sources checked; chart variants do not establish word spelling |

Osmanya's Unicode encoding is documented in the Unicode Core Specification, chapter 19, and the Unicode character chart. These sources establish encoded characters, not the app's full Somali romanization policy. [Unicode Core Specification](https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-19/) · [Osmanya chart](https://www.unicode.org/charts/nameslist/n_10480.html).

The 2023 Unicode African-scripts update said no Borama or Kaddare encoding proposal had been submitted at that time. The Unicode Technical Committee register last updated 2026-10-23 was searched for both names on 2026-10-24 and returned no matching entries. That is a dated check of the public Unicode pipeline, not evidence that no community or legacy encoding exists. [2023 update](https://www.unicode.org/L2/L2023/23203-update-african-scripts.pdf) · [2026 UTC register](https://unicode.org/L2/L-curdoc.htm).

## Copy and import matrix

| Action | Clipboard payload | Editable? | Expected round-trip |
|---|---|---|---|
| Copy text | Windows custom `Saylacian Text v1`, RTF, CF_HTML, and Unicode text containing a versioned ASCII package | Package is editable; raw chart glyphs in rich formats need the matching font | Paste the package into Saylacian; it verifies version, script, character set and digest |
| Copy image | PNG, Windows `CF_DIB`, and descriptive Unicode text | No | Appearance is retained in apps accepting image paste; image does not encode editable glyphs |
| Copy Latin | Ordinary Somali Latin | Yes | Portable reading; original script glyph identities are lost |

Other platforms currently support text and Latin via Kivy's text clipboard; image clipboard output is Windows-only. Pasting untagged private-use text does not infer Borama or Kaddare. Choose a source route explicitly or paste the tagged package. This prevents unrelated fonts that reuse the same private-use code points from being silently read as Saylacian.

## Verification still required

The live Kivy acceptance run checked generated Borama/Kaddare fonts, copy menu availability, clipboard payload construction, tagged import, app font selection and conversion. The repository also has a Windows clipboard test that uses the real clipboard plus a separate WinForms reader. Its existing recorded evidence predates the current menu labels and no longer proves the updated build.

Before marking cross-app behavior verified, test Notepad, a browser input, Word or equivalent, VS Code and a messaging-style field. Record independently whether content is present, glyphs render, text is searchable/editable, and Saylacian round-trip succeeds. Check both with and without the font when feasible. Preserve the original clipboard contents and do not run the real clipboard test if its safety preflight finds non-text clipboard data.
