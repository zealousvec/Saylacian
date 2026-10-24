# Offline translation packs

Saylacian's model-pack manager downloads only after the user chooses **Download** in the app. Packs are installed under the platform's per-user application-data directory (or the directory named by `SAYLACIAN_PACKS_DIR`). It does not require PowerShell activation, a paid service, a user account, or a network connection after installation.

## Available packs

| Pack | Directions | Download size | Model licence | Runtime |
|---|---|---:|---|---|
| Somali / English | English↔Somali Latin | 314,460,609 bytes (~300 MiB) | Apache-2.0 | CTranslate2 4.8.3, SentencePiece 0.2.2 |
| French / English | English↔French | 174,530,568 bytes (~166 MiB) | MIT | CTranslate2 4.8.3, SentencePiece 0.2.2 |

Model repository, exact revision, file size, SHA-256, licence, and runtime pins are recorded in `saylacian/core/data/model_manifest.json` and `somali_model_manifest.json`. The app builds each pack's version from the canonical metadata and asset manifest. Installed `installed.json` records the installed files and their hashes and provenance.

## Safety and storage behavior

- HTTPS sources are restricted to Hugging Face and the pinned GitHub raw-content host.
- Each file's byte count and SHA-256 are checked before it becomes active. Argos archives are additionally checked against their pinned archive hash before extracting only required files.
- Files are staged under a temporary version directory; a `current.json` pointer is switched only after installation succeeds. An interrupted or invalid download cannot become the active pack.
- Progress and cancellation are supported by the manager. The app offers removal; no pack is fetched automatically at startup.
- Installing a newer manifest version creates a new version directory and switches the active pointer. Old versions remain until the user removes that pack, so an update may temporarily need extra free space.
- Pack content is outside the Git repository; the regular source checkout contains manifests, downloader, tests and small configuration only.

## Reproduce pack installation

From PowerShell, run the app and select **Offline language packs**, or use this Python snippet after installing the runtime requirements:

```python
from saylacian.core.model_packs import ModelPackManager

manager = ModelPackManager()
for pack in manager.list_packs():
    print(pack["title"], pack["download_bytes"], pack["license"], pack["version"])

# Explicit opt-in; downloads the chosen full pack and verifies every asset.
manager.install("french", progress=lambda done, total, label: print(done, total, label))
```

Translation can then be explicitly run offline with `translate_meaning(..., provider_override="offline")`. The existing feature remains offline-first; optional providers are documented separately in [ONLINE_TRANSLATION.md](ONLINE_TRANSLATION.md).

Windows full-pack validation downloaded and installed both packs from their pinned HTTPS sources, verified their hashes, then translated English↔Somali and English↔French while selecting the offline provider. The validation downloads were temporary and removed after successful checks. Android/iOS remain unbuilt; see [MOBILE_RUNTIME_STATUS.md](MOBILE_RUNTIME_STATUS.md).
