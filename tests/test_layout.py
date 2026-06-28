"""Unit tests for LayoutRenderer (RDL engine)."""
from __future__ import annotations

import pytest
from jinja2 import DictLoader, Environment

from rendux.core.layout import LayoutRenderer, _deep_get


# ── minimal Jinja2 env with stub widget templates ────────────────────────────

def _env(extra: dict[str, str] | None = None) -> Environment:
    templates = {
        "widgets/badge.html":    '<span class="badge">{{ label }}</span>',
        "widgets/stat_card.html": '<div class="stat">{{ label }}:{{ value }}:{{ status|default("") }}</div>',
        "widgets/alert.html":    '<div class="alert-{{ variant }}">{{ message }}</div>',
        "widgets/divider.html":  '<hr class="divider">',
        "widgets/item_list.html": (
            '<ul>{% for i in items|default([]) %}<li>{{ i.title }}</li>{% endfor %}</ul>'
        ),
    }
    if extra:
        templates.update(extra)
    return Environment(loader=DictLoader(templates))


def _renderer(extra: dict[str, str] | None = None) -> LayoutRenderer:
    return LayoutRenderer(_env(extra))


# ── _deep_get ────────────────────────────────────────────────────────────────

def test_deep_get_flat():
    assert _deep_get({"a": 1}, ["a"]) == 1


def test_deep_get_nested():
    assert _deep_get({"a": {"b": {"c": 42}}}, ["a", "b", "c"]) == 42


def test_deep_get_missing_returns_none():
    assert _deep_get({"a": 1}, ["b"]) is None


def test_deep_get_none_root():
    assert _deep_get(None, ["a"]) is None


# ── widget node ──────────────────────────────────────────────────────────────

def test_widget_renders():
    r = _renderer()
    html = r.render([{"widget": "badge", "label": "Active"}], {})
    assert "badge" in html
    assert "Active" in html


def test_widget_literal_params():
    r = _renderer()
    html = r.render([{"widget": "stat_card", "label": "CPU", "value": "82%"}], {})
    assert "CPU" in html
    assert "82%" in html


def test_widget_ctx_param_resolution():
    r = _renderer()
    ctx = {"current_label": "Memory"}
    html = r.render([{"widget": "badge", "label": "$ctx.current_label"}], ctx)
    assert "Memory" in html


def test_widget_nested_ctx_resolution():
    r = _renderer()
    ctx = {"stats": {"cpu": "45%"}}
    html = r.render([{"widget": "badge", "label": "$ctx.stats.cpu"}], ctx)
    assert "45%" in html


def test_widget_missing_ctx_key_renders_none():
    r = _renderer()
    html = r.render([{"widget": "badge", "label": "$ctx.nonexistent"}], {})
    assert "badge" in html   # widget still renders


# ── when: conditional ────────────────────────────────────────────────────────

def test_when_true_renders():
    r = _renderer()
    html = r.render([{"widget": "badge", "label": "X", "when": "$ctx.show"}], {"show": True})
    assert "badge" in html


def test_when_false_suppresses():
    r = _renderer()
    html = r.render([{"widget": "badge", "label": "X", "when": "$ctx.show"}], {"show": False})
    assert html == ""


def test_when_falsy_zero_suppresses():
    r = _renderer()
    html = r.render([{"widget": "badge", "label": "X", "when": "$ctx.count"}], {"count": 0})
    assert html == ""


def test_when_missing_key_suppresses():
    r = _renderer()
    html = r.render([{"widget": "badge", "label": "X", "when": "$ctx.no_such"}], {})
    assert html == ""


# ── each: iteration ──────────────────────────────────────────────────────────

def test_each_iterates():
    r = _renderer()
    ctx = {"tags": [{"label": "alpha"}, {"label": "beta"}, {"label": "gamma"}]}
    html = r.render([{"widget": "badge", "each": "$ctx.tags", "label": "$item.label"}], ctx)
    assert "alpha" in html
    assert "beta" in html
    assert "gamma" in html


def test_each_empty_collection_renders_nothing():
    r = _renderer()
    html = r.render([{"widget": "badge", "each": "$ctx.tags", "label": "$item.label"}], {"tags": []})
    assert html == ""


def test_each_mixed_static_and_item_params():
    r = _renderer()
    ctx = {"services": [{"label": "api"}, {"label": "auth"}]}
    html = r.render([{
        "widget": "stat_card",
        "each":   "$ctx.services",
        "label":  "$item.label",
        "value":  "ok",
    }], ctx)
    assert "api" in html
    assert "auth" in html
    assert html.count("ok") == 2


# ── layout containers ────────────────────────────────────────────────────────

def test_stack_container():
    r = _renderer()
    html = r.render([{
        "type": "stack",
        "children": [
            {"widget": "badge", "label": "A"},
            {"widget": "badge", "label": "B"},
        ],
    }], {})
    assert 'class="layout-stack"' in html
    assert "A" in html and "B" in html


def test_row_container():
    r = _renderer()
    html = r.render([{"type": "row", "children": [{"widget": "badge", "label": "R"}]}], {})
    assert 'class="layout-row"' in html


def test_grid_container():
    r = _renderer()
    html = r.render([{
        "type": "grid", "columns": 3,
        "children": [{"widget": "badge", "label": "G"}],
    }], {})
    assert 'class="layout-grid-3"' in html


def test_grid_auto():
    r = _renderer()
    html = r.render([{"type": "grid", "children": []}], {})
    assert 'class="layout-grid-auto"' in html


def test_stack_gap_sm():
    r = _renderer()
    html = r.render([{"type": "stack", "gap": "sm", "children": []}], {})
    assert 'class="layout-stack-sm"' in html


def test_section_container():
    r = _renderer()
    html = r.render([{
        "type":     "section",
        "heading":  "Health",
        "children": [{"widget": "badge", "label": "ok"}],
    }], {})
    assert "component-section" in html
    assert "Health" in html
    assert "ok" in html


def test_section_description():
    r = _renderer()
    html = r.render([{
        "type":        "section",
        "heading":     "Stats",
        "description": "Live numbers",
        "children":    [],
    }], {})
    assert "Live numbers" in html


# ── shorthands ───────────────────────────────────────────────────────────────

def test_divider_shorthand():
    r = _renderer()
    html = r.render([{"divider": True}], {})
    assert "divider" in html


def test_heading_shorthand():
    r = _renderer()
    html = r.render([{"heading": "Dashboard"}], {})
    assert "<h2" in html
    assert "Dashboard" in html


def test_heading_level_3():
    r = _renderer()
    html = r.render([{"heading": "Sub", "level": 3}], {})
    assert "<h3" in html


# ── list params resolved ─────────────────────────────────────────────────────

def test_list_param_static():
    r = _renderer()
    html = r.render([{
        "widget": "item_list",
        "items": [{"title": "First"}, {"title": "Second"}],
    }], {})
    assert "First" in html
    assert "Second" in html


def test_list_param_ctx_reference():
    r = _renderer()
    ctx = {"todo": [{"title": "Deploy"}, {"title": "Monitor"}]}
    html = r.render([{"widget": "item_list", "items": "$ctx.todo"}], ctx)
    assert "Deploy" in html
    assert "Monitor" in html


# ── multiple nodes ───────────────────────────────────────────────────────────

def test_multiple_top_level_nodes():
    r = _renderer()
    html = r.render([
        {"widget": "badge",  "label": "First"},
        {"widget": "badge",  "label": "Second"},
        {"widget": "badge",  "label": "Third"},
    ], {})
    assert html.count("badge") == 3
    assert "First" in html and "Second" in html and "Third" in html


def test_empty_nodes_list():
    r = _renderer()
    assert r.render([], {}) == ""


def test_none_nodes_list():
    r = _renderer()
    assert r.render(None, {}) == ""  # type: ignore[arg-type]


# ── integration: service reads ops layout ────────────────────────────────────

def test_ops_view_renders_via_http():
    from starlette.testclient import TestClient
    from demo.main import create_app
    client = TestClient(create_app())
    r = client.get("/ops")
    assert r.status_code == 200
    assert "stat" in r.text            # stat_card widgets present
    assert "timeline" in r.text        # timeline widget present
    assert "Operations" in r.text      # title


def test_ops_htmx_returns_partial():
    from starlette.testclient import TestClient
    from demo.main import create_app
    client = TestClient(create_app())
    r = client.get("/ops", headers={"HX-Request": "true"})
    assert r.status_code == 200
    assert "app-shell" not in r.text   # no shell wrapper
    assert "stat" in r.text
