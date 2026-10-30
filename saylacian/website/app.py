# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate Flask website using the same local language core as Kivy."""

from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request

from saylacian.core.language_detection import detect_language
from saylacian.core.script_info import osmanya_letters
from saylacian.core.translation import translate_meaning
from saylacian.core.transliteration import detect_script
from saylacian.core.transliteration import transliterate


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 24000

    @app.context_processor
    def alphabet_reference():
        return {"alphabet": osmanya_letters()}

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; form-action 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def index():
        return render_template("index.html", result=None, error=None, values={})

    @app.post("/process")
    def process():
        values = request.get_json(silent=True) if request.is_json else request.form
        if not isinstance(values, dict) and not hasattr(values, "get"):
            return jsonify(error="Expected an object."), 400
        text = values.get("text", "")
        source = values.get("source", "Somali Latin")
        target = values.get("target", "Osmanya")
        mode = values.get("mode", "transliterate")
        result = None
        error = None
        status = 200
        try:
            if not all(isinstance(x, str) for x in [text, source, target, mode]):
                raise ValueError("Text, source, target and mode must be strings.")
            if len(text) > 4000:
                raise ValueError("Maximum 4,000 characters.")
            if mode not in {"transliterate", "meaning"}:
                raise ValueError("Unknown mode.")
            if source == "Detect language/script":
                detected_script, _ = detect_script(text)
                if mode == "meaning" and detected_script:
                    raise ValueError(
                        "Osmanya script detected; script recognition is not "
                        "meaning translation."
                    )
                if detected_script:
                    source = detected_script
                    confidence = None
                else:
                    source, confidence, message = detect_language(text)
                    if source is None:
                        raise ValueError(message)
                    if mode == "transliterate" and source != "Somali Latin":
                        raise ValueError(
                            f"Detected {source} ({confidence:.0%} confidence), "
                            "but only Somali Latin ↔ Osmanya writing conversion "
                            "is implemented."
                        )
            result = (
                translate_meaning(text, source, target)
                if mode == "meaning"
                else transliterate(text, source, target)
            )
            if (
                source != values.get("source")
                and values.get("source") == "Detect language/script"
            ):
                note = (
                    f"Detected {source} ({confidence:.0%} confidence). "
                    if confidence is not None
                    else f"Detected {source} script. "
                )
                from saylacian.core.transliteration import Conversion

                result = Conversion(result.text, (note, *result.warnings))
        except ValueError as problem:
            error = str(problem)
            status = 422
        if request.is_json:
            return (
                jsonify(error=error)
                if error
                else jsonify(text=result.text, warnings=result.warnings, status="alpha")
            ), status
        return (
            render_template("index.html", result=result, error=error, values=values),
            status,
        )

    return app
