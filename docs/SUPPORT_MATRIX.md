# Support matrix

Status describes current checked-in code and local resources, not a release-quality claim.

## Meaning translation

| Source | Target | Route | Status |
|---|---|---|---|
| English | French | Local model | Works offline; smoke-tested |
| French | English | Local model | Works offline; smoke-tested |
| English | Somali Latin | Optional AfriSLM 0.8B pack when installed; otherwise the standard offline route | Alpha testing; fluent-speaker review is still needed |
| Somali Latin | English | Optional AfriSLM 4B pack when installed, then 2B, then 0.8B, then standard offline route | Alpha testing; 4B pack is about 2.86 GiB and used about 5 GB working memory in one test; fluent-speaker review is still needed |
| Somali Latin | French | Somali → English → French local models | Alpha testing; pivot errors can compound |
| French | Somali Latin | French → English → Somali local models | Alpha testing; output needs fluent review |

No other meaning-translation pairs are installed. Picker labels distinguish alpha language models from unavailable script mappings. An unavailable script cannot be selected as an active source/target route.

## Script conversion

| Conversion | Status | Limit |
|---|---|---|
| Somali Latin ↔ Osmanya | Character mapping implemented for listed Somali Latin forms | Orthography, ambiguous readings and community validation remain open |
| Somali Latin ↔ Borama | Partial chart-label mapping | Bundled font renders app output. Copy text creates a tagged package; untagged private-use characters are not guessed. Word spelling is not reviewed. |
| Somali Latin ↔ Kaddare | Partial chart-label mapping | Bundled font renders app output. Copy text creates a tagged package; untagged private-use characters are not guessed. Word spelling is not reviewed. |
| Borama / Kaddare clipboard | Windows publisher implements Saylacian Text, RTF, CF_HTML, image and Latin formats; payload fixtures and a guarded separate WinForms acceptance harness exist. The current HWND-owning publisher has not yet been exercised against a real external app. | Real clipboard delivery is unverified until the harness runs in a disposable VM with clipboard sharing disabled. Editable chart text needs a compatible font; exact round-trip uses tagged Saylacian Text. Other OSes support text and Latin; image clipboard is not implemented there. Untagged private-use characters are not guessed. |
| Old Nubian Coptic script → scholarly Latin | Limited table-based transliteration is implemented; listed characters are mapped and unlisted Coptic letters are preserved with a warning | Historical-language/script route only; not meaning translation or complete manuscript coverage. Conventions may differ. |
| Old Nubian scholarly Latin → Coptic script | Reverse character transliteration with alternative letter-boundary parses | Romanization can be ambiguous; alternatives are not validated manuscript readings. |
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
