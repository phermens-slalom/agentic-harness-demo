#!/usr/bin/env bash
# macOS/Linux/Git Bash entry point: scripts/e2e.sh [--keep] [--live-evals] [--from-stage N]
set -euo pipefail
cd "$(dirname "$0")/.."
exec "${PYTHON:-python3}" scripts/e2e.py "$@"
