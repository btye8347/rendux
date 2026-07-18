"""Agent verified-catalog builder."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from rendux.core.contracts import load_widget_registry

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = PROJECT_ROOT / "contracts" / "catalog.verified.json"
BUILDER = PROJECT_ROOT / "scripts" / "build_agent_catalog.py"


def test_verified_contracts_have_descriptions():
    registry = load_widget_registry()
    verified = [c for c in registry.values() if c.get("status") == "verified"]
    assert verified
    for contract in verified:
        assert contract.get("description"), contract["name"]


def test_build_agent_catalog_matches_verified_set():
    result = subprocess.run(
        [sys.executable, str(BUILDER)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "wrote" in result.stdout

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    registry = load_widget_registry()
    verified_names = {n for n, c in registry.items() if c.get("status") == "verified"}
    catalog_names = {w["name"] for w in catalog["widgets"]}

    assert catalog["widget_count"] == len(verified_names)
    assert catalog_names == verified_names
    for widget in catalog["widgets"]:
        assert widget["description"]
        assert "props" in widget
