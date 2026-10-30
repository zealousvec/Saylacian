# Optional online translation

Saylacian's primary translation path is local inference using installed offline packs. Online providers are optional enhancements only. If no pack is installed, remote translation is not silently enabled: install a pack or explicitly configure an online provider. Local translation never consumes a cloud request allowance.

## Self-hosted service

The optional CTranslate2 service can be deployed from [`cloud/oci`](../cloud/oci/DEPLOY.md). The service has finite CPU, memory, and concurrency; its capacity depends on the host. A free-tier virtual machine is suitable only for a small experiment, not a guarantee of unlimited service. Users do not pay per translation through Saylacian, but the server operator remains responsible for hosting costs, availability, abuse protection, and scaling.

Set the service URL and token only if you operate or trust that service:

```powershell
$env:SAYLACIAN_TRANSLATION_URL = "https://your-domain.example"
$env:SAYLACIAN_SERVICE_TOKEN = Read-Host "Saylacian server token"
$env:SAYLACIAN_TRANSLATION_PROVIDER = "selfhosted"
.\.venv\Scripts\python.exe main.py
```

Never embed a shared server token in a public app release. Anyone who extracts it can use the service. A public deployment needs an authentication and abuse-control design appropriate to its users.

## Explicit provider selection

The default provider is `offline`; users can change it to `auto`, `selfhosted`, or `cloudflare` through `SAYLACIAN_TRANSLATION_PROVIDER`. Online services may have their own quotas, capacity limits, privacy terms, or costs. Saylacian does not promise unlimited online capacity, and the application remains usable through installed local packs when an online service is unavailable.

For data privacy, remote translation sends the entered text to the selected service. Do not send sensitive text unless you trust that provider and have reviewed its current terms. Cloud credentials must be supplied by the operator in the process environment; no credentials are bundled in the source.

## Somali quality

Current downloadable Somali packs use multilingual OPUS checkpoints. They are free to run locally after download, but “free” does not imply that every translation is accurate. The current TICO-19 benchmark is a 150-pair health-domain sample and automatic BLEU/chrF scores, not fluent-speaker approval. The synthetic EN-to-Somali candidate is a local experiment and is not distributed in downloadable packs. See [the Somali translation quality report](SOMALI_TRANSLATION_QUALITY.md) and the model manifests for reproducible evidence and limitations. Raw benchmark predictions remain in local app data and are not part of the repository.
