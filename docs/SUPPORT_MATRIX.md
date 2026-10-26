# Support matrix

Status describes current checked-in code and local resources, not a release-quality claim.

## Meaning translation

| Source | Target | Route | Status |
|---|---|---|---|
| English | French | Local model | Works offline; smoke-tested |
| French | English | Local model | Works offline; smoke-tested |
| English | Somali Latin | Standard multilingual OPUS pack, with an optional separately downloadable synthetic-model pack that is tried first and falls back on clearly degenerate output | Available; Somali output has not had fluent-speaker review |
| Somali Latin | English | Local multilingual model | Available; Somali input/output quality has not had fluent-speaker review |
| Somali Latin | French | Somali → English → French local models | Available through English; errors can compound across both steps |
| French | Somali Latin | French → English → Somali local models | Available through English; output may be awkward and has not had fluent-speaker review |

No other meaning-translation pairs are installed. Picker labels distinguish meaning translation from unavailable script mappings. An unavailable script cannot be selected as an active source/target route.

## Script conversion

| Conversion | Status | Limit |
|---|---|---|
| Somali Latin ↔ Osmanya | Mapping implemented | Orthography, ambiguous readings and community validation remain open |
| Somali Latin ↔ Borama | Partial chart-label mapping | Bundled font renders app output. Copy text creates a tagged package; untagged private-use characters are not guessed. Word spelling is not reviewed. |
| Somali Latin ↔ Kaddare | Partial chart-label mapping | Bundled font renders app output. Copy text creates a tagged package; untagged private-use characters are not guessed. Word spelling is not reviewed. |
| Borama / Kaddare clipboard | Windows publisher implements Saylacian Text, RTF, CF_HTML, image and Latin formats; payload fixtures and a guarded separate WinForms acceptance harness exist. The current HWND-owning publisher has not yet been exercised against a real external app. | Real clipboard delivery is unverified until the harness runs in a disposable VM with clipboard sharing disabled. Editable chart text needs a compatible font; exact round-trip uses tagged Saylacian Text. Other OSes support text and Latin; image clipboard is not implemented there. Untagged private-use characters are not guessed. |
| Old Nubian Coptic script → scholarly Latin | Limited table-based transliteration is implemented; listed characters are mapped and unlisted Coptic letters are preserved with a warning | Historical-language/script route only; not meaning translation or complete manuscript coverage. Conventions may differ. |
| Old Nubian scholarly Latin → Coptic script | Limited reverse transliteration with alternatives/warnings | Romanization can be ambiguous; specialist review is needed. |
| Modern Nubian varieties (including Nobiin, Kenzi/Mattokki, Dongolawi/Andaandi, Midob and others) | Unsupported; listed only as research targets | Each variety and writing convention needs separate evidence. Old Nubian mappings and a Coptic font do not establish modern Nubian support. |

Osmanya script conversion changes writing system; it does not translate meaning. The Old Nubian routes above also transliterate writing and do not translate meaning. No PUA or invented Unicode substitute is presented as a real alphabet.

## Language identification and platforms

Offline detection covers English, French and Somali Latin with confidence/short-text abstention. Osmanya is detected as a script. No broad independent accuracy benchmark exists.

| Platform | Status |
|---|---|
| Windows source app | Kivy app and widget workflows checked |
| Windows packaged app | Latest all-pairs onedir build and bundled model/font/data hashes verified; runtime not verified because host Application Control blocked an earlier unsigned executable |
| Android | Not built or device-tested |
| iOS | Not built or device-tested; toolchain/signing requirements remain |
| Website | Local Flask app and shared-core tests; no public deployment |
