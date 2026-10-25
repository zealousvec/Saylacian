# Offline translation packs

Pack downloads are optional and begin only after you choose **Download** in Saylacian. Each pack is downloaded over HTTPS, checked against its pinned file sizes and SHA-256 hashes, staged, then activated. Progress and cancellation are available in the app. No model weights are included in this source checkout.

| Pack | Languages | Download size | Model licence |
|---|---|---:|---|
| French / English | English ↔ French | about 166 MiB | MIT |
| Somali / English | English ↔ Somali Latin | about 300 MiB | Apache-2.0 |
| Somali translation (experimental) | English → Somali | about 62 MiB | CC BY 4.0 |
| Somali detection (experimental) | Somali input detection | about 25 MiB | MIT model; GPL-3.0 training dataset |

Installed packs are stored in the user's application-data folder, outside the project checkout. Use **Offline language packs** to see installed packs, install updates, cancel downloads or remove a pack to reclaim storage. Updating creates a versioned install; old versions remain until removed, so an update can temporarily need extra disk space.

The Somali detection pack is optional. After download, it can recover Somali input that the existing detector leaves uncertain. It does not translate text, and the existing English/French results take precedence. Detection runs on device; its model and runtime dependencies are pinned and work offline after installation.

The optional English-to-Somali pack uses a separate CTranslate2 model. If installed, Saylacian tries it first for English-to-Somali and falls back to the standard Somali/English pack when its output appears copied, unreadable or repetitive. Keep the standard Somali/English pack installed as the fallback. This model has no published score in its model card and still needs fluent-speaker review.

On a verified, licensed Qor sample of 67 short Somali texts, the integrated detector identified 45; the existing short-text route identified 33. At the selected 0.90 Somali score threshold, the candidate produced no Somali predictions among 24,815 sampled MASSIVE test texts from other labeled locales. These dataset labels are proxies, not specialist-verified language judgments, and these samples do not establish general accuracy.

Translation packs work locally without a network connection, account, per-request fee or artificial daily quota. Translation quality is not guaranteed: Somali remains experimental and needs fluent-speaker review. See the [support matrix](SUPPORT_MATRIX.md).

The exact upstream repositories, revisions, hashes, sizes and licences are in `saylacian/core/data/model_manifest.json`, `saylacian/core/data/somali_model_manifest.json`, `saylacian/core/data/somali_synthetic_manifest.json` and `saylacian/core/data/somali_detection_manifest.json`. Model terms are separate from the Saylacian code licence; see [third-party notices](../THIRD_PARTY_NOTICES.md).
