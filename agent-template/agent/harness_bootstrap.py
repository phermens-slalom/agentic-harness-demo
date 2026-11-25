"""The generated agent repo's local agentic-bootstrap check command."""

from __future__ import annotations

import argparse
from pathlib import Path

from .security_harness import scan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentic-bootstrap")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="run harness policy checks")
    check.add_argument("repo", type=Path)
    args = parser.parse_args(argv)
    report = scan(args.repo)
    print(report.to_markdown(), end="")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
