# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests the Saylacian website routes and request handling."""

import os
import unittest
from unittest.mock import patch

from saylacian.core.translation import model_directory
from saylacian.website.app import create_app


def _has_local_route(source, target):
    try:
        model_directory(source, target)
    except ValueError:
        return False
    return True


class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.provider = patch.dict(
            os.environ, {"SAYLACIAN_TRANSLATION_PROVIDER": "offline"}
        )
        self.provider.start()
        self.addCleanup(self.provider.stop)
        self.client = create_app().test_client()

    def test_home(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Content-Security-Policy", str(r.headers).encode())
        self.assertIn(b"Saylacian", r.data)

    def test_core_conversion(self):
        r = self.client.post(
            "/process",
            json=dict(text="dhagax!", source="Somali Latin", target="Osmanya"),
        )
        self.assertEqual(r.json["text"], "𐒊𐒖𐒌𐒖𐒄!")

    @unittest.skipUnless(
        _has_local_route("Somali Latin", "English"),
        "Somali offline pack is not installed",
    )
    def test_somali_english_meaning_api_offline(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            response = self.client.post(
                "/process",
                json=dict(
                    text="Salaan, sidee tahay?",
                    source="Somali Latin",
                    target="English",
                    mode="meaning",
                ),
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["text"], "How are you?")

    @unittest.skipUnless(
        _has_local_route("Somali Latin", "English"),
        "Somali offline pack is not installed",
    )
    def test_auto_detect_somali_meaning_api_offline(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            response = self.client.post(
                "/process",
                json=dict(
                    text="Salaan, sidee tahay?",
                    source="Detect language/script",
                    target="English",
                    mode="meaning",
                ),
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn("How are you?", response.json["text"])
        self.assertIn("Detected Somali Latin", response.json["warnings"][0])

    @unittest.skipUnless(
        _has_local_route("Somali Latin", "French"),
        "Somali/French offline packs are not installed",
    )
    def test_somali_french_pivot_api_offline(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            response = self.client.post(
                "/process",
                json=dict(
                    text="Salaan, sidee tahay?",
                    source="Somali Latin",
                    target="French",
                    mode="meaning",
                ),
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["text"], "Comment allez-vous ?")
        self.assertTrue(
            any("errors may compound" in w for w in response.json["warnings"])
        )

    def test_unsupported(self):
        r = self.client.post(
            "/process", json=dict(text="text", source="English", target="Osmanya")
        )
        self.assertEqual(r.status_code, 422)
        self.assertIn("error", r.json)

    def test_limit(self):
        self.assertEqual(
            self.client.post("/process", json=dict(text="a" * 4001)).status_code, 422
        )

    def test_invalid_type(self):
        self.assertEqual(
            self.client.post("/process", json=dict(text=[1])).status_code, 422
        )

    def test_escape(self):
        r = self.client.post(
            "/process",
            data=dict(
                text="<script>alert(1)</script>",
                source="Somali Latin",
                target="Osmanya",
            ),
        )
        self.assertNotIn(b"<script>", r.data)

    def test_shared_alphabet(self):
        response = self.client.get("/")
        self.assertEqual(response.data.count(b"data-glyph="), 30)
        self.assertIn(b"translator.js", response.data)
