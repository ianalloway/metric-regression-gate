from __future__ import annotations

import json
from pathlib import Path

import pytest

from metric_gate.compare import compare, load_config, load_json
from metric_gate.cli import main


def base_metrics() -> dict:
    return {
        "model_name": "x",
        "overall_accuracy": 0.68,
        "brier": 0.20,
        "clv_summary": {"mean_clv_cents": 2.0},
    }


def test_gate_ok_identical(tmp_path: Path):
    p = tmp_path / "m.json"
    p.write_text(json.dumps(base_metrics()), encoding="utf-8")
    cfg = load_config(None)
    assert compare(load_json(p), load_json(p), cfg) == []


def test_gate_brier_regression(tmp_path: Path):
    b = tmp_path / "b.json"
    c = tmp_path / "c.json"
    good = base_metrics()
    bad = {**good, "brier": 0.30}
    b.write_text(json.dumps(good), encoding="utf-8")
    c.write_text(json.dumps(bad), encoding="utf-8")
    v = compare(load_json(b), load_json(c), load_config(None))
    assert len(v) == 1
    assert "brier" in v[0].message.lower()


def test_gate_accuracy_drop(tmp_path: Path):
    b = tmp_path / "b.json"
    c = tmp_path / "c.json"
    good = base_metrics()
    bad = {**good, "overall_accuracy": 0.60}
    b.write_text(json.dumps(good), encoding="utf-8")
    c.write_text(json.dumps(bad), encoding="utf-8")
    v = compare(load_json(b), load_json(c), load_config(None))
    assert len(v) == 1


def test_cli_passes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    b = tmp_path / "b.json"
    c = tmp_path / "c.json"
    b.write_text(json.dumps(base_metrics()), encoding="utf-8")
    c.write_text(json.dumps(base_metrics()), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["metric-gate", "--baseline", str(b), "--current", str(c)])
    main()


def test_cli_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    b = tmp_path / "b.json"
    c = tmp_path / "c.json"
    g = base_metrics()
    b.write_text(json.dumps(g), encoding="utf-8")
    c.write_text(json.dumps({**g, "brier": 0.99}), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["metric-gate", "--baseline", str(b), "--current", str(c)])
    with pytest.raises(SystemExit) as e:
        main()
    assert e.value.code == 1
