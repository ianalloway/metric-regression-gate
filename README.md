# metric-regression-gate

[![CI](https://github.com/ianalloway/metric-regression-gate/actions/workflows/ci.yml/badge.svg)](https://github.com/ianalloway/metric-regression-gate/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Problem:** Model PRs merge with silent eval drift unless you **enforce** “not worse than `main`” on a small metrics file.

**Solution:** **`metric-gate`** compares two JSON objects (baseline vs current). Each metric has **`direction`** (`higher` or `lower` is better) and **`tolerance`**. Violations → **exit code 1** (CI red).

Default rules (no config): `brier` (lower, +0.03 slack) and `overall_accuracy` (higher, −0.03 slack). Pass **`examples/gate.config.json`** to add dotted paths like `clv_summary.mean_clv_cents`.

```bash
pip install -e .
metric-gate --baseline metrics.main.json --current metrics.json
metric-gate --baseline metrics.main.json --current metrics.json --config examples/gate.config.json
```

## GitHub Actions (composite)

In your repo workflow:

```yaml
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Baseline metrics from main
        run: git show origin/main:metrics.json > metrics.main.json
      - name: Regression gate
        uses: ianalloway/metric-regression-gate@main
        with:
          baseline-file: metrics.main.json
          current-file: metrics.json
          # config-file: scripts/gate.config.json
```

`metrics.json` must be produced by an earlier step (training/eval job).

## Non-goals

- **No** automatic training — you supply both JSON files.
- **No** nested CI for multi-model grids — extend config JSON if needed.

## License

MIT
