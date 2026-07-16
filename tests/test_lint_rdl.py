"""Tests for widget contract registry and RDL linter."""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

from rendux.core.contracts import (
    load_widget_registry,
    list_widget_template_names,
    normalize_widget_props,
)
from rendux.core.lint_rdl import RdlLinter, lint_views_file

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIEWS_PATH = PROJECT_ROOT / "config" / "views.yaml"


def test_registry_matches_template_directory():
    registry = load_widget_registry()
    templates = list_widget_template_names()
    assert set(registry) == templates
    for name, contract in registry.items():
        assert contract["name"] == name


def test_verified_ops_widgets_are_contracted():
    registry = load_widget_registry()
    ops_widgets = {
        "stat_card", "status_grid", "timeline", "item_list", "alert", "progress_bar"
    }
    for name in ops_widgets:
        assert registry[name]["status"] == "verified"


def test_track_a_admin_widgets_are_verified():
    registry = load_widget_registry()
    admin_widgets = {
        "badge", "button", "card", "panel", "empty_state", "kv_table",
        "status_badge", "divider", "form", "data_table", "modal", "tabs",
        "pagination",
    }
    for name in admin_widgets:
        assert registry[name]["status"] == "verified", name
        assert "props" in registry[name], name


def test_ops_views_yaml_passes_strict_lint():
    issues = lint_views_file(VIEWS_PATH, strict=True)
    errors = [i for i in issues if i.level == "error"]
    assert errors == [], "\n".join(f"{e.path}: {e.message}" for e in errors)


def test_lint_fails_on_unknown_prop():
    config = yaml.safe_load(VIEWS_PATH.read_text(encoding="utf-8"))
    broken = copy.deepcopy(config)
    layout = broken["views"]["ops"]["workspace"]["layout"]
    stat_node = layout[0]["children"][0]
    stat_node["labl"] = stat_node.pop("label")

    issues = RdlLinter(strict=True).lint_views_config(broken)
    errors = [i for i in issues if i.level == "error"]
    assert any("unknown prop 'labl'" in e.message for e in errors)


def test_lint_warns_on_deprecated_alias():
    config = yaml.safe_load(VIEWS_PATH.read_text(encoding="utf-8"))
    broken = copy.deepcopy(config)
    layout = broken["views"]["ops"]["workspace"]["layout"]
    stat_node = layout[0]["children"][0]
    stat_node["title"] = stat_node.pop("label")

    issues = RdlLinter(strict=True).lint_views_config(broken)
    warnings = [i for i in issues if i.level == "warning"]
    assert any("deprecated alias 'title'" in w.message for w in warnings)


def test_normalize_widget_props_maps_title_to_label():
    normalized = normalize_widget_props("stat_card", {"title": "CPU", "value": "82%"})
    assert normalized == {"label": "CPU", "value": "82%"}


def test_lint_cli_entrypoint_runs():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "lint_rdl.py"), str(VIEWS_PATH)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
