"""HTMX live polling on /ops layout fragments."""

from __future__ import annotations

from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from rendux.core.layout import LayoutRenderer, find_layout_node
from rendux.views.service import ViewConfigService

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_ops_layout_has_poll_attributes():
    from starlette.testclient import TestClient

    from demo.main import create_app

    client = TestClient(create_app())
    response = client.get("/ops")
    assert response.status_code == 200
    html = response.text
    assert 'id="ops-kpis"' in html
    assert 'hx-get="/partials/ops/ops-kpis"' in html
    assert 'hx-trigger="every 15s"' in html
    assert 'id="ops-timeline"' in html
    assert 'hx-get="/partials/ops/ops-timeline"' in html


def test_ops_kpis_partial_returns_stat_cards():
    from starlette.testclient import TestClient

    from demo.main import create_app

    client = TestClient(create_app())
    response = client.get("/partials/ops/ops-kpis")
    assert response.status_code == 200
    assert "widget-stat-card" in response.text
    assert "live @" in response.text
    assert "hx-trigger" not in response.text  # inner swap only


def test_ops_timeline_partial_returns_live_event():
    from starlette.testclient import TestClient

    from demo.main import create_app

    client = TestClient(create_app())
    response = client.get("/partials/ops/ops-timeline")
    assert response.status_code == 200
    assert "widget-timeline" in response.text
    assert "Live refresh" in response.text


def test_ops_partial_unknown_fragment_404():
    from starlette.testclient import TestClient

    from demo.main import create_app

    client = TestClient(create_app())
    response = client.get("/partials/ops/does-not-exist")
    assert response.status_code == 404


def test_render_fragment_matches_container_children():
    svc = ViewConfigService.from_yaml(PROJECT_ROOT / "config" / "views.yaml")
    ws = svc.resolve_workspace("ops")
    ctx = svc.view_data("ops")
    renderer = LayoutRenderer(
        Environment(loader=FileSystemLoader(PROJECT_ROOT / "rendux" / "templates"), autoescape=True),
    )
    node = find_layout_node(ws["value"], "ops-kpis")
    assert node is not None
    fragment_html = renderer.render_fragment(ws["value"], "ops-kpis", ctx)
    full_html = renderer.render(node.get("children", []), ctx)
    assert fragment_html == full_html
