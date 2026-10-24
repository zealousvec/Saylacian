# UI copy register

Visible wording reviewed across the approved Kivy screens, dialogs, picker, history, alphabet reference, optional website, README, contribution/security guidance, and GitHub release documents. The black-and-white Kivy layout and interaction remain unchanged. Technical limitations stay explicit; implementation details stay in documentation.

| Surface | Previous wording/state | Current wording/state | Reason/status |
|---|---|---|---|
| Home route selector | Internal route labels such as `Somali Latin`, `Old Nubian (Coptic)` and `Old Nubian scholarly Latin` | `Somali`, `Old Nubian`, `Latin reading`; internal route IDs unchanged | Shorter display labels; implementing, live-tested |
| Detection picker | `Detect language/script` with the same language-only note in both modes | `Detect`; note changes by mode (`English, French or Somali` / `Languages and writing systems`) | Shorter and accurate for the active route; verified in picker tests and live Kivy acceptance |
| Translation picker | Mixed script, language and research-only varieties in one list | Only routes for active mode; modern Nubian unavailable routes hidden | Avoid unsupported or nonsensical choices; live-tested |
| Script picker note | `Downloaded models: ...` / internal status strings | Short notes such as `Latin script`, `Somali script`, `Limited conversion` | Avoid implementation jargon in primary flow; needs full copy audit |
| Borama/Kaddare copy menu | `Copy as Latin`, `Copy as Image`, `Copy as Saylacian Text` | `Copy text`, `Copy image`, `Copy Latin` | Matches owner's three requested actions; live Kivy acceptance checked payloads |
| Untagged private-use text | Guessed Borama/Kaddare from code point alone | `This text has no script label. Paste a Saylacian Text package or choose Borama/Kaddare as source.` | Prevent unrelated PUA mappings being silently misread |
| Model progress | `Preparing verified model download...`; `Translating with downloaded model...`; checksum detail after success | `Preparing download...`; `Translating...`; `Pack installed: ...` | Keep routine progress natural; integrity errors remain explicit |
| Chart reference | Repeated experimental/chart-label terminology and PUA explanation | `Limited letter conversion. Word spelling has not been reviewed. Copied text may need the Saylacian font.` | State material limitation in plain language |
| Chart conversion status | Two separate technical warnings plus “Writing converted; meaning unchanged.” | `Limited conversion; word spelling is unreviewed. May need Saylacian font outside this app.` plus any specific unmapped-character warning | Keep important limitation while avoiding clipped/repeated status copy |
| Osmanya reference | “The mapping is experimental” and “Community validation pending” | “W/uu and y/ii share letters, so reverse readings can differ”; “Somali-speaker review is still needed.” | Explain concrete reversal limit and review status plainly |
| Offline pack screen | `Download once. Translate on this device with no account, quota or internet.` | `Download packs once, then translate on this device without internet.` | Accurate offline behavior; no quota claim |
| Pack status and storage | Internal version digest, generic installed message, and retained-version explanation | `Installed · [size] on device`; `[pack] is ready to use offline.`; `Using [size]. Remove a pack to free storage.` | Hide internal version identifier and shorten routine status |
| Pack removal dialog | Long explanation about storage, app and backups | `Remove [pack] and its downloaded files?` | State the action clearly |
| History screen | `Local history / favourites` | `History & favourites` | Replace slash label with natural wording |
| Saved confirmation | Technical `History > Clear saved` navigation | `Favourite saved on this device. Use Clear saved to remove it.` | Keep confirmation short and actionable |
| Old Nubian detection | `Coptic script detected; language is not inferred.` | `Coptic-derived writing detected; language is unknown.` | State script/language distinction in plain language |
| Website result/alphabet copy | Fixed `Experimental.` prefix and `Current experimental mapping` | Show actual warnings; explain alternate readings and ask for Somali-speaker review | Avoid repeated label while keeping quality and review status visible |
| Website coverage/privacy | Long unsupported/complete-support phrasing | Describe limited transliteration, experimental reverse, unimplemented modern varieties, and server handling directly | Keep genuine coverage and privacy limits visible |
| GitHub status documents | Empty-repository and pre-publication wording after public source release | Updated to distinguish the published source alpha from owner-controlled settings and future releases | Remove stale public-repo state |
| KivyMD warning | 1.2.0 startup deprecation notice | Document current pin and low-risk isolated 2.0.0 migration gate | No framework upgrade or UI redesign |

## Remaining

Audit new visible strings whenever UI functionality changes. Do not remove limitation statements; keep detailed explanation in focused docs. Repository description, topics and security settings remain owner-controlled.
