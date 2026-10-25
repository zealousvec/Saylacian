# Offline translation packs

Pack downloads are optional and begin only after you choose **Download** in Saylacian. Each pack is downloaded over HTTPS, checked against its pinned file sizes and SHA-256 hashes, staged, then activated. Progress and cancellation are available in the app. No model weights are included in this source checkout.

| Pack | Languages | Download size | Model licence |
|---|---|---:|---|
| French / English | English ↔ French | about 166 MiB | MIT |
| Somali / English | English ↔ Somali Latin | about 300 MiB | Apache-2.0 |

Installed packs are stored in the user's application-data folder, outside the project checkout. Use **Offline language packs** to see installed packs, install updates, cancel downloads or remove a pack to reclaim storage. Updating creates a versioned install; old versions remain until removed, so an update can temporarily need extra disk space.

After installation, translations run locally without a network connection, account, per-request fee or artificial daily quota. Translation quality is not guaranteed: Somali remains experimental and needs fluent-speaker review. See the [support matrix](SUPPORT_MATRIX.md).

The exact upstream repositories, revisions, hashes, sizes and licences are in `saylacian/core/data/model_manifest.json` and `saylacian/core/data/somali_model_manifest.json`. Model terms are separate from the Saylacian code licence; see [third-party notices](../THIRD_PARTY_NOTICES.md).
