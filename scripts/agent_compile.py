#!/usr/bin/env python3
"""CLI: compile an RDL view fragment for agent authoring loops.

Accepts a YAML file (or stdin) shaped as a view include::

    data: { ... }
    workspace:
      layout: [ ... ]

Runs strict lint + strict render. Prints a JSON report to stdout.
Exit 0 on success, 1 on failure.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml

from rendux.core.agent_compile import compile_fragment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile RDL view fragment for agents")
    parser.add_argument("path", nargs="?", help="YAML fragment path (default: stdin)")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    args = parser.parse_args(argv)

    text = Path(args.path).read_text(encoding="utf-8") if args.path else sys.stdin.read()

    try:
        data = yaml.safe_load(text)
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise ValueError("fragment root must be a mapping")
    except (ValueError, yaml.YAMLError) as exc:
        report = {
            "ok": False,
            "errors": [{"path": "<root>", "message": f"parse error: {exc}"}],
            "warnings": [],
            "notes": [],
            "strict_render_ok": False,
        }
        print(json.dumps(report, indent=2 if args.pretty else None))
        return 1

    report = compile_fragment(data)
    print(json.dumps(report, indent=2 if args.pretty else None))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
