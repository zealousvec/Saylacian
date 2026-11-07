import json

import pytest

from tools.translation_lab import marian_flores_eval
from tools.translation_lab.marian_flores_eval import _read_checkpoint


def test_marian_checkpoint_pins_adapter_and_repairs_torn_tail(tmp_path):
    path = tmp_path / "predictions.jsonl"
    header = {
        "schema_version": 1,
        "archive_sha256": marian_flores_eval.ARCHIVE_SHA256,
        "experiment_id": "candidate-1",
        "model_fingerprint": {"adapter_sha256": "adapter-hash"},
    }
    row = {"id": "1", "base": "base output", "candidate": "candidate output"}
    path.write_text(
        json.dumps(header) + "\n" + json.dumps(row) + "\n" + '{"id":',
        encoding="utf-8",
    )
    assert _read_checkpoint(path, header, resume=True) == {"1": row}
    assert path.read_text(encoding="utf-8").endswith(json.dumps(row) + "\n")
    with pytest.raises(
        ValueError,
        match="fingerprint changed",
    ):
        _read_checkpoint(
            path,
            {**header, "model_fingerprint": {"adapter_sha256": "changed"}},
            resume=True,
        )
    with pytest.raises(FileExistsError, match="pass --resume"):
        _read_checkpoint(path, header, resume=False)
