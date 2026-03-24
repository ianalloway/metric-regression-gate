"""Core comparison logic."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from metric_gate.paths import get_path

DEFAULT_CONFIG: dict[str, Any] = {
    "metrics": {
        "brier": {"path": "brier", "direction": "lower", "tolerance": 0.03},
        "overall_accuracy": {"path": "overall_accuracy", "direction": "higher", "tolerance": 0.03},
    }
}


@dataclass
class Violation:
    metric: str
    baseline: float
    current: float
    message: str


def load_json(p: Path) -> dict[str, Any]:
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSON root must be object")
    return data


def load_config(p: Path | None) -> dict[str, Any]:
    if p is None:
        return json.loads(json.dumps(DEFAULT_CONFIG))
    raw = json.loads(p.read_text(encoding="utf-8"))
    if "metrics" not in raw:
        raise ValueError("config must contain 'metrics' object")
    return raw


def compare(
    baseline: dict[str, Any],
    current: dict[str, Any],
    config: dict[str, Any],
) -> list[Violation]:
    violations: list[Violation] = []
    metrics_cfg = config.get("metrics", {})
    for name, spec in metrics_cfg.items():
        if not isinstance(spec, dict):
            continue
        path = str(spec.get("path", name))
        direction = str(spec.get("direction", "higher"))
        tolerance = float(spec.get("tolerance", 0.01))
        b_val = float(get_path(baseline, path))
        c_val = float(get_path(current, path))
        if direction == "lower":
            # higher is worse; allow small increase
            if c_val > b_val + tolerance:
                violations.append(
                    Violation(
                        name,
                        b_val,
                        c_val,
                        f"{name} ({path}): worse for lower-is-better — baseline {b_val}, "
                        f"current {c_val}, max allowed {b_val + tolerance}",
                    )
                )
        elif direction == "higher":
            if c_val < b_val - tolerance:
                violations.append(
                    Violation(
                        name,
                        b_val,
                        c_val,
                        f"{name} ({path}): worse for higher-is-better — baseline {b_val}, "
                        f"current {c_val}, min allowed {b_val - tolerance}",
                    )
                )
        else:
            raise ValueError(f"unknown direction for {name}: {direction}")
    return violations
