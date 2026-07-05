#!/usr/bin/env python3
"""Agent RDL eval harness — lint and strict-render fixture scenarios."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml
from jinja2 import Environment, FileSystemLoader

from rendux.core.layout import LayoutConfigError, LayoutRenderer
from rendux.core.lint_rdl import RdlLinter

FIXTURES_DIR = ROOT / "tests" / "fixtures" / "agent_rdl"


@dataclass
class ScenarioResult:
    name: str
    lint_ok: bool
    strict_ok: bool
    expect: str
    passed: bool
    detail: str


def _load_scenario(path: Path) -> tuple[list, dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    layout = data.get("layout", [])
    context = data.get("context", {})
    return layout if isinstance(layout, list) else [layout], context


def _expect_from_name(path: Path) -> str:
    return "fail" if path.name.startswith("bad_") else "pass"


def run_scenario(path: Path) -> ScenarioResult:
    name = path.stem
    expect = _expect_from_name(path)
    layout, context = _load_scenario(path)

    lint_issues = RdlLinter(strict=True).lint_views_config({
        "views": {"_eval": {"workspace": {"layout": layout}, "data": context}}
    })
    lint_ok = not any(i.level == "error" for i in lint_issues)

    strict_ok = False
    strict_detail = ""
    try:
        env = Environment(
            loader=FileSystemLoader(str(ROOT / "rendux" / "templates")),
            autoescape=True,
        )
        LayoutRenderer(env, strict=True).render(layout, context)
        strict_ok = True
    except LayoutConfigError as exc:
        strict_detail = str(exc)

    ok = (lint_ok and strict_ok) if expect == "pass" else (not lint_ok or not strict_ok)
    detail = strict_detail or ("lint+strict OK" if lint_ok and strict_ok else "lint failed")

    return ScenarioResult(name, lint_ok, strict_ok, expect, ok, detail)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate agent-style RDL fixtures")
    parser.add_argument(
        "--fixtures",
        default=str(FIXTURES_DIR),
        help="Directory of agent RDL YAML fixtures",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    args = parser.parse_args(argv)

    fixture_dir = Path(args.fixtures)
    paths = sorted(fixture_dir.glob("*.yaml"))
    if not paths:
        print(f"no fixtures in {fixture_dir}", file=sys.stderr)
        return 1

    results = [run_scenario(p) for p in paths]
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    if args.json:
        print(json.dumps({
            "total": total,
            "passed": passed,
            "pass_rate": passed / total if total else 0,
            "results": [r.__dict__ for r in results],
        }, indent=2))
    else:
        print(f"Agent RDL eval: {passed}/{total} scenarios passed\n")
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            print(f"  [{status}] {r.name} (expect {r.expect}) — lint={r.lint_ok} strict={r.strict_ok}")
            if not r.passed or r.expect == "fail":
                print(f"         {r.detail}")
        print("\nTop failure modes for bad fixtures:")
        for r in results:
            if r.expect == "fail" and r.detail:
                print(f"  - {r.name}: {r.detail}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
