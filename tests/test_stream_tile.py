"""stream_tile widget + /cameras demo."""

from __future__ import annotations

from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from starlette.testclient import TestClient

from demo.main import create_app
from rendux.core.agent_compile import compile_fragment
from rendux.core.layout import LayoutRenderer
from rendux.core.lint_rdl import lint_views_file
from rendux.views.service import ViewConfigService

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIEWS_PATH = PROJECT_ROOT / "config" / "views.yaml"


def test_cameras_view_passes_strict_lint():
    errors = [i for i in lint_views_file(VIEWS_PATH, strict=True) if i.level == "error"]
    assert errors == [], "\n".join(f"{e.path}: {e.message}" for e in errors)


def test_cameras_http_renders_tiles():
    client = TestClient(create_app())
    response = client.get("/cameras")
    assert response.status_code == 200
    assert "widget-stream-tile" in response.text
    assert "Driveway" in response.text
    assert 'data-kind="video"' in response.text
    assert 'data-kind="iframe"' in response.text
    assert "status-offline" in response.text
    assert "data-rx-stream-refresh" in response.text
    assert 'data-active-view="cameras"' in response.text


def test_stream_tile_strict_render():
    svc = ViewConfigService.from_yaml(VIEWS_PATH)
    ws = svc.resolve_workspace("cameras")
    renderer = LayoutRenderer(
        Environment(
            loader=FileSystemLoader(str(PROJECT_ROOT / "rendux" / "templates")),
            autoescape=True,
        ),
        strict=True,
    )
    html = renderer.render(ws["value"], svc.view_data("cameras"))
    assert "stream-driveway" in html
    assert "Camera offline" in html
    assert "stream-tile-iframe" in html


def test_cameras_fragment_compiles():
    fragment = yaml.safe_load((PROJECT_ROOT / "config" / "cameras_demo.yaml").read_text())
    report = compile_fragment(fragment)
    assert report["ok"] is True, report["errors"]


def test_camera_embed_static_served():
    client = TestClient(create_app())
    response = client.get("/static/demo/camera_embed.html")
    assert response.status_code == 200
    assert "go2rtc" in response.text
