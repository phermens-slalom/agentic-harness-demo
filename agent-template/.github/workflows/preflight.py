"""Statically inspect a candidate checkout using trusted base-revision code."""

from __future__ import annotations

import ast
import json
import os
import sys
import tomllib
from pathlib import Path

import yaml
from sunglasses.engine import SunglassesEngine
from yaml.resolver import BaseResolver

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from agent.security_harness import scan as policy_scan


class UniqueLoader(yaml.SafeLoader):
    pass


def _mapping(loader: UniqueLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    pairs = loader.construct_pairs(node, deep=deep)
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate YAML key")
        result[key] = value
    return result


UniqueLoader.add_constructor(BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def _json_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError("non-finite JSON value")


def _raise_walk_error(error: OSError) -> None:
    raise error


def _inspect_file(path: Path, relative: Path, scanner: SunglassesEngine) -> None:
    try:
        data = path.read_bytes()
        if len(data) > 1_048_576 or b"\0" in data:
            raise ValueError("binary or oversized file")
        text = data.decode("utf-8")
        suffix = path.suffix.lower()
        if suffix == ".py":
            ast.parse(text, filename=str(relative))
        elif suffix in {".yaml", ".yml"}:
            list(yaml.load_all(text, Loader=UniqueLoader))
        elif suffix in {".json", ".ipynb"}:
            json.loads(text, object_pairs_hook=_json_pairs, parse_constant=_invalid_constant)
        elif suffix == ".toml" or path.name == "uv.lock":
            tomllib.loads(text)
        result = scanner.scan(text, channel="file").to_dict()
        if not result["inspection_complete"] or result["threat_found"]:
            raise ValueError("input scan rejected or incomplete")
    except (OSError, UnicodeError, SyntaxError, ValueError, TypeError, yaml.YAMLError) as exc:
        raise ValueError(f"preflight rejected {relative}: {type(exc).__name__}") from exc


def inspect(root: Path) -> None:
    if (root / ".gitleaksignore").exists() or (root / ".gitleaksignore").is_symlink():
        raise ValueError("candidate-controlled .gitleaksignore is not permitted")
    scanner = SunglassesEngine()
    for directory, directories, files in os.walk(root, followlinks=False, onerror=_raise_walk_error):
        base = Path(directory)
        if base == root and ".git" in directories:
            directories.remove(".git")
        for name in sorted(directories + files):
            path = base / name
            if path.is_symlink():
                raise ValueError(f"symbolic link is not permitted: {path.relative_to(root)}")
        for name in sorted(files):
            path = base / name
            _inspect_file(path, path.relative_to(root), scanner)
    report = policy_scan(root)
    if not report.ok:
        raise ValueError("harness policy scan reported findings")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: preflight.py CANDIDATE_CHECKOUT", file=sys.stderr)
        return 2
    try:
        root = Path(sys.argv[1]).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("candidate checkout is not a directory")
        inspect(root)
    except (OSError, ValueError) as exc:
        print(f"Preflight failed: {exc}", file=sys.stderr)
        return 1
    print("Preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
