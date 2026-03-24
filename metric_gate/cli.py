"""CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from metric_gate.compare import compare, load_config, load_json


def main() -> None:
    p = argparse.ArgumentParser(description="Fail if current metrics regress vs baseline.")
    p.add_argument("--baseline", type=Path, required=True, help="Baseline metrics.json")
    p.add_argument("--current", type=Path, required=True, help="Current metrics.json")
    p.add_argument("--config", type=Path, default=None, help="Gate config JSON (optional)")
    args = p.parse_args()

    b = load_json(args.baseline)
    c = load_json(args.current)
    cfg = load_config(args.config)
    violations = compare(b, c, cfg)
    if violations:
        print("metric-regression-gate: FAILED", file=sys.stderr)
        for v in violations:
            print(f"  {v.message}", file=sys.stderr)
        sys.exit(1)
    print("metric-regression-gate: OK", file=sys.stderr)


if __name__ == "__main__":
    main()
