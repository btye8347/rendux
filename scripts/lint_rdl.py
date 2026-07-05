#!/usr/bin/env python3
"""CLI entry point for RDL layout linting."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rendux.core.lint_rdl import RdlLinter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint RDL layout trees in views.yaml")
    parser.add_argument(
        "config",
        nargs="?",
        default="config/views.yaml",
        help="Path to views config (default: config/views.yaml)",
    )
    parser.add_argument(
        "--permissive",
        action="store_true",
        help="Treat unknown props as warnings instead of errors",
    )
    args = parser.parse_args(argv)

    path = Path(args.config)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    linter = RdlLinter(strict=not args.permissive)
    issues = linter.lint_views_file(path)

    for issue in issues:
        print(f"{issue.level}: {issue.path}: {issue.message}")

    if linter.has_errors():
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
