import io
import json

import pytest

from tools.translation_lab import tico19_french_eval
from tools.translation_lab.tico19_french_eval import ARCHIVE_SHA256
from tools.translation_lab.tico19_french_eval import _read_checkpoint
from tools.translation_lab.tico19_french_eval import parse_french_dev

HEADER = (
    "sourceLang\ttargetLang\tsourceString\ttargetString\tstringID\turl\t"
    "license\ttranslator_ID\n"
)


def _tsv(rows):
    return (HEADER + "".join("\t".join(row) + "\n" for row in rows)).encode()


def test_parse_french_dev_retains_row_rights_and_translator():
    rows = parse_french_dev(
        io.BytesIO(
            _tsv(
                [
                    [
                        "en",
                        "fr",
                        "Hello there",
                        "Bonjour",
                        "id-1",
                        "https://x",
                        "public",
                        "42",
                    ]
                ]
            )
        )
    )
    assert rows == [
        {
            "id": "id-1",
            "english": "Hello there",
            "french": "Bonjour",
            "source_url": "https://x",
            "license": "public",
            "translator_id": "42",
        }
    ]


@pytest.mark.parametrize(
    ("row", "message"),
    [
        (
            ["en", "so", "Hello", "Salaam", "id-1", "", "public", "42"],
            "Unexpected language pair",
        ),
        (
            ["en", "fr", "Hello", "Bonjour", "id-1", "", "", "42"],
            "Empty required field license",
        ),
    ],
)
def test_parse_french_dev_rejects_wrong_pair_and_missing_rights(row, message):
    with pytest.raises(ValueError, match=message):
        parse_french_dev(io.BytesIO(_tsv([row])))


def test_parse_french_dev_rejects_duplicate_ids():
    row = ["en", "fr", "Hello", "Bonjour", "same", "", "public", "42"]
    with pytest.raises(ValueError, match="Duplicate TICO-19 string ID"):
        parse_french_dev(io.BytesIO(_tsv([row, row])))


def test_resume_requires_matching_archive_and_model_fingerprint(tmp_path):
    path = tmp_path / "predictions.jsonl"
    fingerprint = {"en-fr": {"model_sha256": "model"}}
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "archive_sha256": ARCHIVE_SHA256,
                "model_fingerprint": fingerprint,
            }
        )
        + "\n"
        + json.dumps(
            {"id": "1", "english_to_french": "Bonjour", "french_to_english": "Hello"}
        )
        + "\n",
        encoding="utf-8",
    )
    assert _read_checkpoint(path, fingerprint, resume=True) == {
        "1": {
            "id": "1",
            "english_to_french": "Bonjour",
            "french_to_english": "Hello",
        }
    }
    with pytest.raises(ValueError, match="fingerprint changed"):
        _read_checkpoint(path, {"en-fr": {"model_sha256": "changed"}}, resume=True)
    with pytest.raises(FileExistsError, match="pass --resume"):
        _read_checkpoint(path, fingerprint, resume=False)


def test_resume_truncates_only_a_torn_final_checkpoint_row(tmp_path):
    path = tmp_path / "predictions.jsonl"
    fingerprint = {"en-fr": {"model_sha256": "model"}}
    header = {
        "schema_version": 1,
        "archive_sha256": ARCHIVE_SHA256,
        "model_fingerprint": fingerprint,
    }
    complete = {
        "id": "1",
        "english_to_french": "Bonjour",
        "french_to_english": "Hello",
    }
    path.write_text(
        json.dumps(header) + "\n" + json.dumps(complete) + '\n{"id"',
        encoding="utf-8",
    )
    assert _read_checkpoint(path, fingerprint, resume=True) == {"1": complete}
    assert path.read_text(encoding="utf-8").endswith(json.dumps(complete) + "\n")


def test_evaluation_resumes_from_last_complete_aligned_row(tmp_path, monkeypatch):
    from saylacian.core import translation

    rows = [
        {"id": str(i), "english": f"English {i}", "french": f"French {i}"}
        for i in range(3)
    ]
    monkeypatch.setattr(tico19_french_eval, "load_french_dev", lambda _path: rows)
    monkeypatch.setattr(
        tico19_french_eval, "_model_fingerprint", lambda: {"test": "hash"}
    )
    monkeypatch.setattr(
        tico19_french_eval, "_score", lambda _refs, preds: {"n": len(preds)}
    )
    calls = []
    should_fail = True

    def translate(text, source, target, **kwargs):
        nonlocal should_fail
        calls.append((text, source, target))
        if text == "English 1" and should_fail:
            should_fail = False
            raise RuntimeError("interrupted")
        return type("Result", (), {"text": f"{target}:{text}"})()

    monkeypatch.setattr(translation, "translate_meaning", translate)
    with pytest.raises(RuntimeError, match="interrupted"):
        tico19_french_eval.evaluate_french_dev(
            tmp_path, archive_path=tmp_path / "pinned.zip", run_id="resume-run"
        )
    assert len(calls) == 3
    result = tico19_french_eval.evaluate_french_dev(
        tmp_path,
        archive_path=tmp_path / "pinned.zip",
        run_id="resume-run",
        resume=True,
    )
    assert result["rows"] == 3
    assert result["metrics"] == {"en-fr": {"n": 3}, "fr-en": {"n": 3}}
    assert len(calls) == 7


def test_route_matrix_scores_direct_and_english_pivot_routes(tmp_path, monkeypatch):
    from tools.translation_lab import tico19_benchmark

    french = [{"id": "1", "english": "Hello", "french": "Bonjour"}]
    somali = [{"record_id": "1", "source_text": "Hello", "target_text": "Salaan"}]
    monkeypatch.setattr(tico19_french_eval, "load_french_dev", lambda _path: french)
    monkeypatch.setattr(tico19_benchmark, "load_split", lambda *_args: somali)
    monkeypatch.setattr(
        tico19_french_eval,
        "_model_fingerprint",
        lambda _routes: {"models": "verified"},
    )
    scored = []

    def score(references, predictions):
        scored.append((references, predictions))
        return {"rows": len(predictions)}

    monkeypatch.setattr(tico19_french_eval, "_score", score)
    monkeypatch.setattr(
        tico19_french_eval,
        "_translate_many_direct",
        lambda texts, source, target: [f"{source}>{target}:{text}" for text in texts],
    )
    result = tico19_french_eval.evaluate_somali_and_pivot_dev(
        tmp_path, archive_path=tmp_path / "archive.zip", run_id="all-routes"
    )
    assert result["matched_language_ids"] == 1
    assert set(result["metrics"]) == {"en-so", "so-en", "fr-so", "so-fr"}
    assert len(scored) == 4
    assert scored[0] == (["Salaan"], ["English>Somali Latin:Hello"])
