"""Full ops layout conformance — uses real config/views.yaml."""

from __future__ import annotations

from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

from rendux.core.layout import LayoutRenderer, WidgetInvocation
from rendux.core.contracts import normalize_widget_props

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VIEWS_PATH = PROJECT_ROOT / "config" / "views.yaml"

# Expected widget dispatch sequence for views.ops (verified 2026-07-05)
OPS_WIDGET_SEQUENCE = [
    "stat_card", "stat_card", "stat_card", "stat_card",
    "status_grid", "timeline",
    "divider",
    "item_list",
    "alert", "alert",
    "progress_bar", "progress_bar",
]


def _ops_layout_and_ctx() -> tuple[list, dict]:
    views = yaml.safe_load(VIEWS_PATH.read_text(encoding="utf-8"))
    ops = views["views"]["ops"]
    return ops["workspace"]["layout"], ops["data"]


def _renderer() -> LayoutRenderer:
    templates = PROJECT_ROOT / "rendux" / "templates"
    env = Environment(loader=FileSystemLoader(str(templates)), autoescape=True)
    return LayoutRenderer(env)


def test_full_ops_layout_invocation_count_and_sequence():
    layout, ctx = _ops_layout_and_ctx()
    invocations = _renderer().collect_invocations(layout, ctx)
    names = [i.widget for i in invocations]
    assert len(invocations) == 12
    assert names == OPS_WIDGET_SEQUENCE


def test_full_ops_first_stat_card_resolved_params():
    layout, ctx = _ops_layout_and_ctx()
    invocations = _renderer().collect_invocations(layout, ctx)
    first = invocations[0]
    assert first.params["label"] == "Active Services"
    assert first.params["value"] == "24"
    assert first.params["status"] == "ok"


def test_collect_invocations_matches_render_template_params():
    """collect_invocations must agree with params passed to _render_template."""
    layout, ctx = _ops_layout_and_ctx()
    renderer = _renderer()
    rendered: list[WidgetInvocation] = []
    original = renderer._render_template

    def capture(widget: str, render_ctx: dict, extra: dict) -> str:
        safe = normalize_widget_props(widget, extra)
        rendered.append(WidgetInvocation(widget, dict(safe)))
        return original(widget, render_ctx, extra)

    renderer._render_template = capture  # type: ignore[method-assign]
    renderer.render(layout, ctx)

    collected = renderer.collect_invocations(layout, ctx)
    assert [r.widget for r in rendered] == [c.widget for c in collected]
    assert rendered == collected


def test_full_ops_layout_passes_strict_render():
    layout, ctx = _ops_layout_and_ctx()
    renderer = LayoutRenderer(
        Environment(loader=FileSystemLoader(str(PROJECT_ROOT / "rendux" / "templates")), autoescape=True),
        strict=True,
    )
    html = renderer.render(layout, ctx)
    assert "Active Services" in html
    assert "Mail relay unreachable" in html
