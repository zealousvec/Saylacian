# Project code licence and third-party scope

The root `LICENSE` contains the complete, unmodified GNU AGPL version 3 text. The project licensor approved AGPL-3.0-or-later for Saylacian-authored code they own or have the right to license.

## Ownership and contribution audit

All 62 AGPL-marked source/config files were included: 51 Python files, 2 Kivy files, 3 web files, and 6 workflow/packaging/deployment files. Searched for copyright and licence headers, contributor/source references, URLs, and “copied from” / “adapted from” markers. No third-party source-code snippets or unlicensed external implementations were identified. The only source copyright marker is the font metadata emitted by `tools/build_chart_fonts.py`, which attributes the chart-derived PUA fonts to Jugydmort; those generated fonts and chart-label data are explicitly CC BY-SA 4.0 in the separate chart notice. CI references external GitHub Actions but vendors no action code. Dependencies and model weights are not vendored source. At audit time there was no pre-existing Git history or contributor registry, so the scan could not prove every line's history; no specific third-party implementation or contributor exception was identified. The owner's licence grant remains limited to code they own or have the right to license.

The project code licence does not relicense third-party code, fonts, charts, chart-derived mappings/fonts, datasets, or downloaded model weights. In particular, Creative Commons lists GPLv3 (one-way) as compatible with adaptations of CC BY-SA 4.0, but does not list AGPL; Borama/Kaddare chart-derived assets therefore remain separately marked CC BY-SA 4.0. Noto fonts retain SIL OFL 1.1; TICO rows retain CC0 context plus their source URL and source-material licence; downloaded model weights retain their manifest-declared licences; dependencies retain their upstream terms. See `THIRD_PARTY_NOTICES.md`.

Official AGPL text: https://www.gnu.org/licenses/agpl-3.0.txt.
