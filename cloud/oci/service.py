# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small self-hosted translation API for an OCI Always Free VM."""

from __future__ import annotations

import hmac
import json
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

from saylacian.core.translation import translate_meaning

PORT = int(os.environ.get("PORT", "8080"))
SERVICE_TOKEN = os.environ.get("SAYLACIAN_SERVICE_TOKEN", "")
MAX_BODY_BYTES = 20_000
MAX_CONCURRENT_TRANSLATIONS = 2
_translation_slots = threading.BoundedSemaphore(MAX_CONCURRENT_TRANSLATIONS)


class TranslationHandler(BaseHTTPRequestHandler):
    server_version = "SaylacianTranslation/1.0"

    def _send_json(self, status, body):
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if self.path != "/health":
            self._send_json(404, {"error": "not found"})
            return
        self._send_json(200, {"ok": True, "provider": "Saylacian self-hosted models"})

    def do_POST(self):
        if self.path != "/translate":
            self._send_json(404, {"error": "not found"})
            return
        if SERVICE_TOKEN:
            supplied = self.headers.get("Authorization", "")
            expected = f"Bearer {SERVICE_TOKEN}"
            if not hmac.compare_digest(supplied, expected):
                self._send_json(401, {"error": "unauthorized"})
                return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "invalid content length"})
            return
        if length < 1 or length > MAX_BODY_BYTES:
            self._send_json(413, {"error": "request must be between 1 and 20000 bytes"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "request body must be UTF-8 JSON"})
            return
        if not isinstance(payload, dict):
            self._send_json(400, {"error": "request body must be a JSON object"})
            return
        text = payload.get("text")
        source = payload.get("source")
        target = payload.get("target")
        if not all(isinstance(value, str) for value in (text, source, target)):
            self._send_json(400, {"error": "text, source and target must be strings"})
            return
        if not text.strip():
            self._send_json(200, {"translation": "", "warnings": []})
            return
        if len(text) > 4000:
            self._send_json(413, {"error": "maximum 4,000 characters"})
            return
        if not _translation_slots.acquire(timeout=45):
            self._send_json(503, {"error": "translation queue is busy; retry shortly"})
            return
        try:
            result = translate_meaning(
                text,
                source,
                target,
                model_root=PROJECT_ROOT / "models",
                provider_override="offline",
            )
            self._send_json(
                200,
                {
                    "translation": result.text,
                    "warnings": list(result.warnings),
                    "provider": "Saylacian self-hosted models",
                },
            )
        except ValueError as error:
            self._send_json(422, {"error": str(error)})
        except (ImportError, OSError, RuntimeError):
            self._send_json(500, {"error": "translation failed"})
        finally:
            _translation_slots.release()

    def log_message(self, format_string, *args):

        super().log_message(format_string, *args)


class TranslationServer(ThreadingHTTPServer):
    request_queue_size = 64
    daemon_threads = True

    def __init__(self, *args, **kwargs):
        self.request_slots = threading.BoundedSemaphore(16)
        super().__init__(*args, **kwargs)

    def process_request(self, request, client_address):
        if not self.request_slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.request_slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.request_slots.release()


def main():
    if not SERVICE_TOKEN:
        raise SystemExit(
            "Set SAYLACIAN_SERVICE_TOKEN to a long random secret before exposing this API. "
            f"Example: {secrets.token_urlsafe(36)}"
        )
    server = TranslationServer(("0.0.0.0", PORT), TranslationHandler)
    print(f"Saylacian translation API listening on port {PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
