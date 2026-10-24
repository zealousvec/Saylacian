# UI copy register

This register tracks visible wording reviewed against the master directive. The UI itself remains the approved black-and-white Kivy design. A complete string inventory is still in progress; rows below record this session's pass, not a claim that every app or website string has been reviewed.

| Surface | Previous wording/state | Current wording/state | Reason/status |
|---|---|---|---|
| Home route selector | Internal route labels such as `Somali Latin`, `Old Nubian (Coptic)` and `Old Nubian scholarly Latin` | `Somali`, `Old Nubian`, `Latin reading`; internal route IDs unchanged | Shorter display labels; implementing, live-tested |
| Translation picker | Mixed script, language and research-only varieties in one list | Only routes for active mode; modern Nubian unavailable routes hidden | Avoid unsupported or nonsensical choices; live-tested |
| Script picker note | `Downloaded models: ...` / internal status strings | Short notes such as `Latin script`, `Somali script`, `Limited conversion` | Avoid implementation jargon in primary flow; needs full copy audit |
| Borama/Kaddare copy menu | `Copy as Latin`, `Copy as Image`, `Copy as Saylacian Text` | `Copy text`, `Copy image`, `Copy Latin` | Matches owner's three requested actions; live Kivy acceptance checked payloads |
| Untagged private-use text | Guessed Borama/Kaddare from code point alone | `This text has no script label. Paste a Saylacian Text package or choose Borama/Kaddare as source.` | Prevent unrelated PUA mappings being silently misread |
| Model progress | `Preparing verified model download...`; `Translating with downloaded model...`; checksum detail after success | `Preparing download...`; `Translating...`; `Pack installed: ...` | Keep routine progress natural; integrity errors remain explicit |
| Chart reference | Repeated experimental/chart-label terminology and PUA explanation | `Limited letter conversion. Word spelling has not been reviewed. Copied text may need the Saylacian font.` | State material limitation in plain language |
| Chart conversion status | Two separate technical warnings plus “Writing converted; meaning unchanged.” | `Limited conversion; word spelling is unreviewed. May need Saylacian font outside this app.` plus any specific unmapped-character warning | Keep important limitation while avoiding clipped/repeated status copy |
| Osmanya reference | “The mapping is experimental” and “Community validation pending” | “W/uu and y/ii share letters, so reverse readings can differ”; “Somali-speaker review is still needed.” | Explain concrete reversal limit and review status plainly |
| Offline pack screen | `Download once. Translate on this device with no account, quota or internet.` | `Download packs once, then translate on this device without internet.` | Remove inflated/repetitive claims and keep accurate offline behavior |

## Remaining inventory

Review all visible strings in `main.py`, `app/main.kv`, `saylacian/core/`, dialogs, history, settings, pack errors, `saylacian/website/templates/`, README, support pages and release notes. Keep exact before/after notes for any changes. Do not remove limitation statements; move technical detail into focused docs when that keeps the main flow clear. Repository description/topics changes require owner approval.
