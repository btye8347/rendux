"""Strict-mode render tests for LayoutRenderer."""

from __future__ import annotations

import pytest
from jinja2 import DictLoader, Environment

from rendux.core.layout import LayoutConfigError, LayoutRenderer


def _strict_renderer() -> LayoutRenderer:
    env = Environment(
        loader=DictLoader({
            "widgets/stat_card.html": '<div>{{ label }}:{{ value }}</div>',
            "widgets/alert.html": '<div>{{ message }}</div>',
        }),
        autoescape=True,
    )
    return LayoutRenderer(env, strict=True)


def test_strict_raises_on_missing_ctx_path():
    r = _strict_renderer()
    with pytest.raises(LayoutConfigError, match="Unresolved reference"):
        r.render([{"widget": "stat_card", "label": "$ctx.missing", "value": "1"}], {})


def test_strict_allows_falsy_ctx_value():
    r = _strict_renderer()
    html = r.render(
        [{"widget": "alert", "message": "$ctx.msg", "when": "$ctx.flag"}],
        {"msg": "ok", "flag": False},
    )
    assert html == ""


def test_strict_raises_on_unknown_widget_prop():
    r = _strict_renderer()
    with pytest.raises(LayoutConfigError, match="Unknown prop 'labl'"):
        r.render([{"widget": "stat_card", "labl": "CPU", "value": "82%"}], {})


def test_strict_raises_on_unknown_widget():
    r = _strict_renderer()
    with pytest.raises(LayoutConfigError, match="Unknown widget"):
        r.render([{"widget": "not_a_widget", "label": "x", "value": "1"}], {})


def test_strict_raises_on_unknown_container():
    r = _strict_renderer()
    with pytest.raises(LayoutConfigError, match="Unknown container type"):
        r.render([{"type": "carousel", "children": []}], {})


def test_strict_raises_on_item_outside_each():
    r = _strict_renderer()
    with pytest.raises(LayoutConfigError, match="outside each"):
        r.render([{"widget": "stat_card", "label": "$item.label", "value": "1"}], {})


def test_permissive_still_renders_unknown_prop_blank():
    env = Environment(
        loader=DictLoader({
            "widgets/stat_card.html": '<div class="stat-label">{{ label }}</div>',
        }),
        autoescape=True,
    )
    r = LayoutRenderer(env, strict=False)
    html = r.render([{"widget": "stat_card", "labl": "CPU", "value": "82%"}], {})
    assert "CPU" not in html
