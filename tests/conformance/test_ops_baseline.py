"""Conformance tests — assert resolved widget invocations, not HTML."""

from __future__ import annotations

from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

from rendux.core.layout import LayoutRenderer, WidgetInvocation

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _renderer() -> LayoutRenderer:
    templates = PROJECT_ROOT / "rendux" / "templates"
    env = Environment(loader=FileSystemLoader(str(templates)), autoescape=True)
    return LayoutRenderer(env)


def _load_fixture(name: str) -> tuple[list, dict]:
    data = yaml.safe_load((FIXTURES / name).read_text(encoding="utf-8"))
    return data["layout"], data["context"]


def test_stat_card_each_resolves_kpi_row():
    layout, ctx = _load_fixture("kpi_row.yaml")
    invocations = _renderer().collect_invocations(layout, ctx)

    assert len(invocations) == 4
    assert all(i.widget == "stat_card" for i in invocations)
    assert invocations[0].params == {
        "label": "Active Services",
        "value": "24",
        "status": "ok",
        "trend": "+2 today",
        "subtitle": None,
    }
    assert invocations[1].params["label"] == "Open Alerts"
    assert invocations[1].params["status"] == "warn"


def test_status_grid_and_timeline_invocations():
    layout, ctx = _load_fixture("health_activity.yaml")
    invocations = _renderer().collect_invocations(layout, ctx)

    assert invocations[0] == WidgetInvocation(
        "status_grid",
        {
            "title": "Service Health",
            "items": ctx["service_health"],
        },
    )
    assert invocations[1].widget == "timeline"
    assert invocations[1].params["events"] == ctx["recent_events"]
    assert len(invocations[1].params["events"]) == 2


def test_alert_and_progress_bar_stack():
    layout, ctx = _load_fixture("alerts_stack.yaml")
    invocations = _renderer().collect_invocations(layout, ctx)

    assert invocations[0].widget == "alert"
    assert invocations[0].params["variant"] == "warn"
    assert invocations[2].widget == "progress_bar"
    assert invocations[2].params["value"] == 73
    assert invocations[2].params["variant"] == "warn"


def test_when_guard_suppresses_node():
    layout = [
        {"widget": "alert", "when": False, "message": "hidden"},
        {"widget": "alert", "message": "visible"},
    ]
    invocations = _renderer().collect_invocations(layout, {})
    assert len(invocations) == 1
    assert invocations[0].params["message"] == "visible"
