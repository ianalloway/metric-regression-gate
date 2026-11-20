"""Core comparison logic."""

from __future__ import annotations

import json
import math
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
        raise ValueError("expected a JSON object at the root")  # noqa: TRY004 - invalid file contents
    return data


def load_config(p: Path | None) -> dict[str, Any]:
    if p is None:
        return json.loads(json.dumps(DEFAULT_CONFIG))
    raw = load_json(p)
    if "metrics" not in raw:
        raise ValueError("config must contain 'metrics' object")
    return raw


def finite_number(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{name} must be a finite number") from error
    if isinstance(value, bool) or not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def compare(
    baseline: dict[str, Any],
    current: dict[str, Any],
    config: dict[str, Any],
) -> list[Violation]:
    violations: list[Violation] = []
    metrics_cfg = config.get("metrics", {})
    if not isinstance(metrics_cfg, dict) or not metrics_cfg:
        raise ValueError("configure at least one metric")
    for name, spec in metrics_cfg.items():
        if not isinstance(spec, dict):
            raise ValueError(f"invalid configuration for metric {name}")  # noqa: TRY004 - invalid configuration
        path = str(spec.get("path", name))
        direction = str(spec.get("direction", "higher"))
        tolerance = finite_number(spec.get("tolerance", 0.01), f"{name} tolerance")
        if tolerance < 0:
            raise ValueError(f"{name} tolerance must be non-negative")
        b_val = finite_number(get_path(baseline, path), f"baseline {path}")
        c_val = finite_number(get_path(current, path), f"current {path}")
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
