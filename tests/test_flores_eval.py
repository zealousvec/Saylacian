import json
import tarfile

import pytest

from tools.translation_lab import flores_eval
from tools.translation_lab.flores_eval import _read_checkpoint
from tools.translation_lab.flores_eval import parse_flores_lines


def test_parse_flores_lines_preserves_text_and_requires_exact_row_count(monkeypatch):
    monkeypatch.setattr(flores_eval, "ROW_COUNT", 2)
    assert parse_flores_lines(" Héllo \nline two\n".encode(), "english") == [
        " Héllo ",
        "line two",
    ]
    with pytest.raises(ValueError, match="Expected 2"):
        parse_flores_lines(b"one\n", "english")
    with pytest.raises(ValueError, match="Unsupported FLORES language"):
        parse_flores_lines(b"one", "arabic")


def test_loader_reads_only_the_three_expected_devtest_members(tmp_path, monkeypatch):
    path = tmp_path / "official.tar"
    members = {
        member: (f"{language} sentence {index}\n" for index in range(1012))
        for language, member in flores_eval.LANGUAGE_FILES.items()
    }
    with tarfile.open(path, "w") as archive:
        for member, lines in members.items():
            content = "".join(lines).encode("utf-8")
            info = tarfile.TarInfo(member)
            info.size = len(content)
            import io

            archive.addfile(info, io.BytesIO(content))
        hidden = b"DO NOT LOAD HIDDEN TEST ROWS\n"
        info = tarfile.TarInfo("./flores200_dataset/test/eng_Latn.test")
        info.size = len(hidden)
        import io

        archive.addfile(info, io.BytesIO(hidden))

    monkeypatch.setattr(flores_eval, "ARCHIVE_BYTES", path.stat().st_size)
    monkeypatch.setattr(flores_eval, "ARCHIVE_SHA256", flores_eval.sha256_file(path))
    original_open = tarfile.open
    read_members = []

    class ObservedTar:
        def __init__(self, tar):
            self.tar = tar

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.tar.__exit__(*args)

        def getmember(self, name):
            return self.tar.getmember(name)

        def extractfile(self, member):
            read_members.append(member.name)
            return self.tar.extractfile(member)

    monkeypatch.setattr(
        flores_eval.tarfile,
        "open",
        lambda *args, **kwargs: ObservedTar(original_open(*args, **kwargs)),
    )
    rows = flores_eval.load_flores_devtest(path)
    assert len(rows) == 1012
    assert rows[0]["id"] == "1"
    assert len(read_members) == 3
    assert set(read_members) == set(flores_eval.LANGUAGE_FILES.values())
    assert "DO NOT LOAD HIDDEN TEST ROWS" not in str(rows)


def test_resume_requires_matching_archive_and_model_fingerprint(tmp_path):
    path = tmp_path / "predictions.jsonl"
    fingerprint = {"models": "sha256"}
    complete = {
        "id": "1",
        **{route: f"prediction:{route}" for route in flores_eval.ROUTES},
    }
    header = {
        "schema_version": flores_eval.SCHEMA_VERSION,
        "archive_sha256": flores_eval.ARCHIVE_SHA256,
        "model_fingerprint": fingerprint,
    }
    path.write_text(
        json.dumps(header) + "\n" + json.dumps(complete) + "\n" + '{"id":',
        encoding="utf-8",
    )
    assert _read_checkpoint(path, fingerprint, resume=True) == {"1": complete}
    assert path.read_text(encoding="utf-8").endswith(json.dumps(complete) + "\n")
    with pytest.raises(ValueError, match="fingerprint changed"):
        _read_checkpoint(path, {"models": "different"}, resume=True)
    with pytest.raises(FileExistsError, match="pass --resume"):
        _read_checkpoint(path, fingerprint, resume=False)


def test_flores_evaluator_scores_all_routes_and_resumes(tmp_path, monkeypatch):
    rows = [
        {
            "id": str(i),
            "english": f"English {i}",
            "french": f"French {i}",
            "somali": f"Somali {i}",
        }
        for i in range(25)
    ]
    monkeypatch.setattr(flores_eval, "load_flores_devtest", lambda _path: rows)
    monkeypatch.setattr(
        "tools.translation_lab.tico19_french_eval._model_fingerprint",
        lambda _routes: {"models": "verified"},
    )
    scored = []
    monkeypatch.setattr(
        flores_eval,
        "_score",
        lambda refs, preds: scored.append((refs, preds)) or {"rows": len(preds)},
    )
    calls = []
    fail_once = True

    def translate_many(texts, source, target):
        nonlocal fail_once
        calls.append((tuple(texts), source, target))
        if len(calls) == 7 and fail_once:
            fail_once = False
            raise RuntimeError("interrupted")
        return [f"{source}>{target}:{text}" for text in texts]

    monkeypatch.setattr(
        "tools.translation_lab.tico19_french_eval._translate_many_direct",
        translate_many,
    )
    with pytest.raises(RuntimeError, match="interrupted"):
        flores_eval.evaluate_flores_devtest(
            tmp_path, archive_path=tmp_path / "pinned.tar", run_id="route-check"
        )
    first_run_calls = len(calls)
    result = flores_eval.evaluate_flores_devtest(
        tmp_path,
        archive_path=tmp_path / "pinned.tar",
        run_id="route-check",
        resume=True,
    )
    assert result["rows"] == 25
    assert result["hidden_test_split_loaded"] is False
    assert set(result["metrics"]) == set(flores_eval.ROUTES)
    assert len(scored) == len(flores_eval.ROUTES)
    assert result["training_or_promotion"] is False
    assert first_run_calls == 7
    assert len(calls) == 13
