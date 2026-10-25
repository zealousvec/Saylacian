# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests optional online translation providers and error handling."""

import json
import os
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from saylacian.core.online_translation import (
    ACCOUNT_ENV,
    MAX_RESPONSE_BYTES,
    MODEL,
    PROVIDER_ENV,
    SERVICE_TOKEN_ENV,
    SERVICE_URL_ENV,
    TOKEN_ENV,
    online_translation_enabled,
    selected_provider,
    translate_cloudflare,
    translate_self_hosted,
)
from saylacian.core.translation import translate_meaning


class _Response:
    def __init__(self, value):
        self.value = value
        self.requested_size = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        payload = json.dumps(self.value).encode("utf-8")
        self.requested_size = size
        return payload if size < 0 else payload[:size]


class OnlineTranslationTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_offline_is_default_and_online_is_explicit(self):
        self.assertFalse(online_translation_enabled())
        self.assertEqual(selected_provider(), "offline")
        os.environ[PROVIDER_ENV] = "auto"
        self.assertTrue(online_translation_enabled())

    def test_request_uses_open_m2m100_and_secure_environment_credentials(self):
        os.environ[ACCOUNT_ENV] = "account-123"
        os.environ[TOKEN_ENV] = "test-secret"
        requests = []

        @contextmanager
        def fake_open(request, timeout):
            requests.append((request, timeout))
            yield _Response({"success": True, "result": {"answer": "Subax wanaagsan"}})

        text, warnings = translate_cloudflare(
            "Good morning.", "English", "Somali Latin", opener=fake_open
        )
        request, timeout = requests[0]
        self.assertEqual(text, "Subax wanaagsan")
        self.assertIn(MODEL, request.full_url)
        self.assertEqual(request.get_header("Authorization"), "Bearer test-secret")
        self.assertEqual(
            json.loads(request.data),
            {
                "text": "Good morning.",
                "source_lang": "english",
                "target_lang": "somali",
            },
        )
        self.assertEqual(timeout, 45)
        self.assertTrue(any("sent to Cloudflare" in warning for warning in warnings))

    def test_missing_credentials_explains_setup_without_sending_request(self):
        with self.assertRaisesRegex(ValueError, "CLOUDFLARE_ACCOUNT_ID"):
            translate_cloudflare("Hello", "English", "French")

    def test_self_hosted_request_uses_https_token_and_text(self):
        os.environ[SERVICE_URL_ENV] = "https://saylacian.example/"
        os.environ[SERVICE_TOKEN_ENV] = "private-test-token"
        requests = []

        @contextmanager
        def fake_open(request, timeout):
            requests.append((request, timeout))
            yield _Response({"translation": "Bonjour", "warnings": []})

        text, warnings = translate_self_hosted(
            "Hello", "English", "French", opener=fake_open
        )
        request, timeout = requests[0]
        self.assertEqual(text, "Bonjour")
        self.assertEqual(request.full_url, "https://saylacian.example/translate")
        self.assertEqual(
            request.get_header("Authorization"), "Bearer private-test-token"
        )
        self.assertEqual(
            json.loads(request.data),
            {"text": "Hello", "source": "English", "target": "French"},
        )
        self.assertEqual(timeout, 90)
        self.assertTrue(any("self-hosted" in warning for warning in warnings))

    def test_provider_responses_are_bounded_and_must_be_json_objects(self):
        os.environ[ACCOUNT_ENV] = "account-123"
        os.environ[TOKEN_ENV] = "test-secret"
        os.environ[SERVICE_URL_ENV] = "https://saylacian.example"
        providers = (
            (
                translate_cloudflare,
                ("Hello", "English", "French"),
                "Cloudflare returned an invalid translation response",
            ),
            (
                translate_self_hosted,
                ("Hello", "English", "French"),
                "Self-hosted translation server returned invalid JSON",
            ),
        )

        for provider, arguments, invalid_message in providers:
            with self.subTest(provider=provider.__name__):
                oversized = _Response({"translation": "x" * MAX_RESPONSE_BYTES})

                @contextmanager
                def oversized_open(request, timeout, response=oversized):
                    yield response

                with self.assertRaisesRegex(ValueError, "1 MiB limit"):
                    provider(*arguments, opener=oversized_open)
                self.assertEqual(oversized.requested_size, MAX_RESPONSE_BYTES + 1)

                non_object = _Response(["not", "an", "object"])

                @contextmanager
                def non_object_open(request, timeout, response=non_object):
                    yield response

                with self.assertRaisesRegex(ValueError, invalid_message):
                    provider(*arguments, opener=non_object_open)

    def test_self_hosted_rejects_insecure_remote_endpoint(self):
        os.environ[SERVICE_URL_ENV] = "http://public.example"
        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            translate_self_hosted("Hello", "English", "French")

    def test_auto_prefers_configured_self_host_and_then_cloudflare(self):
        os.environ[PROVIDER_ENV] = "auto"
        os.environ[SERVICE_URL_ENV] = "https://saylacian.example"
        with (
            patch(
                "saylacian.core.translation.translate_self_hosted",
                return_value=("Bonjour", ("hosted",)),
            ) as hosted,
            patch("saylacian.core.translation.translate_cloudflare") as cloud,
        ):
            result = translate_meaning("Hello", "English", "French")
        hosted.assert_called_once_with("Hello", "English", "French")
        cloud.assert_not_called()
        self.assertEqual(result.text, "Bonjour")

    def test_auto_uses_cloudflare_when_self_hosted_fails(self):
        os.environ[PROVIDER_ENV] = "auto"
        os.environ[SERVICE_URL_ENV] = "https://saylacian.example"
        with (
            patch(
                "saylacian.core.translation.translate_self_hosted",
                side_effect=ValueError("hosted unavailable"),
            ),
            patch(
                "saylacian.core.translation.translate_cloudflare",
                return_value=("Bonjour", ("cloud",)),
            ),
        ):
            result = translate_meaning("Hello", "English", "French")
        self.assertEqual(result.text, "Bonjour")

    def test_translation_engine_uses_cloudflare(self):
        os.environ[PROVIDER_ENV] = "cloudflare"
        os.environ[ACCOUNT_ENV] = "account-123"
        os.environ[TOKEN_ENV] = "test-secret"
        with patch(
            "saylacian.core.translation.translate_cloudflare",
            return_value=("Subax wanaagsan", ("Cloudflare M2M100",)),
        ) as cloud:
            result = translate_meaning("Good morning.", "English", "Somali Latin")
        cloud.assert_called_once_with("Good morning.", "English", "Somali Latin")
        self.assertEqual(result.text, "Subax wanaagsan")

    def test_auto_falls_back_to_downloaded_models(self):
        os.environ[PROVIDER_ENV] = "auto"
        with (
            patch(
                "saylacian.core.translation.translate_cloudflare",
                side_effect=ValueError("cloud unavailable"),
            ),
            patch(
                "saylacian.core.translation.model_directory",
                side_effect=ValueError("No local model installed."),
            ),
            self.assertRaisesRegex(ValueError, "Downloaded-model fallback unavailable"),
        ):
            translate_meaning("Hello", "English", "French", model_root="missing")

    def test_offline_setting_skips_cloud_provider(self):
        os.environ[PROVIDER_ENV] = "offline"
        with (
            patch("saylacian.core.translation.translate_cloudflare") as cloud,
            self.assertRaises(ValueError),
        ):
            translate_meaning("Hello", "English", "French", model_root="missing")
        cloud.assert_not_called()

    def test_invalid_language_and_oversized_input_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "supports English"):
            translate_cloudflare("Hello", "Osmanya", "French")
        with self.assertRaisesRegex(ValueError, "4,000 characters"):
            translate_cloudflare("x" * 4001, "English", "French")


if __name__ == "__main__":
    unittest.main()
