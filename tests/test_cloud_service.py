# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify bounded, authenticated behavior of the local translation API."""

import json
import os
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from cloud.oci import service
from saylacian.core.online_translation import (
    SERVICE_TOKEN_ENV,
    SERVICE_URL_ENV,
    translate_self_hosted,
)


class QuietTranslationHandler(service.TranslationHandler):
    def log_message(self, format_string, *args):
        pass


class CloudTranslationServiceTests(unittest.TestCase):
    def setUp(self):
        self.token = patch.object(service, "SERVICE_TOKEN", "test-service-token")
        self.token.start()
        self.addCleanup(self.token.stop)
        self.server = service.TranslationServer(
            ("127.0.0.1", 0), QuietTranslationHandler
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._close_server)
        self.url = f"http://127.0.0.1:{self.server.server_port}/translate"

    def _close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def _request(self, token=None):
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        return Request(
            self.url,
            data=json.dumps(
                {"text": "Hello", "source": "English", "target": "French"}
            ).encode("utf-8"),
            headers=headers,
            method="POST",
        )

    def test_unauthorized_request_never_runs_translation(self):
        with (
            patch.object(service, "translate_meaning") as translate,
            self.assertRaises(HTTPError) as response,
        ):
            urlopen(self._request(), timeout=3)

        self.assertEqual(response.exception.code, 401)
        translate.assert_not_called()

    def test_memory_failure_returns_retryable_response_and_releases_slot(self):
        with (
            patch.dict(
                os.environ,
                {
                    SERVICE_URL_ENV: f"http://127.0.0.1:{self.server.server_port}",
                    SERVICE_TOKEN_ENV: "test-service-token",
                },
            ),
            patch.object(service, "translate_meaning", side_effect=MemoryError),
            self.assertRaisesRegex(ValueError, "server is busy"),
        ):
            translate_self_hosted("Hello", "English", "French", timeout=3)

        acquired = []
        try:
            for _ in range(service.MAX_CONCURRENT_TRANSLATIONS):
                acquired.append(service._translation_slots.acquire(blocking=False))
            self.assertTrue(all(acquired))
        finally:
            for success in acquired:
                if success:
                    service._translation_slots.release()


if __name__ == "__main__":
    unittest.main()
