"""Agent compile loop for RDL view fragments."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

from rendux.core.agent_compile import compile_fragment

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = PROJECT_ROOT / "examples" / "agent"
COMPILE = PROJECT_ROOT / "scripts" / "agent_compile.py"


def test_compile_kpi_example_ok():
    report = compile_fragment(yaml.safe_load((EXAMPLES / "kpi_dashboard.yaml").read_text()))
    assert report["ok"] is True
    assert report["errors"] == []
    assert report["strict_render_ok"] is True


def test_compile_service_admin_example_ok():
    report = compile_fragment(yaml.safe_load((EXAMPLES / "service_admin.yaml").read_text()))
    assert report["ok"] is True, report["errors"]


def test_compile_ops_alerts_example_ok():
    report = compile_fragment(yaml.safe_load((EXAMPLES / "ops_alerts.yaml").read_text()))
    assert report["ok"] is True, report["errors"]


def test_compile_rejects_unknown_prop():
    fragment = {
        "data": {"kpi": [{"label": "CPU", "value": "1"}]},
        "workspace": {
            "layout": [
                {
                    "widget": "stat_card",
                    "each": "$ctx.kpi",
                    "labl": "$item.label",
                    "value": "$item.value",
                }
            ]
        },
    }
    report = compile_fragment(fragment)
    assert report["ok"] is False
    assert any("labl" in e["message"] for e in report["errors"])


def test_compile_cli_exits_zero_on_good_example():
    result = subprocess.run(
        [sys.executable, str(COMPILE), str(EXAMPLES / "kpi_dashboard.yaml")],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True


def test_compile_cli_exits_one_on_bad_fragment(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "data: {}\nworkspace:\n  layout:\n    - widget: stat_card\n      labl: x\n      value: y\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(COMPILE), str(bad)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
