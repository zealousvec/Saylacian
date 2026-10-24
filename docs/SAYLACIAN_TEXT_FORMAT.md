# Sharing Borama and Kaddare text

The output copy button offers three formats. These are deliberately distinct: a reading, a picture, and a lossless app interchange package.

| Option | Clipboard data | Works where | What survives |
|---|---|---|---|
| **Copy as Latin** | Ordinary Unicode Somali Latin | Any text editor, message app, or OS with text paste | Readable transliteration; original script glyph identities are not included |
| **Copy as Image** | PNG, Windows CF_DIB, plus descriptive Unicode text | Apps that accept pasted images; CF_DIB is the broad Windows bitmap path | Exact visible glyph appearance from Saylacian's bundled chart font; image is not editable text |
| **Copy as Saylacian Text** | Custom `Saylacian Text v1`, RTF, CF_HTML, and Unicode text fallback | Saylacian can always re-import the plain-text package; rich-text consumers may use RTF/HTML | Exact app chart code points and script identity in the package; formatted glyph run when the receiving app has the named font |

## Portable interchange text

The Unicode fallback is ASCII-only, so it remains legible even in software that knows nothing about Borama/Kaddare fonts. It begins with `SAYLACIAN-TEXT/1` and then one compact JSON object:

```text
SAYLACIAN-TEXT/1
{"format":"Saylacian Text","version":1,"script":"Borama","encoding":"saylacian-chart-pua-v1","text":"\\ue00a...","latin":"...","sha256":"..."}
```

`text` is JSON-escaped Unicode containing the exact Saylacian chart glyph code points. `script` selects Borama or Kaddare; `encoding` identifies this project's chart mapping (these are private-use code points, not an externally standardized Borama/Kaddare Unicode encoding); `latin` is a convenience reading; and `sha256` detects accidental changes to the encoded glyph text/script. The digest is an integrity check, not a signature or proof of authorship.

To restore it, copy the complete package including its first header line and paste into Saylacian's input. The app validates its version, script, code points, Latin reading, and digest, then replaces the package in the input with the original chart glyphs and selects Saylacian's bundled font. Package size is limited by the app's normal 4,000-character text limit. Unknown private-use characters and mixed Borama/Kaddare mappings are rejected rather than guessed.

## Rich-text portability limits

The RTF and CF_HTML clipboard formats include the same chart code points and name `Saylacian Borama Chart` or `Saylacian Kaddare Chart`, followed by a Latin reading. A font *name* is metadata; these formats do not embed the TTF. If the destination lacks the matching font, it can show missing/incorrect symbols even though the Unicode code points are present. Install/use the Saylacian chart font in that destination or use Copy as Image to preserve appearance. To recover editable original chart text, re-import the Saylacian Text package into Saylacian.

No promise is made that every application honors all clipboard formats. Windows consumers choose formats they support. Copy as Image supplies both PNG and standard device-independent bitmap; Copy as Saylacian Text publishes registered Windows custom text, Rich Text Format, HTML Format, and UnicodeText so a consumer can choose. Other platforms currently expose only the Copy as Latin fallback through Kivy's clipboard API.

Implementation: `saylacian/core/interchange.py` defines the format, validation, rich representations, and image renderer; `saylacian/core/clipboard_repr.py` assembles formats; `saylacian/core/windows_clipboard.py` publishes Win32 formats; `main.py` owns the menu and importer. `tools/test_windows_clipboard.ps1` exercises the real Windows clipboard and reads the data in a separate WinForms PowerShell process. The Saylacian Text path is then decoded from that external reader's actual Unicode clipboard read and checked against its expected script/Latin. This proves transport and package round-trip, not GUI paste behavior in every third-party editor. Evidence is preserved under `<USER_PROFILE>\Downloads\Saylacian-Safety-Backups\windows-clipboard-acceptance`.
