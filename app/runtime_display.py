# SPDX-License-Identifier: AGPL-3.0-or-later
"""Initialize lazy Kivy scaling before third-party canvas rules use dp()."""

import math


def initialize_display_metrics(metrics):
    """Keep valid platform scaling; fall back only for invalid measurements."""
    for name, fallback in (("dpi", 96.0), ("density", 1.0), ("fontscale", 1.0)):
        value = getattr(metrics, name)
        if not math.isfinite(value) or value <= 0:
            setattr(metrics, name, fallback)
    return metrics.dpi, metrics.density, metrics.fontscale
