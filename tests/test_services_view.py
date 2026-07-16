"""Application use-case: /services admin catalog view."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from starlette.testclient import TestClient

from demo.main import create_app
from rendux.core.layout import LayoutRenderer
from rendux.core.lint_rdl import lint_views_file
from rendux.views.service import ViewConfigService

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIEWS_PATH = PROJECT_ROOT / "config" / "views.yaml"


def test_services_view_passes_strict_lint():
    errors = [i for i in lint_views_file(VIEWS_PATH, strict=True) if i.level == "error"]
    assert errors == [], "\n".join(f"{e.path}: {e.message}" for e in errors)


def test_services_http_renders_catalog():
    client = TestClient(create_app())
    response = client.get("/services")
    assert response.status_code == 200
    assert "Service catalog" in response.text
    assert "api-gateway" in response.text
    assert "widget-data-table" in response.text
    assert "widget-kv-table" in response.text
    assert "widget-form" in response.text


def test_services_strict_render():
    svc = ViewConfigService.from_yaml(VIEWS_PATH)
    ws = svc.resolve_workspace("services")
    renderer = LayoutRenderer(
        Environment(
            loader=FileSystemLoader(str(PROJECT_ROOT / "rendux" / "templates")),
            autoescape=True,
        ),
        strict=True,
    )
    html = renderer.render(ws["value"], svc.view_data("services"))
    assert "Desired replicas" in html
    assert "Restart api-gateway?" in html
