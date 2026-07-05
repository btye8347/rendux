"""Full components showcase conformance — uses real config/views.yaml include."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from rendux.core.contracts import normalize_widget_props
from rendux.core.layout import LayoutRenderer, WidgetInvocation
from rendux.views.service import ViewConfigService

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VIEWS_PATH = PROJECT_ROOT / "config" / "views.yaml"

# Verified 2026-07-05 — generated config/components_showcase.yaml
COMPONENTS_INVOCATION_COUNT = 107
COMPONENTS_UNIQUE_WIDGETS = 34

# Inline at render time — not dispatched via _render_template (see layout.py)
_NON_TEMPLATE_WIDGETS = frozenset({"_heading"})


def _template_invocations(invocations: list[WidgetInvocation]) -> list[WidgetInvocation]:
    return [i for i in invocations if i.widget not in _NON_TEMPLATE_WIDGETS]


def _components_layout_and_ctx() -> tuple[list, dict]:
    svc = ViewConfigService.from_yaml(VIEWS_PATH)
    ws = svc.resolve_workspace("components")
    assert ws["kind"] == "layout"
    return ws["value"], svc.view_data("components")


def _renderer(*, strict: bool = False) -> LayoutRenderer:
    templates = PROJECT_ROOT / "rendux" / "templates"
    env = Environment(loader=FileSystemLoader(str(templates)), autoescape=True)
    return LayoutRenderer(env, strict=strict)


def test_components_showcase_invocation_count():
    layout, ctx = _components_layout_and_ctx()
    invocations = _renderer().collect_invocations(layout, ctx)
    assert len(invocations) == COMPONENTS_INVOCATION_COUNT
    assert len({i.widget for i in invocations}) == COMPONENTS_UNIQUE_WIDGETS


def test_components_showcase_starts_with_heading_and_buttons():
    layout, ctx = _components_layout_and_ctx()
    names = [i.widget for i in _renderer().collect_invocations(layout, ctx)]
    assert names[:9] == [
        "_heading",
        "button",
        "button",
        "button",
        "button",
        "button",
        "button",
        "button",
        "button",
    ]


def test_collect_invocations_matches_render_template_params():
    layout, ctx = _components_layout_and_ctx()
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
    assert [r.widget for r in _template_invocations(rendered)] == [
        c.widget for c in _template_invocations(collected)
    ]
    assert _template_invocations(rendered) == _template_invocations(collected)


def test_components_showcase_renders_key_sections():
    layout, ctx = _components_layout_and_ctx()
    html = _renderer().render(layout, ctx)
    assert "Widget Library — Tier 1" in html
    assert "Tier 2 — HTMX-assisted" in html
    assert "Widget Library — Tier 3" in html
