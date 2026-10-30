# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cloudflare Workers AI client for the open M2M100 translation model."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.parse import quote
from urllib.parse import urlparse
from urllib.request import Request
from urllib.request import urlopen

LANGUAGE_CODES = {
    "English": "english",
    "French": "french",
    "Somali Latin": "somali",
}
PROVIDER_ENV = "SAYLACIAN_TRANSLATION_PROVIDER"
ACCOUNT_ENV = "CLOUDFLARE_ACCOUNT_ID"
TOKEN_ENV = "CLOUDFLARE_API_TOKEN"
SERVICE_URL_ENV = "SAYLACIAN_TRANSLATION_URL"
SERVICE_TOKEN_ENV = "SAYLACIAN_SERVICE_TOKEN"
API_ROOT = "https://api.cloudflare.com/client/v4/accounts"
MODEL = "@cf/meta/m2m100-1.2b"
MAX_TEXT_LENGTH = 4000
MAX_RESPONSE_BYTES = 1024 * 1024


def _read_json_response(response):
    """Read a bounded JSON response so a broken service cannot exhaust memory."""
    payload = response.read(MAX_RESPONSE_BYTES + 1)
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ValueError("Translation service response exceeded its 1 MiB limit.")
    return payload


def selected_provider():
    """Return offline by default, or an explicitly enabled online provider mode."""
    value = os.environ.get(PROVIDER_ENV, "offline").strip().casefold()
    if value not in {"auto", "selfhosted", "cloudflare", "offline"}:
        raise ValueError(
            "SAYLACIAN_TRANSLATION_PROVIDER must be auto, selfhosted, "
            "cloudflare or offline."
        )
    return value


def online_translation_enabled():
    return selected_provider() != "offline"


def online_provider_label():
    provider = selected_provider()
    if provider == "offline":
        return "Downloaded models"
    if provider == "cloudflare":
        return "Cloudflare M2M100 + downloaded models"
    if provider == "selfhosted" or os.environ.get(SERVICE_URL_ENV, "").strip():
        return "Self-hosted cloud models + downloaded fallback"
    return "Cloudflare M2M100 + downloaded models"


def translate_self_hosted(text, source, target, *, opener=None, timeout=90):
    """Call a Saylacian API running its open models on user-managed cloud compute."""
    if source not in LANGUAGE_CODES or target not in LANGUAGE_CODES:
        raise ValueError(
            "Self-hosted translation supports English, French and Somali Latin only."
        )
    if source == target:
        raise ValueError("Choose different source and target languages.")
    if not text.strip():
        return "", ()
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Maximum {MAX_TEXT_LENGTH:,} characters.")

    base_url = os.environ.get(SERVICE_URL_ENV, "").strip().rstrip("/")
    parsed = urlparse(base_url)
    if not base_url or parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise ValueError(
            "Self-hosted cloud translation needs SAYLACIAN_TRANSLATION_URL, "
            "for example https://your-server.example."
        )
    if parsed.scheme != "https" and parsed.hostname not in {
        "127.0.0.1",
        "localhost",
        "::1",
    }:
        raise ValueError("Self-hosted translation URL must use HTTPS.")

    payload = json.dumps(
        {
            "text": text,
            "source": source,
            "target": target,
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json", "User-Agent": "Saylacian/1.0"}
    token = os.environ.get(SERVICE_TOKEN_ENV, "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(
        f"{base_url}/translate", data=payload, headers=headers, method="POST"
    )
    try:
        with (opener or urlopen)(request, timeout=timeout) as response:
            result = json.loads(_read_json_response(response).decode("utf-8"))
            if not isinstance(result, dict):
                raise TypeError("JSON root must be an object.")
    except HTTPError as error:
        if error.code in (401, 403):
            raise ValueError(
                "Self-hosted translation rejected the configured token."
            ) from None
        if error.code in (429, 503):
            raise ValueError(
                "Self-hosted translation server is busy; retry shortly."
            ) from None
        raise ValueError(
            f"Self-hosted translation failed (HTTP {error.code})."
        ) from None
    except (URLError, TimeoutError, OSError) as error:
        reason = error.reason if isinstance(error, URLError) else error
        raise ValueError(
            f"Self-hosted translation server is unreachable: {reason}"
        ) from None
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError(
            "Self-hosted translation server returned invalid JSON."
        ) from None
    except TypeError:
        raise ValueError(
            "Self-hosted translation server returned invalid JSON."
        ) from None

    translated = result.get("translation")
    if not isinstance(translated, str) or not translated.strip():
        raise ValueError(
            result.get("error", "Self-hosted translation returned empty text.")
        )
    warnings = result.get("warnings", [])
    if not isinstance(warnings, list) or not all(
        isinstance(item, str) for item in warnings
    ):
        warnings = []
    warnings = [
        "Text was sent to the Saylacian self-hosted translation server.",
        *warnings,
    ]
    return translated.strip(), tuple(warnings)


def translate_cloudflare(text, source, target, *, opener=None, timeout=45):
    """Call Cloudflare-hosted Meta M2M100. Credentials come only from environment."""
    if source not in LANGUAGE_CODES or target not in LANGUAGE_CODES:
        raise ValueError(
            "Cloud translation supports English, French and Somali Latin only."
        )
    if source == target:
        raise ValueError("Choose different source and target languages.")
    if not text.strip():
        return "", ()
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Maximum {MAX_TEXT_LENGTH:,} characters.")

    account = os.environ.get(ACCOUNT_ENV, "").strip()
    token = os.environ.get(TOKEN_ENV, "").strip()
    if not account or not token:
        raise ValueError(
            "Cloud translation needs CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN. "
            "Set up a free Cloudflare Workers AI account; no paid plan is required "
            "within its daily free allowance."
        )

    endpoint = f"{API_ROOT}/{quote(account, safe='')}/ai/run/{quote(MODEL, safe='@/-')}"
    payload = json.dumps(
        {
            "text": text,
            "source_lang": LANGUAGE_CODES[source],
            "target_lang": LANGUAGE_CODES[target],
        }
    ).encode("utf-8")
    request = Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Saylacian/1.0",
        },
        method="POST",
    )
    try:
        with (opener or urlopen)(request, timeout=timeout) as response:
            result = json.loads(_read_json_response(response).decode("utf-8"))
            if not isinstance(result, dict):
                raise TypeError("JSON root must be an object.")
    except HTTPError as error:
        if error.code == 429:
            raise ValueError(
                "Cloudflare free daily AI allowance is used up or service is busy. "
                "Try after reset, or switch to downloaded models."
            ) from None
        if error.code in (401, 403):
            raise ValueError(
                "Cloudflare rejected credentials or model access; check account ID, "
                "API token permissions and free-plan access."
            ) from None
        raise ValueError(
            f"Cloudflare translation failed (HTTP {error.code})."
        ) from None
    except (URLError, TimeoutError, OSError) as error:
        reason = error.reason if isinstance(error, URLError) else error
        raise ValueError(f"Cloudflare translation is unreachable: {reason}") from None
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError(
            "Cloudflare returned an invalid translation response."
        ) from None
    except TypeError:
        raise ValueError(
            "Cloudflare returned an invalid translation response."
        ) from None

    if result.get("success") is False:
        errors = result.get("errors") or []
        code = errors[0].get("code") if errors and isinstance(errors[0], dict) else None
        if code == 3036:
            raise ValueError(
                "Cloudflare free daily AI allowance is used up. Try after reset."
            )
        raise ValueError(
            "Cloudflare could not translate this text; check model access."
        )
    translated = (result.get("result") or {}).get("answer")
    if not isinstance(translated, str) or not translated.strip():
        raise ValueError("Cloudflare returned an empty translation.")

    warnings = [
        "Cloudflare Workers AI used open Meta M2M100; text was sent to Cloudflare.",
        "Somali translation quality varies; fluent-speaker review recommended.",
        (
            "Free Workers AI allowance: 10,000 neurons per day; excess "
            "requests fail unless account is upgraded."
        ),
    ]
    return translated.strip(), tuple(warnings)
