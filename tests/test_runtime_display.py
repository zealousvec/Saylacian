# SPDX-License-Identifier: AGPL-3.0-or-later

from types import SimpleNamespace

import pytest

from app.runtime_display import initialize_display_metrics


def test_valid_display_scaling_is_preserved():
    metrics = SimpleNamespace(dpi=120.0, density=1.25, fontscale=1.4)
    assert initialize_display_metrics(metrics) == (120.0, 1.25, 1.4)


@pytest.mark.parametrize("invalid", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_platform_measurements_get_positive_defaults(invalid):
    metrics = SimpleNamespace(dpi=invalid, density=invalid, fontscale=invalid)
    assert initialize_display_metrics(metrics) == (96.0, 1.0, 1.0)
