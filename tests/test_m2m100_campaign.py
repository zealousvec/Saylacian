from __future__ import annotations

import json

import pytest

from tools.translation_lab.config import LabConfig
from tools.translation_lab.m2m100_campaign import _can_resume_experiment
from tools.translation_lab.m2m100_campaign import _evaluate_improvement
from tools.translation_lab.m2m100_campaign import _rate_id
from tools.translation_lab.m2m100_campaign import _validate_campaign_id
from tools.translation_lab.m2m100_campaign import run_campaign
from tools.translation_lab.m2m100_training import _thermal_callback_type


def _evaluation(*, en_so_low: float = 0.2) -> dict:
    return {
        "metrics": {
            route: {
                "delta": {"bleu": 0.1, "chrf_plus_plus": 0.5},
                "paired_sentence_chrf": {
                    "mean_delta_bootstrap_95_ci": [lower, lower + 0.4]
                },
            }
            for route, lower in (("en-so", en_so_low), ("so-en", 0.3))
        }
    }


def test_campaign_gate_requires_both_directions_to_improve():
    accepted, details = _evaluate_improvement(_evaluation())
    assert accepted is True
    assert details["en-so"]["passes"] is True
    assert details["so-en"]["passes"] is True

    accepted, details = _evaluate_improvement(_evaluation(en_so_low=0))
    assert accepted is False
    assert details["en-so"]["passes"] is False


def test_campaign_id_is_path_safe_and_learning_rates_are_named():
    _validate_campaign_id("m2m100-lr-sweep-01")
    assert _rate_id(5e-5) == "5e-05"
    with pytest.raises(ValueError, match="path-safe"):
        _validate_campaign_id("../escape")


def test_resume_requires_existing_experiment_metadata(tmp_path):
    experiment_id = "pilot-1e-04"
    assert _can_resume_experiment(tmp_path, experiment_id, True) is False
    metadata = tmp_path / "experiments" / experiment_id / "experiment.json"
    metadata.parent.mkdir(parents=True)
    metadata.write_text("{}", encoding="utf-8")
    assert _can_resume_experiment(tmp_path, experiment_id, True) is True
    assert _can_resume_experiment(tmp_path, experiment_id, False) is False


def test_thermal_callback_saves_and_stops_when_limit_or_telemetry_fails():
    class BaseCallback:
        pass

    class State:
        global_step = 10

    class Control:
        should_save = False
        should_training_stop = False

    hot_callback = _thermal_callback_type(BaseCallback, 82, lambda: 82)()
    hot_control = Control()
    hot_callback.on_step_end(None, State(), hot_control)
    assert hot_control.should_save is True
    assert hot_control.should_training_stop is True
    assert "82°C" in hot_callback.stop_reason

    def no_telemetry():
        raise RuntimeError("telemetry unavailable")

    guarded_callback = _thermal_callback_type(BaseCallback, 82, no_telemetry)()
    guarded_control = Control()
    guarded_callback.on_step_end(None, State(), guarded_control)
    assert guarded_control.should_save is True
    assert guarded_control.should_training_stop is True


def test_dry_run_describes_bounded_campaign_without_writing(tmp_path):
    result = run_campaign(
        tmp_path,
        LabConfig(training_enabled=True, max_runtime_hours=8),
        campaign_id="dry-run",
        model_dir=tmp_path / "model",
        dry_run=True,
    )
    assert result["status"] == "DRY_RUN"
    assert len(result["plan"]["pilot_learning_rates"]) == 3
    assert result["plan"]["full_candidate_epochs"] == 1
    assert not (tmp_path / "campaigns").exists()


def test_campaign_runs_pilots_then_one_full_candidate_and_dev_gate(
    tmp_path, monkeypatch
):
    from tools.translation_lab import m2m100_campaign
    from tools.translation_lab import m2m100_training
    from tools.translation_lab import resources

    monkeypatch.setattr(
        m2m100_training,
        "_prepared_data",
        lambda *_args, **_kwargs: (
            {
                "dataset_revision": "rev1",
                "split_sha256": {"train.jsonl": "train", "validation.jsonl": "valid"},
            },
            [{"source_text": "Hi", "target_text": "Salaam"}],
            [{"source_text": "Bye", "target_text": "Nabad"}],
        ),
    )
    monkeypatch.setattr(
        resources,
        "gpu_preflight",
        lambda **_kwargs: {"max_process_fraction": 0.65},
    )
    evaluation_calls = []

    def evaluate(_workspace, **kwargs):
        evaluation_calls.append(kwargs["experiment_id"])
        report = _evaluation()
        output_path = kwargs["output_path"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report), encoding="utf-8")
        return report

    monkeypatch.setattr(m2m100_campaign, "_evaluate_isolated", evaluate)
    archive = tmp_path / "cache" / "data" / "tico19" / "tico19-testset-2021-02-26.zip"
    archive.parent.mkdir(parents=True)
    archive.write_bytes(b"pinned in this mocked test")

    calls = []

    def train(_workspace, **kwargs):
        calls.append(kwargs)
        loss_by_rate = {5e-5: 1.2, 1e-4: 0.8, 2e-4: 1.4}
        result = {
            "status": "TRAINED_RESEARCH_CANDIDATE",
            "validation_loss": loss_by_rate.get(kwargs["learning_rate"], 0.7),
            "completed_steps": kwargs.get("max_steps") or 9_856,
            "planned_steps": kwargs.get("max_steps") or 9_857,
            "elapsed_seconds": 10,
        }
        path = (
            tmp_path / "experiments" / kwargs["experiment_id"] / "training-report.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result), encoding="utf-8")
        return result

    monkeypatch.setattr(m2m100_campaign, "_train_isolated", train)
    config = LabConfig(
        approved_source_ids=(
            "google-smol-en-so",
            "opus-infopankki-en-so",
            "opus-paracrawl-en-so",
        ),
        training_enabled=True,
        max_runtime_hours=8,
    )
    result = run_campaign(
        tmp_path,
        config,
        campaign_id="test-campaign",
        model_dir=tmp_path / "model",
        pilot_steps=50,
        max_hours=8,
    )

    assert result["status"] == "COMPLETED"
    assert result["winner_learning_rate"] == 1e-4
    assert result["best_verified_candidate"] == "test-campaign-full-1e-04"
    assert len(calls) == 4
    assert sum(call.get("max_steps") is not None for call in calls) == 3
    assert calls[-1].get("max_steps") is None
    assert len(evaluation_calls) == 4
    assert (
        "all pilots and the full candidate" in result["plan"]["independent_evaluation"]
    )
    assert all(
        item["passes_improvement_gate"] for item in result["pilot_evaluations"].values()
    )
