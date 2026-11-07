# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fast comparison/report tests with synthetic references; no model downloads."""

import argparse
import json
from pathlib import Path

import pytest

from tools import compare_offline_models as comparison


def test_sample_rejects_wrong_route_and_blank_reference(tmp_path):
    path = tmp_path / "sample.json"
    for row in [
        {"route": "de-so", "source": "hello", "reference": "salaan"},
        {"route": "en-so", "source": "hello", "reference": " "},
    ]:
        path.write_text(json.dumps([row]))
        with pytest.raises(ValueError):
            comparison.read_sample(path)


def test_private_outputs_cannot_be_written_into_checkout():
    with pytest.raises(ValueError, match="outside"):
        comparison.private_path(comparison.ROOT / "reports")


def test_comparison_scores_identical_examples_and_writes_resources(
    tmp_path, monkeypatch
):
    rows = [{"route": "en-so", "source": "hello", "reference": "salaan saaxiib"}]
    sample = tmp_path / "sample.json"
    sample.write_text(json.dumps(rows))
    output = tmp_path / "output"

    def fake_worker(command, **_kwargs):
        target = Path(command[command.index("--output") + 1])
        target.mkdir(parents=True)
        prediction = "unrelated" if target.name == "installed" else "salaan saaxiib"
        (target / "predictions.jsonl").write_text(
            json.dumps(
                {
                    "index": 0,
                    "example": rows[0],
                    "prediction": prediction,
                    "seconds": 0.5,
                }
            )
            + "\n"
        )
        (target / "resources.json").write_text(
            json.dumps({"peak_process_working_set_bytes": 123})
        )

    monkeypatch.setattr(comparison.subprocess, "run", fake_worker)
    comparison.compare(
        argparse.Namespace(
            sample=sample,
            output=output,
            workspace=tmp_path / "lab",
            python_app=Path("python"),
            python_training=Path("python"),
            experiments=["candidate"],
        )
    )
    report = json.loads((output / "report.json").read_text())
    scores = report["routes"]["en-so"]
    assert scores["candidate"]["chrf++"] == 100
    assert scores["installed"]["chrf++"] < 100
    assert scores["candidate"]["paired_vs_installed"]["candidate_wins"] == 1
    assert scores["candidate"]["mean_seconds"] == 0.5
    assert report["models"]["installed"]["peak_process_working_set_bytes"] == 123
    assert report["automatic_promotion"] is False
    assert (output / "report.md").is_file()
