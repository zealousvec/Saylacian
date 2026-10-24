# Dependency and model inventory

No Python runtime package was added for this functionality pass. The application keeps its existing pinned Kivy/KivyMD, CTranslate2, SentencePiece, and py3langid dependencies. Offline model artefacts and their pinned sources/hashes are listed in `models/manifest.json` and `models/somali-manifest.json`; language-model use is licensed/provenanced separately from the Python runtime.

## Bundled fonts

- `assets/NotoSansOsmanya.ttf` and `assets/OFL-Osmanya.txt`: existing Noto Project font, SIL OFL 1.1.
- `assets/NotoSansCoptic-Regular.ttf` and `assets/OFL-Coptic.txt`: Noto Sans Coptic from the official Noto Coptic project; SIL OFL 1.1. Used to render Old Nubian's Coptic-derived script. Font cmap coverage for the route's codepoints is tested locally.
- `assets/research/Borama_Alphabet_Chart.jpg` and `Kaddare_Alphabet_Chart.jpg` are by Jugydmort under CC BY-SA 4.0. Related chart-derived mapping data and display fonts are adaptations under CC BY-SA 4.0; attribution, hashes, and modifications are in `notices/HISTORICAL_SCRIPT_CHARTS.md`. These mappings are experimental and do not establish word-level orthography.

Sources: [Noto Coptic repository/license](https://github.com/notofonts/coptic), [Noto Coptic font proof](https://notofonts.github.io/coptic/).

## Offline boundary

Translation functions do not call web APIs or download models at runtime. Pack downloads are explicit user actions; after installation, model inference and transliteration use local files. Tests patch `socket.socket.connect` to fail if a network connection is attempted.

## Measured on this development PC

On the development Windows host, `tools/benchmark_translation.py` completed 10 examples per direction/route with network connections blocked. Mean CPU wall times: English→French 62 ms, French→English 50 ms, English→Somali 136 ms, Somali→English 114 ms, Somali→French pivot 92 ms, and French→Somali pivot 112 ms. The pivot run can appear faster because the per-process model cache was already warm. Peak process working set during the full run was 679,718,912 bytes (initial process: 26,812,416 bytes); this includes Python, runtime and loaded models. The complete `models/` directory occupied 681,479,977 bytes (about 650 MiB), including archived packages and extracted runtime files. These are measurements of this run and machine, not minimum requirements or universal performance claims. Raw 60-sample outputs/timings are in `docs/translation-benchmark.json`.
