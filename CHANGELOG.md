# Changelog

Changes are recorded after local verification. The source is in alpha testing; no tagged binary release is published.

## Unreleased

- Prefer the standard EN→SO pack over incidental local synthetic weights; retain
  explicit experimental opt-in and standard fallbacks.
- Add numeric-format and source-negation review cues without replacing text;
  avoid rejecting source-supplied overlapping names as prefix corruption.
- Recognize existing Coptic mappings such as ϣ/Ϣ during script detection without
  inferring Old Nubian or another language.

- Corrected the Borama Q chart mapping while retaining legacy copied-text decoding.
- Added bounded Osmanya alternative readings and exposed Old Nubian routes and
  alternative readings on the local website.
- Added Old Nubian digraph warnings without selecting a pronunciation.
- Published the independent Python runner, PowerShell commands and corrected
  M2M100 evaluation direction handling. Research weights remain private and the
  production translation models are unchanged.
- Initialized display scaling before canvas rules and isolated hardware input
  hooks during hidden self-tests. Windows binary execution and distribution
  checks remain open; see [alpha status](docs/ALPHA_COMPLETION_2026-11-07.md).

## 0.1.0a1 — alpha testing (2026-10-30)

- Kept meaning translation local-first, free of daily quotas, and optional online providers nonessential.
- Preserved the English-to-Somali output safeguard and made route labels clear for alpha testing.
- Replaced the Old Nubian letter table with the 29 entries in a CC BY 4.0 scholarly source and added attribution.
- Added offline pack manifest metadata for model licence, upstream repository, runtime versions, and integrity-derived version IDs.
- Added Windows CI for Python syntax, repository credential-pattern scanning, and tests without downloading offline translation packs.
- Added a pinned portable Windows ZIP build recipe with a file manifest and SHA-256 checksums. Runtime verification on a clean Windows host remains outstanding.
- Added release documentation and kept weights, generated build output, caches, and editor settings out of the repository candidate.

## Unreleased release-candidate corrections

- Corrected the portable setup note to distinguish offline translation packs from the bundled language-identification model.
- Included the active CPython licence and exact SDL2 wheel notices in portable builds.
- Corrected Pillow's licence label and added the GLEW 2.3.1 upstream notice; binary provenance and Intel runtime redistribution checks remain release gates.
