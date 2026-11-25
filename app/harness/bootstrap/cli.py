"""agentic-bootstrap: stage 1 `new`, stage 2 `check`, stage 3 `plan`."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from . import security_harness, template, terraform_plan
from .spec import AgentSpec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="agentic-bootstrap")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new", help="stage 1: render an agent repo from the template")
    n.add_argument("spec", type=Path)
    n.add_argument("dest", type=Path)
    c = sub.add_parser("check", help="stage 2: harness-specific policy checks; non-zero exit on findings")
    c.add_argument("repo", type=Path)
    p = sub.add_parser("plan", help="stage 3: ordered workload PR plan as JSON")
    p.add_argument("spec", type=Path)
    a = ap.parse_args(argv)

    if a.cmd == "new":
        files = template.render(AgentSpec.load(a.spec), a.dest)
        print(f"wrote {len(files)} files to {a.dest}")
    elif a.cmd == "check":
        report = security_harness.scan(a.repo)
        print(report.to_markdown())
        return 0 if report.ok else 1
    else:
        spec = AgentSpec.load(a.spec)
        if problems := spec.validate():
            print("\n".join(problems), file=sys.stderr)
            return 1
        print(json.dumps([asdict(x) for x in terraform_plan.plan_prs(spec)], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
