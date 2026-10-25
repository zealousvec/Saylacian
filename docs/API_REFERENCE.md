# Saylacian API reference

## Contents

- [Python core](#python-core)
- [Optional self-hosted HTTP API](#optional-self-hosted-http-api)
- [Clipboard interchange](#clipboard-interchange)
- [Operational limits](#operational-limits)

Saylacian does not currently operate a public translation API. The desktop app uses the local Python core. The HTTP service described below is an optional, self-hosted deployment; it is not needed by the app and has no project-hosted capacity or availability promise.

## Python core

Run from a source checkout with the dependencies installed. These functions are code-level integration points, not a separately versioned stable SDK.

```python
from saylacian.core.capabilities import list_capabilities
from saylacian.core.interchange import decode_saylacian_text, encode_saylacian_text
from saylacian.core.transliteration import transliterate
from saylacian.core.translation import translate_meaning

routes = list_capabilities(mode="transliteration")
result = transliterate("hello!", "Somali Latin", "Borama")
package = encode_saylacian_text(result.text, "Borama")
restored = decode_saylacian_text(package)
translation = translate_meaning("Hello.", "English", "French")
```

- `list_capabilities(mode=None)` returns implemented routes and their declared status. It does not certify language quality.
- `transliterate(text, source, target)` returns a `Conversion` with `text`, `warnings`, and optional `alternatives`.
- `translate_meaning(text, source, target, model_root=None, *, provider_override=None)` returns a `Conversion`. Offline translation needs the matching installed model files and runtime dependencies.
- `encode_saylacian_text(text, script)` creates a validated ASCII envelope for Borama or Kaddare chart text.
- `decode_saylacian_text(value)` returns a `SaylacianText` record for a supported envelope, `None` for ordinary text, and raises `ValueError` for an invalid or unsupported package.

Route coverage, model status, font behavior and research limits are listed in the [support matrix](SUPPORT_MATRIX.md). Treat Somali, Osmanya, Borama, Kaddare and reverse Old Nubian results as experimental or limited where indicated.

## Optional self-hosted HTTP API

The service in `cloud/oci/service.py` provides two endpoints. It runs local models on the operator's server. It does not use a third-party translation quota, but the operator supplies and pays for the server, storage, network, and model downloads. The repository does not promise unlimited server capacity.

### `GET /health`

Returns `200` with a small JSON health response.

```json
{"ok": true, "provider": "Saylacian self-hosted models"}
```

### `POST /translate`

Send UTF-8 JSON. The service returns translated text and any warnings.

```http
POST /translate HTTP/1.1
Content-Type: application/json
Authorization: Bearer YOUR_SERVER_TOKEN
```

```json
{"text":"Hello.","source":"English","target":"French"}
```

Example response:

```json
{"translation":"Bonjour.","warnings":[],"provider":"Saylacian self-hosted models"}
```

The `Authorization` header is required when the server is configured with `SAYLACIAN_SERVICE_TOKEN`; deployment refuses to start without a token. Do not expose the service over an untrusted network without HTTPS and a strong secret. Follow [self-hosted deployment guidance](../cloud/oci/DEPLOY.md).

## Clipboard interchange

Saylacian Text v1 is a portable ASCII envelope for the current experimental Borama/Kaddare mapping. It preserves the app's private-use character sequence and script label so Saylacian can restore them. It is not a public Unicode assignment and does not guarantee glyph rendering in third-party apps. The clipboard's RTF/HTML formats also require a compatible font and an app that accepts those formats. See [the user guide](USER_GUIDE.md) and [interoperability details](SOMALI_SCRIPT_INTEROPERABILITY.md).

## Operational limits

The self-hosted service accepts at most 4,000 characters per translation and a 20,000-byte request body. Two translations may run at once; requests that cannot obtain a slot within 45 seconds receive `503`. These are implementation limits, not quotas imposed on the local desktop app. The desktop app can translate offline without contacting this service when its local packs are installed.
