"""Pin config merge precedence as executable spec."""

from __future__ import annotations

from copy import deepcopy

from rendux.views.service import ViewConfigService, deep_merge


def test_deep_merge_nested_dicts():
    base = {"shell": {"id": "default", "theme": "dark"}, "extra": "keep"}
    override = {"shell": {"template": "custom.html"}, "label": "Home"}
    merged = deep_merge(base, override)
    assert merged["shell"]["id"] == "default"
    assert merged["shell"]["theme"] == "dark"
    assert merged["shell"]["template"] == "custom.html"
    assert merged["extra"] == "keep"
    assert merged["label"] == "Home"


def test_shell_defaults_view_overrides_template():
    config = {
        "version": "0.1.0",
        "shell": {"id": "default", "template": "chrome/shells/default.html"},
        "views": {
            "home": {
                "label": "Home",
                "route": "/",
                "template": "chrome/shells/blank.html",
                "workspace": {"template": "workspaces/home.html"},
            }
        },
    }
    shell = ViewConfigService(config).get_shell_view("home")
    assert shell["template"] == "chrome/shells/blank.html"
    assert shell["shell_id"] == "default"
    assert shell["active_view"]["id"] == "home"


def test_shell_id_preserved_when_view_has_no_shell_keys():
    config = {
        "version": "0.1.0",
        "shell": {"id": "default", "template": "chrome/shells/default.html"},
        "views": {"ops": {"label": "Ops", "route": "/ops", "workspace": {"layout": []}}},
    }
    shell = ViewConfigService(config).get_shell_view("ops")
    assert shell["shell_id"] == "default"
    assert shell["template"] == "chrome/shells/default.html"


def test_surface_defaults_applied_to_declared_surface():
    config = {
        "version": "0.1.0",
        "shell": {"id": "default"},
        "views": {"home": {"label": "Home", "route": "/", "workspace": {}}},
        "surfaces": {
            "defaults": {
                "open_mode": "controlled_wrapper",
                "frame_mode": "allow_declared",
                "fallback": "external_link",
            },
            "metrics": {
                "label": "Metrics",
                "type": "controlled_surface",
                "params": {"service": "api"},
            },
        },
    }
    svc = ViewConfigService(config)
    surface = svc.get_surface("metrics")
    assert surface["frame_mode"] == "allow_declared"
    assert surface["fallback"] == "external_link"
    assert surface["params"]["service"] == "api"


def test_surface_declared_values_override_defaults():
    config = {
        "version": "0.1.0",
        "shell": {"id": "default"},
        "views": {"home": {"label": "Home", "route": "/", "workspace": {}}},
        "surfaces": {
            "defaults": {"frame_mode": "allow_declared", "fallback": "external_link"},
            "external": {
                "label": "External",
                "frame_mode": "external_only",
                "fallback": "blocked",
            },
        },
    }
    surface = ViewConfigService(config).get_surface("external")
    assert surface["frame_mode"] == "external_only"
    assert surface["fallback"] == "blocked"


def test_view_data_static_yaml_block():
    config = {
        "version": "0.1.0",
        "shell": {"id": "default"},
        "views": {
            "ops": {
                "label": "Ops",
                "route": "/ops",
                "data": {"kpi": [{"label": "CPU", "value": "1"}]},
                "workspace": {"layout": []},
            }
        },
    }
    svc = ViewConfigService(config)
    assert svc.view_data("ops") == {"kpi": [{"label": "CPU", "value": "1"}]}
    assert svc.view_data("home") == {}


def test_render_context_precedence_route_over_yaml_data():
    """Mirrors demo/main.py: globals < view_data < view_ctx."""
    template_globals = {"url_for": lambda x: "/", "theme_list": ["light"]}
    view_data = {"kpi": [{"label": "Static", "value": "1"}], "flag": True}
    view_ctx = {"kpi": [{"label": "Dynamic", "value": "99"}], "extra": "live"}

    render_ctx = {**template_globals, **view_data, **view_ctx}

    assert render_ctx["kpi"][0]["label"] == "Dynamic"
    assert render_ctx["flag"] is True
    assert render_ctx["extra"] == "live"
    assert "theme_list" in render_ctx


def test_resolve_workspace_layout_beats_template():
    config = {
        "version": "0.1.0",
        "shell": {"id": "default"},
        "views": {
            "ops": {
                "label": "Ops",
                "route": "/ops",
                "workspace": {
                    "template": "workspaces/ignored.html",
                    "layout": [{"widget": "alert", "message": "hi"}],
                },
            }
        },
    }
    ws = ViewConfigService(config).resolve_workspace("ops")
    assert ws["kind"] == "layout"
    assert ws["value"][0]["widget"] == "alert"
