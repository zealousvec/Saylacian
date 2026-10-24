# Support matrix

Status describes current checked-in code and local resources, not a release-quality claim.

## Meaning translation

| Source | Target | Route | Status |
|---|---|---|---|
| English | French | Local model | Works offline; smoke-tested |
| French | English | Local model | Works offline; smoke-tested |
| English | Somali Latin | Downloaded packs use multilingual OPUS; builds with the locally prepared synthetic candidate prefer it and fall back on degenerate output | Experimental; no synthetic model is included in current downloadable pack; fluent review needed |
| Somali Latin | English | Local multilingual model | Experimental; fluent review needed |
| Somali Latin | French | Somali → English → French local models | Experimental pivot; errors compound |
| French | Somali Latin | French → English → Somali local models | Experimental pivot; known awkward output |

No other meaning-translation pairs are installed. Picker labels distinguish experimental meaning models from unavailable script mappings. An unavailable script cannot be selected as an active source/target route.

## Script conversion

| Conversion | Status | Limit |
|---|---|---|
| Somali Latin ↔ Osmanya | Experimental mapping implemented | Orthography, ambiguous readings and community validation remain open |
| Somali Latin ↔ Borama | Experimental partial chart-label mapping | Bundled font renders app-generated private-use output; app paste auto-detects that mapping. Not portable/standardized; external PUA font mappings cannot be inferred. |
| Somali Latin ↔ Kaddare | Experimental partial chart-label mapping | Bundled font renders app-generated private-use output; app paste auto-detects that mapping. Not portable/standardized; external PUA font mappings cannot be inferred. |
| Borama / Kaddare clipboard | Windows: Latin, image, Saylacian Text v1, RTF and CF_HTML published and read by a separate WinForms process | Plain text and images are broadly consumable according to receiving-app paste support. Editable PUA glyph display needs the matching chart font; exact round-trip is via Saylacian Text v1 in Saylacian. Other OSes currently offer Latin only. |
| Nubian | Unsupported and underspecified | Exact language variety and writing convention need a source-backed decision |

Osmanya script conversion changes writing system; it does not translate meaning. No PUA or invented Unicode substitute is presented as a real alphabet.

## Language identification and platforms

Offline detection covers English, French and Somali Latin with confidence/short-text abstention. Osmanya is detected as a script. No broad independent accuracy benchmark exists.

| Platform | Status |
|---|---|
| Windows source app | Kivy app and widget workflows checked |
| Windows packaged app | Latest all-pairs onedir build and bundled model/font/data hashes verified; runtime not verified because host Application Control blocked an earlier unsigned executable |
| Android | Not built or device-tested |
| iOS | Not built or device-tested; toolchain/signing requirements remain |
| Website | Local Flask app and shared-core tests; no public deployment |
