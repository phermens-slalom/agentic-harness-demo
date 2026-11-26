"""Fail-closed, owner-configured coverage check for the generated agent."""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import yaml


def coverage_threshold(path: Path) -> float:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise TypeError("eval thresholds must be a mapping")
    value = config.get("coverage")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("coverage threshold must be a percentage from 80 to 100")
    if not math.isfinite(value) or not 80 <= value <= 100:
        raise ValueError("coverage threshold must be a finite percentage from 80 to 100")
    return float(value)


def main() -> int:
    try:
        threshold = coverage_threshold(Path("evals/thresholds.yaml"))
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(f"Coverage configuration error: {exc}", file=sys.stderr)
        return 2
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--cov=agent",
            "--cov-report=term-missing",
            f"--cov-fail-under={threshold}",
        ],
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
