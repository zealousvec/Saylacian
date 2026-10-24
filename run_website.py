# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run a local website separately from the Kivy app."""

from saylacian.website.app import create_app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
